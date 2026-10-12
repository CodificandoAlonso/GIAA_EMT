"""
Parte 2: distribuciones de ocupacion por parada y franja (TimeSlot del viaje),
quitando la fila anomala (como hoy) frente a quitar el viaje entero.

Variantes (todas sobre laborables sin gratuidad, mismo pipeline del notebook):
    A          fila: lo actual. Fuera filas con Occupation fuera de [0, 75) y
               outliers EDC fila a fila en las franjas no normales.
    B_err      viaje: fuera el viaje entero si tiene algun error claro del APC
               (Occupation < 0, Board/DropOff fuera de [0, 80) o ruptura de
               conservacion). Occupation >= 75 se sigue quitando solo como fila.
    B_all      viaje: fuera el viaje entero ante cualquier anomalia, incluida
               Occupation >= 75.
    B_err_edc  B_err y, ademas, fuera el viaje entero de cada fila que el test
               EDC elimina como outlier (en cualquier parada y franja).
    A_fixdaily A con la correccion de la busqueda de outliers en la version diaria
               (solo cambia los resultados por dia de la semana).

Salidas en AAA_TEST/output/part2/:
    cells.csv                  una fila por (variante, sentido, dia, parada, franja)
    variant_summary.csv        % normales, filas y viajes por variante
    comparison_vs_A.csv        diferencias de media/std y distancia de Bhattacharyya vs A
    carryover.csv              desviacion (z) de las filas validas de viajes anomalos
    NORMAL_OCCUPATION_<sentido>_<variante>.csv   mismo formato que known_data
    *.png
"""

import os
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import (COLOR, INK, STOPS, TIMESLOTS, WEEKDAYS, flag_anomalies, load_direction,
                    outdir, setup_matplotlib)
from occupation_pipeline import run_stop
from fussion_gauss import bhattacharyya_distance

OUT = outdir("part2")
DIRS = ("toA", "toB")
DAYS = ("ALL",) + tuple(WEEKDAYS)


# --------------------------------------------------------------------------

def _job(args):
    stop_df, days, fixed = args
    return run_stop(stop_df, days, fixed)


def run_pipeline(rows: pd.DataFrame, fixed_daily: bool = False) -> pd.DataFrame:
    """Pipeline del notebook sobre las filas dadas (ya filtradas por sentido y laborables)."""
    rows = rows[(rows["Occupation"] >= 0) & (rows["Occupation"] < 75)]      # clean_dataframe
    stops = [g for _, g in rows.groupby("Stop")]
    with Pool(4) as p:
        res = p.map(_job, [(g, DAYS, fixed_daily) for g in stops])
    return pd.DataFrame([r for part in res for r in part])


def variant_rows(df: pd.DataFrame, variant: str) -> pd.DataFrame:
    if variant in ("A", "A_fixdaily"):
        return df
    err = df["cons"] | df["thr_bd"] | (df["Occupation"] < 0)
    if variant in ("B_err", "B_err_edc"):
        bad = set(df.loc[err, "TripId"])
    elif variant == "B_all":
        bad = set(df.loc[err | df["thr_occ"], "TripId"])
    return df[~df["TripId"].isin(bad)]


