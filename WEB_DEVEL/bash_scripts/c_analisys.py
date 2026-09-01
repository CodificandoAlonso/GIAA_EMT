#!/usr/bin/env python
"""
Analisis de la simulacion — version para la reescritura en C.

Diferencia con el script original de GAMA: en lugar de N_SIMS ficheros por
carpeta (log_Simulation 0.csv ... log_Simulation 999.csv) se lee UN solo
fichero por carpeta, con cabecera:

    RESULTS/results.csv
    EVENTS/anomalies.csv
    PASSENGERS/passengers.csv

Las cabeceras deben usar exactamente los nombres de columna que el script
original asignaba con `names=`. Ver COLUMNS_* mas abajo.

La salida (JSONs, PNGs, CSVs de Bhattacharyya) es identica a la del script
original.
"""

import ast
import json
import math
import os
from math import exp, log, sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

# ---------------------------------------------------------------------------
# Cabeceras esperadas.
#
# El emisor en C debe escribir estos nombres, en este orden, como primera
# linea de cada fichero.
# ---------------------------------------------------------------------------
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

# La simulacion en C emite la direccion como entero (0 = CIBELES = toA).
DIRECTION_MAP = {0: "toA", 1: "toB", "0": "toA", "1": "toB"}


with open(f"{os.getcwd()}/.last_simulation", "r") as f:
    sim_dir = f.read().strip()


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


# ---------------------------------------------------------------------------
# Paradas cabecera excluidas de la COMPARACION de distribuciones.
#
# 2646 (La Peseta) y 5727 (Cibeles) son cabecera y terminal segun el sentido.
# En la terminal la magnitud registrada son bajadas, y en la cabecera la
# ocupacion es el resultado inmediato del embarque: en ninguno de los dos
# casos se compara lo mismo que en una parada intermedia, de modo que su
# coeficiente de Bhattacharyya no es homogeneo con el resto y distorsiona el
# porcentaje de equivalencia.
#
# ALCANCE: SOLO la comparacion de distribuciones de ocupacion. Las medias
# (KPIs globales, ocupacion por franja, ocupacion por viaje) siguen
# calculandose sobre TODAS las paradas.
#
# NO se aplica a los tiempos entre paradas: el tramo 2646-562 es una medida
# de transito legitima con valor esperado propio. Poner a True la bandera de
# abajo si se quiere excluir tambien los tramos que tocan una cabecera.
# ---------------------------------------------------------------------------
EXCLUDED_STOPS = {2646, 5727}
EXCLUDE_TERMINALS_IN_TIMES = False


# ---------------------------------------------------------------------------
# Carga: un fichero por carpeta.
# ---------------------------------------------------------------------------
def load_single_csv(path, expected_columns, required=True):
    """Lee un CSV con cabecera y comprueba que estan las columnas esperadas.

    Devuelve el DataFrame con las columnas en el orden canonico. Las columnas
    ausentes se rellenan con NaN y se avisa por stderr, para que un fichero
    al que le falte un campo no tumbe todo el analisis.
    """
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(path)
        print(f"  aviso: {path} no existe, se omite")
        return pd.DataFrame(columns=expected_columns)

    df = pd.read_csv(path, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]

    missing = [c for c in expected_columns if c not in df.columns]
    extra = [c for c in df.columns if c not in expected_columns]
    if missing:
        print(f"  aviso: {os.path.basename(path)} sin columnas {missing}")
        for c in missing:
            df[c] = np.nan
    if extra:
        print(f"  aviso: {os.path.basename(path)} con columnas de mas {extra}")

    return df[expected_columns]


print("Cargando datos...")

joint_dataframe_results = load_single_csv(
    f"{os.getcwd()}/{sim_dir}/RESULTS/results.csv", COLUMNS_RESULTS)

joint_dataframe_events = load_single_csv(
    f"{os.getcwd()}/{sim_dir}/EVENTS/anomalies.csv", COLUMNS_EVENTS,
    required=False)

joint_dataframe_passengers = load_single_csv(
    f"{os.getcwd()}/{sim_dir}/PASSENGERS/passengers.csv", COLUMNS_PASSENGERS)

N_SIMS = int(joint_dataframe_results["simulation_id"].nunique())
print(f"  {len(joint_dataframe_results)} filas de resultados, "
      f"{N_SIMS} replicas")


# --- normalizacion de la direccion: entero -> 'toA' / 'toB' ---------------
def normalize_direction(series):
    if series.isna().all():
        return series
    if series.dtype == object and series.astype(str).str.startswith("to").any():
        return series          # ya viene como texto
    return series.map(DIRECTION_MAP)


joint_dataframe_results["direction"] = normalize_direction(
    joint_dataframe_results["direction"])
if len(joint_dataframe_events):
    joint_dataframe_events["direction"] = normalize_direction(
        joint_dataframe_events["direction"])


# --- lista de tiempos de generacion --------------------------------------
def parse_time_list(v):
    """Acepta '[1, 2, 3]' (GAMA) y '1 2 3' (C), ademas de vacio."""
    if isinstance(v, (list, tuple)):
        return list(v)
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return []
    s = str(v).strip().strip('"')
    if not s:
        return []
    if s.startswith("["):
        try:
            return ast.literal_eval(s)
        except (ValueError, SyntaxError):
            return []
    return [int(float(x)) for x in s.replace(",", " ").split()]


joint_dataframe_passengers["list_passengers_time"] = (
    joint_dataframe_passengers["list_passengers_time"].apply(parse_time_list)
)

joint_dataframe_passengers["current_time"] = pd.to_numeric(
    joint_dataframe_passengers["current_time"], errors="coerce")


