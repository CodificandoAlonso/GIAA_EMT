"""
Carga y utilidades comunes para el analisis de AAA_TEST.

Trabaja sobre AAA_TEST/data (copia de DATOS/data) y reutiliza las funciones
estadisticas de DATOS/src (generate_gaussian.py) sin modificarlas.

Convenciones (las mismas que analisis_ALL_OCCUPATION.ipynb y la web):
    toA = Direction 2, sale de 2646 y termina en 5727 (ficheros E01_toA/NEW)
    toB = Direction 1, sale de 5727 y termina en 2646 (ficheros E01_toB)

Cada fichero clean_data_*.csv es una parada y contiene los dos sentidos.
Columnas del bloque de viaje: TripId, EventDate, EventTime (salida desde
cabecera, constante en todo el viaje), TimeSlot (franja de esa salida),
LogicVehicle, Weekday, DayType, FreeDay...
Columnas del bloque de parada: Stop, EventDate.1, EventTime.1 (paso por la
parada), TimeSlot.1, Board, DropOff, Occupation.
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AAA = os.path.join(ROOT, "AAA_TEST")
DATA = os.path.join(AAA, "data")
OUT = os.path.join(AAA, "output")

# Funciones estadisticas originales del proyecto
sys.path.insert(0, os.path.join(ROOT, "DATOS", "src"))

TIMESLOTS = list(range(5, 24))
WEEKDAYS = ["L", "M", "X", "J", "V"]

with open(os.path.join(ROOT, "BASE_DATA", "input_stops.txt")) as _f:
    _lines = _f.read().split()
STOPS = {
    "toA": [int(s) for s in _lines[0].split(",")],
    "toB": [int(s) for s in _lines[1].split(",")],
}

DIRECTION = {"toA": 2, "toB": 1}
HEADER = {"toA": 2646, "toB": 5727}
FILES = {
    "toA": os.path.join(DATA, "E01_toA", "NEW", "clean_data_newnew_*.csv"),
    "toB": os.path.join(DATA, "E01_toB", "clean_data_*.csv"),
}

# Umbrales de clean_dataframe / clean_dataframe_advanced / generate_gaussian_*
OCC_MIN, OCC_MAX = 0, 75          # clean_dataframe: 0 <= Occupation < 75
BD_MIN, BD_MAX = 0, 80            # clean_dataframe_advanced: 0 <= Board, DropOff < 80


def outdir(*parts: str) -> str:
    path = os.path.join(OUT, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def load_direction(direction: str, workdays_only: bool = True) -> pd.DataFrame:
    """Todas las filas de un sentido, con la posicion de la parada en la ruta.

    workdays_only aplica el filtro del proyecto: laborables sin gratuidad
    (DayType == "LA" y FreeDay == 0).
    """
    frames = []
    for f in sorted(glob.glob(FILES[direction])):
        x = pd.read_csv(f, encoding="utf-8")
        x["file_row"] = np.arange(len(x))       # orden original del fichero de la parada
        frames.append(x)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["Direction"] == DIRECTION[direction]].copy()
    if workdays_only:
        df = df[(df["DayType"] == "LA") & (df["FreeDay"] == 0)].copy()
    df["pos"] = df["Stop"].map({s: i for i, s in enumerate(STOPS[direction])})
    df["dep"] = pd.to_datetime(df["EventDate"] + " " + df["EventTime"].str.slice(0, 8))
    df["pass_time"] = pd.to_datetime(df["EventDate.1"] + " " + df["EventTime.1"].str.slice(0, 8))
    return df.sort_values(["TripId", "pos"]).reset_index(drop=True)


def flag_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Marca por fila los tipos de anomalia del APC.

    thr_occ   Occupation fuera de [0, 75)            (filtro de clean_dataframe)
    thr_bd    Board o DropOff fuera de [0, 80)       (filtro de clean_dataframe_advanced)
    clip0     el APC conto mas bajadas que gente a bordo y la ocupacion se
              guardo recortada a 0 (Occupation = 0 < anterior + subidas - bajadas)
    cons      ruptura real de conservacion entre paradas consecutivas:
              Occupation != max(0, anterior + subidas - bajadas)
    """
    df = df.copy()
    g = df.groupby("TripId", sort=False)
    prev_pos = g["pos"].shift()
    prev_occ = g["Occupation"].shift()
    consecutive = prev_pos == df["pos"] - 1
    expected = prev_occ + df["Board"] - df["DropOff"]

    df["thr_occ"] = (df["Occupation"] < OCC_MIN) | (df["Occupation"] >= OCC_MAX)
    df["thr_bd"] = (
        (df["Board"] < BD_MIN) | (df["Board"] >= BD_MAX)
        | (df["DropOff"] < BD_MIN) | (df["DropOff"] >= BD_MAX)
    )
    df["clip0"] = consecutive & (expected < 0) & (df["Occupation"] == 0)
    df["cons"] = consecutive & (df["Occupation"] != expected.clip(lower=0))
    df["thr"] = df["thr_occ"] | df["thr_bd"]
    return df


def trips_with(df: pd.DataFrame, mask: pd.Series) -> set:
    return set(df.loc[mask, "TripId"])


# ---- Estilo de graficas -------------------------------------------------
# Paleta categorica validada (azul, naranja, aqua) y rampa secuencial azul.
COLOR = {"toA": "#2a78d6", "toB": "#eb6834", "third": "#1baf7a"}
INK = {"primary": "#0b0b0b", "secondary": "#52514e", "grid": "#e4e3df"}
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 140,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.edgecolor": INK["secondary"],
        "axes.labelcolor": INK["primary"],
        "axes.titlesize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": INK["grid"],
        "grid.linewidth": 0.8,
        "xtick.color": INK["secondary"],
        "ytick.color": INK["secondary"],
        "legend.frameon": False,
        "lines.linewidth": 2,
    })
    return plt


def seq_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
