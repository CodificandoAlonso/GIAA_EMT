"""
Parte 3: donde se concentran las distribuciones que no pasan el test de
normalidad (IsNormal = FALSE), a partir de output/part2/cells.csv.

Se estudian la variante actual (A) y la recomendada (por defecto B_err), tanto la
version que se exporta (ALL: todos los laborables juntos) como la diaria (L-V),
que tiene muchas mas celdas FALSE y anade el dia de la semana.

Salidas en AAA_TEST/output/part3/:
    false_cells_ALL.csv        las celdas FALSE exportadas, con sus caracteristicas
    false_by_stop.csv          % FALSE por parada (diario), con posicion en ruta
    false_by_slot.csv          % FALSE por franja (diario)
    false_by_weekday.csv       % FALSE por dia de la semana
    false_by_factor.csv        % FALSE por tamano de muestra, media, ceros y asimetria
    false_causes.csv           clasificacion heuristica de la causa de cada FALSE
    *.png
"""

import os
import sys

import numpy as np
import pandas as pd

from common import COLOR, STOPS, TIMESLOTS, WEEKDAYS, outdir, seq_cmap, setup_matplotlib

IN = os.path.join(outdir("part2"), "cells.csv")
OUT = outdir("part3")
DIRS = ("toA", "toB")
VARIANTS = ("A", sys.argv[1] if len(sys.argv) > 1 else "B_err")


def load() -> pd.DataFrame:
    c = pd.read_csv(IN)
    c = c[c["variant"].isin(VARIANTS) & (c["is_normal"] != "NO DATA")].copy()
    c["false"] = c["is_normal"].astype(str) != "True"
    c["pos"] = [STOPS[d].index(s) for d, s in zip(c["dir"], c["Stop"])]
    c["pos_label"] = [
        "cabecera" if p == 0 else ("terminal" if p == len(STOPS[d]) - 1 else "intermedia")
        for d, p in zip(c["dir"], c["pos"])
    ]
    c["cv"] = c["std"] / c["mean"].replace(0, np.nan)
    return c


def cause(row) -> str:
    """Causa probable (heuristica, la primera que aplica)."""
    if row["zero_share"] >= 0.15 or (row["mean"] > 0 and row["mean"] < 1.5 * row["std"] and row["skew"] > 0.5):
        return "suelo en 0 (ocupación baja, asimetría a la derecha)"
    if row["skew"] < -0.3 and row["mean"] >= 40:
        return "techo por el corte en 75 (asimetría a la izquierda)"
    if row["test_branch"] == "n<50":
        return "muestra pequeña (n < 50, criterio z = 1,96)"
    if abs(row["skew"]) < 0.5 and row["kurt"] > 1:
        return "colas pesadas (curtosis alta, simétrica)"
    return "asimetría moderada"


def share(df: pd.DataFrame, by) -> pd.DataFrame:
    g = df.groupby(by)["false"].agg(["sum", "count"])
    g["pct_false"] = (100 * g["sum"] / g["count"]).round(1)
    return g.rename(columns={"sum": "false", "count": "cells"})


