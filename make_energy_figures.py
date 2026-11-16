#!/usr/bin/env python3
"""Energy / resource figures (English) for the two latest simulation batches.

Energy samples exist only for the batch whose window is covered by
_energy/energy_timeseries.csv; resource figures are drawn for both.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "WEB_DEVEL/data/logs"
sys.path.insert(0, str(LOGS.parent.parent / "bash_scripts"))
import monitor_analyzer as ma  # noqa: E402

OUT = ROOT / "paper_figures/energy"
OUT.mkdir(parents=True, exist_ok=True)
RUNS = {  # label -> sim dir
    "Without passenger agents": "SIMULATION_20261013_093049",
    "With passenger agents": "SIMULATION_20261014_082628",
}
COLS = ["#1f77b4", "#d62728"]
DOMAIN = ma.PRIMARY_DOMAIN

plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.grid": True,
                     "grid.alpha": 0.3, "savefig.dpi": 300, "savefig.bbox": "tight"})


def save(fig, name):
    for e in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{e}")
    plt.close(fig)
    print("->", OUT / f"{name}.png")


def res(label, d):
    mon = LOGS / d / "MONITOR"
    s = pd.read_json(mon / "monitor_summary.json", typ="series")
    t = pd.read_csv(mon / "monitor_timeseries.csv")
    t["t_rel"] = t.t_mono - s["t0_mono"]
    t["cpu_pct_core"] = pd.to_numeric(t.cpu_pct_core, errors="coerce")
    t["replicas_done"] = pd.to_numeric(t.replicas_done, errors="coerce").ffill()
    return s, t


def main():
    R = {k: res(k, v) for k, v in RUNS.items()}
    e_all = pd.read_csv(LOGS / "_energy/energy_timeseries.csv")

    # which runs have energy samples inside their window
    energy_run = None
    for k, (s, t) in R.items():
        # monotonic clocks restart at boot, so match on wall-clock time
        w = e_all[(e_all.t_wall >= s.t0_wall) & (e_all.t_wall <= s.t0_wall + s.duration_s)]
        print(f"{k}: {len(w)} energy samples in window (wall clock)")
        if len(w) > 0.9 * s.duration_s / 2:
            energy_run = k
    rows = []
    for k, (s, t) in R.items():
        rows.append({"run": k, "duration_min": round(s.duration_s / 60, 1),
                     "replicas": int(s.replicas_done),
                     "mean_cpu_pct_of_core": s.cpu_pct_core_mean,
                     "cpu_time_h": round(s.cpu_time_s / 3600, 2),
                     "peak_memory_GiB": s.memory_peak_gb,
                     "replicas_per_hour": s.replicas_per_hour})

    # ---- CPU, memory, progress (both runs)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for c, (k, (s, t)) in zip(COLS, R.items()):
        d = t.dropna(subset=["cpu_pct_core"])
        ax.plot(d.t_rel / 60, d.cpu_pct_core.rolling(30, center=True, min_periods=1).mean(),
                color=c, lw=1.3, label=k)
    ax.axhline(600, color="0.4", ls="--", lw=1, label="Saturation (6 threads)")
    ax.set_xlabel("Time (min)"); ax.set_ylabel("CPU (% of one core)")
    ax.legend(fontsize=8); save(fig, "cpu_usage")

    fig, ax = plt.subplots(figsize=(7, 3.4))
    for c, (k, (s, t)) in zip(COLS, R.items()):
        d = t.dropna(subset=["memory_current"])
        ax.plot(d.t_rel / 60, d.memory_current / 1024**3, color=c, lw=1.1, label=k)
    ax.set_xlabel("Time (min)"); ax.set_ylabel("Resident memory (GiB)")
    ax.legend(fontsize=8); save(fig, "memory_usage")

    fig, ax = plt.subplots(figsize=(7, 3.4))
    for c, (k, (s, t)) in zip(COLS, R.items()):
        d = t.dropna(subset=["replicas_done", "usage_usec"])
        ax.plot(d.replicas_done, (d.usage_usec - d.usage_usec.iloc[0]) / 3.6e9,
                color=c, lw=1.5, label=k)
    ax.set_xlabel("Completed replicas"); ax.set_ylabel("Cumulative CPU time (h)")
    ax.legend(fontsize=8); save(fig, "cpu_time_vs_replicas")

    # ---- energy (run with samples)
    if energy_run:
        s, _ = R[energy_run]
        sd = LOGS / RUNS[energy_run]
        run = ma.load_run(energy_run, sd, LOGS / "_energy/energy_timeseries.csv",
                          LOGS / "_energy/energy_summary.json",
                          baseline=LOGS / "_energy/baseline.json")
        e = run["e_ts"]
        t = e.t_rel / 60
        fig, ax = plt.subplots(figsize=(7, 3.4))
        p = e[f"{DOMAIN}_power_w"]
        ax.plot(t, p, lw=0.5, alpha=0.35, color=COLS[1])
        ax.plot(t, p.rolling(15, center=True, min_periods=1).mean(), lw=1.6, color=COLS[1],
                label=f"Power ({DOMAIN})")
        pi = run["energy"][DOMAIN]["p_idle_w"]
        if pi:
            ax.axhline(pi, color="0.4", ls=":", label=f"Idle power = {pi:.2f} W")
        ax.set_xlabel("Time (min)"); ax.set_ylabel("Power (W)")
        ax2 = ax.twinx(); ax2.grid(False)
        ax2.plot(t, e.temp_pkg_c.rolling(15, center=True, min_periods=1).mean(),
                 color="tab:orange", lw=1.1, label="Package temperature")
        ax2.set_ylabel("Temperature (°C)")
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")
        save(fig, "power_and_temperature")

        m = run["merged"].dropna(subset=["replicas_done"])
        fig, ax = plt.subplots(figsize=(7, 3.4))
        ax.plot(m.replicas_done, m[f"{DOMAIN}_cum_j"] / 1000, color=COLS[1], lw=1.6)
        ax.set_xlabel("Completed replicas"); ax.set_ylabel("Cumulative energy (kJ)")
        save(fig, "cumulative_energy_vs_replicas")

        b = ma.block_table(run, DOMAIN, 10)
        if b is not None and len(b):
            fig, ax = plt.subplots(figsize=(7, 3.4))
            ax.plot(b.block, b.j_per_replica, "o-", color=COLS[1],
                    label=f"Mean {b.j_per_replica.mean():.1f} J")
            ax.set_xlabel("Replica block (1..10)")
            ax.set_ylabel("Attributable energy per replica (J)")
            ax.legend(); save(fig, "energy_dispersion_by_block")
        en = run["energy"][DOMAIN]
        rows[list(RUNS).index(energy_run)].update({
            "energy_domain": DOMAIN, "gross_energy_kJ": round(en["energy_j"] / 1e3, 1),
            "attributable_energy_kJ": round(en["energy_attributable_j"] / 1e3, 1),
            "attributable_Wh": round(en["energy_attributable_j"] / 3600, 1),
            "J_per_replica": round(en["energy_attributable_j"] / s.replicas_done, 2),
            "mean_power_W": round(en["mean_power_w"], 2),
            "peak_temp_C": float(e.temp_pkg_c.max())})
    pd.DataFrame(rows).to_csv(OUT / "summary_table.csv", index=False)
    print(pd.DataFrame(rows).T)


main()