# ---------------------------------------------------------------------------
# Tiempo de espera por pasajero.
#
# GAMA escribia en 'list_passengers_time' la espera ya calculada. La
# simulacion en C escribe el instante de CREACION de cada pasajero
# (global_clock cuando se genero), de modo que sus valores son marcas de
# reloj absolutas (~20000-85000 s) y no esperas.
#
# La espera es current_time - instante_de_creacion. Se detecta cual de los
# dos formatos viene comparando la magnitud de los valores con la hora de
# boarding de su propia fila: si el maximo de la lista es del orden del
# reloj, son marcas absolutas y hay que restar.
#
# La cola de pasajeros es FIFO y se recorta por delante, asi que el primer
# elemento es el que mas ha esperado: las esperas resultantes deben salir
# ordenadas de mayor a menor y no negativas.
# ---------------------------------------------------------------------------
def _looks_absolute(df, sample=2000):
    """True si 'list_passengers_time' contiene marcas de reloj absolutas."""
    n_abs = n_rel = 0
    for ct, lst in zip(df["current_time"].head(sample),
                       df["list_passengers_time"].head(sample)):
        if not lst or not np.isfinite(ct):
            continue
        # Una marca absoluta es cercana a current_time; una espera es mucho
        # menor. El umbral de la mitad del reloj separa ambos casos con
        # holgura (esperas de horas no existen en una linea de autobus).
        if max(lst) > ct * 0.5:
            n_abs += 1
        else:
            n_rel += 1
    return n_abs > n_rel


def _to_waits(ct, lst):
    if not lst or not np.isfinite(ct):
        return []
    return [int(ct) - int(g) for g in lst]


if len(joint_dataframe_passengers) and _looks_absolute(joint_dataframe_passengers):
    print("  'list_passengers_time' contiene instantes de creacion: "
          "se convierte a espera (current_time - creacion)")
    joint_dataframe_passengers["list_passengers_time"] = [
        _to_waits(ct, lst)
        for ct, lst in zip(joint_dataframe_passengers["current_time"],
                           joint_dataframe_passengers["list_passengers_time"])
    ]

    _neg = sum(1 for lst in joint_dataframe_passengers["list_passengers_time"]
               for t in lst if t < 0)
    if _neg:
        print(f"  aviso: {_neg} esperas negativas — hay pasajeros con instante"
              f" de creacion posterior al embarque")
        joint_dataframe_passengers["list_passengers_time"] = [
            [t for t in lst if t >= 0]
            for lst in joint_dataframe_passengers["list_passengers_time"]
        ]


# --- columnas numericas: cualquier celda vacia o ilegible pasa a NaN ------
# Sin esto, una sola celda vacia contamina np.std (devuelve NaN), el guardia
# de varianza no salta y gaussian_kde revienta con "array must not contain
# infs or NaNs".
for _c in ("boards", "residual_boards", "dropoffs", "occupation",
           "time_between_stops", "timeslot", "departure_timeslot",
           "stop_num", "bus_code", "travels_completed", "simulation_id"):
    joint_dataframe_results[_c] = pd.to_numeric(
        joint_dataframe_results[_c], errors="coerce")

_n_nan = int(joint_dataframe_results["time_between_stops"].isna().sum())
if _n_nan:
    print(f"  aviso: {_n_nan} filas sin 'time_between_stops' "
          f"({100.0 * _n_nan / max(len(joint_dataframe_results), 1):.2f}%)")


# --- tiempos: la simulacion en C los emite ya en segundos -----------------
HAS_CURRENT_TIME = joint_dataframe_results["current_time"].notna().any()
if not HAS_CURRENT_TIME:
    print("  aviso: results.csv sin 'current_time'; la regularidad quedara a"
          " NaN. Anadir el campo al struct results_row para calcularla.")


def to_seconds(value):
    """Convierte a segundos tanto 'HH:MM[:SS]' como un entero de segundos."""
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

regularity_toA = {}
regularity_toB = {}

# Se recortan la primera y la ultima parada: la regularidad se mide entre la
# segunda y la penultima, no sobre el recorrido completo.
known_times_stops_toA_regularity = known_times_stops_toA.iloc[1:-1]
known_times_stops_toB_regularity = known_times_stops_toB.iloc[1:-1]

for timeslot in timeslots:
    col_name = f"Mean_{timeslot}"
    regularity_toA[timeslot] = known_times_stops_toA_regularity[col_name].sum()
    # caso especial para toB si se selecciona la franja 5
    if timeslot == 5:
        regularity_toB[timeslot] = (
            known_times_stops_toB_regularity["Mean_6"].sum())
    else:
        regularity_toB[timeslot] = (
            known_times_stops_toB_regularity[col_name].sum())


# ---------------------------------------------------------------------------
# Bhattacharyya
# ---------------------------------------------------------------------------
threshold = 0.97

# Una fila por celda (tipo, sentido, parada/tramo, franja), TAMBIEN si la
# celda se descarta. Las funciones de comparacion tienen returns tempranos
# (varianza esperada nula, menos de dos muestras, varianza simulada nula):
# si solo se contasen las celdas que llegan a dibujarse, el denominador del
# porcentaje seria falso. Se reportan por eso dos porcentajes, sobre celdas
# evaluadas y sobre celdas totales.
#
# Las paradas de EXCLUDED_STOPS no se registran: quedan fuera del numerador
# y del denominador, no cuentan como "no evaluables".
bhatt_registry = []