def carryover(df: pd.DataFrame, d: str) -> pd.DataFrame:
    """Desviacion de las filas que hoy entran en las distribuciones (Occupation en
    [0, 75)) de viajes con anomalia, antes y despues de la primera parada anomala,
    frente a las de viajes limpios. z respecto a media/std de los viajes limpios
    en la misma (parada, franja)."""
    df = df.copy()
    df["occ_neg"] = df["Occupation"] < 0
    df["occ_high"] = df["Occupation"] >= 75
    anomalous = df["thr"] | df["cons"]
    clean_trips = set(df["TripId"]) - set(df.loc[anomalous, "TripId"])
    ref = df[df["TripId"].isin(clean_trips)].groupby(["Stop", "TimeSlot"])["Occupation"].agg(["mean", "std"])
    df = df.join(ref, on=["Stop", "TimeSlot"])
    df["z"] = (df["Occupation"] - df["mean"]) / df["std"]
    ok = (df["Occupation"] >= 0) & (df["Occupation"] < 75) & ~df["thr_bd"]
    last = len(STOPS[d]) - 1
    term = df[df["pos"] == last].set_index("TripId")["Occupation"]

    out = []

    def add(label, mask, trips_set):
        x = df[mask]
        rt = term.reindex(list(trips_set)).dropna()
        out.append({
            "dir": d, "group": label, "rows": int(len(x)), "trips": len(trips_set),
            "z_mean": round(float(x["z"].mean()), 3),
            "abs_z_mean": round(float(x["z"].abs().mean()), 3),
            "share_abs_z_gt2": round(float((x["z"].abs() > 2).mean()), 4),
            "terminal_residual_median": float(rt.median()) if len(rt) else np.nan,
            "terminal_residual_p90": float(rt.quantile(0.9)) if len(rt) else np.nan,
        })

    add("viajes limpios", ok & df["TripId"].isin(clean_trips), clean_trips)
    k = df[anomalous].groupby("TripId")["pos"].min().rename("k")
    df = df.join(k, on="TripId")
    anom_trips = set(k.index)
    add("anómalos: antes de la anomalía", ok & df["k"].notna() & (df["pos"] < df["k"]), anom_trips)
    add("anómalos: después de la anomalía", ok & df["k"].notna() & (df["pos"] > df["k"]) & ~anomalous, anom_trips)

    # Solo errores claros del contador (sin viajes con Occupation >= 75, que son
    # viajes cargados de punta a punta y mezclarian el efecto)
    err = df["occ_neg"] | df["thr_bd"] | df["cons"]
    high_trips = set(df.loc[df["occ_high"], "TripId"])
    k_err = df[err & ~df["TripId"].isin(high_trips)].groupby("TripId")["pos"].min().rename("k_err")
    df = df.join(k_err, on="TripId")
    err_trips = set(k_err.index)
    add("errores claros: antes del error", ok & df["k_err"].notna() & (df["pos"] < df["k_err"]), err_trips)
    add("errores claros: después del error", ok & df["k_err"].notna() & (df["pos"] > df["k_err"]) & ~err, err_trips)
    kinds = {"Occupation < 0": "occ_neg", "Occupation >= 75": "occ_high",
             "Board/DropOff fuera de rango": "thr_bd", "ruptura de conservación": "cons"}
    sets = {lab: set(df.loc[df[c], "TripId"]) for lab, c in kinds.items()}
    for lab, s in sets.items():
        only = s - set().union(*[o for l2, o in sets.items() if l2 != lab])
        add(f"solo {lab}", ok & df["TripId"].isin(only), only)
    return pd.DataFrame(out)


def export_normal(cells: pd.DataFrame, d: str, variant: str):
    """Mismo formato que WEB_DEVEL/data/known_data/NORMAL_OCCUPATION_<d>.csv."""
    c = cells[(cells["dir"] == d) & (cells["variant"] == variant) & (cells["day"] == "ALL")]
    wide = {"Stop": []}
    for t in TIMESLOTS:
        wide[f"Mean_{t}"] = []
        wide[f"std_{t}"] = []
    for stop, g in c.groupby("Stop", sort=False):
        g = g.set_index("TimeSlot")
        wide["Stop"].append(stop)
        for t in TIMESLOTS:
            wide[f"Mean_{t}"].append(g.at[t, "mean"])
            wide[f"std_{t}"].append(g.at[t, "std"])
    pd.DataFrame(wide).to_csv(os.path.join(OUT, f"NORMAL_OCCUPATION_{d}_{variant}.csv"), index=False)


# --------------------------------------------------------------------------

