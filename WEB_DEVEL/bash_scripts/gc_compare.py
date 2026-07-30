#!/usr/bin/env python3
"""
gc_compare.py — separa CONJUNTO VIVO de HEAP COMPROMETIDO a partir de gc.log.

memory.current del cgroup mide RSS: heap comprometido + off-heap + page cache.
No dice cuanta memoria ocupan de verdad los agentes. El log de G1 si: cada
pausa registra ocupacion_antes -> ocupacion_despues (heap_comprometido).

La ocupacion DESPUES de una pausa mixed/full es la mejor aproximacion al
conjunto vivo, porque la joven ya se ha evacuado.

Uso:
  python3 gc_compare.py sol1 /ruta/SIMULATION_A/MONITOR \
                        sol2 /ruta/SIMULATION_B/MONITOR
"""
import re
import sys
from pathlib import Path

# G1 con decoradores time,uptime,level:  "... 3456M->1234M(8192M) 12.345ms"
PAT = re.compile(r"(\d+)([KMG])->(\d+)([KMG])\((\d+)([KMG])\)")
UNIT = {"K": 1 / 1024, "M": 1.0, "G": 1024.0}          # todo a MiB
UP = re.compile(r"\[(\d+[.,]\d+)s\]")                   # uptime del decorador


def to_mib(v, u):
    return float(v) * UNIT[u]


def parse(mondir):
    mondir = Path(mondir)
    # filecount=1 -> puede haber gc.log y gc.log.0 (rotado). Se leen ambos.
    files = sorted(mondir.glob("gc.log*"))
    if not files:
        return None

    before, after, committed, upt = [], [], [], []
    n_lines = 0
    for f in files:
        try:
            txt = f.read_text(errors="ignore")
        except OSError:
            continue
        for line in txt.splitlines():
            m = PAT.search(line)
            if not m:
                continue
            n_lines += 1
            before.append(to_mib(m.group(1), m.group(2)))
            after.append(to_mib(m.group(3), m.group(4)))
            committed.append(to_mib(m.group(5), m.group(6)))
            u = UP.search(line)
            if u:
                upt.append(float(u.group(1).replace(",", ".")))

    if not before:
        return None

    span = (max(upt) - min(upt)) if len(upt) > 1 else None
    # bytes reclamados ~ suma(antes - despues): proxy de la tasa de asignacion
    reclaimed = sum(b - a for b, a in zip(before, after))
    return {
        "files": [f.name for f in files],
        "gc_events": n_lines,
        "heap_used_max_mib": max(before),
        "live_after_gc_max_mib": max(after),
        "live_after_gc_p50_mib": sorted(after)[len(after) // 2],
        "heap_committed_max_mib": max(committed),
        "reclaimed_total_gib": reclaimed / 1024,
        "span_s": span,
        "alloc_rate_mib_s": (reclaimed / span) if span else None,
        "gc_per_min": (n_lines / (span / 60)) if span else None,
    }


def main():
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2:
        sys.exit(__doc__)
    runs = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]

    res = {}
    for label, d in runs:
        r = parse(d)
        if r is None:
            print(f"[{label}] sin gc.log utilizable en {d}", file=sys.stderr)
            continue
        res[label] = r

    if not res:
        sys.exit("ningun gc.log parseado")

    rows = [
        ("ficheros",                 "files",                  None),
        ("eventos GC",               "gc_events",              "{:.0f}"),
        ("GC por minuto",            "gc_per_min",             "{:.2f}"),
        ("heap usado maximo (MiB)",  "heap_used_max_mib",      "{:.0f}"),
        ("VIVO tras GC, max (MiB)",  "live_after_gc_max_mib",  "{:.0f}"),
        ("VIVO tras GC, p50 (MiB)",  "live_after_gc_p50_mib",  "{:.0f}"),
        ("heap COMPROMETIDO (MiB)",  "heap_committed_max_mib", "{:.0f}"),
        ("reclamado total (GiB)",    "reclaimed_total_gib",    "{:.1f}"),
        ("tasa asignacion (MiB/s)",  "alloc_rate_mib_s",       "{:.1f}"),
    ]
    labels = list(res)
    w = max(len(l) for l in labels) + 2

    print(f"\n{'metrica':<26}" + "".join(f"{l:>{w+8}}" for l in labels))
    print("-" * (26 + (w + 8) * len(labels)))
    for name, key, fmt in rows:
        line = f"{name:<26}"
        for l in labels:
            v = res[l].get(key)
            if v is None:
                cell = "-"
            elif fmt is None:
                cell = ",".join(v) if isinstance(v, list) else str(v)
            else:
                cell = fmt.format(v)
            line += f"{cell:>{w+8}}"
        print(line)

    if len(labels) == 2:
        a, b = labels
        print(f"\ncocientes {b}/{a}:")
        for name, key, _ in rows[1:]:
            va, vb = res[a].get(key), res[b].get(key)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and va:
                print(f"  {name:<26} {vb/va:6.3f}")

    print("""
Lectura:
  - Si 'VIVO tras GC' es parecido en ambos, los agentes pasajero NO pesan en
    memoria: el conjunto vivo lo domina la maquinaria del batch, no el modelo.
  - Si 'heap COMPROMETIDO' es mayor donde la 'tasa de asignacion' es mayor,
    el RSS lo fija el rendimiento (G1 pide holgura), no la complejidad.
  - 'reclamado total' es el volumen de basura generada: ahi SI deberia verse
    el coste de crear y destruir agentes y mensajes FIPA.""")


if __name__ == "__main__":
    main()