def register_bhatt(tipo, direction, key, timeslot, coeff=None, dist=None,
                   estado="evaluada", metodo=None, n_sim=0,
                   mean_sim=None, std_sim=None, mean_esp=None, std_esp=None):
    """tipo: 'ocupacion' | 'tiempo'.  key: codigo de parada o 'A-B'.

    Se guardan las medias y desviaciones de ambos lados: sin ellas el
    coeficiente dice QUE una celda falla, pero no HACIA DONDE. Con ellas se
    distingue un desfase sistematico de nivel (todas las celdas por debajo)
    de un error de perfil (unas por encima y otras por debajo, que se
    cancelan en la media global).
    """
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
        "metodo": metodo,                    # 'normal' | 'kde' | None
        "n_sim": n_sim,
        "coeff": coeff,
        "distancia": dist,
        "estado": estado,                    # evaluada | sin_* (motivo)
        "fusionable": (None if coeff is None else bool(coeff >= threshold)),
        "mean_sim": (None if mean_sim is None else float(mean_sim)),
        "std_sim": (None if std_sim is None else float(std_sim)),
        "mean_esp": (None if mean_esp is None else float(mean_esp)),
        "std_esp": (None if std_esp is None else float(std_esp)),
        "sesgo": sesgo,                      # sim - esperado
        "sesgo_sigmas": sesgo_sigmas,        # normalizado por sigma esperada
    })


def resumen_bhatt(sub):
    """Agrega un subconjunto del registro a un diccionario de metricas."""
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


def central_moment(x, r):
    mean = np.nanmean(x)
    return sum((xi - mean) ** r for xi in x) / len(x)


def kurtosis(x):
    return (central_moment(x, 4) / central_moment(x, 2) ** 2) - 3


def skewness(x):
    return central_moment(x, 3) / central_moment(x, 2) ** (3 / 2)


def is_normal_simplified(variables: list):
    # central_moment mezcla np.nanmean con una division por len(x): con NaN
    # presentes el numerador los ignora y el denominador no, de modo que
    # asimetria y curtosis saldrian mal y se elegiria la rama equivocada.
    variables = np.asarray(variables, dtype=float)
    variables = variables[np.isfinite(variables)].tolist()

    if len(variables) == 0:
        return np.bool_(False), [], 0, 0
    elif len(variables) < 50:      # CASO Z score 1.96
        z_crit = 1.96
    elif len(variables) < 300:     # CASO Z score 3.29
        z_crit = 3.29
    else:
        z_crit = "False"

    # Varianza nula: skewness y kurtosis dividen por el momento central de
    # orden 2 y darian ZeroDivisionError. Una muestra constante no es normal
    # a efectos de esta comprobacion.
    if central_moment(variables, 2) <= 1e-12:
        return np.bool_(False), variables, float(np.mean(variables)), 0.0

    skew = skewness(variables)
    kurt = kurtosis(variables)

    n = len(variables)
    se_skew = math.sqrt(6.0 / n)
    se_kurt = math.sqrt(24.0 / n)

    mean = np.nanmean(variables)
    std_dev = math.sqrt(central_moment(variables, 2))
    z_skew = skew / se_skew
    z_kurt = kurt / se_kurt

    if z_crit != "False":
        approx_normal = (abs(z_skew) <= z_crit) and (abs(z_kurt) <= z_crit)
    else:
        approx_normal = (abs(skew) <= 2) and (abs(kurt) + 3 <= 7)

    return approx_normal, variables, mean, std_dev


# KPI 1. % de ocupacion medio, por franja horaria y por autobus.
MAX_CAPACITY = 80


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


json_output_general_info = {}

data_toA = joint_dataframe_results[joint_dataframe_results["direction"] == "toA"]
data_toB = joint_dataframe_results[joint_dataframe_results["direction"] == "toB"]

json_output_general_info["Occupation_toA"] = (
    data_toA["occupation"].mean() / MAX_CAPACITY) * 100
json_output_general_info["Occupation_toB"] = (
    data_toB["occupation"].mean() / MAX_CAPACITY) * 100
json_output_general_info["Occupation"] = (
    joint_dataframe_results["occupation"].mean() / MAX_CAPACITY) * 100

logic_buses = joint_dataframe_results["bus_code"].unique()
json_output_general_info["Logical_Buses"] = len(logic_buses)

trips_counter = 0
for bus in logic_buses:
    data_per_bus = joint_dataframe_results[
        joint_dataframe_results["bus_code"] == bus]["travels_completed"]
    trips_counter += (max(data_per_bus) + 1)   # +1: travels_completed empieza en 0

json_output_general_info["Total_Trips"] = int(trips_counter)

mean_time_awaital_passenger = np.nanmean(
    [t for data in joint_dataframe_passengers["list_passengers_time"]
     for t in data]
)
json_output_general_info["Mean_await_passengers"] = mean_time_awaital_passenger

json_output_general_info["Regularity_value"] = 0
regularity_global = []


# --- graficas de evolucion del % de ocupacion a lo largo del dia ----------
list_occupation_values_toA = []
list_occupation_values_toB = []
list_occupation = []
for timeslot in timeslots:
    data_toA_per_ts = data_toA[data_toA["departure_timeslot"] == timeslot]
    data_toB_per_ts = data_toB[data_toB["departure_timeslot"] == timeslot]
    data_general = joint_dataframe_results[
        joint_dataframe_results["departure_timeslot"] == timeslot]
    list_occupation_values_toA.append(
        (data_toA_per_ts["occupation"].mean() / MAX_CAPACITY) * 100)
    list_occupation_values_toB.append(
        (data_toB_per_ts["occupation"].mean() / MAX_CAPACITY) * 100)
    list_occupation.append(
        (data_general["occupation"].mean() / MAX_CAPACITY) * 100)


plt.style.use('seaborn-v0_8-whitegrid')


def save_barcode(horizontal_data, vertical_data, horizontal_label,
                 vertical_label, leyend, label, filename):
    x = np.arange(len(horizontal_data))
    plt.figure(figsize=(12, 5))
    plt.bar(x, vertical_data, width=0.4, label=leyend)
    plt.xticks(x + 0.2, horizontal_data, rotation=90)
    plt.ylabel(vertical_label)
    plt.xlabel(horizontal_label)
    plt.title(label)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()