def plot_carryover(co: pd.DataFrame, plt):
    groups = ["viajes limpios", "errores claros: antes del error", "errores claros: después del error",
              "solo Occupation >= 75"]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    x = np.arange(len(groups))
    for i, d in enumerate(DIRS):
        v = co[co["dir"] == d].set_index("group").loc[groups, "share_abs_z_gt2"] * 100
        bars = ax.bar(x + (i - 0.5) * 0.38, v, 0.36, color=COLOR[d], label=d)
        for b, val in zip(bars, v):
            ax.annotate(f"{val:.1f} %", (b.get_x() + b.get_width() / 2, val), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=8, color=INK["secondary"])
    ax.set_xticks(x)
    ax.set_xticklabels(["viajes limpios", "error del contador:\nfilas antes del error",
                        "error del contador:\nfilas después del error", "viajes con ocupación ≥ 75:\nresto de filas"])
    ax.set_ylabel("% de filas con |z| > 2")
    ax.set_title("Filas que hoy entran en las distribuciones: desviación respecto a viajes limpios")
    ax.legend(loc="upper left")
    ax.grid(axis="x", visible=False)
    fig.savefig(os.path.join(OUT, "carryover.png"))
    plt.close(fig)


def plot_delta_heatmaps(cmp: pd.DataFrame, plt):
    """Cambio de la media (variante - A) por parada y franja, celdas ALL."""
    variants = ["B_err_edc", "B_all"]
    fig, axes = plt.subplots(len(DIRS), len(variants), figsize=(13, 8.2))
    from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
    div = LinearSegmentedColormap.from_list("div", ["#c0392b", "#f0efec", "#2a78d6"])
    lim = max(1.0, float(cmp.loc[cmp["variant"].isin(variants), "d_mean"].abs().quantile(0.99)))
    for r, d in enumerate(DIRS):
        for c, v in enumerate(variants):
            ax = axes[r, c]
            x = cmp[(cmp["dir"] == d) & (cmp["variant"] == v)]
            mat = x.pivot(index="Stop", columns="TimeSlot", values="d_mean").reindex(STOPS[d])
            im = ax.imshow(mat.values, aspect="auto", cmap=div, norm=TwoSlopeNorm(0, -lim, lim))
            ax.set_yticks(range(len(mat.index)))
            ax.set_yticklabels(mat.index, fontsize=7)
            ax.set_xticks(range(0, len(TIMESLOTS), 2))
            ax.set_xticklabels(TIMESLOTS[::2], fontsize=8)
            ax.grid(False)
            name = {"B_err_edc": "B_err+EDC (recomendada)", "B_all": "B_all"}[v]
            ax.set_title(f"{d} · {name} − A (viajeros)", fontsize=10)
            if c == 0:
                ax.set_ylabel("parada (orden de ruta)")
            if r == len(DIRS) - 1:
                ax.set_xlabel("franja")
    fig.colorbar(im, ax=axes, shrink=0.6, label="cambio de la media de ocupación")
    fig.savefig(os.path.join(OUT, "delta_mean_heatmaps.png"))
    plt.close(fig)


# --------------------------------------------------------------------------

def main_carryover():
    plt = setup_matplotlib()
    co = pd.concat([carryover(flag_anomalies(load_direction(d)), d) for d in DIRS], ignore_index=True)
    co.to_csv(os.path.join(OUT, "carryover.csv"), index=False)
    plot_carryover(co, plt)
    print(co.to_string())


