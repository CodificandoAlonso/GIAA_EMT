#!/usr/bin/env python3
"""
monitor_comparator.py — figuras y tablas COMPARATIVAS entre dos soluciones.

Complemento de monitor_analyzer.py: aquel produce el analisis individual de
cada ejecucion, este produce unicamente las vistas enfrentadas de dos
ejecuciones. Ninguna figura de aqui tiene sentido con un solo --run.

Funciona con la serie de recursos del contenedor (monitor_resources.py) sola.
La serie de energia del host (monitor_energy.py) es OPCIONAL: si se pasa con
--energy se anaden las figuras de potencia, temperatura y energia; si no, se
omiten y se avisa por stdout. Esto permite comparar ejecuciones en las que
el muestreador RAPL no estuvo activo.

Criterio de normalizacion: el eje x de las figuras comparativas centrales es
el PROGRESO (replicas completadas), no el tiempo, porque las duraciones de
ambas soluciones difieren y una comparacion a tiempo igual compara puntos
distintos del batch.

Uso minimo (solo recursos):
  python3 monitor_comparator.py \
      --run sol1 /ruta/SIMULATION_AAA \
      --run sol2 /ruta/SIMULATION_BBB \
      --outdir /ruta/PLOTS/comparativa

Con energia (cuando monitor_energy.py si estuvo corriendo):
  python3 monitor_comparator.py \
      --run sol1 /ruta/SIMULATION_AAA \
      --run sol2 /ruta/SIMULATION_BBB \
      --energy sol1 /ruta/energy_timeseries_sol1.csv /ruta/energy_summary_sol1.json \
      --energy sol2 /ruta/energy_timeseries_sol2.csv /ruta/energy_summary_sol2.json \
      --baseline /ruta/baseline.json \
      --outdir /ruta/PLOTS/comparativa
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
FIGSIZE = (10, 4.5)
FIGSIZE_TALL = (10, 6.0)
COLORS = ["#1f77b4", "#d62728"]
PRIMARY_DOMAIN = "package-0-core"
SMOOTH = 15          # muestras de la media movil
GRID_N = 200         # puntos de la rejilla comun de replicas


# =========================================================================== #
# Carga
# =========================================================================== #
def num(df, col):
    """Serie numerica o None si la columna no existe."""
    if col not in df.columns:
        return None
    return pd.to_numeric(df[col], errors="coerce")


def load_run(label, simdir, energy=None, baseline=None):
    simdir = Path(simdir)
    mon = simdir / "MONITOR"
    summ_p = mon / "monitor_summary.json"
    ts_p = mon / "monitor_timeseries.csv"
    for p in (summ_p, ts_p):
        if not p.exists():
            raise SystemExit(f"[{label}] ERROR: no existe {p}")

    res_sum = json.loads(summ_p.read_text())
    ts = pd.read_csv(ts_p)

    t0 = res_sum["t0_mono"]
    ts["t_rel"] = num(ts, "t_mono") - t0
    ts["replicas_done"] = num(ts, "replicas_done").ffill()
    ts["cpu_pct_core"] = num(ts, "cpu_pct_core")
    ts["memory_current"] = num(ts, "memory_current")

    u = num(ts, "usage_usec")
    ts["cpu_h"] = None if u is None else (u - u.iloc[0]) / 1e6 / 3600.0

    run = {
        "label": label,
        "simdir": simdir,
        "res_sum": res_sum,
        "ts": ts.sort_values("t_rel").reset_index(drop=True),
        "t0": t0,
        "e_ts": None,
        "e_sum": None,
        "domains": [],
        "p_idle": {},
    }

    if energy:
        e_csv, e_json = energy
        e_ts = pd.read_csv(e_csv)
        e_sum = json.loads(Path(e_json).read_text())
        dur = res_sum["duration_s"]
        e_ts = e_ts[(num(e_ts, "t_mono") >= t0) &
                    (num(e_ts, "t_mono") <= t0 + dur)].copy()
        if e_ts.empty:
            print(f"[{label}] AVISO: la serie de energia no solapa con la "
                  f"ventana del batch; se ignora.")
        else:
            e_ts["t_rel"] = num(e_ts, "t_mono") - t0
            domains = [c[:-len("_power_w")] for c in e_ts.columns
                       if c.endswith("_power_w")]
            for d in domains:
                e_ts[d + "_power_w"] = num(e_ts, d + "_power_w")
                e_ts[d + "_delta_uj"] = num(e_ts, d + "_delta_uj")
                e_ts[d + "_cum_j"] = e_ts[d + "_delta_uj"].fillna(0).cumsum() / 1e6
            for c in ("temp_pkg_c", "freq_p_mhz", "freq_e_mhz"):
                if c in e_ts.columns:
                    e_ts[c] = num(e_ts, c)

            p_idle = {}
            if baseline:
                b = json.loads(Path(baseline).read_text())
                for d in domains:
                    v = b.get("domains", {}).get(d, {}).get("mean_power_w")
                    if v is not None:
                        p_idle[d] = v
            for d in domains:
                p_idle.setdefault(
                    d, e_sum.get("domains", {}).get(d, {}).get("p_idle_w"))

            # progreso interpolado sobre la rejilla de energia, para poder
            # dibujar energia frente a replicas
            r = run["ts"].dropna(subset=["replicas_done"])
            e_ts["replicas_done"] = np.interp(
                e_ts["t_rel"], r["t_rel"], r["replicas_done"],
                left=np.nan, right=np.nan)

            run.update(e_ts=e_ts.sort_values("t_rel").reset_index(drop=True),
                       e_sum=e_sum, domains=domains, p_idle=p_idle)
    return run


def smooth(s, w=SMOOTH):
    return s.rolling(w, center=True, min_periods=1).mean()


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    print(f"  -> {path}")
    return path


def common_replica_grid(runs, n=GRID_N):
    tops = [r["ts"]["replicas_done"].max() for r in runs]
    top = np.nanmin([t for t in tops if t and not np.isnan(t)])
    return np.linspace(1, top, n), top


def interp_on_replicas(run, col, grid):
    d = run["ts"].dropna(subset=["replicas_done", col])
    if d.empty:
        return None
    # replicas_done es monotona no decreciente: se colapsa a su ultimo valor
    g = d.groupby("replicas_done")[col].last()
    return np.interp(grid, g.index.values, g.values,
                     left=np.nan, right=np.nan)


# =========================================================================== #
# Comparativas de recursos
# =========================================================================== #
def cmp_cpu_time(runs, outdir):
    """Figura central: CPU sobre el eje temporal, en paralelo."""
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_TALL, sharex=False)

    ax = axes[0]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["cpu_pct_core"])
        if d.empty:
            continue
        t = d["t_rel"] / 60.0
        ax.plot(t, d["cpu_pct_core"], lw=0.4, alpha=0.25, color=COLORS[i])
        ax.plot(t, smooth(d["cpu_pct_core"]), lw=1.6, color=COLORS[i],
                label=f"{r['label']} (media {r['res_sum'].get('cpu_pct_core_mean')}%)")
    cores = runs[0]["res_sum"].get("cores_assumed")
    if cores:
        ax.axhline(cores * 100, ls="--", lw=1, color="grey",
                   label=f"saturacion ({cores} hilos = {cores*100}%)")
    ax.set_ylabel("CPU (% de un nucleo)")
    ax.set_title("Utilizacion de CPU frente al tiempo")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)
    ax.set_xlabel("Tiempo (min)")

    ax = axes[1]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["cpu_pct_core", "replicas_done"])
        if d.empty:
            continue
        ax.plot(d["replicas_done"], smooth(d["cpu_pct_core"]),
                lw=1.5, color=COLORS[i], label=r["label"])
    if cores:
        ax.axhline(cores * 100, ls="--", lw=1, color="grey")
    ax.set_xlabel("Replicas completadas")
    ax.set_ylabel("CPU (% de un nucleo)")
    ax.set_title("Utilizacion de CPU frente al progreso")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)
    return save(fig, outdir / "cmp_cpu.png")


def cmp_memory(runs, outdir):
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_TALL)

    ax = axes[0]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["memory_current"])
        if d.empty:
            continue
        ax.plot(d["t_rel"] / 60.0, d["memory_current"] / 1024**3,
                lw=1.1, color=COLORS[i], label=r["label"])
        pk = r["res_sum"].get("memory_peak_bytes")
        if pk:
            ax.axhline(pk / 1024**3, ls=":", lw=1.1, color=COLORS[i],
                       label=f"{r['label']} memory.peak = {pk/1024**3:.2f} GiB")
    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("Memoria residente (GiB)")
    ax.set_title("Evolucion de memoria frente al tiempo")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    ax = axes[1]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["memory_current", "replicas_done"])
        if d.empty:
            continue
        ax.plot(d["replicas_done"], d["memory_current"] / 1024**3,
                lw=1.1, color=COLORS[i], label=r["label"])
    ax.set_xlabel("Replicas completadas")
    ax.set_ylabel("Memoria residente (GiB)")
    ax.set_title("Evolucion de memoria frente al progreso")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return save(fig, outdir / "cmp_memoria.png")


def cmp_cputime_vs_replicas(runs, outdir):
    """CPU-time acumulado y su cociente sobre rejilla comun de replicas.
    El cociente es la lectura directa del sobrecoste de una solucion."""
    if any(r["ts"]["cpu_h"] is None for r in runs):
        print("  (sin usage_usec: se omite cmp_cputime)")
        return None
    grid, top = common_replica_grid(runs)
    curves = [interp_on_replicas(r, "cpu_h", grid) for r in runs]
    if any(c is None for c in curves):
        return None

    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_TALL, sharex=True)
    ax = axes[0]
    for i, (r, c) in enumerate(zip(runs, curves)):
        ax.plot(grid, c, lw=1.7, color=COLORS[i],
                label=f"{r['label']} ({r['res_sum'].get('cpu_s_per_replica')} s/replica)")
    ax.set_ylabel("CPU-time acumulado (h)")
    ax.set_title("CPU-time acumulado frente al progreso")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)

    ax = axes[1]
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = curves[1] / curves[0]
    ax.plot(grid, ratio, lw=1.7, color="#7f7f7f")
    ax.axhline(1.0, ls="--", lw=1, color="black", alpha=0.6)
    fin = ratio[np.isfinite(ratio)]
    if fin.size:
        ax.axhline(fin[-1], ls=":", lw=1, color="#7f7f7f",
                   label=f"valor final = {fin[-1]:.3f}")
        ax.legend(fontsize=9)
    ax.set_xlabel("Replicas completadas")
    ax.set_ylabel(f"CPU-time {runs[1]['label']} / {runs[0]['label']}")
    ax.set_title("Cociente de coste computacional a igual progreso")
    ax.grid(alpha=0.25)
    return save(fig, outdir / "cmp_cputime_ratio.png")


def cmp_progress(runs, outdir, window=30):
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_TALL)

    ax = axes[0]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["replicas_done"])
        if d.empty:
            continue
        ax.plot(d["t_rel"] / 60.0, d["replicas_done"], lw=1.6, color=COLORS[i],
                label=f"{r['label']} ({r['res_sum'].get('duration_s',0)/60:.0f} min, "
                      f"{int(r['res_sum'].get('replicas_done') or 0)} replicas)")
    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("Replicas completadas")
    ax.set_title("Curva de progreso")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    ax = axes[1]
    for i, r in enumerate(runs):
        d = r["ts"].dropna(subset=["replicas_done"])
        if d.empty:
            continue
        rate = ((d["replicas_done"].diff() / (d["t_rel"].diff() / 3600.0))
                .rolling(window, center=True, min_periods=5).mean())
        ax.plot(d["t_rel"] / 60.0, rate, lw=1.4, color=COLORS[i],
                label=f"{r['label']} (media {r['res_sum'].get('replicas_per_hour')}/h)")
        rp = r["res_sum"].get("replicas_per_hour")
        if rp:
            ax.axhline(rp, ls="--", lw=0.9, color=COLORS[i], alpha=0.6)
    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("Replicas / hora")
    ax.set_title("Tasa de progreso")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return save(fig, outdir / "cmp_progreso.png")


def cmp_distributions(runs, outdir):
    """Dispersion de CPU y memoria. Es dispersion INTRA-ejecucion: las
    muestras comparten deriva termica y estado de la JVM, no son
    observaciones independientes."""
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE)
    for ax, col, lab, scale in (
            (axes[0], "cpu_pct_core", "CPU (% de un nucleo)", 1.0),
            (axes[1], "memory_current", "Memoria residente (GiB)", 1 / 1024**3)):
        data, labels = [], []
        for r in runs:
            s = r["ts"][col].dropna()
            if s.empty:
                continue
            data.append(s.values * scale)
            labels.append(r["label"])
        if not data:
            continue
        # 'labels' se renombro a 'tick_labels' en matplotlib 3.9
        mv = tuple(int(x) for x in matplotlib.__version__.split(".")[:2])
        kw = "tick_labels" if mv >= (3, 9) else "labels"
        bp = ax.boxplot(data, showmeans=True, widths=0.55,
                        patch_artist=True, showfliers=False, **{kw: labels})
        for i, box in enumerate(bp["boxes"]):
            box.set_facecolor(COLORS[i % len(COLORS)])
            box.set_alpha(0.35)
        for med in bp["medians"]:
            med.set_color("black")
        ax.set_ylabel(lab)
        ax.grid(alpha=0.25, axis="y")
    fig.suptitle("Dispersion intra-ejecucion de CPU y memoria")
    return save(fig, outdir / "cmp_dispersion.png")


def cmp_bars(runs, outdir):
    """Resumen escalar normalizado por replica."""
    metrics = [
        ("cpu_s_per_replica", "CPU-s por replica", 1.0),
        ("memory_peak_gb", "RAM pico (GiB)", 1.0),
        ("replicas_per_hour", "Replicas / hora", 1.0),
        ("cpu_pct_alloc_mean", "Ocupacion media del cpuset (%)", 1.0),
    ]
    avail = [(k, lab, sc) for k, lab, sc in metrics
             if all(r["res_sum"].get(k) is not None for r in runs)]
    if not avail:
        return None
    fig, axes = plt.subplots(1, len(avail), figsize=(3.0 * len(avail), 4.0))
    if len(avail) == 1:
        axes = [axes]
    for ax, (k, lab, sc) in zip(axes, avail):
        vals = [r["res_sum"][k] * sc for r in runs]
        labels = [r["label"] for r in runs]
        bars = ax.bar(labels, vals, color=COLORS[:len(runs)], alpha=0.75,
                      edgecolor="black", lw=0.6)
        for b, v in zip(bars, vals):
            ax.annotate(f"{v:.4g}", xy=(b.get_x() + b.get_width() / 2, v),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=8)
        if vals[0]:
            ax.set_xlabel(f"cociente = {vals[1]/vals[0]:.3f}", fontsize=8)
        ax.set_title(lab, fontsize=9)
        ax.grid(alpha=0.25, axis="y")
    fig.suptitle("Metricas escalares normalizadas")
    return save(fig, outdir / "cmp_escalares.png")


# =========================================================================== #
# Comparativas de energia (solo si se paso --energy)
# =========================================================================== #
def cmp_power_thermal(runs, outdir, domain):
    runs_e = [r for r in runs if r["e_ts"] is not None and domain in r["domains"]]
    if len(runs_e) < 2:
        return None
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_TALL, sharex=True)

    ax = axes[0]
    for i, r in enumerate(runs_e):
        d = r["e_ts"].dropna(subset=[domain + "_power_w"])
        t = d["t_rel"] / 60.0
        ax.plot(t, d[domain + "_power_w"], lw=0.4, alpha=0.2, color=COLORS[i])
        ax.plot(t, smooth(d[domain + "_power_w"]), lw=1.6, color=COLORS[i],
                label=r["label"])
        pi = r["p_idle"].get(domain)
        if pi:
            ax.axhline(pi, ls=":", lw=1, color=COLORS[i], alpha=0.7,
                       label=f"{r['label']} P_idle = {pi:.2f} W")
    ax.set_ylabel("Potencia (W)")
    ax.set_title(f"Potencia frente al tiempo — dominio {domain}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    ax = axes[1]
    any_t = False
    for i, r in enumerate(runs_e):
        if "temp_pkg_c" not in r["e_ts"].columns:
            continue
        d = r["e_ts"].dropna(subset=["temp_pkg_c"])
        if d.empty:
            continue
        ax.plot(d["t_rel"] / 60.0, smooth(d["temp_pkg_c"]), lw=1.5,
                color=COLORS[i],
                label=f"{r['label']} (pico {r['e_sum'].get('peak_pkg_temp_c')} C)")
        any_t = True
    if any_t:
        ax.axhline(100, ls="--", lw=0.9, color="grey", alpha=0.6,
                   label="limite de union")
        ax.set_ylabel("Temperatura de paquete (C)")
        ax.set_title("Temperatura frente al tiempo")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
    else:
        ax.set_visible(False)
    ax.set_xlabel("Tiempo (min)")
    return save(fig, outdir / "cmp_potencia_temperatura.png")


def cmp_energy_vs_replicas(runs, outdir, domain):
    runs_e = [r for r in runs if r["e_ts"] is not None and domain in r["domains"]]
    if len(runs_e) < 2:
        return None
    fig, axes = plt.subplots(2, 1, figsize=FIGSIZE_TALL, sharex=True)

    ax = axes[0]
    for i, r in enumerate(runs_e):
        d = r["e_ts"].dropna(subset=["replicas_done"])
        ax.plot(d["replicas_done"], d[domain + "_cum_j"] / 1000.0,
                lw=1.7, color=COLORS[i], label=r["label"])
    ax.set_ylabel("Energia acumulada (kJ)")
    ax.set_title(f"Energia acumulada frente al progreso — dominio {domain}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)

    ax = axes[1]
    grid, _ = common_replica_grid(runs_e)
    curves = []
    for r in runs_e:
        d = r["e_ts"].dropna(subset=["replicas_done", domain + "_cum_j"])
        g = d.groupby("replicas_done")[domain + "_cum_j"].last()
        curves.append(np.interp(grid, g.index.values, g.values,
                                left=np.nan, right=np.nan))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = curves[1] / curves[0]
    ax.plot(grid, ratio, lw=1.7, color="#7f7f7f")
    ax.axhline(1.0, ls="--", lw=1, color="black", alpha=0.6)
    fin = ratio[np.isfinite(ratio)]
    if fin.size:
        ax.axhline(fin[-1], ls=":", lw=1, color="#7f7f7f",
                   label=f"valor final = {fin[-1]:.3f}")
        ax.legend(fontsize=9)
    ax.set_xlabel("Replicas completadas")
    ax.set_ylabel(f"Energia {runs_e[1]['label']} / {runs_e[0]['label']}")
    ax.set_title("Cociente de energia a igual progreso")
    ax.grid(alpha=0.25)
    return save(fig, outdir / "cmp_energia_ratio.png")


# =========================================================================== #
# Tabla
# =========================================================================== #
def summary_row(run, domain):
    rs = run["res_sum"]
    rep = rs.get("replicas_done") or 0
    row = {
        "label": run["label"],
        "duracion_s": rs.get("duration_s"),
        "duracion_min": round((rs.get("duration_s") or 0) / 60.0, 1),
        "replicas": rep,
        "muestras": rs.get("samples"),
        "cpu_time_s": rs.get("cpu_time_s"),
        "cpu_time_h": round((rs.get("cpu_time_s") or 0) / 3600.0, 3),
        "cpu_user_s": rs.get("cpu_user_s"),
        "cpu_system_s": rs.get("cpu_system_s"),
        "cpu_s_por_replica": rs.get("cpu_s_per_replica"),
        "cpu_pct_core_media": rs.get("cpu_pct_core_mean"),
        "cpu_pct_core_max": rs.get("cpu_pct_core_max"),
        "cpu_pct_alloc_media": rs.get("cpu_pct_alloc_mean"),
        "replicas_por_hora": rs.get("replicas_per_hour"),
        "s_pared_por_replica": (round((rs.get("duration_s") or 0) / rep, 3)
                               if rep else None),
        "ram_pico_gib": rs.get("memory_peak_gb"),
        "io_lectura_mib": (None if rs.get("io_read_bytes") is None
                           else round(rs["io_read_bytes"] / 1024**2, 1)),
        "io_escritura_mib": (None if rs.get("io_write_bytes") is None
                             else round(rs["io_write_bytes"] / 1024**2, 1)),
        "cores": rs.get("cores_assumed"),
        "afinidad_n": len(rs.get("host", {}).get("affinity", []) or []),
    }
    if run["e_ts"] is not None and domain in run["domains"]:
        d = run["e_ts"]
        win = float(d["t_rel"].iloc[-1] - d["t_rel"].iloc[0])
        j = float(d[domain + "_delta_uj"].fillna(0).sum()) / 1e6
        pi = run["p_idle"].get(domain)
        att = None if pi is None else j - pi * win
        row.update({
            "dominio_energia": domain,
            "energia_bruta_j": round(j, 1),
            "energia_atribuible_j": None if att is None else round(att, 1),
            "j_por_replica": (None if (att is None or not rep)
                              else round(att / rep, 3)),
            "potencia_media_w": round(j / win, 2) if win > 0 else None,
            "potencia_pico_w": round(float(d[domain + "_power_w"].max()), 2),
            "temp_pico_c": run["e_sum"].get("peak_pkg_temp_c"),
        })
    return row


def comparison_table(rows):
    a, b = rows[0], rows[1]
    keys = [k for k in a if k != "label"]
    out = []
    for k in keys:
        va, vb = a.get(k), b.get(k)
        ratio = None
        if all(isinstance(v, (int, float)) and not isinstance(v, bool)
               for v in (va, vb)) and va:
            ratio = round(vb / va, 4)
        out.append({"metrica": k, a["label"]: va, b["label"]: vb,
                    f"ratio_{b['label']}_{a['label']}": ratio})
    return pd.DataFrame(out)


# =========================================================================== #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", nargs=2, action="append", required=True,
                    metavar=("LABEL", "SIMDIR"),
                    help="Exactamente dos. El primero es la referencia del cociente.")
    ap.add_argument("--energy", nargs=3, action="append", default=[],
                    metavar=("LABEL", "ENERGY_CSV", "ENERGY_JSON"),
                    help="Opcional, por etiqueta. Si falta, se omiten las "
                         "figuras de potencia, temperatura y energia.")
    ap.add_argument("--baseline", help="baseline.json para recalcular P_idle")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--domain", default=PRIMARY_DOMAIN)
    args = ap.parse_args()

    if len(args.run) != 2:
        sys.exit("ERROR: se requieren exactamente dos --run "
                 "(este script solo produce comparativas).")

    emap = {lab: (csv, js) for lab, csv, js in args.energy}
    args.outdir.mkdir(parents=True, exist_ok=True)

    runs = [load_run(lab, sd, energy=emap.get(lab), baseline=args.baseline)
            for lab, sd in args.run]

    print(f"Referencia del cociente: {runs[0]['label']}  "
          f"(cociente = {runs[1]['label']} / {runs[0]['label']})\n")
    for r in runs:
        rs = r["res_sum"]
        aff = len(rs.get("host", {}).get("affinity", []) or [])
        print(f"[{r['label']}] {rs.get('duration_s',0)/60:.1f} min | "
              f"{rs.get('replicas_done')} replicas | "
              f"{rs.get('cpu_s_per_replica')} CPU-s/replica | "
              f"RAM pico {rs.get('memory_peak_gb')} GiB | "
              f"afinidad {aff} CPUs")
        if aff and rs.get("cores_assumed") and aff != rs["cores_assumed"]:
            print(f"  AVISO: afinidad ({aff}) != cores_assumed "
                  f"({rs['cores_assumed']}).")
        if r["e_ts"] is None:
            print("  AVISO: sin serie de energia; no habra figuras de "
                  "potencia, temperatura ni energia.")

    print("\nFiguras comparativas de recursos:")
    cmp_cpu_time(runs, args.outdir)
    cmp_memory(runs, args.outdir)
    cmp_cputime_vs_replicas(runs, args.outdir)
    cmp_progress(runs, args.outdir)
    cmp_distributions(runs, args.outdir)
    cmp_bars(runs, args.outdir)

    if all(r["e_ts"] is not None for r in runs):
        print("\nFiguras comparativas de energia:")
        cmp_power_thermal(runs, args.outdir, args.domain)
        cmp_energy_vs_replicas(runs, args.outdir, args.domain)
    else:
        print("\n(sin energia en ambas ejecuciones: se omiten sus comparativas)")

    print("\nTablas:")
    rows = [summary_row(r, args.domain) for r in runs]
    p = args.outdir / "cmp_tabla_resumen.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    print(f"  -> {p}")
    p = args.outdir / "cmp_tabla_comparativa.csv"
    comparison_table(rows).to_csv(p, index=False)
    print(f"  -> {p}")
    p = args.outdir / "cmp_analisis.json"
    p.write_text(json.dumps({"reference": runs[0]["label"],
                             "runs": rows, "domain": args.domain}, indent=2))
    print(f"  -> {p}")


if __name__ == "__main__":
    main()