#!/usr/bin/env python3
"""
monitor_resources.py — muestreador de recursos del CONTENEDOR (cgroup v2).

Se ejecuta DENTRO del contenedor. Lee cgroup v2, no /proc global: dentro de
Docker, /proc/stat y /proc/meminfo muestran el host. Al leer el cgroup se
captura ademas todo el arbol de procesos de GAMA (gama-headless.sh lanza un
java hijo; vigilar solo el PID del wrapper mediria el shell, no la JVM).

Las marcas de tiempo usan CLOCK_MONOTONIC, que es el mismo reloj que en el
host (Docker no usa time namespaces por defecto): eso permite el join exacto
con energy_timeseries.csv de monitor_energy.py.

Uso desde el lanzador:
    GAMA_PID=$!
    python3 monitor_resources.py --outdir "$BASE_DIR/MONITOR" \
        --results-dir "$RESULTS" --watch-pid "$GAMA_PID" \
        --cores "$HPC_CORES" --label sol1 &
    MONITOR_PID=$!
    wait $GAMA_PID
    kill -TERM $MONITOR_PID; wait $MONITOR_PID
"""

import argparse
import csv
import json
import os
import signal
import sys
import time
from pathlib import Path

CG = Path("/sys/fs/cgroup")
_stop = False


def _on_signal(signum, frame):
    global _stop
    _stop = True


# --------------------------------------------------------------------------- #
# Lectores de cgroup v2 (degradacion limpia si falta algun fichero)
# --------------------------------------------------------------------------- #
def read_cpu_stat():
    out = {"usage_usec": None, "user_usec": None, "system_usec": None}
    try:
        for line in (CG / "cpu.stat").read_text().splitlines():
            k, _, v = line.partition(" ")
            if k in out:
                out[k] = int(v)
    except (OSError, ValueError):
        pass
    return out


def read_int(name):
    try:
        return int((CG / name).read_text().strip())
    except (OSError, ValueError):
        return None


def read_io_stat():
    """Suma rbytes/wbytes sobre todos los dispositivos."""
    r = w = rios = wios = 0
    found = False
    try:
        for line in (CG / "io.stat").read_text().splitlines():
            fields = line.split()[1:]
            for f in fields:
                k, _, v = f.partition("=")
                try:
                    v = int(v)
                except ValueError:
                    continue
                found = True
                if k == "rbytes":
                    r += v
                elif k == "wbytes":
                    w += v
                elif k == "rios":
                    rios += v
                elif k == "wios":
                    wios += v
    except OSError:
        return None
    return {"rbytes": r, "wbytes": w, "rios": rios, "wios": wios} if found else None


def count_completed(results_dir, tick_wall, pattern="*.csv", settle=2.0):
    """Cuenta CSV terminados.

    Con HPC_CORES replicas concurrentes es casi seguro pillar ficheros a medio
    escribir. Se exige tamano no nulo y mtime anterior a (tick - settle), lo
    que descarta los que se estan escribiendo ahora mismo. Si GAMA escribe a
    .tmp y renombra, este guardado sobra pero no estorba.
    """
    if results_dir is None or not results_dir.is_dir():
        return None
    n = 0
    cutoff = tick_wall - settle
    try:
        for p in results_dir.rglob(pattern):
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_size > 0 and st.st_mtime < cutoff:
                n += 1
    except OSError:
        return None
    return n


