"""
Reproduccion de generate_gaussian_per_slot_all_days / generate_gaussian_per_slot_days
de DATOS/src/analisis_ALL_OCCUPATION.ipynb.

La logica es la misma linea a linea (is_normal_modified, estimate_outliers con
n = 1 % de la muestra, eliminacion de los outliers por primera aparicion del
valor en la franja y nuevo test); solo cambia que devuelve, ademas de
media/std/normalidad, el indice de las filas eliminadas como outlier, para
poder quitar el viaje entero en las variantes por viaje.

fixed_daily=True corrige un detalle de la version diaria: los outliers se
detectan en los datos del dia de la semana, pero el notebook los busca para
borrarlos en la franja con todos los dias; si el valor aparece antes en otro dia
se borra esa otra fila y el outlier sigue en la muestra. Con fixed_daily se
buscan solo entre las filas de ese dia.
"""

from math import sqrt

import numpy as np
import pandas as pd

import common  # noqa: F401  (anade DATOS/src al path)
from generate_gaussian import central_moment, estimate_outliers, is_normal_modified

PARAM = "Occupation"


def cell(data_per_timeslot: pd.DataFrame, day: str, time: int, fixed_daily: bool = False) -> dict:
    """Una celda (parada, franja[, dia]) exactamente como en el notebook."""
    gauss_hypothesis, instances_involved = is_normal_modified(data_per_timeslot, day, time, PARAM, False)
    outliers_found, dropped = [], []
    tested_before = None

    if not isinstance(instances_involved, list) and not instances_involved.empty:
        tested_before = bool(gauss_hypothesis)
        current_values = instances_involved[PARAM].tolist()
        n = int(0.01 * len(instances_involved))
        outliers_found = estimate_outliers(current_values, n, False)

        if not gauss_hypothesis and len(outliers_found) > 0:
            search = data_per_timeslot
            if fixed_daily and day != "ALL":
                search = data_per_timeslot[data_per_timeslot["Weekday"] == day]
            temp_values = search[PARAM].tolist()
            for outlier in outliers_found:
                if outlier in temp_values:
                    idx = search.index[temp_values.index(outlier)]
                    dropped.append(idx)
                    temp_values[temp_values.index(outlier)] = None
            data_cleaned = data_per_timeslot.drop(index=dropped)
            gauss_hypothesis, instances_involved = is_normal_modified(data_cleaned, day, time, PARAM, False)

    if not isinstance(instances_involved, list) and not instances_involved.empty:
        values = instances_involved[PARAM].tolist()
        x = np.asarray(values, dtype=float)
        n = len(values)
        m2 = central_moment(values, 2)
        skew = central_moment(values, 3) / m2 ** 1.5 if m2 > 0 else np.nan
        kurt = central_moment(values, 4) / m2 ** 2 - 3 if m2 > 0 else np.nan
        return {
            "mean": float(np.mean(values)), "std": sqrt(m2), "is_normal": bool(gauss_hypothesis),
            "normal_before_outliers": tested_before, "n": n, "n_outliers_found": len(outliers_found),
            "n_dropped": len(dropped), "dropped_idx": dropped,
            "skew": float(skew), "kurt": float(kurt),
            "zero_share": float((x == 0).mean()),
            "test_branch": "n<50" if n < 50 else ("50<=n<300" if n < 300 else "n>=300"),
        }
    return {"mean": 0, "std": 0, "is_normal": "NO DATA", "normal_before_outliers": None, "n": 0,
            "n_outliers_found": 0, "n_dropped": 0, "dropped_idx": [], "skew": np.nan,
            "kurt": np.nan, "zero_share": np.nan, "test_branch": "none"}


def run_stop(stop_df: pd.DataFrame, days=("ALL",), fixed_daily: bool = False) -> list:
    """Todas las franjas de una parada. stop_df ya filtrado (sentido, laborables, Occupation)."""
    dataframe = stop_df[(stop_df[PARAM] <= 80) & (stop_df[PARAM] >= 0)]
    dataframe = dataframe[(dataframe["DayType"] == "LA") & (dataframe["FreeDay"] == 0)]
    dataframe = dataframe.sort_values("file_row")            # orden del fichero original
    rows = []
    if dataframe.empty:
        return rows
    stop = int(dataframe["Stop"].iloc[0])
    for day in days:
        for time in range(5, 24):
            data_per_timeslot = dataframe[dataframe["TimeSlot"] == time].copy()
            r = cell(data_per_timeslot, day, time, fixed_daily)
            r.update({"Stop": stop, "day": day, "TimeSlot": time})
            rows.append(r)
    return rows