def main():
    plt = setup_matplotlib()
    all_cells, summaries, co_all = [], [], []

    for d in DIRS:
        df = flag_anomalies(load_direction(d))
        co_all.append(carryover(df, d))

        edc_trips = set()
        for variant in ("A", "A_fixdaily", "B_err", "B_all", "B_err_edc"):
            rows = variant_rows(df, variant)
            if variant == "B_err_edc":
                rows = rows[~rows["TripId"].isin(edc_trips)]
            cells = run_pipeline(rows, fixed_daily=(variant == "A_fixdaily"))
            if variant == "B_err":
                dropped = [i for lst in cells.loc[cells["day"] == "ALL", "dropped_idx"] for i in lst]
                edc_trips = set(rows.loc[dropped, "TripId"])
            cells["dir"] = d
            cells["variant"] = variant
            all_cells.append(cells)

            used = rows[(rows["Occupation"] >= 0) & (rows["Occupation"] < 75)]
            for scope, sub in (("ALL", cells[cells["day"] == "ALL"]), ("diario", cells[cells["day"] != "ALL"])):
                tested = sub[sub["is_normal"] != "NO DATA"]
                summaries.append({
                    "dir": d, "variant": variant, "scope": scope,
                    "cells_tested": len(tested), "true": int((tested["is_normal"] == True).sum()),  # noqa: E712
                    "pct_true": round(100 * (tested["is_normal"] == True).mean(), 2),  # noqa: E712
                    "rows_used": len(used), "trips_used": used["TripId"].nunique(),
                    "trips_removed": df["TripId"].nunique() - rows["TripId"].nunique(),
                    "edc_rows_dropped": int(sub["n_dropped"].sum()),
                })
            print(d, variant, summaries[-2]["pct_true"], summaries[-1]["pct_true"], flush=True)

    cells = pd.concat(all_cells, ignore_index=True)
    cells.drop(columns=["dropped_idx"]).to_csv(os.path.join(OUT, "cells.csv"), index=False)
    summary = pd.DataFrame(summaries)
    summary.to_csv(os.path.join(OUT, "variant_summary.csv"), index=False)
    co = pd.concat(co_all, ignore_index=True)
    co.to_csv(os.path.join(OUT, "carryover.csv"), index=False)

    # Comparacion de cada variante frente a A (celdas ALL, las que se exportan)
    key = ["dir", "Stop", "TimeSlot"]
    base = cells[(cells["variant"] == "A") & (cells["day"] == "ALL")].set_index(key)
    cmp = []
    for v in ("B_err", "B_all", "B_err_edc"):
        x = cells[(cells["variant"] == v) & (cells["day"] == "ALL")].set_index(key)
        j = x.join(base, rsuffix="_A")
        j["d_mean"] = j["mean"] - j["mean_A"]
        j["d_std"] = j["std"] - j["std_A"]
        j["bhattacharyya"] = [bhattacharyya_distance(a, b, s1, s2) if s1 > 0 and s2 > 0 else np.nan
                              for a, b, s1, s2 in zip(j["mean"], j["mean_A"], j["std"], j["std_A"])]
        j["normal_changed"] = j["is_normal"].astype(str) != j["is_normal_A"].astype(str)
        j["variant"] = v
        cmp.append(j.reset_index()[key + ["variant", "mean_A", "mean", "d_mean", "std_A", "std", "d_std",
                                          "bhattacharyya", "is_normal_A", "is_normal", "normal_changed",
                                          "n_A", "n"]])
    cmp = pd.concat(cmp, ignore_index=True)
    cmp.to_csv(os.path.join(OUT, "comparison_vs_A.csv"), index=False)

    for d in DIRS:
        for v in ("A", "B_err", "B_all", "B_err_edc"):
            export_normal(cells, d, v)

    # Celdas punta: donde se concentran las Occupation >= 75
    peak = cmp.groupby(["dir", "variant"]).apply(
        lambda g: pd.Series({
            "cells": len(g),
            "mean_abs_d_mean": g["d_mean"].abs().mean(),
            "max_abs_d_mean": g["d_mean"].abs().max(),
            "mean_d_mean": g["d_mean"].mean(),
            "cells_abs_d_mean_gt1": int((g["d_mean"].abs() > 1).sum()),
            "bhattacharyya_mean": g["bhattacharyya"].mean(),
            "bhattacharyya_max": g["bhattacharyya"].max(),
            "normal_changed": int(g["normal_changed"].sum()),
        }), include_groups=False).round(3)
    peak.to_csv(os.path.join(OUT, "comparison_summary.csv"))

    plot_carryover(co, plt)
    plot_delta_heatmaps(cmp, plt)
    print(summary.to_string())
    print(co.to_string())
    print(peak.to_string())


def main_plots():
    plt = setup_matplotlib()
    plot_carryover(pd.read_csv(os.path.join(OUT, "carryover.csv")), plt)
    plot_delta_heatmaps(pd.read_csv(os.path.join(OUT, "comparison_vs_A.csv")), plt)


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    {"carryover": main_carryover, "plots": main_plots}.get(mode, main)()