def compute_and_save_distribution_comparasion(
    sim_data, mean_2, std_2, direction, stopcode, timeslot, is_normal=True
):
    # Cabeceras fuera del numerador y del denominador del porcentaje.
    if int(stopcode) in EXCLUDED_STOPS:
        return

    # NaN e inf fuera antes de cualquier estadistico: np.std los propaga, el
    # guardia de varianza no saltaria y gaussian_kde fallaria mas abajo.
    sim_data = np.asarray(sim_data, dtype=float)
    sim_data = sim_data[np.isfinite(sim_data)]

    if not np.isfinite(mean_2) or not np.isfinite(std_2):
        register_bhatt("ocupacion", direction, stopcode, timeslot,
                       estado="sin_dato_esperado", n_sim=len(sim_data))
        return

    if std_2 <= 1e-9 or len(sim_data) < 2:
        register_bhatt("ocupacion", direction, stopcode, timeslot,
                       estado=("sin_varianza_esperada" if std_2 <= 1e-9
                               else "sin_datos_sim"),
                       n_sim=len(sim_data))
        return

    x_min_exp = mean_2 - 4 * std_2
    x_max_exp = mean_2 + 4 * std_2

    if is_normal:
        # Bhattacharyya como normal
        mean_1 = np.mean(sim_data)
        std_1 = np.std(sim_data, ddof=1)
        if std_1 <= 1e-9:
            register_bhatt("ocupacion", direction, stopcode, timeslot,
                           estado="sin_varianza_sim", metodo="normal",
                           n_sim=len(sim_data))
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
        # KDE + Bhattacharyya
        from scipy.stats import gaussian_kde

        if np.std(sim_data, ddof=1) <= 1e-9:
            register_bhatt("ocupacion", direction, stopcode, timeslot,
                           estado="sin_varianza_sim", metodo="kde",
                           n_sim=len(sim_data))
            return
        kde = gaussian_kde(sim_data)
        x_min = min(np.min(sim_data) - 1, x_min_exp)
        x_max = max(np.max(sim_data) + 1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = kde(x)
        y2 = norm.pdf(x, mean_2, std_2)

        bc_integrand = np.sqrt(y1 * y2)
        bhatt_coeff = np.trapezoid(bc_integrand, x)
        bhatt_coeff = min(bhatt_coeff, 1.0)
        bhatt_dist = -np.log(bhatt_coeff) if bhatt_coeff > 0 else np.inf
        sim_label = f"Simulación KDE (n={len(sim_data)})"

    veredict = ("Fusionables ('Equivalentes')" if bhatt_coeff >= threshold
                else "No fusionables (Distintas)")

    register_bhatt("ocupacion", direction, stopcode, timeslot,
                   coeff=float(bhatt_coeff), dist=float(bhatt_dist),
                   estado="evaluada",
                   metodo=("normal" if is_normal else "kde"),
                   n_sim=len(sim_data),
                   mean_sim=float(np.mean(sim_data)),
                   std_sim=float(np.std(sim_data, ddof=1)),
                   mean_esp=float(mean_2), std_esp=float(std_2))

    plt.figure(figsize=(12, 5))
    plt.plot(x, y1, color="blue", linewidth=2, label=sim_label)
    plt.fill_between(x, y1, alpha=0.15, color="blue")
    plt.plot(x, y2, color="red", linewidth=2,
             label=f"Esperado (μ={mean_2:.2f}, σ={std_2:.2f})")
    plt.fill_between(x, y2, alpha=0.15, color="red")

    plt.xlabel("Ocupación del Autobús al paso por parada")
    plt.ylabel("Densidad de probabilidad")
    plt.title(f"Comparativa de distribuciones – parada {stopcode}, "
              f"Franja {timeslot}")
    plt.legend(
        title=(f"Distancia de Bhattacharyya = {bhatt_dist:.4f}  "
               f"coeff = {bhatt_coeff:.4f}\n→ {veredict}"),
        loc="upper right"
    )
    plt.tight_layout()
    plt.savefig(
        f"{os.getcwd()}/{sim_dir}/PLOTS/{direction}/stops/"
        f"occupation_comparaison_{stopcode}_per_timeslot_{timeslot}.png",
        dpi=300
    )
    plt.close()


def compute_and_save_distribution_comparasion_times(
    sim_data, mean_2, std_2, direction, stopcode, timeslot, is_normal=True
):
    # Los tramos solo se excluyen si se ha pedido explicitamente.
    if tramo_excluido(stopcode):
        return

    tramo = f"{stopcode[0]}-{stopcode[1]}"

    # Mismo saneado que en la comparacion de ocupacion.
    sim_data = np.asarray(sim_data, dtype=float)
    sim_data = sim_data[np.isfinite(sim_data)]

    if not np.isfinite(mean_2) or not np.isfinite(std_2):
        register_bhatt("tiempo", direction, tramo, timeslot,
                       estado="sin_dato_esperado", n_sim=len(sim_data))
        return

    if std_2 <= 1e-9 or len(sim_data) < 2:
        register_bhatt("tiempo", direction, tramo, timeslot,
                       estado=("sin_varianza_esperada" if std_2 <= 1e-9
                               else "sin_datos_sim"),
                       n_sim=len(sim_data))
        return

    x_min_exp = mean_2 - 4 * std_2
    x_max_exp = mean_2 + 4 * std_2

    if is_normal:
        mean_1 = np.mean(sim_data)
        std_1 = np.std(sim_data, ddof=1)
        if std_1 <= 1e-9:
            register_bhatt("tiempo", direction, tramo, timeslot,
                           estado="sin_varianza_sim", metodo="normal",
                           n_sim=len(sim_data))
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

        if np.std(sim_data, ddof=1) <= 1e-9:
            register_bhatt("tiempo", direction, tramo, timeslot,
                           estado="sin_varianza_sim", metodo="kde",
                           n_sim=len(sim_data))
            return

        kde = gaussian_kde(sim_data)
        x_min = min(np.min(sim_data) - 1, x_min_exp)
        x_max = max(np.max(sim_data) + 1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = kde(x)
        y2 = norm.pdf(x, mean_2, std_2)

        bc_integrand = np.sqrt(y1 * y2)
        bhatt_coeff = np.trapezoid(bc_integrand, x)
        bhatt_coeff = min(bhatt_coeff, 1.0)
        bhatt_dist = -np.log(bhatt_coeff) if bhatt_coeff > 0 else np.inf
        sim_label = f"Simulación KDE (n={len(sim_data)})"

    verdict = ("Fusionables ('Equivalentes')" if bhatt_coeff >= threshold
               else "No fusionables (Distintas)")

    register_bhatt("tiempo", direction, tramo, timeslot,
                   coeff=float(bhatt_coeff), dist=float(bhatt_dist),
                   estado="evaluada",
                   metodo=("normal" if is_normal else "kde"),
                   n_sim=len(sim_data),
                   mean_sim=float(np.mean(sim_data)),
                   std_sim=float(np.std(sim_data, ddof=1)),
                   mean_esp=float(mean_2), std_esp=float(std_2))

    plt.figure(figsize=(12, 5))
    plt.plot(x, y1, color="blue", linewidth=2, label=sim_label)
    plt.fill_between(x, y1, alpha=0.15, color="blue")
    plt.plot(x, y2, color="red", linewidth=2,
             label=f"Esperado (μ={mean_2:.2f}, σ={std_2:.2f})")
    plt.fill_between(x, y2, alpha=0.15, color="red")

    plt.xlabel(f"Tiempo medio entre paradas {stopcode[0]}-{stopcode[1]} "
               f"medido en segundos")
    plt.ylabel("Densidad de probabilidad")
    plt.title(f"Comparativa de distribuciones – paradas "
              f"{stopcode[0]}-{stopcode[1]}, Franja {timeslot}")
    plt.legend(
        title=(f"Distancia de Bhattacharyya = {bhatt_dist:.4f}  "
               f"coeff = {bhatt_coeff:.4f}\n→ {verdict}"),
        loc="upper right"
    )
    plt.tight_layout()
    plt.savefig(
        f"{os.getcwd()}/{sim_dir}/PLOTS/{direction}/times/"
        f"time_between_stops_comparaison_{stopcode[0]}-{stopcode[1]}"
        f"_per_timeslot_{timeslot}.png",
        dpi=300
    )
    plt.close()


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


print("Procesando paradas sentido A...")
for stopcode in stops_list_toA:
    list_per_ts_per_stop = []
    json_stops_info_toA[f"{stopcode}"] = {}

    data_stopcode = data_toA[data_toA["stop_num"] == stopcode]

    # Marca para la interfaz: la parada se calcula igual que siempre, solo
    # queda fuera del porcentaje de equivalencia de distribuciones.
    json_stops_info_toA[f"{stopcode}"]["excluded_from_bhatt"] = bool(
        stopcode in EXCLUDED_STOPS)
    json_stops_info_toA[f"{stopcode}"]["Occupation_percentage_per_timeslot"] = {}
    json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"] = {}

    if stopcode == stops_list_toA[-1]:
        for timeslot in timeslots:
            data_for_occupation = data_stopcode[
                data_stopcode["departure_timeslot"] == timeslot]
            actual_percentage = (
                data_for_occupation["dropoffs"].mean() / MAX_CAPACITY) * 100
            list_per_ts_per_stop.append(
                (actual_percentage, data_for_occupation["dropoffs"], 0, 0,
                 data_for_occupation["dropoffs"].mean()))
            j = json_stops_info_toA[f"{stopcode}"]
            j["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            j["Board_dropoff_per_timeslot"][timeslot] = {
                "boards": 0,
                "unable_boards": 0,
                "dropoffs": data_for_occupation["dropoffs"].mean(),
            }

        save_barcode(timeslots, [d[0] for d in list_per_ts_per_stop],
                     "TimeSlots", "% de Ocupación", f"Stop {stopcode}",
                     "Ocupación media por franja horaria de los autobuses",
                     f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/stops/"
                     f"occupation_per_timeslot_{stopcode}.png")
    else:
        for timeslot in timeslots:
            data_per_ts_per_stop = data_stopcode[
                data_stopcode["timeslot"] == timeslot]
            data_for_occupation = data_stopcode[
                data_stopcode["departure_timeslot"] == timeslot]

            actual_percentage = (
                data_for_occupation["occupation"].mean() / MAX_CAPACITY) * 100
            list_per_ts_per_stop.append(
                (actual_percentage, data_for_occupation["occupation"],
                 data_per_ts_per_stop["boards"].mean(),
                 data_per_ts_per_stop["residual_boards"].mean(),
                 data_per_ts_per_stop["dropoffs"].mean()))
            j = json_stops_info_toA[f"{stopcode}"]
            j["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            j["Board_dropoff_per_timeslot"][timeslot] = {
                "boards": data_per_ts_per_stop["boards"].mean(),
                "unable_boards": data_per_ts_per_stop["residual_boards"].mean(),
                "dropoffs": data_per_ts_per_stop["dropoffs"].mean(),
            }

        save_barcode(timeslots, [d[0] for d in list_per_ts_per_stop],
                     "TimeSlots", "% de Ocupación", f"Stop {stopcode}",
                     "Ocupación media por franja horaria de los autobuses",
                     f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/stops/"
                     f"occupation_per_timeslot_{stopcode}.png")

    j = json_stops_info_toA[f"{stopcode}"]
    j["Occupation_percentage"] = np.nanmean([d[0] for d in list_per_ts_per_stop])
    j["mean_boards"] = np.nanmean([d[2] for d in list_per_ts_per_stop])
    j["unable_boards"] = np.nanmean([d[3] for d in list_per_ts_per_stop])
    j["mean_dropoffs"] = np.nanmean([d[4] for d in list_per_ts_per_stop])

    # KPI: distribucion teorica vs real de ocupacion por franja y parada
    for iter_ts in range(0, (timeslots[-1] - timeslots[0]) + 1):
        normal_sim, vars_sim, mean_sim, std_sim = is_normal_simplified(
            list_per_ts_per_stop[iter_ts][1].dropna().tolist())

        timeslot = timeslots[iter_ts]
        data_stop = known_occupation_values_toA[
            known_occupation_values_toA["Stop"] == stopcode]
        mean_known = data_stop[f"Mean_{timeslot}"].iloc[0]
        std_known = data_stop[f"std_{timeslot}"].iloc[0]

        compute_and_save_distribution_comparasion(
            vars_sim, mean_known, std_known, "to_A", stopcode, timeslot,
            normal_sim)

    # Tiempo medio de espera por pasajero (general y por franja)
    data_passengers_in_stop = joint_dataframe_passengers[
        joint_dataframe_passengers["stop_num"] == stopcode]
    mean_time_awaital_passenger = np.nanmean(
        [t for data in data_passengers_in_stop["list_passengers_time"]
         for t in data])

    j["Mean_await_time_general"] = mean_time_awaital_passenger
    j["Mean_await_time_per_timeslot"] = {}

    for timeslot in timeslots:
        data_passengers_timeslotted = data_passengers_in_stop[
            data_passengers_in_stop["timeslot"] == timeslot]
        j["Mean_await_time_per_timeslot"][timeslot] = np.nanmean(
            [t for data in data_passengers_timeslotted["list_passengers_time"]
             for t in data])


print("Procesando paradas sentido B...")
for stopcode in stops_list_toB:
    list_per_ts_per_stop = []

    json_stops_info_toB[f"{stopcode}"] = {}
    json_stops_info_toB[f"{stopcode}"]["excluded_from_bhatt"] = bool(
        stopcode in EXCLUDED_STOPS)
    json_stops_info_toB[f"{stopcode}"]["Occupation_percentage_per_timeslot"] = {}
    json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"] = {}

    data_stopcode = data_toB[data_toB["stop_num"] == stopcode]
    if stopcode == stops_list_toB[-1]:
        for timeslot in timeslots:
            data_for_occupation = data_stopcode[
                data_stopcode["departure_timeslot"] == timeslot]
            actual_percentage = (
                data_for_occupation["dropoffs"].mean() / MAX_CAPACITY) * 100
            list_per_ts_per_stop.append(
                (actual_percentage, data_for_occupation["dropoffs"], 0, 0,
                 data_for_occupation["dropoffs"].mean()))
            j = json_stops_info_toB[f"{stopcode}"]
            j["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            j["Board_dropoff_per_timeslot"][timeslot] = {
                "boards": 0,
                "unable_boards": 0,
                "dropoffs": data_for_occupation["dropoffs"].mean(),
            }

        save_barcode(timeslots, [d[0] for d in list_per_ts_per_stop],
                     "TimeSlots", "% de Ocupación", f"Stop {stopcode}",
                     "Ocupación media por franja horaria de los autobuses",
                     f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/stops/"
                     f"occupation_per_timeslot_{stopcode}.png")
    else:
        for timeslot in timeslots:
            data_per_ts_per_stop = data_stopcode[
                data_stopcode["timeslot"] == timeslot]
            data_for_occupation = data_stopcode[
                data_stopcode["departure_timeslot"] == timeslot]

            actual_percentage = (
                data_for_occupation["occupation"].mean() / MAX_CAPACITY) * 100
            list_per_ts_per_stop.append(
                (actual_percentage, data_for_occupation["occupation"],
                 data_per_ts_per_stop["boards"].mean(),
                 data_per_ts_per_stop["residual_boards"].mean(),
                 data_per_ts_per_stop["dropoffs"].mean()))
            j = json_stops_info_toB[f"{stopcode}"]
            j["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            j["Board_dropoff_per_timeslot"][timeslot] = {
                "boards": data_per_ts_per_stop["boards"].mean(),
                "unable_boards": data_per_ts_per_stop["residual_boards"].mean(),
                "dropoffs": data_per_ts_per_stop["dropoffs"].mean(),
            }

        save_barcode(timeslots, [d[0] for d in list_per_ts_per_stop],
                     "TimeSlots", "% de Ocupación", f"Stop {stopcode}",
                     "Ocupación media por franja horaria de los autobuses",
                     f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/stops/"
                     f"occupation_per_timeslot_{stopcode}.png")

    j = json_stops_info_toB[f"{stopcode}"]
    j["Occupation_percentage"] = np.nanmean([d[0] for d in list_per_ts_per_stop])
    j["mean_boards"] = np.nanmean([d[2] for d in list_per_ts_per_stop])
    j["unable_boards"] = np.nanmean([d[3] for d in list_per_ts_per_stop])
    j["mean_dropoffs"] = np.nanmean([d[4] for d in list_per_ts_per_stop])

    for iter_ts in range(0, ((timeslots[-1] - timeslots[0]) + 1)):
        normal_sim, vars_sim, mean_sim, std_sim = is_normal_simplified(
            list_per_ts_per_stop[iter_ts][1].dropna().tolist())

        timeslot = timeslots[iter_ts]
        data_stop = known_occupation_values_toB[
            known_occupation_values_toB["Stop"] == stopcode]
        mean_known = data_stop[f"Mean_{timeslot}"].iloc[0]
        std_known = data_stop[f"std_{timeslot}"].iloc[0]

        compute_and_save_distribution_comparasion(
            vars_sim, mean_known, std_known, "to_B", stopcode, timeslot,
            normal_sim)

    data_passengers_in_stop = joint_dataframe_passengers[
        joint_dataframe_passengers["stop_num"] == stopcode]
    mean_time_awaital_passenger = np.nanmean(
        [t for data in data_passengers_in_stop["list_passengers_time"]
         for t in data])

    j["Mean_await_time_general"] = mean_time_awaital_passenger
    j["Mean_await_time_per_timeslot"] = {}

    for timeslot in timeslots:
        data_passengers_timeslotted = data_passengers_in_stop[
            data_passengers_in_stop["timeslot"] == timeslot]
        j["Mean_await_time_per_timeslot"][timeslot] = np.nanmean(
            [t for data in data_passengers_timeslotted["list_passengers_time"]
             for t in data])


# ---------------------------------------------------------------------------
# Ocupacion por autobus fisico
# ---------------------------------------------------------------------------
print("Procesando autobuses...")
unique_bus = joint_dataframe_results["bus_code"].unique()

input_json_route = f"{os.getcwd()}/{sim_dir}/includes/INPUTS/final_input.json"
with open(input_json_route, "r") as f:
    input_json = json.load(f)

new_bus_json_data = {}

for bus in unique_bus:
    trip_occupation_percentage = 0

    data_per_bus = joint_dataframe_results[
        joint_dataframe_results["bus_code"] == bus]
    events_per_bus = (joint_dataframe_events[
        joint_dataframe_events["bus_code"] == bus]
        if len(joint_dataframe_events) else joint_dataframe_events)

    unique_trips = data_per_bus['travels_completed'].unique()
    unique_trips = [int(data) for data in unique_trips]

    new_bus_json_data[f"{bus}"] = {}

    for trip in unique_trips:
        if len(events_per_bus):
            events_per_unique_trip = events_per_bus[
                events_per_bus["travels_completed"] == trip]
        else:
            events_per_unique_trip = events_per_bus

        total_percentage_of_delays_per_trip = (
            len(events_per_unique_trip) / N_SIMS) * 100

        if len(events_per_unique_trip):
            mean_delay_in_minutes_per_trip = (
                pd.Series([to_seconds(d)
                           for d in events_per_unique_trip["time_event"]])
                - pd.Series([to_seconds(d)
                             for d in events_per_unique_trip["param_event_1"]])
            ).mean()
        else:
            mean_delay_in_minutes_per_trip = float("nan")

        data_inputs = input_json[str(bus)][trip]

        data_simulation_per_trip = data_per_bus[
            data_per_bus['travels_completed'] == trip]
        trip_occupation_percentage = (
            data_simulation_per_trip["occupation"].mean() / MAX_CAPACITY) * 100

        mean_time_of_trip = 0
        list_mean_values = []
        direction = ""
        regularity_value = float("nan")

        if int(data_inputs[0]) == stops_list_toA[0]:
            direction = "to_A"
            stops_here = stops_list_toA
            regularity_table = regularity_toA
        else:
            direction = "toB"
            stops_here = stops_list_toB
            regularity_table = regularity_toB

        if HAS_CURRENT_TIME:
            # Tiempo medio de viaje: llegada a la ultima parada menos salida
            # de la primera.
            data_per_trip_last_stop = data_simulation_per_trip[
                data_simulation_per_trip["stop_num"] == stops_here[-1]]
            time_per_last_stop = [to_seconds(d) for d in
                                  data_per_trip_last_stop["current_time"]]
            data_per_trip_first_stop = data_simulation_per_trip[
                data_simulation_per_trip["stop_num"] == stops_here[0]]
            time_per_first_stop = [to_seconds(d) for d in
                                   data_per_trip_first_stop["current_time"]]

            if time_per_last_stop and time_per_first_stop:
                mean_time_of_trip = (np.nanmean(time_per_last_stop)
                                     - np.nanmean(time_per_first_stop))

            # Regularidad: entre la segunda y la penultima parada.
            data_top = data_simulation_per_trip[
                data_simulation_per_trip["stop_num"] == stops_here[-2]]
            time_top = [to_seconds(d) for d in data_top["current_time"]]
            data_bottom = data_simulation_per_trip[
                data_simulation_per_trip["stop_num"] == stops_here[1]]
            time_bottom = [to_seconds(d) for d in data_bottom["current_time"]]

            if time_top and time_bottom and len(data_per_trip_last_stop):
                regularity_interval = (np.nanmean(time_top)
                                       - np.nanmean(time_bottom))
                timeslot_trip = data_per_trip_last_stop["timeslot"].iloc[0]
                if timeslot_trip > 23:
                    timeslot_trip = 23
                regularity_value = regularity_calc(
                    regularity_table[timeslot_trip], regularity_interval, True)
                regularity_global.append(regularity_value)

        for stop in stops_here:
            data_per_trip_per_stop = data_simulation_per_trip[
                data_simulation_per_trip["stop_num"] == stop]
            if stop != stops_here[-1]:
                list_mean_values.append(
                    (data_per_trip_per_stop["occupation"].mean()
                     / MAX_CAPACITY) * 100)
            else:
                list_mean_values.append(
                    (data_per_trip_per_stop["dropoffs"].mean()
                     / MAX_CAPACITY) * 100)

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
print("Procesando tiempos entre paradas...")
json_stops_info_toA["times_stops"] = {}
counter = 0
for stop in stops_list_toA[1:]:
    key = f"{stops_list_toA[counter]}-{stop}"
    json_stops_info_toA["times_stops"][key] = {}

    data_stop = joint_dataframe_results[
        joint_dataframe_results["stop_num"] == stop]
    data_stop = data_stop[data_stop["direction"] == "toA"]

    json_stops_info_toA["times_stops"][key]["general_time"] = (
        data_stop["time_between_stops"].mean())
    json_stops_info_toA["times_stops"][key]["time_per_timeslot"] = {}
    json_stops_info_toA["times_stops"][key]["expected_time_per_timeslot"] = {}

    times_known = known_times_stops_toA[
        known_times_stops_toA["StopsCodes"] == key]

    expected_times = []
    for timeslot in timeslots:
        data_stop_per_timeslot = data_stop[
            data_stop["timeslot"] == timeslot]["time_between_stops"].dropna()
        json_stops_info_toA["times_stops"][key]["time_per_timeslot"][timeslot] = (
            data_stop_per_timeslot.mean())

        normal_sim, var_sim, mean_sim, std_sim = is_normal_simplified(
            data_stop_per_timeslot.tolist())

        mean_known = times_known[f"Mean_{timeslot}"].iloc[0]
        std_known = times_known[f"Std_{timeslot}"].iloc[0]

        expected_times.append(mean_known)
        (json_stops_info_toA["times_stops"][key]
         ["expected_time_per_timeslot"][timeslot]) = mean_known

        compute_and_save_distribution_comparasion_times(
            var_sim, mean_known, std_known, "to_A",
            [stops_list_toA[counter], stop], timeslot, normal_sim)

    json_stops_info_toA["times_stops"][key]["expected_time"] = np.mean(
        expected_times)
    counter += 1


json_stops_info_toB["times_stops"] = {}
counter = 0
for stop in stops_list_toB[1:]:
    key = f"{stops_list_toB[counter]}-{stop}"
    json_stops_info_toB["times_stops"][key] = {}

    data_stop = joint_dataframe_results[
        joint_dataframe_results["stop_num"] == stop]
    data_stop = data_stop[data_stop["direction"] == "toB"]

    json_stops_info_toB["times_stops"][key]["general_time"] = (
        data_stop["time_between_stops"].mean())
    json_stops_info_toB["times_stops"][key]["time_per_timeslot"] = {}
    json_stops_info_toB["times_stops"][key]["expected_time_per_timeslot"] = {}

    times_known = known_times_stops_toB[
        known_times_stops_toB["StopsCodes"] == key]

    expected_times = []
    for timeslot in timeslots:
        data_stop_per_timeslot = data_stop[
            data_stop["timeslot"] == timeslot]["time_between_stops"].dropna()
        json_stops_info_toB["times_stops"][key]["time_per_timeslot"][timeslot] = (
            data_stop_per_timeslot.mean())

        normal_sim, var_sim, mean_sim, std_sim = is_normal_simplified(
            data_stop_per_timeslot.tolist())

        mean_known = times_known[f"Mean_{timeslot}"].iloc[0]
        std_known = times_known[f"Std_{timeslot}"].iloc[0]
        expected_times.append(mean_known)
        (json_stops_info_toB["times_stops"][key]
         ["expected_time_per_timeslot"][timeslot]) = mean_known

        compute_and_save_distribution_comparasion_times(
            var_sim, mean_known, std_known, "to_B",
            [stops_list_toB[counter], stop], timeslot, normal_sim)

    json_stops_info_toB["times_stops"][key]["expected_time"] = np.mean(
        expected_times)
    counter += 1


json_output_general_info["Regularity_value"] = (
    np.nanmean(regularity_global) if regularity_global else float("nan"))


# ---------------------------------------------------------------------------
# Porcentaje de distribuciones equivalentes (coeficiente de Bhattacharyya)
#
# Agregacion a cuatro niveles y separando ocupacion de tiempos entre paradas,
# porque son magnitudes distintas con distinto numero de celdas y no deben
# promediarse juntas salvo como cifra de contexto ('conjunto').
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
        _ev = sub[sub["estado"] == "evaluada"].dropna(subset=["sesgo"])
        if len(_ev):
            _res["sesgo_medio"] = float(_ev["sesgo"].astype(float).mean())
            _res["sesgo_medio_sigmas"] = float(
                _ev["sesgo_sigmas"].dropna().astype(float).mean())
            _res["pct_celdas_por_debajo"] = float(
                100.0 * (_ev["sesgo"].astype(float) < 0).mean())
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
    # Cifra de contexto: ocupacion y tiempos juntos.
    bhatt_summary["general"]["conjunto"] = resumen_bhatt(df_bhatt)

json_output_general_info["Bhattacharyya"] = bhatt_summary

# Cifras planas para la interfaz, sin navegar el diccionario.
for _t in ("ocupacion", "tiempo", "conjunto"):
    _g = bhatt_summary["general"].get(_t)
    if _g:
        json_output_general_info[f"Pct_equivalentes_{_t}"] = _g["pct_fusionables"]

print(f"\n=== Equivalencia de distribuciones (Bhattacharyya >= {threshold}) ===")
print(f"  paradas fuera de la comparacion: {sorted(EXCLUDED_STOPS)}")
for _t in ("ocupacion", "tiempo", "conjunto"):
    _g = bhatt_summary["general"].get(_t)
    if not _g:
        continue
    _p = "n/d" if _g["pct_fusionables"] is None else f"{_g['pct_fusionables']:.2f}%"
    print(f"  {_t:10} {_g['fusionables']:4}/{_g['evaluadas']:4} = {_p:>8}"
          f"   (no evaluables: {_g['no_evaluables']}, "
          f"coeff medio: {_g['coeff_medio']})")
    if _g.get("sesgo_medio") is not None:
        print(f"             sesgo medio {_g['sesgo_medio']:+.3f} "
              f"({_g['sesgo_medio_sigmas']:+.2f} sigma), "
              f"{_g['pct_celdas_por_debajo']:.1f}% de celdas por debajo")


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
    plt.savefig(outfile, dpi=300)
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
    plt.savefig(outfile, dpi=300)
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
    plt.savefig(outfile, dpi=300)
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
    plt.savefig(outfile, dpi=300)
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

print("\nHecho.")