def pid_alive(pid):
    if pid is None:
        return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def host_metadata():
    model = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {
        "cpu_model": model,
        "cpu_count_visible": os.cpu_count(),
        "cgroup_v2": (CG / "cgroup.controllers").exists(),
        "memory_peak_available": (CG / "memory.peak").exists(),
        "affinity": sorted(os.sched_getaffinity(0)),
    }


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--results-dir", type=Path)
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--watch-pid", type=int,
                    help="Autoterminarse si este PID desaparece (red de seguridad)")
    ap.add_argument("--cores", type=int, default=None,
                    help="HPC_CORES: normaliza cpu_pct_alloc. Si se omite se usa "
                         "el tamano de la mascara de afinidad.")
    ap.add_argument("--label", default="run")
    ap.add_argument("--pattern", default="*.csv")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    meta = host_metadata()
    if not meta["cgroup_v2"]:
        print("[monitor_resources] ERROR: cgroup v2 no detectado.", file=sys.stderr)
        sys.exit(2)

    cores = args.cores or len(meta["affinity"]) or 1

    ts_path = args.outdir / "monitor_timeseries.csv"
    header = [
        "t_mono", "t_wall", "dt_s",
        "usage_usec", "user_usec", "system_usec",
        "cpu_pct_core",   # % de UN nucleo: delta_usage / delta_t * 100
        "cpu_pct_alloc",  # el anterior dividido por --cores
        "memory_current", "memory_swap",
        "io_rbytes", "io_wbytes", "io_rios", "io_wios",
        "replicas_done",
    ]

    prev_usage = None
    prev_mono = None
    peak_cur = 0
    max_pct_core = 0.0
    n = 0
    replicas_last = None

    t0_mono = time.monotonic()
    t0_wall = time.time()
    io_first = None
    cpu_first = read_cpu_stat()

    with ts_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)

        tick = 0
        while not _stop:
            now_mono = time.monotonic()
            now_wall = time.time()
            dt = None if prev_mono is None else now_mono - prev_mono

            cpu = read_cpu_stat()
            mem_cur = read_int("memory.current")
            mem_swap = read_int("memory.swap.current")
            io = read_io_stat()
            if io_first is None and io is not None:
                io_first = io
            done = count_completed(args.results_dir, now_wall, args.pattern)
            if done is not None:
                replicas_last = done

            if mem_cur:
                peak_cur = max(peak_cur, mem_cur)

            # el primer sample no tiene delta: se descarta
            if dt and dt > 0 and prev_usage is not None and cpu["usage_usec"] is not None:
                d_usage = cpu["usage_usec"] - prev_usage
                pct_core = (d_usage / 1e6) / dt * 100.0
                max_pct_core = max(max_pct_core, pct_core)
                pct_core_s = f"{pct_core:.2f}"
                pct_alloc_s = f"{pct_core / cores:.2f}"
            else:
                pct_core_s = pct_alloc_s = ""

            w.writerow([
                f"{now_mono:.6f}", f"{now_wall:.6f}",
                "" if dt is None else f"{dt:.6f}",
                cpu["usage_usec"], cpu["user_usec"], cpu["system_usec"],
                pct_core_s, pct_alloc_s,
                mem_cur, mem_swap,
                io["rbytes"] if io else "", io["wbytes"] if io else "",
                io["rios"] if io else "", io["wios"] if io else "",
                "" if done is None else done,
            ])
            fh.flush()

            prev_usage = cpu["usage_usec"]
            prev_mono = now_mono
            n += 1
            tick += 1

            if not pid_alive(args.watch_pid):
                break

            target = t0_mono + tick * args.interval
            slp = target - time.monotonic()
            if slp > 0:
                time.sleep(slp)

    elapsed = time.monotonic() - t0_mono
    cpu_end = read_cpu_stat()
    io_end = read_io_stat()

    def _d(a, b, k):
        if not a or not b or a.get(k) is None or b.get(k) is None:
            return None
        return b[k] - a[k]

    cpu_time_s = _d(cpu_first, cpu_end, "usage_usec")
    cpu_time_s = cpu_time_s / 1e6 if cpu_time_s is not None else None

    # memory.peak es exacto (kernel >= 5.19); el maximo muestreado se conserva
    # como comprobacion cruzada, pero a 2 s pierde picos transitorios de GC.
    mem_peak = read_int("memory.peak")

    summary = {
        "mode": "run",
        "label": args.label,
        "duration_s": round(elapsed, 3),
        "samples": n,
        "interval_s": args.interval,
        "t0_mono": t0_mono,
        "t0_wall": t0_wall,
        "cores_assumed": cores,
        "cpu_time_s": None if cpu_time_s is None else round(cpu_time_s, 3),
        "cpu_user_s": (lambda v: None if v is None else round(v / 1e6, 3))(
            _d(cpu_first, cpu_end, "user_usec")),
        "cpu_system_s": (lambda v: None if v is None else round(v / 1e6, 3))(
            _d(cpu_first, cpu_end, "system_usec")),
        "cpu_pct_core_mean": (
            None if cpu_time_s is None or elapsed <= 0
            else round(cpu_time_s / elapsed * 100.0, 2)),
        "cpu_pct_core_max": round(max_pct_core, 2),
        "cpu_pct_alloc_mean": (
            None if cpu_time_s is None or elapsed <= 0
            else round(cpu_time_s / elapsed * 100.0 / cores, 2)),
        "memory_peak_bytes": mem_peak,
        "memory_peak_sampled_bytes": peak_cur,
        "memory_peak_gb": None if mem_peak is None else round(mem_peak / 1024**3, 3),
        "io_read_bytes": _d(io_first, io_end, "rbytes"),
        "io_write_bytes": _d(io_first, io_end, "wbytes"),
        "io_available": io_end is not None,
        "replicas_done": replicas_last,
        "replicas_per_hour": (
            None if not replicas_last or elapsed <= 0
            else round(replicas_last / (elapsed / 3600.0), 2)),
        "cpu_s_per_replica": (
            None if not replicas_last or cpu_time_s is None
            else round(cpu_time_s / replicas_last, 4)),
        "host": meta,
        "timeseries": str(ts_path),
    }

    out = args.outdir / "monitor_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"[monitor_resources] summary -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()