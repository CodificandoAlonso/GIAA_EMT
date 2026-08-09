#!/usr/bin/env python3
"""
io_wave_analysis.py — dos analisis complementarios sobre monitor_resources.py:

  (A) E/S y reparto usuario/sistema. Responde a si la escritura de trazas y
      resultados pesa en el tiempo de computo. Si cpu_system_s es una fraccion
      pequena de cpu_time_s, la E/S no es el cuello de botella.

      Aviso: io.stat del cgroup contabiliza bloques que llegan al dispositivo,
      no llamadas write() de la aplicacion. Con page cache de por medio puede
      subestimar lo escrito. cpu_system_s es el indicador mas fiable.

  (B) Efecto de barrera por tandas. GAMA despacha las replicas en tandas del
      tamano del pool y no inicia la siguiente hasta que la anterior termina
      por completo, de modo que cada tanda dura lo que su replica mas lenta.
      Se cuantifica mediante la ocupacion del cpuset y el tiempo de pared
      recuperable con un planificador de reposicion continua.

      'tiempo recuperable' = duracion - cpu_time/cores. Es una COTA SUPERIOR:
      supone paralelismo perfecto e ignora secciones intrinsecamente seriales.

Uso:
  python3 io_wave_analysis.py --outdir /ruta/PLOTS/oleadas \
      sol1 /ruta/SIMULATION_A/MONITOR \
      sol2 /ruta/SIMULATION_B/MONITOR
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DPI = 150
COLORS = ["#1f77b4", "#d62728"]


# --------------------------------------------------------------------------- #
def num(df, col):
    return pd.to_numeric(df[col], errors="coerce") if col in df.columns else None


def load(label, mondir):
    mondir = Path(mondir)
    sp, tp = mondir / "monitor_summary.json", mondir / "monitor_timeseries.csv"
    for p in (sp, tp):
        if not p.exists():
            sys.exit(f"[{label}] ERROR: no existe {p}")

    s = json.loads(sp.read_text())
    ts = pd.read_csv(tp)
    ts["t_rel"] = num(ts, "t_mono") - s["t0_mono"]
    for c in ("cpu_pct_core", "replicas_done", "io_wbytes", "io_rbytes",
              "usage_usec", "user_usec", "system_usec"):
        if c in ts.columns:
            ts[c] = num(ts, c)
    ts["replicas_done"] = ts["replicas_done"].ffill()
    ts = ts.sort_values("t_rel").reset_index(drop=True)

    cores = s.get("cores_assumed") or len(s.get("host", {}).get("affinity", [])) or 1
    ts["occ"] = ts["cpu_pct_core"] / (cores * 100.0)
    return {"label": label, "s": s, "ts": ts, "cores": cores, "dir": mondir}


# --------------------------------------------------------------------------- #
# (A) E/S
# --------------------------------------------------------------------------- #
def io_metrics(r):
    s, ts = r["s"], r["ts"]
    dur = s.get("duration_s") or 0
    rep = s.get("replicas_done") or 0
    cpu = s.get("cpu_time_s")
    usr, sysc = s.get("cpu_user_s"), s.get("cpu_system_s")
    wb, rb = s.get("io_write_bytes"), s.get("io_read_bytes")

    # sys+usr no tiene por que sumar exactamente usage_usec (contabilidad
    # distinta en cgroup v2); se normaliza sobre usage para el porcentaje.
    sys_pct = (sysc / cpu * 100.0) if (cpu and sysc is not None) else None

    return {
        "duracion_s": round(dur, 1),
        "replicas": rep,
        "cpu_time_s": cpu,
        "cpu_user_s": usr,
        "cpu_system_s": sysc,
        "sys_pct_de_cpu": None if sys_pct is None else round(sys_pct, 2),
        "io_escritura_mib": None if wb is None else round(wb / 1024**2, 1),
        "io_lectura_mib": None if rb is None else round(rb / 1024**2, 1),
        "escritura_mib_por_replica": (None if not (wb and rep)
                                      else round(wb / 1024**2 / rep, 3)),
        "escritura_mib_s": (None if not (wb and dur)
                            else round(wb / 1024**2 / dur, 3)),
    }


def fig_io(runs, outdir):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.0))

    ax = axes[0]
    labels = [r["label"] for r in runs]
    usr = [r["s"].get("cpu_user_s") or 0 for r in runs]
    sysc = [r["s"].get("cpu_system_s") or 0 for r in runs]
    x = np.arange(len(runs))
    ax.bar(x, usr, 0.55, label="usuario", color="#4c72b0", edgecolor="black", lw=0.6)
    ax.bar(x, sysc, 0.55, bottom=usr, label="sistema", color="#dd8452",
           edgecolor="black", lw=0.6)
    for i, (u, s_) in enumerate(zip(usr, sysc)):
        if u + s_:
            ax.annotate(f"sys {s_/(u+s_)*100:.1f}%", xy=(i, u + s_),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("CPU-time (s)")
    ax.set_title("Reparto usuario / sistema")
    ax.legend(fontsize=8); ax.grid(alpha=0.25, axis="y")

    ax = axes[1]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["io_wbytes"])
        if d.empty:
            continue
        base = d["io_wbytes"].iloc[0]
        ax.plot(d["t_rel"] / 60.0, (d["io_wbytes"] - base) / 1024**2,
                lw=1.5, color=COLORS[i], label=r["label"])
    ax.set_xlabel("Tiempo (min)"); ax.set_ylabel("Escritura acumulada (MiB)")
    ax.set_title("Volumen de escritura a disco")
    ax.legend(fontsize=8); ax.grid(alpha=0.25)

    ax = axes[2]
    vals, lab2 = [], []
    for r in runs:
        m = io_metrics(r)
        if m["escritura_mib_por_replica"] is not None:
            vals.append(m["escritura_mib_por_replica"]); lab2.append(r["label"])
    if vals:
        b = ax.bar(lab2, vals, color=COLORS[:len(vals)], alpha=0.8,
                   edgecolor="black", lw=0.6)
        for bb, v in zip(b, vals):
            ax.annotate(f"{v:.3g}", xy=(bb.get_x() + bb.get_width() / 2, v),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=8)
    ax.set_ylabel("MiB escritos por replica")
    ax.set_title("Escritura normalizada")
    ax.grid(alpha=0.25, axis="y")

    fig.tight_layout()
    p = outdir / "io_reparto.png"
    fig.savefig(p, dpi=DPI); plt.close(fig)
    print(f"  -> {p}")


# --------------------------------------------------------------------------- #
# (B) Barrera por tandas
# --------------------------------------------------------------------------- #
def wave_metrics(r):
    s, ts, cores = r["s"], r["ts"], r["cores"]
    dur = s.get("duration_s") or 0
    cpu = s.get("cpu_time_s") or 0
    rep = s.get("replicas_done") or 0

    occ = ts["occ"].dropna()
    hilos_medios = (cpu / dur) if dur else None
    ideal = (cpu / cores) if cores else None
    lost = (dur - ideal) if ideal is not None else None

    # tamano de tanda: saltos positivos de replicas_done
    d = ts["replicas_done"].dropna().diff()
    jumps = d[d > 0]

    return {
        "cores": cores,
        "hilos_activos_medios": None if hilos_medios is None else round(hilos_medios, 2),
        "ocupacion_media_pct": (None if hilos_medios is None
                                else round(hilos_medios / cores * 100, 2)),
        "ocupacion_p50_pct": None if occ.empty else round(occ.median() * 100, 2),
        "ocupacion_p10_pct": None if occ.empty else round(occ.quantile(0.10) * 100, 2),
        "frac_tiempo_bajo_80_pct": (None if occ.empty
                                    else round((occ < 0.80).mean() * 100, 2)),
        "frac_tiempo_bajo_50_pct": (None if occ.empty
                                    else round((occ < 0.50).mean() * 100, 2)),
        "duracion_min": round(dur / 60, 1),
        "duracion_ideal_min": None if ideal is None else round(ideal / 60, 1),
        "recuperable_min": None if lost is None else round(lost / 60, 1),
        "recuperable_pct": (None if (lost is None or not dur)
                            else round(lost / dur * 100, 2)),
        "n_saltos_progreso": int(len(jumps)),
        "salto_mediano": None if jumps.empty else float(jumps.median()),
        "s_pared_por_replica": round(dur / rep, 3) if rep else None,
    }


def fig_waves(runs, outdir):
    n = len(runs)
    fig, axes = plt.subplots(n + 1, 1, figsize=(11, 3.2 * (n + 1)))
    if n + 1 == 1:
        axes = [axes]

    for i, r in enumerate(runs):
        ax = axes[i]
        d = r["ts"].dropna(subset=["occ"])
        ax.plot(d["t_rel"] / 60.0, d["occ"] * 100, lw=0.7, color=COLORS[i],
                alpha=0.85)
        m = wave_metrics(r)
        ax.axhline(100, ls="--", lw=1, color="black", alpha=0.5,
                   label=f"saturacion ({r['cores']} hilos)")
        if m["ocupacion_media_pct"]:
            ax.axhline(m["ocupacion_media_pct"], ls=":", lw=1.3, color="grey",
                       label=f"media = {m['ocupacion_media_pct']:.1f}%")
        ax.set_ylim(0, 115)
        ax.set_ylabel("Ocupacion del cpuset (%)")
        ax.set_title(f"{r['label']} — ocupacion frente al tiempo "
                     f"(bajo 80% el {m['frac_tiempo_bajo_80_pct']}% del tiempo)")
        ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=0.25)
        ax.set_xlabel("Tiempo (min)")

    ax = axes[-1]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["occ"])
        if d.empty:
            continue
        v = np.sort(d["occ"].values * 100)
        ax.plot(v, np.linspace(0, 100, v.size), lw=1.8, color=COLORS[i],
                label=r["label"])
    ax.axvline(100, ls="--", lw=1, color="black", alpha=0.5)
    ax.set_xlabel("Ocupacion del cpuset (%)")
    ax.set_ylabel("% de muestras por debajo")
    ax.set_title("Distribucion acumulada de la ocupacion")
    ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.tight_layout()
    p = outdir / "oleadas_ocupacion.png"
    fig.savefig(p, dpi=DPI); plt.close(fig)
    print(f"  -> {p}")


def fig_progress_steps(runs, outdir):
    fig, ax = plt.subplots(figsize=(11, 4.2))
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["replicas_done"])
        ax.step(d["t_rel"] / 60.0, d["replicas_done"], where="post",
                lw=1.4, color=COLORS[i], label=r["label"])
    ax.set_xlabel("Tiempo (min)"); ax.set_ylabel("Replicas completadas")
    ax.set_title("Curva de progreso (los tramos planos delatan la barrera por tandas)")
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout()
    p = outdir / "oleadas_progreso.png"
    fig.savefig(p, dpi=DPI); plt.close(fig)
    print(f"  -> {p}")


# --------------------------------------------------------------------------- #
def to_latex(df, caption, label, colfracs):
    ncol = len(df.columns)
    spec = "|" + "|".join(f"Q{{{f:.2f}}}" for f in colfracs) + "|"
    out = ["\\begin{table}[H]",
           "    \\ttabbox[\\linewidth]",
           f"    {{\\caption{{{caption}}}\\label{{{label}}}}}",
           "    {\\centering",
           f"\\begin{{tabular}}{{{spec}}}",
           "\\hline"]
    out.append(" & ".join(f"\\textbf{{{c}}}" for c in df.columns) + "\\\\")
    out.append("\\hline")
    for _, row in df.iterrows():
        cells = ["-" if pd.isna(v) else str(v) for v in row]
        out.append(" & ".join(cells) + "\\\\")
        out.append("\\hline")
    out.append(f"\\multicolumn{{{ncol}}}{{l}}{{Fuente: elaboración propia.}}")
    out.append("\\end{tabular}}")
    out.append("\\end{table}")
    return "\n".join(out)


def build_table(runs, fn, nombres):
    rows = []
    ms = [fn(r) for r in runs]
    for k, nice in nombres.items():
        rec = {"Métrica": nice}
        for r, m in zip(runs, ms):
            rec[r["label"]] = m.get(k)
        if len(runs) == 2:
            a, b = ms[0].get(k), ms[1].get(k)
            rec["Cociente"] = (round(a / b, 3)
                               if all(isinstance(v, (int, float)) for v in (a, b)) and b
                               else None)
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("pairs", nargs="+", metavar="LABEL DIR")
    a = ap.parse_args()

    if len(a.pairs) % 2:
        sys.exit("ERROR: los argumentos van en pares LABEL DIR.")
    runs = [load(a.pairs[i], a.pairs[i + 1]) for i in range(0, len(a.pairs), 2)]
    a.outdir.mkdir(parents=True, exist_ok=True)

    print("\n=== (A) E/S y reparto usuario/sistema ===")
    t_io = build_table(runs, io_metrics, {
        "cpu_time_s": "CPU-time total (s)",
        "cpu_user_s": "CPU-time usuario (s)",
        "cpu_system_s": "CPU-time sistema (s)",
        "sys_pct_de_cpu": "Sistema sobre el total (%)",
        "io_escritura_mib": "Escritura a disco (MiB)",
        "io_lectura_mib": "Lectura de disco (MiB)",
        "escritura_mib_por_replica": "Escritura por réplica (MiB)",
        "escritura_mib_s": "Tasa de escritura (MiB/s)",
    })
    print(t_io.to_string(index=False))

    print("\n=== (B) Barrera por tandas ===")
    t_w = build_table(runs, wave_metrics, {
        "cores": "Hilos asignados",
        "hilos_activos_medios": "Hilos activos medios",
        "ocupacion_media_pct": "Ocupación media (%)",
        "ocupacion_p50_pct": "Ocupación p50 (%)",
        "ocupacion_p10_pct": "Ocupación p10 (%)",
        "frac_tiempo_bajo_80_pct": "Tiempo bajo el 80% (%)",
        "frac_tiempo_bajo_50_pct": "Tiempo bajo el 50% (%)",
        "duracion_min": "Duración real (min)",
        "duracion_ideal_min": "Duración con reparto ideal (min)",
        "recuperable_min": "Tiempo recuperable (min)",
        "recuperable_pct": "Tiempo recuperable (%)",
        "s_pared_por_replica": "Segundos de pared por réplica",
    })
    print(t_w.to_string(index=False))

    print("\nFiguras:")
    fig_io(runs, a.outdir)
    fig_waves(runs, a.outdir)
    fig_progress_steps(runs, a.outdir)

    print("\nTablas:")
    for df, name, cap, lab, fr in (
        (t_io, "tabla_io", "Reparto de tiempo de CPU y volumen de entrada/salida",
         "tab:io_reparto", [0.40, 0.20, 0.20, 0.20]),
        (t_w, "tabla_oleadas", "Ocupación del conjunto de hilos y efecto de la "
         "sincronización por tandas", "tab:oleadas", [0.40, 0.20, 0.20, 0.20]),
    ):
        fr = fr[:len(df.columns)]
        fr = [f / sum(fr) for f in fr]
        p = a.outdir / f"{name}.csv"; df.to_csv(p, index=False); print(f"  -> {p}")
        p = a.outdir / f"{name}.tex"
        p.write_text(to_latex(df, cap, lab, fr)); print(f"  -> {p}")

    print("""
Lectura:
  (A) Si 'Sistema sobre el total' es de un digito, la escritura de trazas y
      resultados NO explica el tiempo de computo: el proceso esta ligado a CPU.
  (B) 'Ocupación media' por debajo de 100 mide el desaprovechamiento del
      cpuset. Si es sensiblemente menor en sol1, parte de su mayor duracion
      NO es mas trabajo, sino peor reparto: con mas agentes crece la dispersion
      del tiempo por replica y cada tanda espera a su rezagada.
      'Tiempo recuperable' es cota superior: asume paralelismo perfecto.""")


if __name__ == "__main__":
    main()