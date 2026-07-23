#!/usr/bin/env python3
"""
monitor_energy.py — muestreador de energia (RAPL), temperatura y frecuencia.

Se ejecuta EN EL HOST, como root (energy_uj requiere privilegios desde la
mitigacion de Platypus). Escribe una serie temporal con marcas de
CLOCK_MONOTONIC, que es el reloj comun con el contenedor (Docker no usa
time namespaces por defecto), lo que permite el join a posteriori con la
serie de cgroup producida por monitor_resources.py.

Modos:
  --baseline SEGUNDOS   Mide el reposo del host y escribe baseline.json.
                        Sirve tambien para VERIFICAR que dominios RAPL
                        incrementan realmente (psys suele estar expuesto
                        pero estatico en portatiles).
  (por defecto)         Muestrea hasta recibir SIGTERM/SIGINT y vuelca
                        energy_timeseries.csv + energy_summary.json.

Uso tipico:
  sudo ./monitor_energy.py --outdir ./MONITOR --baseline 120
  sudo ./monitor_energy.py --outdir ./MONITOR --baseline-file ./MONITOR/baseline.json &
  MON=$!
  ... lanzar el batch ...
  kill -TERM $MON; wait $MON
"""

import argparse
import csv
import json
import os
import platform
import signal
import sys
import time
from pathlib import Path

POWERCAP = Path("/sys/class/powercap")
HWMON = Path("/sys/class/hwmon")
CPUFREQ = Path("/sys/devices/system/cpu")

_stop = False


def _on_signal(signum, frame):
    global _stop
    _stop = True


# --------------------------------------------------------------------------- #
# Descubrimiento de dominios RAPL
# --------------------------------------------------------------------------- #
def discover_rapl():
    """Devuelve {etiqueta: {path, max_uj}} para cada dominio legible.

    Se ignora intel-rapl-mmio: es una interfaz alternativa al MISMO contador
    de package, y sumarla supondria doble contabilidad.
    """
    domains = {}
    if not POWERCAP.is_dir():
        return domains

    for p in sorted(POWERCAP.glob("intel-rapl:*")):
        if "mmio" in p.name:
            continue
        try:
            name = (p / "name").read_text().strip()
            max_uj = int((p / "max_energy_range_uj").read_text().strip())
            int((p / "energy_uj").read_text().strip())  # sonda de permisos
        except (OSError, ValueError):
            continue

        parts = p.name.split(":")
        if len(parts) == 3:  # subdominio intel-rapl:X:Y
            try:
                parent = (POWERCAP / f"intel-rapl:{parts[1]}" / "name").read_text().strip()
                label = f"{parent}-{name}"
            except OSError:
                label = name
        else:
            label = name

        domains[label] = {"path": p, "max_uj": max_uj}
    return domains


def read_energy(domain):
    try:
        return int((domain["path"] / "energy_uj").read_text().strip())
    except (OSError, ValueError):
        return None


def delta_energy(prev, now, max_uj):
    """Delta con gestion de wraparound.

    Con max_energy_range_uj ~262 kJ y ~45 W sostenidos el contador da la
    vuelta cada ~1.6 h: en un batch largo el wrap es camino normal, no
    caso borde.
    """
    if prev is None or now is None:
        return None
    d = now - prev
    if d < 0:
        d += max_uj
    return d


# --------------------------------------------------------------------------- #
# Limites RAPL (PL1/PL2) — hay que releerlos: el EC/firmware de muchos
# portatiles los reescribe periodicamente.
# --------------------------------------------------------------------------- #
def read_constraints(domains):
    out = {}
    for label, d in domains.items():
        for i in (0, 1):
            try:
                name = (d["path"] / f"constraint_{i}_name").read_text().strip()
                uw = int((d["path"] / f"constraint_{i}_power_limit_uw").read_text().strip())
                out[f"{label}:{name}_w"] = uw / 1e6
            except (OSError, ValueError):
                continue
    return out


# --------------------------------------------------------------------------- #
# Temperatura y frecuencia
# --------------------------------------------------------------------------- #
def discover_coretemp():
    """Localiza el sensor de paquete de coretemp."""
    for h in sorted(HWMON.glob("hwmon*")):
        try:
            if (h / "name").read_text().strip() != "coretemp":
                continue
        except OSError:
            continue
        for lbl in sorted(h.glob("temp*_label")):
            try:
                if "package" in lbl.read_text().strip().lower():
                    return h / lbl.name.replace("_label", "_input")
            except OSError:
                continue
    return None


