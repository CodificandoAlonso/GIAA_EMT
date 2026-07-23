#!/usr/bin/env python3
"""
monitor_analyzer.py — figuras y tablas de la monitorizacion de recursos y energia.

Une la serie de energia (host, monitor_energy.py) con la de recursos
(contenedor, monitor_resources.py) mediante CLOCK_MONOTONIC, que es el mismo
reloj a ambos lados porque Docker no usa time namespaces por defecto. La
ventana del batch se recorta con t0_mono y duration_s de monitor_summary.json,
de modo que la extraccion Python posterior queda fuera automaticamente.

Modos:
  1 run  -> analisis individual
  2 runs -> individual de cada uno + figuras y tablas comparativas

Las tablas se generan como CSV/JSON, no como LaTeX: el formato final se
aplica aparte con las convenciones del documento.

Uso:
  python3 monitor_analyzer.py \
      --run sol1 /ruta/SIMULATION_XXX /ruta/energy_timeseries_sol1.csv \
                 /ruta/energy_summary_sol1.json \
      --run sol2 /ruta/SIMULATION_YYY /ruta/energy_timeseries_sol2.csv \
                 /ruta/energy_summary_sol2.json \
      --baseline /ruta/baseline.json \
      --outdir /ruta/PLOTS/monitoring
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

try:
    from scipy.signal import find_peaks
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

DPI = 150
FIGSIZE = (10, 4.5)
COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"]

# Dominio sobre el que se ancla el argumento energetico. PP0 (nucleos) es el
# menos contaminado por iGPU y uncore, y la carga es CPU-bound.
PRIMARY_DOMAIN = "package-0-core"


# =========================================================================== #
# Carga y alineamiento
# =========================================================================== #
def discover_domains(df):
    return [c[:-len("_power_w")] for c in df.columns if c.endswith("_power_w")]


def load_run(label, simdir, energy_csv, energy_json, baseline=None):
    simdir = Path(simdir)
    mon = simdir / "MONITOR"

    res_sum = json.loads((mon / "monitor_summary.json").read_text())
    res_ts = pd.read_csv(mon / "monitor_timeseries.csv")
    e_sum = json.loads(Path(energy_json).read_text())
    e_ts = pd.read_csv(Path(energy_csv))

    # --- ventana del batch, definida por la serie de recursos --------------
    t0 = res_sum["t0_mono"]
    dur = res_sum["duration_s"]
    t1 = t0 + dur

    n_before = len(e_ts)
    e_ts = e_ts[(e_ts["t_mono"] >= t0) & (e_ts["t_mono"] <= t1)].copy()
    if e_ts.empty:
        raise SystemExit(
            f"[{label}] ERROR: la serie de energia no solapa con la ventana del "
            f"batch. Comprueba que ambos muestreadores corrieron a la vez."
        )

    res_ts = res_ts.copy()
    res_ts["t_rel"] = res_ts["t_mono"] - t0
    e_ts["t_rel"] = e_ts["t_mono"] - t0

    # replicas_done puede venir vacia en algun tick
    res_ts["replicas_done"] = (
        pd.to_numeric(res_ts["replicas_done"], errors="coerce").ffill()
    )
    res_ts["cpu_pct_core"] = pd.to_numeric(res_ts["cpu_pct_core"], errors="coerce")

    domains = discover_domains(e_ts)
    for d in domains:
        for suf in ("_power_w", "_delta_uj"):
            e_ts[d + suf] = pd.to_numeric(e_ts[d + suf], errors="coerce")
        e_ts[f"{d}_cum_j"] = e_ts[d + "_delta_uj"].fillna(0).cumsum() / 1e6

    for c in ("temp_pkg_c", "freq_p_mhz", "freq_e_mhz"):
        if c in e_ts.columns:
            e_ts[c] = pd.to_numeric(e_ts[c], errors="coerce")

    # --- join por reloj monotonico -----------------------------------------
    merged = pd.merge_asof(
        e_ts.sort_values("t_mono"),
        res_ts[["t_mono", "replicas_done", "cpu_pct_core", "memory_current"]]
            .sort_values("t_mono"),
        on="t_mono", direction="nearest", tolerance=5.0,
    )

    # --- P_idle: se recalcula si se pasa un baseline explicito -------------
    p_idle = {}
    src = "summary"
    if baseline:
        b = json.loads(Path(baseline).read_text())
        for d in domains:
            v = b.get("domains", {}).get(d, {}).get("mean_power_w")
            if v is not None:
                p_idle[d] = v
        src = str(baseline)
    for d in domains:
        if d not in p_idle:
            p_idle[d] = e_sum.get("domains", {}).get(d, {}).get("p_idle_w")

    # --- energia de la VENTANA (no de toda la sesion) ----------------------
    win_s = float(e_ts["t_rel"].iloc[-1] - e_ts["t_rel"].iloc[0])
    energy = {}
    for d in domains:
        j = float(e_ts[d + "_delta_uj"].fillna(0).sum()) / 1e6
        pi = p_idle.get(d)
        energy[d] = {
            "energy_j": j,
            "mean_power_w": j / win_s if win_s > 0 else None,
            "peak_power_w": float(e_ts[d + "_power_w"].max()),
            "p_idle_w": pi,
            "energy_attributable_j": None if pi is None else j - pi * win_s,
        }

    return {
        "label": label,
        "simdir": simdir,
        "res_sum": res_sum,
        "res_ts": res_ts,
        "e_ts": e_ts,
        "merged": merged,
        "e_sum": e_sum,
        "domains": domains,
        "energy": energy,
        "window_s": win_s,
        "p_idle_source": src,
        "energy_rows_dropped": n_before - len(e_ts),
    }


# =========================================================================== #
# Figuras individuales
# =========================================================================== #
def fig_cpu(run, outdir, npeaks=5, window=15):
    d = run["res_ts"].dropna(subset=["cpu_pct_core"])
    if d.empty:
        return None
    t = d["t_rel"] / 60.0
    y = d["cpu_pct_core"]
    sm = y.rolling(window, center=True, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(t, y, lw=0.5, alpha=0.35, color=COLORS[0])
    ax.plot(t, sm, lw=1.6, color=COLORS[0], label=f"media movil ({window} muestras)")

    cores = run["res_sum"].get("cores_assumed")
    if cores:
        ax.axhline(cores * 100, ls="--", lw=1, color="grey",
                   label=f"saturacion ({cores} hilos = {cores*100}%)")

    peaks = peak_table(run, npeaks, window)
    for _, p in peaks.iterrows():
        ax.annotate(f"{p['cpu_pct_core']:.0f}%",
                    xy=(p["t_rel_min"], p["cpu_pct_core"]),
                    xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=7,
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="grey"))

    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("CPU (% de un nucleo)")
    ax.set_title(f"Utilizacion de CPU — {run['label']}")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25)
    return save(fig, outdir / f"cpu_{run['label']}.png")


def fig_memory(run, outdir):
    d = run["res_ts"].dropna(subset=["memory_current"])
    if d.empty:
        return None
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(d["t_rel"] / 60.0, d["memory_current"] / 1024**3,
            lw=1.0, color=COLORS[2])
    pk = run["res_sum"].get("memory_peak_bytes")
    if pk:
        ax.axhline(pk / 1024**3, ls="--", lw=1.2, color=COLORS[1],
                   label=f"memory.peak = {pk/1024**3:.2f} GiB")
        ax.legend(fontsize=8)
    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("Memoria residente (GiB)")
    ax.set_title(f"Consumo de memoria — {run['label']}")
    ax.grid(alpha=0.25)
    return save(fig, outdir / f"memoria_{run['label']}.png")


def fig_power_thermal(run, outdir, domain=None):
    """Potencia, temperatura y frecuencia. Diagnostica limitacion termica:
    si la potencia decae mientras la CPU sigue saturada, el punto de
    operacion lo fija la temperatura y no la carga."""
    domain = domain or (PRIMARY_DOMAIN if PRIMARY_DOMAIN in run["domains"]
                        else run["domains"][0])
    d = run["e_ts"].dropna(subset=[domain + "_power_w"])
    if d.empty:
        return None
    t = d["t_rel"] / 60.0

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(t, d[domain + "_power_w"], lw=0.6, alpha=0.4, color=COLORS[0])
    ax.plot(t, d[domain + "_power_w"].rolling(15, center=True, min_periods=1).mean(),
            lw=1.6, color=COLORS[0], label=f"potencia {domain}")
    pi = run["energy"][domain]["p_idle_w"]
    if pi:
        ax.axhline(pi, ls=":", lw=1, color="grey", label=f"P_idle = {pi:.2f} W")
    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("Potencia (W)")
    ax.grid(alpha=0.25)

    if "temp_pkg_c" in d.columns and d["temp_pkg_c"].notna().any():
        ax2 = ax.twinx()
        ax2.plot(t, d["temp_pkg_c"].rolling(15, center=True, min_periods=1).mean(),
                 lw=1.2, color=COLORS[1], alpha=0.8, label="temperatura")
        ax2.set_ylabel("Temperatura de paquete (°C)", color=COLORS[1])
        ax2.tick_params(axis="y", labelcolor=COLORS[1])
        ax2.axhline(100, ls="--", lw=0.8, color=COLORS[1], alpha=0.5)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper right")
    else:
        ax.legend(fontsize=8)

    ax.set_title(f"Potencia y temperatura — {run['label']}")
    return save(fig, outdir / f"potencia_{run['label']}.png")


def fig_rate(run, outdir, window=30):
    d = run["res_ts"].dropna(subset=["replicas_done"])
    if d.empty or d["replicas_done"].max() == 0:
        return None
    dr = d["replicas_done"].diff()
    dt = d["t_rel"].diff() / 3600.0
    rate = (dr / dt).rolling(window, center=True, min_periods=5).mean()

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(d["t_rel"] / 60.0, rate, lw=1.3, color=COLORS[3])
    ax.axhline(run["res_sum"].get("replicas_per_hour", np.nan), ls="--", lw=1,
               color="grey", label="media global")
    ax.set_xlabel("Tiempo (min)")
    ax.set_ylabel("Replicas / hora")
    ax.set_title(f"Tasa de progreso — {run['label']}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    return save(fig, outdir / f"progreso_{run['label']}.png")


# =========================================================================== #
# Figuras comparativas (eje x = progreso, no tiempo)
# =========================================================================== #
def fig_energy_vs_replicas(runs, outdir, domain=None):
    """Figura comparativa central: normaliza por progreso, no por tiempo,
    porque las duraciones de ambas soluciones difieren."""
    domain = domain or PRIMARY_DOMAIN
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ok = False
    for i, r in enumerate(runs):
        if domain not in r["domains"]:
            continue
        m = r["merged"].dropna(subset=["replicas_done"])
        if m.empty:
            continue
        ax.plot(m["replicas_done"], m[f"{domain}_cum_j"] / 1000.0,
                lw=1.6, color=COLORS[i % len(COLORS)], label=r["label"])
        ok = True
    if not ok:
        plt.close(fig)
        return None
    ax.set_xlabel("Replicas completadas")
    ax.set_ylabel("Energia acumulada (kJ)")
    ax.set_title(f"Energia acumulada frente a progreso — dominio {domain}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return save(fig, outdir / "comparativa_energia_vs_replicas.png")


def fig_cputime_vs_replicas(runs, outdir):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ok = False
    for i, r in enumerate(runs):
        d = r["res_ts"].dropna(subset=["replicas_done", "usage_usec"])
        if d.empty:
            continue
        cpu_h = (d["usage_usec"] - d["usage_usec"].iloc[0]) / 1e6 / 3600.0
        ax.plot(d["replicas_done"], cpu_h, lw=1.6,
                color=COLORS[i % len(COLORS)], label=r["label"])
        ok = True
    if not ok:
        plt.close(fig)
        return None
    ax.set_xlabel("Replicas completadas")
    ax.set_ylabel("CPU-time acumulado (h)")
    ax.set_title("CPU-time acumulado frente a progreso")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return save(fig, outdir / "comparativa_cputime_vs_replicas.png")


def fig_blocks(runs, outdir, domain=None, nblocks=10):
    domain = domain or PRIMARY_DOMAIN
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ok = False
    for i, r in enumerate(runs):
        b = block_table(r, domain, nblocks)
        if b is None or b.empty:
            continue
        ax.errorbar(b["block"], b["j_per_replica"], fmt="o-", lw=1.3, ms=4,
                    color=COLORS[i % len(COLORS)],
                    label=f"{r['label']} (media {b['j_per_replica'].mean():.1f} J)")
        ok = True
    if not ok:
        plt.close(fig)
        return None
    ax.set_xlabel(f"Bloque de replicas (1..{nblocks})")
    ax.set_ylabel("Energia atribuible por replica (J)")
    ax.set_title(f"Dispersion intra-ejecucion — dominio {domain}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    return save(fig, outdir / "comparativa_bloques.png")


# =========================================================================== #
# Tablas
# =========================================================================== #
def peak_table(run, k=5, window=15):
    d = run["res_ts"].dropna(subset=["cpu_pct_core"]).reset_index(drop=True)
    if d.empty:
        return pd.DataFrame()
    sm = d["cpu_pct_core"].rolling(window, center=True, min_periods=1).mean()
    if HAVE_SCIPY:
        idx, _ = find_peaks(sm.values, prominence=sm.std() * 0.5,
                            distance=max(1, window))
        idx = sorted(idx, key=lambda i: -sm.values[i])[:k]
    else:
        idx = sm.nlargest(k).index.tolist()
    rows = []
    for i in sorted(idx):
        rows.append({
            "t_rel_min": round(d["t_rel"].iloc[i] / 60.0, 2),
            "cpu_pct_core": round(float(sm.iloc[i]), 1),
            "replicas_done": (None if pd.isna(d["replicas_done"].iloc[i])
                              else int(d["replicas_done"].iloc[i])),
            "memory_gib": (None if pd.isna(d["memory_current"].iloc[i]) else
                           round(d["memory_current"].iloc[i] / 1024**3, 2)),
        })
    return pd.DataFrame(rows)


def block_table(run, domain=None, nblocks=10):
    """Dispersion intra-ejecucion por bloques de replicas.

    NO son replicas independientes: comparten deriva termica y estado de la
    JVM. Es dispersion intra-ejecucion, no varianza entre ejecuciones, y
    debe declararse como tal.
    """
    domain = domain or PRIMARY_DOMAIN
    if domain not in run["domains"]:
        return None
    m = run["merged"].dropna(subset=["replicas_done"]).copy()
    if m.empty:
        return None
    total = m["replicas_done"].max()
    if not total or total < nblocks:
        return None
    edges = np.linspace(0, total, nblocks + 1)
    pi = run["energy"][domain]["p_idle_w"] or 0.0

    rows = []
    for i in range(nblocks):
        s = m[(m["replicas_done"] > edges[i]) & (m["replicas_done"] <= edges[i + 1])]
        if len(s) < 2:
            continue
        n_rep = s["replicas_done"].iloc[-1] - s["replicas_done"].iloc[0]
        dt = s["t_rel"].iloc[-1] - s["t_rel"].iloc[0]
        j = float(s[domain + "_delta_uj"].fillna(0).sum()) / 1e6
        if n_rep <= 0:
            continue
        rows.append({
            "block": i + 1,
            "replicas": int(n_rep),
            "duration_s": round(dt, 1),
            "energy_j": round(j, 1),
            "j_per_replica": round((j - pi * dt) / n_rep, 3),
            "mean_power_w": round(j / dt, 2) if dt > 0 else None,
            "mean_temp_c": (round(float(s["temp_pkg_c"].mean()), 1)
                            if "temp_pkg_c" in s else None),
        })
    return pd.DataFrame(rows)


def summary_row(run, domain=None):
    domain = domain or PRIMARY_DOMAIN
    rs = run["res_sum"]
    e = run["energy"].get(domain, {})
    rep = rs.get("replicas_done") or 0
    att = e.get("energy_attributable_j")
    row = {
        "label": run["label"],
        "duracion_s": rs.get("duration_s"),
        "duracion_min": round((rs.get("duration_s") or 0) / 60.0, 1),
        "replicas": rep,
        "cpu_time_s": rs.get("cpu_time_s"),
        "cpu_time_h": round((rs.get("cpu_time_s") or 0) / 3600.0, 3),
        "cpu_pct_core_media": rs.get("cpu_pct_core_mean"),
        "cpu_pct_core_max": rs.get("cpu_pct_core_max"),
        "cpu_s_por_replica": rs.get("cpu_s_per_replica"),
        "replicas_por_hora": rs.get("replicas_per_hour"),
        "ram_pico_gib": rs.get("memory_peak_gb"),
        "io_lectura_mib": (None if rs.get("io_read_bytes") is None
                           else round(rs["io_read_bytes"] / 1024**2, 1)),
        "io_escritura_mib": (None if rs.get("io_write_bytes") is None
                             else round(rs["io_write_bytes"] / 1024**2, 1)),
        "dominio_energia": domain,
        "energia_bruta_j": round(e.get("energy_j", 0), 1),
        "energia_atribuible_j": None if att is None else round(att, 1),
        "energia_atribuible_wh": None if att is None else round(att / 3600.0, 4),
        "p_idle_w": e.get("p_idle_w"),
        "potencia_media_w": (None if e.get("mean_power_w") is None
                             else round(e["mean_power_w"], 2)),
        "potencia_pico_w": e.get("peak_power_w"),
        "j_por_replica": (None if (att is None or not rep)
                          else round(att / rep, 3)),
        "temp_pico_c": run["e_sum"].get("peak_pkg_temp_c"),
        "pl1_drift": run["e_sum"].get("constraints_drift"),
        "cores": rs.get("cores_assumed"),
        "afinidad_n": len(rs.get("host", {}).get("affinity", []) or []),
    }
    return row


def comparison_table(rows):
    a, b = rows[0], rows[1]
    numeric = [k for k, v in a.items()
               if isinstance(v, (int, float)) and not isinstance(v, bool)]
    out = []
    for k in numeric:
        va, vb = a.get(k), b.get(k)
        ratio = (round(vb / va, 4) if isinstance(va, (int, float))
                 and isinstance(vb, (int, float)) and va else None)
        out.append({"metrica": k, a["label"]: va, b["label"]: vb,
                    f"ratio_{b['label']}_{a['label']}": ratio})
    return pd.DataFrame(out)


# =========================================================================== #
def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    print(f"  -> {path}")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", nargs=4, action="append", required=True,
                    metavar=("LABEL", "SIMDIR", "ENERGY_CSV", "ENERGY_JSON"),
                    help="Repetible. Dos --run activan el modo comparativo.")
    ap.add_argument("--baseline", help="baseline.json con el que RECALCULAR "
                                       "P_idle, ignorando el del summary")
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--domain", default=PRIMARY_DOMAIN)
    ap.add_argument("--peaks", type=int, default=5)
    ap.add_argument("--blocks", type=int, default=10)
    args = ap.parse_args()

    if len(args.run) > 2:
        sys.exit("ERROR: maximo dos --run.")

    args.outdir.mkdir(parents=True, exist_ok=True)
    runs = [load_run(*r, baseline=args.baseline) for r in args.run]

    for r in runs:
        print(f"[{r['label']}] ventana {r['window_s']:.0f} s | "
              f"{r['energy_rows_dropped']} muestras de energia fuera de ventana "
              f"| P_idle de: {r['p_idle_source']}")
        if r["res_sum"].get("cores_assumed") and \
           len(r["res_sum"].get("host", {}).get("affinity", [])) != \
           r["res_sum"]["cores_assumed"]:
            print(f"  AVISO: afinidad "
                  f"({len(r['res_sum']['host']['affinity'])} CPUs) no coincide "
                  f"con cores_assumed ({r['res_sum']['cores_assumed']}).")

    print("\nFiguras individuales:")
    for r in runs:
        fig_cpu(r, args.outdir, args.peaks)
        fig_memory(r, args.outdir)
        fig_power_thermal(r, args.outdir, args.domain)
        fig_rate(r, args.outdir)

    print("\nFiguras comparativas:")
    fig_energy_vs_replicas(runs, args.outdir, args.domain)
    fig_cputime_vs_replicas(runs, args.outdir)
    fig_blocks(runs, args.outdir, args.domain, args.blocks)

    print("\nTablas:")
    rows = [summary_row(r, args.domain) for r in runs]
    p = args.outdir / "tabla_resumen.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    print(f"  -> {p}")

    for r in runs:
        pt = peak_table(r, args.peaks)
        if not pt.empty:
            p = args.outdir / f"tabla_picos_{r['label']}.csv"
            pt.to_csv(p, index=False)
            print(f"  -> {p}")
        bt = block_table(r, args.domain, args.blocks)
        if bt is not None and not bt.empty:
            p = args.outdir / f"tabla_bloques_{r['label']}.csv"
            bt.to_csv(p, index=False)
            print(f"  -> {p}")
            print(f"     {r['label']}: {bt['j_per_replica'].mean():.2f} "
                  f"+/- {bt['j_per_replica'].std():.2f} J/replica "
                  f"(dispersion intra-ejecucion, n={len(bt)} bloques)")

    if len(runs) == 2:
        p = args.outdir / "tabla_comparativa.csv"
        comparison_table(rows).to_csv(p, index=False)
        print(f"  -> {p}")

    p = args.outdir / "analisis.json"
    p.write_text(json.dumps({"runs": rows, "domain": args.domain}, indent=2))
    print(f"  -> {p}")


if __name__ == "__main__":
    main()