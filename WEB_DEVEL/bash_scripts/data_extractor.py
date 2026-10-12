#!/usr/bin/env python
"""
Analisis de la simulacion GAMA — version optimizada.

Mismo contrato de entrada que la version original (un CSV por replica en
RESULTS/, EVENTS/ y PASSENGERS/, con la linea de cabecera que escribe GAMA)
y mismas salidas (JSONs, PNGs, CSVs de Bhattacharyya). Los cambios son de
estructura interna, no de formato:

  1. Lectura: los 3 x N_SIMS ficheros se concatenan en memoria descartando
     la primera linea de cada uno (equivalente exacto a skiprows=1) y se
     parsean con UNA llamada a read_csv por carpeta, en lugar de 3000
     read_csv seguidos de concat.
  2. Las listas de espera se convierten a float de forma vectorizada (una
     sola conversion sobre la concatenacion) en lugar de ast.literal_eval
     fila a fila, y se explotan UNA vez a formato largo; antes se
     re-aplanaban dentro de cada bucle de parada y de franja.
  3. Los filtros booleanos repetidos dentro de bucles anidados se sustituyen
     por unas pocas agrupaciones (groupby) calculadas de antemano.
  4. Los momentos centrales se calculan con numpy en una sola pasada.
  5. El dibujado se acumula en una cola y se reparte entre procesos al final;
     cada trabajador reutiliza una unica figura.

Los valores numericos coinciden con la version original salvo en la ultima
cifra decimal (el orden de suma de algunas medias cambia). Diferencias de
comportamiento deliberadas, solo en casos limite que en la original
abortaban la ejecucion o contaminaban el porcentaje:

  - Celda de datos conocidos inexistente o NaN: se registra como
    'sin_dato_esperado' (no evaluable). La original abortaba si faltaba la
    fila y, si el valor era NaN, contaba la celda como evaluada y no
    fusionable.
  - Viaje sin filas en alguna parada de referencia: duracion/regularidad a
    NaN en lugar de ZeroDivisionError / IndexError.

Variables de entorno:
    SIM_N        numero de replicas a leer (defecto 1000, igual que antes)
    SIM_PLOTS    all (defecto) | summary | none
    SIM_PLOT_DPI 300 (defecto); 150 reduce el tiempo de rasterizado a ~1/4
    SIM_WORKERS  numero de procesos de dibujado (defecto: nucleos)
"""

import io
import json
import math
import os
import time as _time
from math import exp, log, sqrt

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

_T0 = _time.perf_counter()


def _tick(msg):
    print(f"[{_time.perf_counter() - _T0:7.1f} s] {msg}")


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
N_SIMS = int(os.environ.get("SIM_N", "1000"))
PLOT_MODE = os.environ.get("SIM_PLOTS", "all").lower()   # all | summary | none
PLOT_DPI = int(os.environ.get("SIM_PLOT_DPI", "300"))
N_WORKERS = int(os.environ.get("SIM_WORKERS", str(os.cpu_count() or 4)))

PLOT_STYLE = "seaborn-v0_8-whitegrid"

COLUMNS_RESULTS = [
    "simulation_id", "bus_code", "travels_completed", "stop_num", "direction",
    "current_time", "timeslot", "departure_timeslot", "boards",
    "residual_boards", "dropoffs", "occupation", "time_between_stops",
]

COLUMNS_EVENTS = [
    "simulation_id", "bus_code", "travels_completed", "stop_num", "direction",
    "timeslot", "event_code", "time_event", "param_event_1", "param_event_2",
]

COLUMNS_PASSENGERS = [
    "simulation_id", "bus_code", "travels_completed", "stop_num", "timeslot",
    "current_time", "list_passengers_time",
]


# ---------------------------------------------------------------------------
# Paradas cabecera excluidas de la COMPARACION de distribuciones.
#
# 2646 (La Peseta) y 5727 (Cibeles) son cabecera y terminal segun el sentido.
# En la terminal la magnitud registrada son bajadas, y en la cabecera la
# ocupacion es el resultado inmediato del embarque: en ninguno de los dos
# casos se compara lo mismo que en una parada intermedia.
#
# ALCANCE: SOLO la comparacion de distribuciones de ocupacion. Las medias
# siguen calculandose sobre TODAS las paradas. No se aplica a los tiempos
# entre paradas salvo que se active la bandera de abajo.
# ---------------------------------------------------------------------------
EXCLUDED_STOPS = {2646, 5727}
EXCLUDE_TERMINALS_IN_TIMES = False

MAX_CAPACITY = 80
threshold = 0.97


# ---------------------------------------------------------------------------
# Cola de dibujado
#
# Dibujar es la mayor parte del tiempo total y es trivialmente paralelizable:
# cada grafica es independiente. Se acumulan descripciones serializables
# (arrays ya calculados, etiquetas y ruta de salida) y se reparten al final.
# ---------------------------------------------------------------------------
_plot_jobs = []


def enqueue(job):
    if PLOT_MODE == "all":
        _plot_jobs.append(job)


_FIG = None


def _worker_init():
    global _FIG
    plt.style.use(PLOT_STYLE)
    _FIG = plt.figure()


def _fig(size):
    """Figura reutilizada: crear y destruir una por grafica cuesta mas que
    dibujarla cuando hay un millar de ellas."""
    global _FIG
    if _FIG is None:
        _worker_init()
    _FIG.clf()
    _FIG.set_size_inches(*size)
    return _FIG


def _render_bar(job):
    fig = _fig((12, 5))
    ax = fig.add_subplot(111)
    x = np.arange(len(job["x_labels"]))
    ax.bar(x, job["values"], width=0.4, label=job["legend"])
    ax.set_xticks(x + 0.2)
    ax.set_xticklabels(job["x_labels"], rotation=90)
    ax.set_ylabel(job["ylabel"])
    ax.set_xlabel(job["xlabel"])
    ax.set_title(job["title"])
    ax.legend()
    fig.tight_layout()
    fig.savefig(job["path"], dpi=PLOT_DPI)


def _render_dist(job):
    fig = _fig((12, 5))
    ax = fig.add_subplot(111)
    x = job["x"]
    ax.plot(x, job["y1"], color="blue", linewidth=2, label=job["sim_label"])
    ax.fill_between(x, job["y1"], alpha=0.15, color="blue")
    ax.plot(x, job["y2"], color="red", linewidth=2, label=job["exp_label"])
    ax.fill_between(x, job["y2"], alpha=0.15, color="red")
    ax.set_xlabel(job["xlabel"])
    ax.set_ylabel("Densidad de probabilidad")
    ax.set_title(job["title"])
    ax.legend(title=job["legend_title"], loc="upper right")
    fig.tight_layout()
    fig.savefig(job["path"], dpi=PLOT_DPI)


_RENDERERS = {"bar": _render_bar, "dist": _render_dist}


def _render(job):
    _RENDERERS[job["kind"]](job)


def flush_plots():
    if not _plot_jobs:
        return
    _tick(f"Dibujando {len(_plot_jobs)} graficas con {N_WORKERS} procesos...")
    if N_WORKERS <= 1:
        _worker_init()
        for job in _plot_jobs:
            _render(job)
        return
    import multiprocessing as mp
    ctx = mp.get_context("fork") if hasattr(os, "fork") else mp.get_context()
    with ctx.Pool(N_WORKERS, initializer=_worker_init) as pool:
        for _ in pool.imap_unordered(_render, _plot_jobs, chunksize=8):
            pass