def read_temp(path):
    if path is None:
        return None
    try:
        return int(path.read_text().strip()) / 1000.0
    except (OSError, ValueError):
        return None


def read_freqs(cpus):
    """Frecuencia media (MHz) sobre el conjunto de CPUs indicado."""
    vals = []
    for c in cpus:
        f = CPUFREQ / f"cpu{c}" / "cpufreq" / "scaling_cur_freq"
        try:
            vals.append(int(f.read_text().strip()) / 1000.0)
        except (OSError, ValueError):
            continue
    return sum(vals) / len(vals) if vals else None


def parse_cpu_list(spec):
    """'0,2,4-6' -> [0, 2, 4, 5, 6]"""
    out = []
    if not spec:
        return out
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return sorted(set(out))


# --------------------------------------------------------------------------- #
# Metadatos del host
# --------------------------------------------------------------------------- #
def host_metadata():
    model = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass

    governor = None
    try:
        governor = (CPUFREQ / "cpufreq/policy0/scaling_governor").read_text().strip()
    except OSError:
        pass

    no_turbo = None
    try:
        no_turbo = int((CPUFREQ / "intel_pstate/no_turbo").read_text().strip())
    except (OSError, ValueError):
        pass

    mem_total_kb = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                mem_total_kb = int(line.split()[1])
                break
    except (OSError, ValueError, IndexError):
        pass

    return {
        "cpu_model": model,
        "cpu_count": os.cpu_count(),
        "mem_total_gb": round(mem_total_kb / 1024 / 1024, 2) if mem_total_kb else None,
        "kernel": platform.release(),
        "scaling_governor": governor,
        "no_turbo": no_turbo,
    }


# --------------------------------------------------------------------------- #
# Bucle de muestreo
# --------------------------------------------------------------------------- #
def sample_loop(domains, interval, outdir, duration=None, pcores=None, ecores=None):
    coretemp = discover_coretemp()
    labels = sorted(domains.keys())

    ts_path = outdir / "energy_timeseries.csv"
    header = ["t_mono", "t_wall", "dt_s"]
    for lb in labels:
        header += [f"{lb}_energy_uj_raw", f"{lb}_delta_uj", f"{lb}_power_w"]
    header += ["temp_pkg_c", "freq_p_mhz", "freq_e_mhz"]

    prev_raw = {lb: None for lb in labels}
    prev_mono = None
    acc = {lb: 0 for lb in labels}
    peak_w = {lb: 0.0 for lb in labels}
    peak_temp = None
    n = 0

    t0_mono = time.monotonic()
    t0_wall = time.time()

    with ts_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)

        tick = 0
        while not _stop:
            now_mono = time.monotonic()
            now_wall = time.time()
            dt = None if prev_mono is None else now_mono - prev_mono

            row = [f"{now_mono:.6f}", f"{now_wall:.6f}",
                   "" if dt is None else f"{dt:.6f}"]

            for lb in labels:
                raw = read_energy(domains[lb])
                d = delta_energy(prev_raw[lb], raw, domains[lb]["max_uj"])
                # el primer sample no tiene delta: se descarta
                if d is not None and dt and dt > 0:
                    pw = (d / 1e6) / dt
                    acc[lb] += d
                    peak_w[lb] = max(peak_w[lb], pw)
                    row += [raw, d, f"{pw:.3f}"]
                else:
                    row += [raw, "", ""]
                prev_raw[lb] = raw

            t = read_temp(coretemp)
            if t is not None:
                peak_temp = t if peak_temp is None else max(peak_temp, t)
            row += ["" if t is None else f"{t:.1f}",
                    _fmt(read_freqs(pcores or [])),
                    _fmt(read_freqs(ecores or []))]

            w.writerow(row)
            fh.flush()

            prev_mono = now_mono
            n += 1
            tick += 1

            if duration is not None and (now_mono - t0_mono) >= duration:
                break

            # planificacion absoluta: evita deriva acumulada del sleep
            target = t0_mono + tick * interval
            slp = target - time.monotonic()
            if slp > 0:
                time.sleep(slp)

    elapsed = time.monotonic() - t0_mono
    stats = {}
    for lb in labels:
        j = acc[lb] / 1e6
        stats[lb] = {
            "energy_j": round(j, 3),
            "energy_wh": round(j / 3600.0, 6),
            "mean_power_w": round(j / elapsed, 3) if elapsed > 0 else None,
            "peak_power_w": round(peak_w[lb], 3),
            "counter_alive": acc[lb] > 0,
        }

    return {
        "duration_s": round(elapsed, 3),
        "samples": n,
        "interval_s": interval,
        "t0_mono": t0_mono,
        "t0_wall": t0_wall,
        "domains": stats,
        "peak_pkg_temp_c": peak_temp,
        "constraints_end": read_constraints(domains),
        "host": host_metadata(),
        "timeseries": str(ts_path),
    }, ts_path


