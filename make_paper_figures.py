#!/usr/bin/env python3
"""Paper figures (English) from one simulation batch.

Usage: python3 make_paper_figures.py [SIMULATION_DIR] [OUTDIR]
Directions are labelled Cibeles / La Peseta (never toA / toB).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
SIM = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    ROOT / "WEB_DEVEL/data/logs/SIMULATION_20261012_170524"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "paper_figures"
OUT.mkdir(parents=True, exist_ok=True)

DIR_NAME = {"to_A": "Cibeles", "to_B": "La Peseta", "toA": "Cibeles", "toB": "La Peseta"}
ORDER = {  # stop order along each direction (as in relacion_oferta_error.py)
    "to_A": [2646, 562, 4090, 4188, 5939, 3995, 3991, 3903, 2539, 2535, 1929, 4032, 5360, 82, 5727],
    "to_B": [5727, 81, 1167, 2538, 3929, 3990, 3994, 5938, 4187, 2964, 649, 2646],
}
COL = {"to_A": "#1f77b4", "to_B": "#d62728"}
THRESH = 0.97

plt.rcParams.update({
    "font.family": "serif", "font.size": 10, "axes.labelsize": 10,
    "axes.titlesize": 10, "legend.fontsize": 9, "axes.grid": True,
    "grid.alpha": 0.3, "figure.dpi": 100, "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print("->", OUT / f"{name}.png")


# ---------------------------------------------------------------- convergence
def convergence():
    cols = ["sim", "bus", "trip", "stop", "dir", "time", "ts", "dep_ts",
            "boards", "resid", "drop", "occ", "tbs"]
    means = []
    files = sorted((SIM / "RESULTS").glob("log_Simulation *.csv"),
                   key=lambda p: int(p.stem.split()[-1]))
    for f in files:
        d = pd.read_csv(f, skiprows=1, header=None, names=cols, usecols=range(13))
        means.append(d["occ"].mean())
    m = np.array(means)
    n = np.arange(1, len(m) + 1)
    cum = np.cumsum(m) / n
    sd = np.array([m[:k].std(ddof=1) if k > 1 else 0 for k in n])
    ci = 1.96 * sd / np.sqrt(n)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.plot(n, cum, color="b", lw=1.4, label="Cumulative mean occupancy")
    ax.axhline(cum[-1], color="r", ls="--", lw=1, label=f"Final mean: {cum[-1]:.4f}")
    ax.fill_between(n, cum - ci, cum + ci, color="b", alpha=0.25, label="95% CI")
    ax.set_xlabel("Number of replicas")
    ax.set_ylabel("Cumulative mean occupancy (passengers)")
    ax.legend(loc="upper right")
    save(fig, "convergence")


# ----------------------------------------------------------------- validation
def load_detail():
    d = pd.read_csv(SIM / "PLOTS/general/bhatt_detalle.csv")
    return d[d.estado == "evaluada"].dropna(
        subset=["mean_sim", "std_sim", "mean_esp", "std_esp"]).copy()


def regression(d, tipo, label, unit):
    d = d[d.tipo == tipo]
    if d.empty:
        return
    x, y = d.mean_esp.astype(float), d.mean_sim.astype(float)
    reg = stats.linregress(x, y)
    lim = float(max(x.max(), y.max())) * 1.05
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    ax.scatter(x, y, s=14, alpha=0.65, color="0.25", edgecolor="none",
               label=f"Stop/time-slot cells (n={len(d)})")
    xs = np.array([0, lim])
    ax.plot(xs, xs, "k--", lw=1, label="Identity")
    ax.plot(xs, reg.intercept + reg.slope * xs, color="#1f77b4", lw=1.8,
            label=f"Fit: $y={reg.intercept:+.2f}+{reg.slope:.3f}x$\n$R^2={reg.rvalue**2:.3f}$")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim); ax.set_aspect("equal")
    ax.set_xlabel(f"Observed mean {label} ({unit})")
    ax.set_ylabel(f"Simulated mean {label} ({unit})")
    ax.legend(loc="upper left")
    save(fig, f"regression_{ {"ocupacion": "occupancy", "tiempo": "travel_time"}[tipo] }")


# ----------------------------------------------------------------- dispersion
def dispersion(d):
    d = d[d.tipo == "ocupacion"].copy()
    d["ratio"] = d.std_sim / d.std_esp
    d["elemento"] = d.elemento.astype(int)
    d["pos"] = [ORDER[r.direccion].index(r.elemento) + 1
                if r.elemento in ORDER[r.direccion] else np.nan
                for r in d.itertuples()]

    # (a) along the route, one panel per direction
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, k in zip(axs, ("to_A", "to_B")):
        s = d[d.direccion == k].dropna(subset=["pos"])
        g = s.groupby("pos")["ratio"]
        ax.scatter(s.pos, s.ratio, s=8, alpha=0.25, color=COL[k], edgecolor="none")
        ax.errorbar(g.mean().index, g.mean().values, yerr=g.std().values,
                    fmt="o-", color=COL[k], capsize=3, lw=1.5, ms=4,
                    label="Mean $\\pm$ SD")
        ax.axhline(1, color="0.3", ls="--", lw=1, label="$\\sigma_{sim}=\\sigma_{obs}$")
        ax.set_xlabel("Stop position along the route")
        ax.set_title(f"Direction {DIR_NAME[k]}")
        ax.set_xticks(range(1, len(ORDER[k]) + 1))
    axs[0].set_ylabel("$\\sigma_{sim}/\\sigma_{obs}$")
    axs[0].legend(loc="upper left")
    save(fig, "dispersion_along_route")

    # (b) along the day, by time slot
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for k in ("to_A", "to_B"):
        g = d[d.direccion == k].groupby("franja")["ratio"]
        ax.errorbar(g.mean().index, g.mean().values, yerr=g.std().values,
                    fmt="o-", color=COL[k], capsize=3, lw=1.5, ms=4,
                    label=f"Direction {DIR_NAME[k]}")
    ax.axhline(1, color="0.3", ls="--", lw=1)
    ax.set_xlabel("Time slot (hour of day)")
    ax.set_ylabel("$\\sigma_{sim}/\\sigma_{obs}$")
    ax.legend()
    save(fig, "dispersion_along_day")


# ------------------------------------------------------------- Bhattacharyya
K049 = float(np.sqrt(8 * -np.log(THRESH)))  # |dmu| <= 0.4936 sigma for BC>=0.97, equal sigmas


def bhatt(d, band):
    d = d[d.tipo == "ocupacion"]
    x, y = d.mean_esp.astype(float), d.mean_sim.astype(float)
    ok = d.fusionable.astype(bool)
    lim = float(max(x.max(), y.max())) * 1.05
    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    xs = np.linspace(0, lim, 200)
    note = None
    if band:
        b, a = np.polyfit(x, d.std_esp.astype(float), 1)  # sigma_obs as a function of the mean
        w = K049 * np.clip(a + b * xs, 0, None)
        ax.fill_between(xs, xs - w, xs + w, color="0.85", alpha=0.7, lw=0,
                        label=f"Mean tolerance for BC $\\geq$ {THRESH}\n($|\\Delta\\mu|\\leq$ {K049:.2f} $\\sigma_{{obs}}$)")
        inside = (d.mean_sim - d.mean_esp).abs() <= K049 * d.std_esp
        n_disp = int((inside & ~ok).sum())
        note = f"Rejected only by dispersion: {100*n_disp/len(d):.1f}% (n={n_disp})"
    ax.scatter(x[~ok], y[~ok], s=14, alpha=0.6, color="#d62728", edgecolor="none",
               label=f"Non-equivalent (n={int((~ok).sum())})")
    ax.scatter(x[ok], y[ok], s=14, alpha=0.85, color="#2ca02c", edgecolor="none",
               label=f"Equivalent (n={int(ok.sum())})")
    ax.plot(xs, xs, "k--", lw=1, label="Identity")
    if note:
        ax.plot([], [], " ", label=note)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim); ax.set_aspect("equal")
    ax.set_xlabel("Observed mean occupancy (passengers)")
    ax.set_ylabel("Simulated mean occupancy (passengers)")
    ax.legend(loc="upper left", fontsize=7.5)
    save(fig, "bhattacharyya_band" if band else "bhattacharyya_sim_vs_observed")


if __name__ == "__main__":
    convergence()
    det = load_detail()
    regression(det, "ocupacion", "occupancy", "passengers")
    regression(det, "tiempo", "travel time", "s")
    dispersion(det)
    bhatt(det, False)
    bhatt(det, True)