def save_barcode(horizontal_data, vertical_data, horizontal_label,
                 vertical_label, leyend, label, filename):
    enqueue({
        "kind": "bar",
        "x_labels": list(horizontal_data),
        "values": [float(v) if v is not None and np.isfinite(v) else np.nan
                   for v in vertical_data],
        "xlabel": horizontal_label,
        "ylabel": vertical_label,
        "legend": leyend,
        "title": label,
        "path": filename,
    })


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
# SIM_DIR (exported by run_simulation.sh) names the simulation to analyse;
# .last_simulation is only a fallback for running this script by hand.
sim_dir = os.environ.get("SIM_DIR")
if not sim_dir:
    with open(f"{os.getcwd()}/.last_simulation", "r") as f:
        sim_dir = f.read().strip()
# Every path below is built as f"{os.getcwd()}/{sim_dir}/...".
sim_dir = os.path.relpath(sim_dir, os.getcwd())

DESCRIPTION = {}
with open(f"{os.getcwd()}/{sim_dir}/description.txt", "r") as f:
    for line in f:
        parts = line.strip().split(" ", 1)
        if len(parts) == 2:
            DESCRIPTION[parts[0]] = parts[1]

if DESCRIPTION.get("line") == "401":
    stops_list_toA = [2646, 562, 4090, 4188, 5939, 3995, 3991, 3903, 2539,
                      2535, 1929, 4032, 5360, 82, 5727]
    stops_list_toB = [5727, 81, 1167, 2538, 3929, 3990, 3994, 5938, 4187,
                      2964, 649, 2646]
    to_A = "Cibeles"
    to_B = "La Peseta"


def read_sim_logs(folder, columns, required=True, str_cols=()):
    """Lee los N_SIMS logs de una carpeta como un unico DataFrame.

    Cada fichero se abre en binario, se descarta su primera linea (la
    cabecera de GAMA, igual que skiprows=1 en la version original) y los
    cuerpos se concatenan en memoria. El parseo es una sola llamada a
    read_csv, con lo que desaparecen 1000 inicializaciones del lector y el
    concat posterior. El orden de filas es el mismo: replica 0, 1, 2, ...

    required=False reproduce el try/except de EVENTS: un fichero ausente o
    con solo cabecera no aporta filas.
    """
    base = f"{os.getcwd()}/{sim_dir}/{folder}"
    chunks = []
    missing = 0
    for i in range(N_SIMS):
        path = f"{base}/log_Simulation {i}.csv"
        try:
            with open(path, "rb") as fh:
                fh.readline()
                body = fh.read()
        except FileNotFoundError:
            if required:
                raise
            missing += 1
            continue
        if body:
            if not body.endswith(b"\n"):
                body += b"\n"
            chunks.append(body)

    if missing:
        print(f"  {folder}: {missing} replicas sin fichero (sin filas)")
    if not chunks:
        return pd.DataFrame(columns=columns)

    buf = b"".join(chunks)
    kw = dict(header=None, names=columns, encoding="utf-8",
              dtype={c: str for c in str_cols})
    # pyarrow parsea en varios hilos; si no esta instalado o rechaza algo,
    # se cae al motor C, que es el que usaba la version original.
    try:
        return pd.read_csv(io.BytesIO(buf), engine="pyarrow", **kw)
    except Exception:
        return pd.read_csv(io.BytesIO(buf), low_memory=False, **kw)


_tick("Cargando datos...")

joint_dataframe_results = read_sim_logs(
    "RESULTS", COLUMNS_RESULTS, str_cols=("current_time",))

joint_dataframe_events = read_sim_logs(
    "EVENTS", COLUMNS_EVENTS, required=False,
    str_cols=("time_event", "param_event_1"))

joint_dataframe_passengers = read_sim_logs(
    "PASSENGERS", COLUMNS_PASSENGERS,
    str_cols=("current_time", "list_passengers_time"))

print(f"  {len(joint_dataframe_results)} filas de resultados, "
      f"{len(joint_dataframe_passengers)} de pasajeros, "
      f"{len(joint_dataframe_events)} eventos")


def to_seconds(value):
    """Convierte a segundos tanto 'HH:MM[:SS]' como un numero de segundos."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float("nan")
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    s = str(value).strip()
    if ":" in s:
        parts = [int(p) for p in s.split(":")]
        while len(parts) < 3:
            parts.append(0)
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return float(s)


def to_seconds_series(series):
    """Version vectorizada de to_seconds para una columna 'H:MM[:SS]'.

    Una jornada tiene como mucho unas decenas de miles de instantes
    distintos frente a millones de filas: se convierte cada valor distinto
    una sola vez y se reexpande con los codigos de factorize.
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    codes, uniques = pd.factorize(series)
    conv = np.array([to_seconds(u) for u in uniques], dtype=np.float64)
    out = np.full(len(series), np.nan)
    ok = codes >= 0
    out[ok] = conv[codes[ok]]
    return pd.Series(out, index=series.index)


joint_dataframe_results["current_time_s"] = to_seconds_series(
    joint_dataframe_results["current_time"])


# ---------------------------------------------------------------------------
# Tiempos de espera: explosion unica a formato largo.
#
# GAMA escribe cada lista como '[12.0,30.5,...]'. En lugar de evaluar cada
# fila con ast.literal_eval, se limpian los corchetes con operaciones de
# cadena de pandas, se concatena todo y se convierte a float en una sola
# llamada. El numero de elementos por fila sale de contar separadores, y
# se comprueba contra el total convertido: cualquier valor malformado
# aborta con la fila culpable, igual que abortaba literal_eval.
# ---------------------------------------------------------------------------
def explode_wait_lists(series):
    # Corchetes y comillas exteriores fuera; ';' -> ',' por si la lista
    # llegara con el separador que se puso al guardarla.
    txt = (series.fillna("").astype(str)
           .str.strip("[]\"' ")
           .str.replace(";", ",", regex=False))
    nonempty = txt.str.len().to_numpy() > 0
    rows = txt[nonempty].tolist()

    lens = np.zeros(len(txt), dtype=np.int64)
    if not rows:
        return np.empty(0, dtype=np.float64), lens

    # Elementos por fila sin recorrer las filas en Python: se unen con un
    # separador de fila ('|') y se cuentan las comas entre separadores.
    joined = "|".join(rows)
    raw = np.frombuffer(joined.encode("ascii", "replace"), dtype=np.uint8)
    commas = np.cumsum(raw == ord(","))
    bounds = np.flatnonzero(raw == ord("|"))
    per_row_commas = np.diff(np.concatenate(
        ([0], commas[bounds], [commas[-1]])))
    lens[nonempty] = per_row_commas + 1
    total = int(lens.sum())

    try:
        flat = np.fromstring(joined.replace("|", ","), dtype=np.float64,
                             sep=",")
    except ValueError:
        flat = np.empty(0, dtype=np.float64)

    if flat.size != total:
        for i, v in enumerate(txt.tolist()):
            try:
                if v:
                    [float(x) for x in v.split(",")]
            except ValueError:
                raise ValueError(
                    f"list_passengers_time malformado en la fila {i}: "
                    f"{series.iloc[i]!r}") from None
        raise ValueError("list_passengers_time: recuento de valores "
                         f"inconsistente ({flat.size} != {total})")
    return flat, lens