def _fmt(v):
    return "" if v is None else f"{v:.1f}"


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--interval", type=float, default=2.0,
                    help="Intervalo de muestreo en segundos (defecto 2, coherente "
                         "con el bucle de progreso del lanzador)")
    ap.add_argument("--baseline", type=float, metavar="SEGUNDOS",
                    help="Modo calibracion: mide el reposo del host y escribe "
                         "baseline.json. Verifica ademas que dominios estan vivos.")
    ap.add_argument("--baseline-file", type=Path,
                    help="baseline.json previo; permite calcular energia atribuible")
    ap.add_argument("--label", default="run",
                    help="Etiqueta de la ejecucion (p. ej. sol1, sol2)")
    ap.add_argument("--pcores", default="0,2,4,6,8,10",
                    help="CPUs consideradas P-cores para la media de frecuencia")
    ap.add_argument("--ecores", default="12,13,14,15",
                    help="CPUs consideradas E-cores para la media de frecuencia")
    args = ap.parse_args()

    if os.geteuid() != 0:
        print("[monitor_energy] AVISO: sin root, energy_uj sera ilegible.",
              file=sys.stderr)

    args.outdir.mkdir(parents=True, exist_ok=True)

    domains = discover_rapl()
    if not domains:
        print("[monitor_energy] ERROR: ningun dominio RAPL legible. "
              "Comprueba privilegios y /sys/class/powercap.", file=sys.stderr)
        sys.exit(2)

    print(f"[monitor_energy] dominios: {', '.join(sorted(domains))}", file=sys.stderr)

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    pcores = parse_cpu_list(args.pcores)
    ecores = parse_cpu_list(args.ecores)

    constraints_start = read_constraints(domains)

    if args.baseline:
        summary, ts = sample_loop(domains, args.interval, args.outdir,
                                  duration=args.baseline,
                                  pcores=pcores, ecores=ecores)
        summary["mode"] = "baseline"
        summary["constraints_start"] = constraints_start
        dead = [k for k, v in summary["domains"].items() if not v["counter_alive"]]
        if dead:
            print(f"[monitor_energy] AVISO: contadores estaticos (no usar): "
                  f"{', '.join(dead)}", file=sys.stderr)
        out = args.outdir / "baseline.json"
        out.write_text(json.dumps(summary, indent=2))
        print(f"[monitor_energy] baseline -> {out}", file=sys.stderr)
        for lb, s in summary["domains"].items():
            print(f"  {lb:24s} P_idle = {s['mean_power_w']} W  "
                  f"(vivo: {s['counter_alive']})", file=sys.stderr)
        return

    summary, ts = sample_loop(domains, args.interval, args.outdir,
                              pcores=pcores, ecores=ecores)
    summary["mode"] = "run"
    summary["label"] = args.label
    summary["constraints_start"] = constraints_start
    summary["constraints_drift"] = (
        constraints_start != summary["constraints_end"]
    )

    # Energia atribuible = bruta - P_idle * duracion
    if args.baseline_file and args.baseline_file.is_file():
        try:
            base = json.loads(args.baseline_file.read_text())
            summary["baseline_file"] = str(args.baseline_file)
            for lb, s in summary["domains"].items():
                p_idle = base.get("domains", {}).get(lb, {}).get("mean_power_w")
                if p_idle is None:
                    continue
                s["p_idle_w"] = p_idle
                attr = s["energy_j"] - p_idle * summary["duration_s"]
                s["energy_attributable_j"] = round(attr, 3)
                s["energy_attributable_wh"] = round(attr / 3600.0, 6)
        except (OSError, ValueError, KeyError) as e:
            summary["baseline_error"] = str(e)

    out = args.outdir / "energy_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"[monitor_energy] summary -> {out}", file=sys.stderr)
    if summary["constraints_drift"]:
        print("[monitor_energy] AVISO: los limites RAPL cambiaron durante la "
              "ejecucion (EC/firmware). Revisar antes de comparar batches.",
              file=sys.stderr)


if __name__ == "__main__":
    main()