def plot_heatmaps(c: pd.DataFrame, variant: str, plt):
    """Numero de dias de la semana (0-5) en que la celda es FALSE."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    d_ = c[(c["variant"] == variant) & (c["day"] != "ALL")]
    for ax, d in zip(axes, DIRS):
        x = d_[d_["dir"] == d].groupby(["Stop", "TimeSlot"])["false"].sum().unstack().reindex(STOPS[d])
        im = ax.imshow(x.values, aspect="auto", cmap=seq_cmap(), vmin=0, vmax=5)
        ax.set_yticks(range(len(x.index)))
        ax.set_yticklabels(x.index, fontsize=8)
        ax.set_xticks(range(0, len(TIMESLOTS), 2))
        ax.set_xticklabels(TIMESLOTS[::2], fontsize=8)
        ax.grid(False)
        ax.set_title(f"{d}: días L–V con FALSE ({variant})")
        ax.set_xlabel("franja")
        for (i, j), v in np.ndenumerate(x.values):
            if v >= 3:
                ax.text(j, i, int(v), ha="center", va="center", fontsize=7, color="white")
    axes[0].set_ylabel("parada (orden de ruta)")
    fig.colorbar(im, ax=axes, shrink=0.8, label="días FALSE (de 5)")
    fig.savefig(os.path.join(OUT, f"false_heatmap_{variant}.png"))
    plt.close(fig)


def plot_profiles(c: pd.DataFrame, variant: str, plt):
    d_ = c[(c["variant"] == variant) & (c["day"] != "ALL")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.6))
    for d in DIRS:
        s = share(d_[d_["dir"] == d], "TimeSlot")
        axes[0].plot(s.index, s["pct_false"], color=COLOR[d], marker="o", ms=4, label=d)
        p = share(d_[d_["dir"] == d], "pos")
        axes[1].plot(p.index + 1, p["pct_false"], color=COLOR[d], marker="o", ms=4, label=d)
    axes[0].set_title(f"% FALSE por franja ({variant}, diario)")
    axes[0].set_xlabel("franja")
    axes[0].set_xticks(TIMESLOTS[::2])
    axes[1].set_title(f"% FALSE por posición en la ruta ({variant}, diario)")
    axes[1].set_xlabel("parada nº (1 = cabecera)")
    for ax in axes:
        ax.set_ylabel("% de celdas FALSE")
        ax.legend(loc="upper center")
    fig.savefig(os.path.join(OUT, f"false_profiles_{variant}.png"))
    plt.close(fig)


def main():
    plt = setup_matplotlib()
    c = load()
    c["cause"] = c.apply(cause, axis=1)

    allc = c[c["day"] == "ALL"]
    cols = ["variant", "dir", "Stop", "pos", "pos_label", "TimeSlot", "n", "test_branch", "mean", "std",
            "skew", "kurt", "zero_share", "normal_before_outliers", "n_dropped", "cause"]
    allc[allc["false"]][cols].sort_values(["variant", "dir", "pos", "TimeSlot"]).round(3).to_csv(
        os.path.join(OUT, "false_cells_ALL.csv"), index=False)

    daily = c[c["day"] != "ALL"]
    by_stop = share(daily, ["variant", "dir", "pos", "Stop", "pos_label"])
    by_stop.to_csv(os.path.join(OUT, "false_by_stop.csv"))
    share(daily, ["variant", "dir", "TimeSlot"]).to_csv(os.path.join(OUT, "false_by_slot.csv"))
    wd = share(daily, ["variant", "dir", "day"]).reset_index()
    wd["day"] = pd.Categorical(wd["day"], WEEKDAYS, ordered=True)
    wd.sort_values(["variant", "dir", "day"]).to_csv(os.path.join(OUT, "false_by_weekday.csv"), index=False)

    f = c.copy()
    f["mean_bin"] = pd.cut(f["mean"], [-0.1, 5, 10, 20, 40, 80], labels=["<5", "5-10", "10-20", "20-40", ">=40"])
    f["zero_bin"] = pd.cut(f["zero_share"], [-0.01, 0.05, 0.15, 1], labels=["<5 %", "5-15 %", ">=15 %"])
    f["skew_bin"] = pd.cut(f["skew"], [-10, -0.3, 0.3, 1, 100], labels=["<-0,3", "-0,3..0,3", "0,3..1", ">1"])
    f["scope"] = np.where(f["day"] == "ALL", "ALL", "diario")
    rows = []
    for factor in ("test_branch", "mean_bin", "zero_bin", "skew_bin", "pos_label"):
        s = share(f, ["variant", "scope", factor]).reset_index()
        s = s.rename(columns={factor: "level"})
        s.insert(1, "factor", factor)
        rows.append(s)
    pd.concat(rows).to_csv(os.path.join(OUT, "false_by_factor.csv"), index=False)

    causes = c[c["false"]].groupby(["variant", "dir", c["day"].eq("ALL").map({True: "ALL", False: "diario"}), "cause"]).size()
    causes.rename("cells").to_csv(os.path.join(OUT, "false_causes.csv"))

    for v in VARIANTS:
        plot_heatmaps(c, v, plt)
        plot_profiles(c, v, plt)

    pd.set_option("display.width", 200)
    print(allc[allc["false"]][cols].sort_values(["variant", "dir", "pos", "TimeSlot"]).round(2).to_string())
    print(by_stop.to_string())
    print(pd.read_csv(os.path.join(OUT, "false_by_factor.csv")).to_string())
    print(causes.to_string())
    print(wd.to_string())


if __name__ == "__main__":
    main()