_tick("Explotando tiempos de espera...")

_flat, _lens = explode_wait_lists(
    joint_dataframe_passengers["list_passengers_time"])
_total = int(_flat.size)
_rowidx = np.repeat(np.arange(len(_lens), dtype=np.int64), _lens)

_pass_stop = joint_dataframe_passengers["stop_num"].to_numpy()
_pass_ts = joint_dataframe_passengers["timeslot"].to_numpy()

waits_df = pd.DataFrame({
    "stop_num": _pass_stop[_rowidx],
    "timeslot": _pass_ts[_rowidx],
    "wait": _flat,
})

MEAN_WAIT_GLOBAL = float(np.nanmean(_flat)) if _total else float("nan")
_wait_by_stop = (waits_df.groupby("stop_num")["wait"].mean().to_dict()
                 if _total else {})
_wait_by_stop_ts = (
    waits_df.groupby(["stop_num", "timeslot"])["wait"].mean().to_dict()
    if _total else {})

del _flat, _rowidx, waits_df


# ---------------------------------------------------------------------------
# Datos conocidos
# ---------------------------------------------------------------------------
known_occupation_values_toA = pd.read_csv(
    f"{os.getcwd()}/../data/known_data/NORMAL_OCCUPATION_toA.csv")
known_occupation_values_toB = pd.read_csv(
    f"{os.getcwd()}/../data/known_data/NORMAL_OCCUPATION_toB.csv")
known_times_stops_toA = pd.read_csv(
    f"{os.getcwd()}/../data/known_data/NORMAL_times_stops_toA.csv")
known_times_stops_toB = pd.read_csv(
    f"{os.getcwd()}/../data/known_data/NORMAL_times_stops_toB.csv")

timeslots = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
             22, 23]


def _index_first(df, col):
    """Indexa por `col` quedandose con la primera fila de cada clave, que es
    la que devolvia el .iloc[0] de la version original."""
    t = df.set_index(col)
    return t[~t.index.duplicated(keep="first")]


_known_occ = {
    "to_A": _index_first(known_occupation_values_toA, "Stop"),
    "to_B": _index_first(known_occupation_values_toB, "Stop"),
}
_known_tim = {
    "to_A": _index_first(known_times_stops_toA, "StopsCodes"),
    "to_B": _index_first(known_times_stops_toB, "StopsCodes"),
}


def known_occupation(direction, stopcode, timeslot):
    tab = _known_occ[direction]
    try:
        row = tab.loc[stopcode]
    except KeyError:
        return float("nan"), float("nan")
    return float(row[f"Mean_{timeslot}"]), float(row[f"std_{timeslot}"])


def known_time(direction, key, timeslot):
    tab = _known_tim[direction]
    try:
        row = tab.loc[key]
    except KeyError:
        return float("nan"), float("nan")
    return float(row[f"Mean_{timeslot}"]), float(row[f"Std_{timeslot}"])


regularity_toA = {}
regularity_toB = {}

known_times_stops_toA_regularity = known_times_stops_toA.iloc[1:-1]
known_times_stops_toB_regularity = known_times_stops_toB.iloc[1:-1]

for timeslot in timeslots:
    col_name = f"Mean_{timeslot}"
    regularity_toA[timeslot] = known_times_stops_toA_regularity[col_name].sum()
    # caso especial toB: la franja 5 no tiene datos, se usa la 6
    if timeslot == 5:
        regularity_toB[timeslot] = (
            known_times_stops_toB_regularity["Mean_6"].sum())
    else:
        regularity_toB[timeslot] = (
            known_times_stops_toB_regularity[col_name].sum())


# ---------------------------------------------------------------------------
# Registro de comparaciones Bhattacharyya.
#
# Una fila por celda (tipo, sentido, parada/tramo, franja), TAMBIEN si la
# celda se descarta, para que el denominador del porcentaje sea honesto. Se
# reportan dos porcentajes: sobre celdas evaluadas y sobre celdas totales.
# Las paradas de EXCLUDED_STOPS no se registran.
# ---------------------------------------------------------------------------
bhatt_registry = []


def register_bhatt(tipo, direction, key, timeslot, coeff=None, dist=None,
                   estado="evaluada", metodo=None, n_sim=0,
                   mean_sim=None, std_sim=None, mean_esp=None, std_esp=None):
    """tipo: 'ocupacion' | 'tiempo'.  key: codigo de parada o 'A-B'."""
    sesgo = None
    if mean_sim is not None and mean_esp is not None:
        sesgo = float(mean_sim) - float(mean_esp)
    sesgo_sigmas = None
    if sesgo is not None and std_esp:
        sesgo_sigmas = sesgo / float(std_esp)
    bhatt_registry.append({
        "tipo": tipo,
        "direccion": direction,
        "elemento": str(key),
        "franja": timeslot,
        "metodo": metodo,
        "n_sim": n_sim,
        "coeff": coeff,
        "distancia": dist,
        "estado": estado,
        "fusionable": (None if coeff is None else bool(coeff >= threshold)),
        "mean_sim": (None if mean_sim is None else float(mean_sim)),
        "std_sim": (None if std_sim is None else float(std_sim)),
        "mean_esp": (None if mean_esp is None else float(mean_esp)),
        "std_esp": (None if std_esp is None else float(std_esp)),
        "sesgo": sesgo,
        "sesgo_sigmas": sesgo_sigmas,
    })


def resumen_bhatt(sub):
    n = len(sub)
    ev = sub[sub["estado"] == "evaluada"]
    n_ev = len(ev)
    fus = int(ev["fusionable"].sum()) if n_ev else 0
    return {
        "celdas": n,
        "evaluadas": n_ev,
        "no_evaluables": n - n_ev,
        "fusionables": fus,
        "pct_fusionables": (100.0 * fus / n_ev) if n_ev else None,
        "pct_fusionables_sobre_total": (100.0 * fus / n) if n else None,
        "coeff_medio": float(ev["coeff"].mean()) if n_ev else None,
        "coeff_mediana": float(ev["coeff"].median()) if n_ev else None,
        "coeff_min": float(ev["coeff"].min()) if n_ev else None,
    }


def tramo_excluido(par):
    """True si el tramo toca una cabecera y se ha pedido excluirlos."""
    return EXCLUDE_TERMINALS_IN_TIMES and bool(set(par) & EXCLUDED_STOPS)


def bhattacharyya_distance(mean_1, mean_2, std_1, std_2):
    return (0.25 * ((mean_1 - mean_2) ** 2 / (std_1 ** 2 + std_2 ** 2))
            + 0.5 * log((std_1 ** 2 + std_2 ** 2) / (2 * (std_1 * std_2))))


def bhattacharyya_coefficient(mean_1, mean_2, std_1, std_2):
    return (sqrt(2 * (std_1 * std_2 / (std_1 ** 2 + std_2 ** 2)))
            * exp(-(((mean_1 - mean_2) ** 2) / (4 * (std_1 ** 2 + std_2 ** 2)))))


# ---------------------------------------------------------------------------
# Momentos y normalidad: una pasada vectorizada en lugar de cinco generadores
# de Python por celda. El criterio de decision es el de la version original.
# ---------------------------------------------------------------------------
def _moments(x):
    """Devuelve (n, media, m2, m3, m4) en una sola pasada."""
    n = x.size
    mean = x.mean()
    d = x - mean
    d2 = d * d
    m2 = d2.mean()
    m3 = (d2 * d).mean()
    m4 = (d2 * d2).mean()
    return n, float(mean), float(m2), float(m3), float(m4)


def is_normal_simplified(variables):
    """Devuelve (aprox_normal, muestra_saneada, media, desviacion)."""
    x = np.asarray(variables, dtype=float)
    x = x[np.isfinite(x)]

    if x.size == 0:
        return np.bool_(False), x, 0, 0
    elif x.size < 50:
        z_crit = 1.96
    elif x.size < 300:
        z_crit = 3.29
    else:
        z_crit = "False"

    n, mean, m2, m3, m4 = _moments(x)

    # Varianza nula: en la original asimetria y curtosis salian NaN y la
    # comparacion devolvia False. Mismo resultado, sin el aviso de numpy.
    if m2 <= 1e-12:
        return np.bool_(False), x, float(mean), 0.0

    skew = m3 / m2 ** 1.5
    kurt = (m4 / m2 ** 2) - 3

    se_skew = math.sqrt(6.0 / n)
    se_kurt = math.sqrt(24.0 / n)
    std_dev = math.sqrt(m2)

    if z_crit != "False":
        approx_normal = (abs(skew / se_skew) <= z_crit) and \
                        (abs(kurt / se_kurt) <= z_crit)
    else:
        approx_normal = (abs(skew) <= 2) and (abs(kurt) + 3 <= 7)

    return np.bool_(approx_normal), x, mean, std_dev


def regularity_calc(theoretical_interval, real_interval,
                    in_time_format: bool) -> float:
    if not in_time_format:
        It = to_seconds(theoretical_interval) / 60
        Ir = to_seconds(real_interval) / 60
    else:
        It = theoretical_interval / 60
        Ir = real_interval / 60

    if np.isnan(Ir) or np.isnan(It):
        return float("nan")

    if Ir > 2 * It:
        return 0.0

    if It <= 10:
        if Ir - It <= 2:
            return 100.0
        return 100 * (1 - ((Ir - (It + 2)) / (It - 2)))
    elif It <= 25:
        if Ir <= 1.2 * It:
            return 100.0
        return 100 * (1 - ((Ir - 1.2 * It) / (0.8 * It)))
    else:
        if Ir - It <= 5:
            return 100.0
        return 100 * (1 - ((Ir - (It + 5)) / (It - 5)))


# ---------------------------------------------------------------------------
# Comparacion de distribuciones. El coeficiente se calcula aqui (hace falta
# para el registro); solo el dibujado se difiere.
# ---------------------------------------------------------------------------
def _compare(tipo, sim_data, mean_2, std_2, direction, key, timeslot,
             is_normal, plot):
    """Nucleo comun a ocupacion y tiempos. `plot` describe el dibujado."""
    sim_data = np.asarray(sim_data, dtype=float)
    sim_data = sim_data[np.isfinite(sim_data)]

    if not np.isfinite(mean_2) or not np.isfinite(std_2):
        register_bhatt(tipo, direction, key, timeslot,
                       estado="sin_dato_esperado", n_sim=sim_data.size)
        return

    if std_2 <= 1e-9 or sim_data.size < 2:
        register_bhatt(tipo, direction, key, timeslot,
                       estado=("sin_varianza_esperada" if std_2 <= 1e-9
                               else "sin_datos_sim"),
                       n_sim=sim_data.size)
        return

    x_min_exp = mean_2 - 4 * std_2
    x_max_exp = mean_2 + 4 * std_2

    mean_1 = float(sim_data.mean())
    std_1 = float(sim_data.std(ddof=1))

    if is_normal:
        if std_1 <= 1e-9:
            register_bhatt(tipo, direction, key, timeslot,
                           estado="sin_varianza_sim", metodo="normal",
                           n_sim=sim_data.size)
            return

        x_min = min(mean_1 - 4 * std_1, x_min_exp)
        x_max = max(mean_1 + 4 * std_1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = norm.pdf(x, mean_1, std_1)
        y2 = norm.pdf(x, mean_2, std_2)

        bhatt_dist = bhattacharyya_distance(mean_1, mean_2, std_1, std_2)
        bhatt_coeff = bhattacharyya_coefficient(mean_1, mean_2, std_1, std_2)
        sim_label = f"Simulación Normal (μ={mean_1:.2f}, σ={std_1:.2f})"
    else:
        from scipy.stats import gaussian_kde

        if std_1 <= 1e-9:
            register_bhatt(tipo, direction, key, timeslot,
                           estado="sin_varianza_sim", metodo="kde",
                           n_sim=sim_data.size)
            return
        kde = gaussian_kde(sim_data)
        x_min = min(float(sim_data.min()) - 1, x_min_exp)
        x_max = max(float(sim_data.max()) + 1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = kde(x)
        y2 = norm.pdf(x, mean_2, std_2)

        # Coeficiente de Bhattacharyya por integracion trapezoidal
        bhatt_coeff = float(np.trapezoid(np.sqrt(y1 * y2), x))
        bhatt_coeff = min(bhatt_coeff, 1.0)
        bhatt_dist = -np.log(bhatt_coeff) if bhatt_coeff > 0 else np.inf
        sim_label = f"Simulación KDE (n={sim_data.size})"

    veredict = ("Fusionables ('Equivalentes')" if bhatt_coeff >= threshold
                else "No fusionables (Distintas)")

    register_bhatt(tipo, direction, key, timeslot,
                   coeff=float(bhatt_coeff), dist=float(bhatt_dist),
                   estado="evaluada",
                   metodo=("normal" if is_normal else "kde"),
                   n_sim=sim_data.size,
                   mean_sim=mean_1, std_sim=std_1,
                   mean_esp=float(mean_2), std_esp=float(std_2))

    enqueue({
        "kind": "dist",
        "x": x, "y1": y1, "y2": y2,
        "sim_label": sim_label,
        "exp_label": f"Esperado (μ={mean_2:.2f}, σ={std_2:.2f})",
        "xlabel": plot["xlabel"],
        "title": plot["title"],
        "legend_title": (f"Distancia de Bhattacharyya = {bhatt_dist:.4f}  "
                         f"coeff = {bhatt_coeff:.4f}\n→ {veredict}"),
        "path": plot["path"],
    })


def compute_and_save_distribution_comparasion(
    sim_data, mean_2, std_2, direction, stopcode, timeslot, is_normal=True
):
    # Cabeceras fuera del numerador y del denominador del porcentaje.
    if int(stopcode) in EXCLUDED_STOPS:
        return
    _compare(
        "ocupacion", sim_data, mean_2, std_2, direction, stopcode, timeslot,
        is_normal,
        {
            "xlabel": "Ocupación del Autobús al paso por parada",
            "title": (f"Comparativa de distribuciones – parada {stopcode}, "
                      f"Franja {timeslot}"),
            "path": (f"{os.getcwd()}/{sim_dir}/PLOTS/{direction}/stops/"
                     f"occupation_comparaison_{stopcode}"
                     f"_per_timeslot_{timeslot}.png"),
        })


def compute_and_save_distribution_comparasion_times(
    sim_data, mean_2, std_2, direction, stopcode, timeslot, is_normal=True
):
    # Los tramos solo se excluyen si se ha pedido explicitamente.
    if tramo_excluido(stopcode):
        return
    tramo = f"{stopcode[0]}-{stopcode[1]}"
    _compare(
        "tiempo", sim_data, mean_2, std_2, direction, tramo, timeslot,
        is_normal,
        {
            "xlabel": (f"Tiempo medio entre paradas {stopcode[0]}-"
                       f"{stopcode[1]} medido en segundos"),
            "title": (f"Comparativa de distribuciones – paradas "
                      f"{stopcode[0]}-{stopcode[1]}, Franja {timeslot}"),
            "path": (f"{os.getcwd()}/{sim_dir}/PLOTS/{direction}/times/"
                     f"time_between_stops_comparaison_{stopcode[0]}-"
                     f"{stopcode[1]}_per_timeslot_{timeslot}.png"),
        })


# ---------------------------------------------------------------------------
# Agrupaciones precalculadas: unas pocas pasadas sobre los datos y despues
# todo son consultas a diccionario, en lugar de una mascara booleana sobre
# el DataFrame completo por cada celda.
# ---------------------------------------------------------------------------
def group_arrays(df, keys, value):
    """{clave: ndarray} con los valores finitos de `value` por grupo, en el
    orden original de las filas."""
    sub = df[keys + [value]].dropna(subset=[value])
    if not len(sub):
        return {}
    return {k: v.to_numpy(dtype=float)
            for k, v in sub.groupby(keys, sort=False)[value]}


def group_means(df, keys, value):
    sub = df[keys + [value]]
    if not len(sub):
        return {}
    return sub.groupby(keys, sort=False)[value].mean().to_dict()


def gmean(d, key):
    v = d.get(key)
    return float("nan") if v is None else v


_tick("Agrupando resultados...")

data_toA = joint_dataframe_results[joint_dataframe_results["direction"] == "toA"]
data_toB = joint_dataframe_results[joint_dataframe_results["direction"] == "toB"]

_by_dir = {"to_A": data_toA, "to_B": data_toB}

# Arrays por (parada, franja de salida): necesarios para normalidad y KDE.
G_OCC_DEP = {d: group_arrays(df, ["stop_num", "departure_timeslot"],
                             "occupation")
             for d, df in _by_dir.items()}
G_DROP_DEP = {d: group_arrays(df, ["stop_num", "departure_timeslot"],
                              "dropoffs")
              for d, df in _by_dir.items()}

# Medias por (parada, franja de paso): boards, residuales y bajadas.
M_BOARDS_TS = {d: group_means(df, ["stop_num", "timeslot"], "boards")
               for d, df in _by_dir.items()}
M_RESID_TS = {d: group_means(df, ["stop_num", "timeslot"], "residual_boards")
              for d, df in _by_dir.items()}
M_DROP_TS = {d: group_means(df, ["stop_num", "timeslot"], "dropoffs")
             for d, df in _by_dir.items()}

# Tiempos entre paradas por (parada, franja de paso).
G_TIME_TS = {d: group_arrays(df, ["stop_num", "timeslot"],
                             "time_between_stops")
             for d, df in _by_dir.items()}
M_TIME_TS = {d: group_means(df, ["stop_num", "timeslot"], "time_between_stops")
             for d, df in _by_dir.items()}
M_TIME_ALL = {d: group_means(df, ["stop_num"], "time_between_stops")
              for d, df in _by_dir.items()}


# ---------------------------------------------------------------------------
# KPIs generales
# ---------------------------------------------------------------------------
json_output_general_info = {}

json_output_general_info["Occupation_toA"] = (
    data_toA["occupation"].mean() / MAX_CAPACITY) * 100
json_output_general_info["Occupation_toB"] = (
    data_toB["occupation"].mean() / MAX_CAPACITY) * 100
json_output_general_info["Occupation"] = (
    joint_dataframe_results["occupation"].mean() / MAX_CAPACITY) * 100

logic_buses = joint_dataframe_results["bus_code"].unique()
json_output_general_info["Logical_Buses"] = len(logic_buses)

# +1 porque travels_completed empieza en 0
_max_trip = joint_dataframe_results.groupby("bus_code")["travels_completed"].max()
json_output_general_info["Total_Trips"] = int((_max_trip + 1).sum())

json_output_general_info["Mean_await_passengers"] = MEAN_WAIT_GLOBAL
json_output_general_info["Regularity_value"] = 0
regularity_global = []


# --- graficas de evolucion del % de ocupacion a lo largo del dia ----------
_occ_dep_toA = data_toA.groupby("departure_timeslot")["occupation"].mean()
_occ_dep_toB = data_toB.groupby("departure_timeslot")["occupation"].mean()
_occ_dep_all = joint_dataframe_results.groupby(
    "departure_timeslot")["occupation"].mean()

list_occupation_values_toA = [
    (_occ_dep_toA.get(ts, np.nan) / MAX_CAPACITY) * 100 for ts in timeslots]
list_occupation_values_toB = [
    (_occ_dep_toB.get(ts, np.nan) / MAX_CAPACITY) * 100 for ts in timeslots]
list_occupation = [
    (_occ_dep_all.get(ts, np.nan) / MAX_CAPACITY) * 100 for ts in timeslots]

plt.style.use(PLOT_STYLE)

save_barcode(timeslots, list_occupation_values_toA, "TimeSlots",
             "% de Ocupación", f"Sentido {to_A}",
             "Ocupación del bus por franja horaria",
             f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/"
             f"occupation_per_timeslot_toA.png")

save_barcode(timeslots, list_occupation_values_toB, "TimeSlots",
             "% de Ocupación", f"Sentido {to_B}",
             "Ocupación del bus por franja horaria",
             f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/"
             f"occupation_per_timeslot_toB.png")

save_barcode(timeslots, list_occupation, "TimeSlots", "% de Ocupación",
             "Datos Generales", "Ocupación del bus por franja horaria",
             f"{os.getcwd()}/{sim_dir}/PLOTS/general/"
             f"occupation_per_timeslot_general.png")


stops_list_toA = [int(data) for data in stops_list_toA]
stops_list_toB = [int(data) for data in stops_list_toB]

json_stops_info_toA = {}
json_stops_info_toB = {}


def procesa_paradas(direction, stops_here, out_json, plots_subdir):
    """Bucle de paradas, comun a ambos sentidos.

    La ultima parada del sentido es terminal: la magnitud registrada son
    bajadas y no ocupacion, y no hay embarques.
    """
    occ_dep = G_OCC_DEP[direction]
    drop_dep = G_DROP_DEP[direction]
    m_boards = M_BOARDS_TS[direction]
    m_resid = M_RESID_TS[direction]
    m_drop = M_DROP_TS[direction]

    for stopcode in stops_here:
        es_terminal = (stopcode == stops_here[-1])
        j = out_json[f"{stopcode}"] = {}
        # Marca para la interfaz: la parada se calcula igual que siempre, solo
        # queda fuera del porcentaje de equivalencia de distribuciones.
        j["excluded_from_bhatt"] = bool(stopcode in EXCLUDED_STOPS)
        j["Occupation_percentage_per_timeslot"] = {}
        j["Board_dropoff_per_timeslot"] = {}

        pct_por_ts = []
        muestras_por_ts = []
        boards_por_ts = []
        resid_por_ts = []
        drop_por_ts = []

        for timeslot in timeslots:
            fuente = drop_dep if es_terminal else occ_dep
            vals = fuente.get((stopcode, timeslot))
            if vals is None:
                vals = np.array([], dtype=float)
            muestras_por_ts.append(vals)

            media = float(vals.mean()) if vals.size else float("nan")
            pct = (media / MAX_CAPACITY) * 100
            pct_por_ts.append(pct)

            if es_terminal:
                b = r = 0
                d = media
            else:
                b = gmean(m_boards, (stopcode, timeslot))
                r = gmean(m_resid, (stopcode, timeslot))
                d = gmean(m_drop, (stopcode, timeslot))

            boards_por_ts.append(b)
            resid_por_ts.append(r)
            drop_por_ts.append(d)

            j["Occupation_percentage_per_timeslot"][timeslot] = pct
            j["Board_dropoff_per_timeslot"][timeslot] = {
                "boards": b, "unable_boards": r, "dropoffs": d,
            }

        save_barcode(timeslots, pct_por_ts, "TimeSlots", "% de Ocupación",
                     f"Stop {stopcode}",
                     "Ocupación media por franja horaria de los autobuses",
                     f"{os.getcwd()}/{sim_dir}/PLOTS/{plots_subdir}/stops/"
                     f"occupation_per_timeslot_{stopcode}.png")

        j["Occupation_percentage"] = np.nanmean(pct_por_ts)
        j["mean_boards"] = np.nanmean(boards_por_ts)
        j["unable_boards"] = np.nanmean(resid_por_ts)
        j["mean_dropoffs"] = np.nanmean(drop_por_ts)

        # KPI: distribucion teorica frente a simulada, por franja.
        for idx, timeslot in enumerate(timeslots):
            normal_sim, vars_sim, _, _ = is_normal_simplified(
                muestras_por_ts[idx])
            mean_known, std_known = known_occupation(
                direction, stopcode, timeslot)
            compute_and_save_distribution_comparasion(
                vars_sim, mean_known, std_known, direction, stopcode,
                timeslot, normal_sim)

        # Tiempo medio de espera por pasajero (ambos sentidos, como antes).
        j["Mean_await_time_general"] = _wait_by_stop.get(
            stopcode, float("nan"))
        j["Mean_await_time_per_timeslot"] = {
            ts: _wait_by_stop_ts.get((stopcode, ts), float("nan"))
            for ts in timeslots
        }


_tick("Procesando paradas sentido A...")
procesa_paradas("to_A", stops_list_toA, json_stops_info_toA, "to_A")

_tick("Procesando paradas sentido B...")
procesa_paradas("to_B", stops_list_toB, json_stops_info_toB, "to_B")


# ---------------------------------------------------------------------------
# Ocupacion por autobus fisico
# ---------------------------------------------------------------------------
_tick("Procesando autobuses...")
unique_bus = joint_dataframe_results["bus_code"].unique()

input_json_route = f"{os.getcwd()}/{sim_dir}/includes/INPUTS/final_input.json"
with open(input_json_route, "r") as f:
    input_json = json.load(f)

# Una pasada por cada magnitud que el bucle recalculaba con mascaras.
_bts = ["bus_code", "travels_completed", "stop_num"]
M_TRIP_STOP_OCC = group_means(joint_dataframe_results, _bts, "occupation")
M_TRIP_STOP_DROP = group_means(joint_dataframe_results, _bts, "dropoffs")
M_TRIP_STOP_TIME = group_means(joint_dataframe_results, _bts, "current_time_s")
M_TRIP_OCC = group_means(joint_dataframe_results,
                         ["bus_code", "travels_completed"], "occupation")
F_TRIP_STOP_TS = (joint_dataframe_results
                  .groupby(_bts, sort=False)["timeslot"].first().to_dict())
TRIPS_BY_BUS = (joint_dataframe_results
                .groupby("bus_code", sort=False)["travels_completed"]
                .unique().to_dict())

# bus_code NO se convierte a numero: en GAMA es el id del JSON de entrada y
# puede no ser numerico.
if len(joint_dataframe_events):
    _ev = joint_dataframe_events
    _delay = (to_seconds_series(_ev["time_event"])
              - to_seconds_series(_ev["param_event_1"]))
    _g = _delay.groupby([_ev["bus_code"], _ev["travels_completed"]],
                        sort=False)
    EV_COUNT = _g.size().to_dict()
    EV_DELAY = _g.mean().to_dict()
else:
    EV_COUNT, EV_DELAY = {}, {}

new_bus_json_data = {}

for bus in unique_bus:
    new_bus_json_data[f"{bus}"] = {}
    unique_trips = [int(t) for t in TRIPS_BY_BUS.get(bus, [])]

    for trip in unique_trips:
        n_events = EV_COUNT.get((bus, trip), 0)
        total_percentage_of_delays_per_trip = (n_events / N_SIMS) * 100
        mean_delay_in_minutes_per_trip = EV_DELAY.get((bus, trip),
                                                      float("nan"))

        data_inputs = input_json[str(bus)][trip]

        trip_occupation_percentage = (
            gmean(M_TRIP_OCC, (bus, trip)) / MAX_CAPACITY) * 100

        mean_time_of_trip = float("nan")
        regularity_value = float("nan")

        if int(data_inputs[0]) == stops_list_toA[0]:
            direction = "to_A"
            stops_here = stops_list_toA
            regularity_table = regularity_toA
        else:
            direction = "toB"
            stops_here = stops_list_toB
            regularity_table = regularity_toB

        # Duracion media: llegada media a la terminal - paso medio por cabecera
        t_last = gmean(M_TRIP_STOP_TIME, (bus, trip, stops_here[-1]))
        t_first = gmean(M_TRIP_STOP_TIME, (bus, trip, stops_here[0]))
        mean_time_of_trip = t_last - t_first

        # Regularidad entre la segunda y la penultima parada
        t_top = gmean(M_TRIP_STOP_TIME, (bus, trip, stops_here[-2]))
        t_bottom = gmean(M_TRIP_STOP_TIME, (bus, trip, stops_here[1]))
        ts_last = F_TRIP_STOP_TS.get((bus, trip, stops_here[-1]))

        if ts_last is not None and np.isfinite(ts_last):
            timeslot_trip = int(ts_last)
            if timeslot_trip > 23:
                timeslot_trip = 23
            regularity_value = regularity_calc(
                regularity_table[timeslot_trip], t_top - t_bottom, True)
            regularity_global.append(regularity_value)

        list_mean_values = []
        for stop in stops_here:
            if stop != stops_here[-1]:
                v = gmean(M_TRIP_STOP_OCC, (bus, trip, stop))
            else:
                v = gmean(M_TRIP_STOP_DROP, (bus, trip, stop))
            list_mean_values.append((v / MAX_CAPACITY) * 100)

        if direction == "to_A":
            save_barcode(stops_list_toA, list_mean_values,
                         f"Paradas en sentido {to_A}", "% de Ocupación",
                         f"Ocupación del viaje nº: {trip}",
                         f"Ocupación del autobús por parada para el bus: "
                         f"{bus} con salida estimada {data_inputs[1]}",
                         f"{os.getcwd()}/{sim_dir}/PLOTS/buses/"
                         f"mean_occupation_per_stop_toA_{bus}_{trip}.png")
        else:
            save_barcode(stops_list_toB, list_mean_values,
                         f"Paradas en sentido {to_B}", "% de ocupación",
                         f"Ocupación del viaje nº: {trip}",
                         f"Ocupación del autobús por parada para el bus: "
                         f"{bus} con salida estimada {data_inputs[1]}",
                         f"{os.getcwd()}/{sim_dir}/PLOTS/buses/"
                         f"mean_occupation_per_stop_toB_{bus}_{trip}.png")

        new_bus_json_data[f"{bus}"][f"{data_inputs[0]}-{data_inputs[1]}"] = {
            "Mean_Occupation_Percentage": trip_occupation_percentage,
            "Direction": direction,
            "Mean_time_of_trip": mean_time_of_trip,
            "Percentage_sims_delay_departure": total_percentage_of_delays_per_trip,
            "Mean_Minutes_departure_delay": mean_delay_in_minutes_per_trip,
            "Regularity_value": regularity_value,
        }


# ---------------------------------------------------------------------------
# Tiempos entre paradas
# ---------------------------------------------------------------------------
_tick("Procesando tiempos entre paradas...")


def procesa_tiempos(direction, stops_here, out_json):
    """El tiempo entre paradas se registra en la parada de llegada."""
    out_json["times_stops"] = {}
    g_arr = G_TIME_TS[direction]
    m_ts = M_TIME_TS[direction]
    m_all = M_TIME_ALL[direction]

    for counter, stop in enumerate(stops_here[1:]):
        prev = stops_here[counter]
        key = f"{prev}-{stop}"
        entry = out_json["times_stops"][key] = {}
        entry["general_time"] = gmean(m_all, stop)
        entry["time_per_timeslot"] = {}
        entry["expected_time_per_timeslot"] = {}

        expected_times = []
        for timeslot in timeslots:
            entry["time_per_timeslot"][timeslot] = gmean(m_ts,
                                                         (stop, timeslot))
            vals = g_arr.get((stop, timeslot))
            if vals is None:
                vals = np.array([], dtype=float)

            normal_sim, var_sim, _, _ = is_normal_simplified(vals)
            mean_known, std_known = known_time(direction, key, timeslot)
            expected_times.append(mean_known)
            entry["expected_time_per_timeslot"][timeslot] = mean_known

            compute_and_save_distribution_comparasion_times(
                var_sim, mean_known, std_known, direction, [prev, stop],
                timeslot, normal_sim)

        entry["expected_time"] = np.mean(expected_times)


procesa_tiempos("to_A", stops_list_toA, json_stops_info_toA)
procesa_tiempos("to_B", stops_list_toB, json_stops_info_toB)

json_output_general_info["Regularity_value"] = (
    np.nanmean(regularity_global) if regularity_global else float("nan"))


# ---------------------------------------------------------------------------
# Porcentaje de distribuciones equivalentes (coeficiente de Bhattacharyya)
#
# Agregacion a cuatro niveles separando ocupacion de tiempos entre paradas;
# 'conjunto' es solo una cifra de contexto.
# ---------------------------------------------------------------------------
df_bhatt = pd.DataFrame(bhatt_registry)

bhatt_summary = {
    "umbral": threshold,
    "paradas_excluidas_de_la_comparacion": sorted(EXCLUDED_STOPS),
    "tramos_excluidos": EXCLUDE_TERMINALS_IN_TIMES,
    "general": {},
    "por_direccion": {},
    "por_elemento": {},
    "por_franja": {},
}

if len(df_bhatt):
    for tipo in ("ocupacion", "tiempo"):
        sub = df_bhatt[df_bhatt["tipo"] == tipo]
        if not len(sub):
            continue
        _res = resumen_bhatt(sub)
        _ev2 = sub[sub["estado"] == "evaluada"].dropna(subset=["sesgo"])
        if len(_ev2):
            _res["sesgo_medio"] = float(_ev2["sesgo"].astype(float).mean())
            _res["sesgo_medio_sigmas"] = float(
                _ev2["sesgo_sigmas"].dropna().astype(float).mean())
            _res["pct_celdas_por_debajo"] = float(
                100.0 * (_ev2["sesgo"].astype(float) < 0).mean())
        bhatt_summary["general"][tipo] = _res
        bhatt_summary["por_direccion"][tipo] = {
            str(x): resumen_bhatt(sub[sub["direccion"] == x])
            for x in sorted(sub["direccion"].unique())
        }
        bhatt_summary["por_elemento"][tipo] = {
            str(x): resumen_bhatt(sub[sub["elemento"] == x])
            for x in sorted(sub["elemento"].unique())
        }
        bhatt_summary["por_franja"][tipo] = {
            str(int(x)): resumen_bhatt(sub[sub["franja"] == x])
            for x in sorted(sub["franja"].unique())
        }
    bhatt_summary["general"]["conjunto"] = resumen_bhatt(df_bhatt)

json_output_general_info["Bhattacharyya"] = bhatt_summary

# Cifras planas para la interfaz, sin navegar el diccionario.
for _t in ("ocupacion", "tiempo", "conjunto"):
    _g2 = bhatt_summary["general"].get(_t)
    if _g2:
        json_output_general_info[f"Pct_equivalentes_{_t}"] = _g2["pct_fusionables"]

print(f"\n=== Equivalencia de distribuciones (Bhattacharyya >= {threshold}) ===")
print(f"  paradas fuera de la comparacion: {sorted(EXCLUDED_STOPS)}")
for _t in ("ocupacion", "tiempo", "conjunto"):
    _g2 = bhatt_summary["general"].get(_t)
    if not _g2:
        continue
    _p = "n/d" if _g2["pct_fusionables"] is None else f"{_g2['pct_fusionables']:.2f}%"
    print(f"  {_t:10} {_g2['fusionables']:4}/{_g2['evaluadas']:4} = {_p:>8}"
          f"   (no evaluables: {_g2['no_evaluables']}, "
          f"coeff medio: {_g2['coeff_medio']})")
    if _g2.get("sesgo_medio") is not None:
        print(f"             sesgo medio {_g2['sesgo_medio']:+.3f} "
              f"({_g2['sesgo_medio_sigmas']:+.2f} sigma), "
              f"{_g2['pct_celdas_por_debajo']:.1f}% de celdas por debajo")


def sanitize_for_json(obj):
    """Recursively replace NaN/Inf with None for valid JSON."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    elif isinstance(obj, (np.floating, np.integer)):
        val = float(obj)
        return None if math.isnan(val) or math.isinf(val) else val
    return obj


with open(f"{os.getcwd()}/{sim_dir}/PLOTS/buses/general_info.json", "w") as f:
    json.dump(sanitize_for_json(new_bus_json_data), f, indent=4)

with open(f"{os.getcwd()}/{sim_dir}/PLOTS/json_output_general_info.json", "w") as f:
    json.dump(sanitize_for_json(json_output_general_info), f, indent=4)

with open(f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/general_info_toA.json", "w") as f:
    json.dump(sanitize_for_json(json_stops_info_toA), f, indent=4)

with open(f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/general_info_toB.json", "w") as f:
    json.dump(sanitize_for_json(json_stops_info_toB), f, indent=4)


# ---------------------------------------------------------------------------
# Salidas de la equivalencia de distribuciones
# ---------------------------------------------------------------------------
BHATT_DIR = f"{os.getcwd()}/{sim_dir}/PLOTS/general"
BHATT_COL = {"ocupacion": "#1f77b4", "tiempo": "#d62728"}


def fig_bhatt_pct_por_franja(summary, outfile):
    tipos = [t for t in ("ocupacion", "tiempo") if t in summary["por_franja"]]
    if not tipos:
        return
    franjas = sorted({int(f) for t in tipos for f in summary["por_franja"][t]})
    x = np.arange(len(franjas))
    w = 0.8 / len(tipos)
    plt.figure(figsize=(12, 5))
    for i, t in enumerate(tipos):
        vals = [(summary["por_franja"][t].get(str(f)) or {}).get("pct_fusionables")
                for f in franjas]
        vals = [np.nan if v is None else v for v in vals]
        plt.bar(x + i * w, vals, width=w, label=t.capitalize(),
                color=BHATT_COL[t])
    plt.xticks(x + 0.4 - w / 2, franjas)
    plt.ylim(0, 105)
    plt.xlabel("Franja horaria")
    plt.ylabel("% de distribuciones equivalentes")
    plt.title("Equivalencia de distribuciones por franja "
              f"(Bhattacharyya >= {threshold})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outfile, dpi=PLOT_DPI)
    plt.close()


def fig_bhatt_histograma(df, outfile):
    ev = df[df["estado"] == "evaluada"]
    if not len(ev):
        return
    plt.figure(figsize=(12, 5))
    for t in ("ocupacion", "tiempo"):
        s = ev[ev["tipo"] == t]["coeff"].astype(float)
        if len(s):
            plt.hist(s, bins=40, alpha=0.55, color=BHATT_COL[t],
                     label=f"{t.capitalize()} (n={len(s)})")
    plt.axvline(threshold, ls="--", lw=1.5, color="black",
                label=f"umbral = {threshold}")
    plt.xlabel("Coeficiente de Bhattacharyya")
    plt.ylabel("Numero de celdas")
    plt.title("Distribucion del coeficiente de Bhattacharyya")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outfile, dpi=PLOT_DPI)
    plt.close()


def fig_bhatt_sim_vs_esperado(df, tipo, outfile):
    """Diagnostico: media simulada frente a media esperada, celda a celda.

    Nube por debajo de la diagonal = desfase sistematico de nivel.
    Nube dispersa a ambos lados  = error de perfil que se cancela en la
    media global y que el KPI agregado no deja ver.
    """
    ev = df[(df["estado"] == "evaluada") & (df["tipo"] == tipo)]
    ev = ev.dropna(subset=["mean_sim", "mean_esp"])
    if not len(ev):
        return
    xs = ev["mean_esp"].astype(float)
    ys = ev["mean_sim"].astype(float)
    ok = ev["fusionable"].astype(bool)
    lim = float(max(xs.max(), ys.max())) * 1.05
    plt.figure(figsize=(7, 7))
    plt.scatter(xs[~ok], ys[~ok], s=18, alpha=0.55, color="#d62728",
                label=f"No equivalentes (n={int((~ok).sum())})")
    plt.scatter(xs[ok], ys[ok], s=18, alpha=0.75, color="#2ca02c",
                label=f"Equivalentes (n={int(ok.sum())})")
    plt.plot([0, lim], [0, lim], ls="--", lw=1.2, color="black",
             label="identidad")
    _b = float(ev["sesgo"].astype(float).mean())
    plt.xlim(0, lim)
    plt.ylim(0, lim)
    plt.xlabel("Media esperada (datos EMT)")
    plt.ylabel("Media simulada")
    plt.title(f"Simulado frente a esperado por celda ({tipo})\n"
              f"sesgo medio = {_b:+.2f}")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(outfile, dpi=PLOT_DPI)
    plt.close()


def fig_bhatt_pct_por_elemento(summary, tipo, outfile):
    d = summary["por_elemento"].get(tipo)
    if not d:
        return
    items = sorted(d.items(),
                   key=lambda kv: (kv[1]["pct_fusionables"] is None,
                                   kv[1]["pct_fusionables"]))
    keys = [k for k, _ in items]
    vals = [np.nan if v["pct_fusionables"] is None else v["pct_fusionables"]
            for _, v in items]
    plt.figure(figsize=(12, 5))
    plt.bar(np.arange(len(keys)), vals, width=0.6, color=BHATT_COL[tipo])
    plt.xticks(np.arange(len(keys)), keys, rotation=90)
    plt.ylim(0, 105)
    plt.xlabel("Parada" if tipo == "ocupacion" else "Tramo")
    plt.ylabel("% de distribuciones equivalentes")
    plt.title("Equivalencia por "
              f"{'parada' if tipo == 'ocupacion' else 'tramo'} ({tipo})")
    plt.tight_layout()
    plt.savefig(outfile, dpi=PLOT_DPI)
    plt.close()


if len(df_bhatt):
    df_bhatt.to_csv(f"{BHATT_DIR}/bhatt_detalle.csv", index=False)

    _rows = []
    for _nivel in ("general", "por_direccion", "por_elemento", "por_franja"):
        _blk = bhatt_summary[_nivel]
        for _tipo, _v in _blk.items():
            if _nivel == "general":
                _rows.append({"nivel": _nivel, "tipo": _tipo, "clave": "-", **_v})
            else:
                for _k, _m in _v.items():
                    _rows.append({"nivel": _nivel, "tipo": _tipo,
                                  "clave": _k, **_m})
    pd.DataFrame(_rows).to_csv(f"{BHATT_DIR}/bhatt_resumen.csv", index=False)

    if PLOT_MODE in ("all", "summary"):
        fig_bhatt_pct_por_franja(bhatt_summary,
                                 f"{BHATT_DIR}/bhatt_pct_por_franja.png")
        fig_bhatt_histograma(df_bhatt,
                             f"{BHATT_DIR}/bhatt_histograma_coeff.png")
        fig_bhatt_pct_por_elemento(bhatt_summary, "ocupacion",
                                   f"{BHATT_DIR}/bhatt_pct_por_parada.png")
        fig_bhatt_pct_por_elemento(bhatt_summary, "tiempo",
                                   f"{BHATT_DIR}/bhatt_pct_por_tramo.png")
        fig_bhatt_sim_vs_esperado(df_bhatt, "ocupacion",
                                  f"{BHATT_DIR}/bhatt_sim_vs_esperado_ocupacion.png")
        fig_bhatt_sim_vs_esperado(df_bhatt, "tiempo",
                                  f"{BHATT_DIR}/bhatt_sim_vs_esperado_tiempo.png")

    with open(f"{BHATT_DIR}/bhatt_summary.json", "w") as f:
        json.dump(sanitize_for_json(bhatt_summary), f, indent=4)


flush_plots()

_tick("Hecho.")