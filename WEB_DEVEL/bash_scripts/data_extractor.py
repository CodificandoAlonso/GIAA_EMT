#/usr/bin/python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import ast
from scipy.stats import norm

with open(f"{os.getcwd()}/.last_simulation", "r") as f:
    sim_dir = f.read().strip()



DESCRIPTION = {}

with open(f"{os.getcwd()}/{sim_dir}/description.txt", "r") as f:
    for line in f:
        parts = line.strip().split(" ", 1)  # split only on first space
        if len(parts) == 2:
            DESCRIPTION[parts[0]] = parts[1]

if DESCRIPTION.get("line") == "401":
    stops_list_toA = [2646, 562, 4090, 4188, 5939, 3995, 3991, 3903, 2539, 2535, 1929, 4032, 5360, 82, 5727]
    stops_list_toB = [5727, 81, 1167, 2538, 3929, 3990, 3994, 5938, 4187, 2964, 649, 2646]
    to_A = "Cibeles"
    to_B = "La Peseta"



#HARDCODDED NUMBER OF SIMS
N_SIMS = 1000

columns = ["simulation_id", "bus_code", "travels_completed","stop_num", "direction", "current_time","timeslot", "departure_timeslot",
           "boards","residual_boards","dropoffs", "occupation", "time_between_stops"]

joint_dataframe_results = pd.DataFrame(columns=columns)

dataframes_to_join_results = []
for iteration in range(0,N_SIMS):
    new_dataframe = pd.read_csv(f"{os.getcwd()}/{sim_dir}/RESULTS/log_Simulation {iteration}.csv", skiprows = 1,
            names = columns, encoding="utf-8")
    dataframes_to_join_results.append(new_dataframe)



joint_dataframe_results = pd.concat(data for data in dataframes_to_join_results)

# # ── Monte Carlo convergence plot ──────────────────────────────────
# CONVERGENCE_OUTPUT = os.path.expanduser("~/Desktop")

# # Mean occupation per simulation run
# occupation_per_sim = (
#     joint_dataframe_results
#     .groupby("simulation_id")["occupation"]
#     .mean()
#     .sort_index()
#     .values
# )

# # Running cumulative mean
# running_mean = np.cumsum(occupation_per_sim) / np.arange(1, len(occupation_per_sim) + 1)
# final_mean = running_mean[-1]

# # Running standard error
# running_std = np.array([
#     np.std(occupation_per_sim[:i+1], ddof=1) / np.sqrt(i+1)
#     if i > 0 else 0.0
#     for i in range(len(occupation_per_sim))
# ])

# fig, ax1 = plt.subplots(figsize=(12, 5))

# ax1.plot(range(1, len(running_mean) + 1), running_mean, color="blue", linewidth=1.5,
#          label="Media acumulada de ocupación")
# ax1.axhline(y=final_mean, color="red", linestyle="--", linewidth=1,
#             label=f"Media final: {final_mean:.4f}")
# ax1.fill_between(
#     range(1, len(running_mean) + 1),
#     running_mean - 1.96 * running_std,
#     running_mean + 1.96 * running_std,
#     alpha=0.2, color="blue", label="IC 95%"
# )
# ax1.set_xlabel("Número de iteraciones")
# ax1.set_ylabel("Media acumulada de ocupación (pasajeros)")
# ax1.set_title("Convergencia Monte Carlo — Ocupación media por iteración")
# ax1.legend(loc="upper right")
# ax1.grid(True, alpha=0.3)

# plt.tight_layout()
# plt.savefig(f"{CONVERGENCE_OUTPUT}/montecarlo_convergence_occupation.png", dpi=300)
# plt.close()

# print(f"[✓] Convergence plot saved to {CONVERGENCE_OUTPUT}/montecarlo_convergence_occupation.png")
# # ──────────────────────────────────────────────────────────────────


N_SIMS = 1000


columns = ["simulation_id", "bus_code","travels_completed", "stop_num", "direction","timeslot", "event_code", 
           "time_event","param_event_1", "param_event_2"]

joint_dataframe_events = pd.DataFrame(columns=columns)

dataframes_to_join_events = []
for iteration in range(0,N_SIMS):
    try:
        new_dataframe = pd.read_csv(f"{os.getcwd()}/{sim_dir}//EVENTS/log_Simulation {iteration}.csv",skiprows = 1,
                             names = columns, encoding="utf-8")
        dataframes_to_join_events.append(new_dataframe)
    except:
        pass


joint_dataframe_events = pd.concat(data for data in dataframes_to_join_events)


columns = ["simulation_id", "bus_code","travels_completed", "stop_num", "timeslot", "current_time","list_passengers_time"]

joint_dataframe_passengers = pd.DataFrame(columns=columns)

dataframes_to_join_passengers = []
for iteration in range(0,N_SIMS):
    new_dataframe = pd.read_csv(f"{os.getcwd()}/{sim_dir}//PASSENGERS/log_Simulation {iteration}.csv", skiprows = 1,
                names=columns, encoding="utf-8")
    dataframes_to_join_passengers.append(new_dataframe)



joint_dataframe_passengers = pd.concat(data for data in dataframes_to_join_passengers)



joint_dataframe_passengers["list_passengers_time"] = (
    joint_dataframe_passengers["list_passengers_time"]
    .apply(ast.literal_eval)
)
known_occupation_values_toA = pd.read_csv(f"{os.getcwd()}/../data/known_data/NORMAL_OCCUPATION_toA.csv")
known_occupation_values_toB = pd.read_csv(f"{os.getcwd()}/../data/known_data/NORMAL_OCCUPATION_toB.csv")
known_times_stops_toA = pd.read_csv(f"{os.getcwd()}/../data/known_data/NORMAL_times_stops_toA.csv")
known_times_stops_toB = pd.read_csv(f"{os.getcwd()}/../data/known_data/NORMAL_times_stops_toB.csv")


timeslots = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]

regularity_toA = {}
regularity_toB = {}


#trim the first and the last instances of known_times_toA and toB, then for each timeslot, navigate trough the columns and compute the man of the times. The full goal
# is to known the standard time between the 2 and the n-1 stops in a direction to then later on do the regularity value

known_times_stops_toA_regularity = known_times_stops_toA.iloc[1:-1]
known_times_stops_toB_regularity = known_times_stops_toB.iloc[1:-1]



for timeslot in timeslots:
    col_name = f"Mean_{timeslot}"
    theoretical_time_toA = known_times_stops_toA_regularity[col_name].sum()
    regularity_toA[timeslot] = theoretical_time_toA
    #special case for toB, incase timeslot 5 is selected.
    if timeslot == 5:
        col_name = f"Mean_6"
        theoretical_time_toB = known_times_stops_toB_regularity[col_name].sum()
        regularity_toB[timeslot] = theoretical_time_toB
    else:
        theoretical_time_toB = known_times_stops_toB_regularity[col_name].sum()
        regularity_toB[timeslot] = theoretical_time_toB



# la idea de esto es generar gráficas a mansalva. La idea detrás ed esto es poder tener tantas gráficas como se guste y en la interfaz de usuario poder agrupar esas gráficas para que se den varios puntos de vista.




#-------------------------------------------------------------------------
#-----------------------Imported from fussion gauss-----------------------
#-------------------------------------------------------------------------
import math

from math import sqrt

from math import log

from math import exp




threshold = 0.97

def bhattacharyya_distance(mean_1, mean_2, std_1, std_2):
    return 0.25*((mean_1 -mean_2)**2/(std_1**2 + std_2**2)) + 0.5*(log((std_1**2 + std_2**2)/(2*(std_1 * std_2))))



def bhattacharyya_coefficient(mean_1, mean_2, std_1, std_2):
    return (sqrt(2*(std_1*std_2/(std_1**2 + std_2**2))))*exp(-(((mean_1 -mean_2)**2)/(4*(std_1**2 + std_2**2))))


import numpy as np



def central_moment(x, r):
    mean = np.nanmean(x)
    return sum((xi - mean) ** r for xi in x) / len(x)


def kurtosis(x):
    return (central_moment(x, 4) / central_moment(x, 2) ** 2) -3

def skewness(x):
    return central_moment(x, 3) / central_moment(x, 2)**(3/2)


def is_normal_simplified(variables:list):


    if len(variables) == 0:
        return np.bool_(False), [], 0, 0

    elif len(variables) < 50: #CASO Z score 1.96
        z_crit = 1.96
    elif len(variables) < 300: #CASO Z score 3.29
        z_crit = 3.29
    else:
        z_crit = "False"

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



 #KPI 1. % de ocupación medio. % de ocupacion por franja horaria. % de ocupación de cada autobús en acda una de sus franjas
MAX_CAPACITY = 80

def time_to_seconds(time_str, include_seconds: bool):
    if include_seconds:
        h, m, s = map(int, time_str.split(":"))
    else:
        h,m = map(int, time_str.split(":"))
        s = 0
    return h * 3600 + m * 60 + s


def time_to_minutes(time_str, include_seconds: bool):
    if include_seconds:
        h, m, s = map(int, time_str.split(":"))
    else:
        h,m = map(int, time_str.split(":"))
        s = 0
    return h * 60 + m + s/60


def regularity_calc(theoretical_interval, real_interval, in_time_format: bool) -> float:
    if not in_time_format:
        It = time_to_minutes(theoretical_interval, False)
        Ir = time_to_minutes(real_interval, False)
    else:
        It = theoretical_interval / 60
        Ir = real_interval / 60

    if Ir > 2 * It:
        return 0.0

    if It <= 10:
        if Ir - It <= 2:
            return 100.0
        else:
            return 100 * (1 - ((Ir - (It + 2)) / (It - 2)))

    elif It <= 25:
        if Ir <= 1.2 * It:
            return 100.0
        else:
            return 100 * (1 - ((Ir - 1.2 * It) / (0.8 * It)))

    else:
        if Ir - It <= 5:
            return 100.0
        else:
            return 100 * (1 - ((Ir - (It + 5)) / (It - 5)))

#La easy.
percentage_occupation_per_stop = 0


json_output_general_info = {}



data_toA = joint_dataframe_results[joint_dataframe_results["direction"] == "toA"]
data_toB = joint_dataframe_results[joint_dataframe_results["direction"] == "toB"]

json_output_general_info["Occupation_toA"] = (data_toA["occupation"].mean()/MAX_CAPACITY)*100
json_output_general_info["Occupation_toB"] = (data_toB["occupation"].mean()/MAX_CAPACITY)*100
json_output_general_info["Occupation"] = (joint_dataframe_results["occupation"].mean()/MAX_CAPACITY)*100

#extract also the logical buses that run the sim to save it in the general info
logic_buses = joint_dataframe_results["bus_code"].unique()
json_output_general_info["Logical_Buses"] = len(logic_buses)

#also add the total number of trips that were made
trips_counter = 0
for bus in logic_buses:
    data_per_bus = joint_dataframe_results[joint_dataframe_results["bus_code"] == bus]["travels_completed"]
    trips_counter += (max(data_per_bus) + 1)# +1 because travels_completed starts at 0

json_output_general_info["Total_Trips"] = trips_counter

#add also the mean wait time per passenger


#compute time will go brrrr
mean_time_awaital_passenger = np.nanmean(
    [t for data in joint_dataframe_passengers["list_passengers_time"] for t in data]
)

json_output_general_info["Mean_await_passengers"] = mean_time_awaital_passenger

json_output_general_info["Regularity_value"] = 0
regularity_global = []


#Empiezan las graficassss
#graficas de evolucion a lo largo del tiempon de valor de %Occupation
list_occupation_values_toA = []

list_occupation_values_toB = []
list_occupation = []
for timeslot in timeslots:
    data_toA_per_ts = data_toA[data_toA["departure_timeslot"] == timeslot]
    data_toB_per_ts = data_toB[data_toB["departure_timeslot"] == timeslot]
    data_general = joint_dataframe_results[joint_dataframe_results["departure_timeslot"] == timeslot]
    list_occupation_values_toA.append((data_toA_per_ts["occupation"].mean()/MAX_CAPACITY)*100)
    list_occupation_values_toB.append((data_toB_per_ts["occupation"].mean()/MAX_CAPACITY)*100)
    list_occupation.append((data_general["occupation"].mean()/MAX_CAPACITY)*100)


plt.style.use('seaborn-v0_8-whitegrid')


def save_barcode(horizontal_data, vertical_data, horizontal_label, vertical_label, leyend, label, filename):
    x = np.arange(len(horizontal_data))
    plt.figure(figsize=(12,5))
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
    sim_data,
    mean_2, std_2,
    direction, stopcode, timeslot,
    is_normal=True
):
    if std_2 <= 1e-9 or len(sim_data) < 2:
        return

    x_min_exp = mean_2 - 4 * std_2
    x_max_exp = mean_2 + 4 * std_2

    if is_normal:
        #Bhattacharyya as normal
        mean_1 = np.mean(sim_data)
        std_1  = np.std(sim_data, ddof=1)
        if std_1 <= 1e-9:
            return

        x_min = min(mean_1 - 4 * std_1, x_min_exp)
        x_max = max(mean_1 + 4 * std_1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = norm.pdf(x, mean_1, std_1)
        y2 = norm.pdf(x, mean_2, std_2)

        bhatt_dist  = bhattacharyya_distance(mean_1, mean_2, std_1, std_2)
        bhatt_coeff = bhattacharyya_coefficient(mean_1, mean_2, std_1, std_2)
        sim_label = f"Simulación Normal (μ={mean_1:.2f}, σ={std_1:.2f})"
    else:
        #KDE + Bhattacharyya
        from scipy.stats import gaussian_kde

        if np.std(sim_data, ddof=1) <= 1e-9:
            return
        kde = gaussian_kde(sim_data)
        x_min = min(np.min(sim_data) - 1, x_min_exp)
        x_max = max(np.max(sim_data) + 1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = kde(x)
        y2 = norm.pdf(x, mean_2, std_2)

        # Bhattacharyya coefficient trapezoidal integration
        bc_integrand = np.sqrt(y1 * y2)
        bhatt_coeff  = np.trapezoid(bc_integrand, x)
        bhatt_coeff  = min(bhatt_coeff, 1.0)
        bhatt_dist   = -np.log(bhatt_coeff) if bhatt_coeff > 0 else np.inf
        sim_label = f"Simulación KDE (n={len(sim_data)})"

    veredict = ("Fusionables ('Equivalentes')" if bhatt_coeff >= threshold
               else "No fusionables (Distintas)")

    plt.figure(figsize=(12, 5))
    plt.plot(x, y1, color="blue", linewidth=2, label=sim_label)
    plt.fill_between(x, y1, alpha=0.15, color="blue")
    plt.plot(x, y2, color="red", linewidth=2,
             label=f"Esperado (μ={mean_2:.2f}, σ={std_2:.2f})")
    plt.fill_between(x, y2, alpha=0.15, color="red")

    plt.xlabel("Ocupación del Autobús al paso por parada")
    plt.ylabel("Densidad de probabilidad")
    plt.title(f"Comparativa de distribuciones – parada {stopcode}, Franja {timeslot}")
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
    sim_data,
    mean_2, std_2,
    direction, stopcode, timeslot,
    is_normal=True
):
    if std_2 <= 1e-9 or len(sim_data) < 2:
        return

    x_min_exp = mean_2 - 4 * std_2
    x_max_exp = mean_2 + 4 * std_2

    if is_normal:
        mean_1 = np.mean(sim_data)
        std_1  = np.std(sim_data, ddof=1)
        if std_1 <= 1e-9:
            return

        x_min = min(mean_1 - 4 * std_1, x_min_exp)
        x_max = max(mean_1 + 4 * std_1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = norm.pdf(x, mean_1, std_1)
        y2 = norm.pdf(x, mean_2, std_2)

        bhatt_dist  = bhattacharyya_distance(mean_1, mean_2, std_1, std_2)
        bhatt_coeff = bhattacharyya_coefficient(mean_1, mean_2, std_1, std_2)
        sim_label = f"Simulación Normal (μ={mean_1:.2f}, σ={std_1:.2f})"
    else:
        from scipy.stats import gaussian_kde

        if np.std(sim_data, ddof=1) <= 1e-9:
            return
        
        kde = gaussian_kde(sim_data)
        x_min = min(np.min(sim_data) - 1, x_min_exp)
        x_max = max(np.max(sim_data) + 1, x_max_exp)
        x = np.linspace(x_min, x_max, 500)

        y1 = kde(x)
        y2 = norm.pdf(x, mean_2, std_2)

        bc_integrand = np.sqrt(y1 * y2)
        bhatt_coeff  = np.trapezoid(bc_integrand, x)
        bhatt_coeff  = min(bhatt_coeff, 1.0)
        bhatt_dist   = -np.log(bhatt_coeff) if bhatt_coeff > 0 else np.inf
        sim_label = f"Simulación KDE (n={len(sim_data)})"

    verdict = ("Fusionables ('Equivalentes')" if bhatt_coeff >= threshold
               else "No fusionables (Distintas)")

    plt.figure(figsize=(12, 5))
    plt.plot(x, y1, color="blue", linewidth=2, label=sim_label)
    plt.fill_between(x, y1, alpha=0.15, color="blue")
    plt.plot(x, y2, color="red", linewidth=2,
             label=f"Esperado (μ={mean_2:.2f}, σ={std_2:.2f})")
    plt.fill_between(x, y2, alpha=0.15, color="red")

    plt.xlabel(f"Tiempo medio entre paradas {stopcode[0]}-{stopcode[1]} medido en segundos")
    plt.ylabel("Densidad de probabilidad")
    plt.title(f"Comparativa de distribuciones – paradas {stopcode[0]}-{stopcode[1]}, Franja {timeslot}")
    plt.legend(
        title=(f"Distancia de Bhattacharyya = {bhatt_dist:.4f}  "
               f"coeff = {bhatt_coeff:.4f}\n→ {verdict}"),
        loc="upper right"
    )
    plt.tight_layout()
    plt.savefig(
        f"{os.getcwd()}/{sim_dir}/PLOTS/{direction}/times/"
        f"time_between_stops_comparaison_{stopcode[0]}-{stopcode[1]}_per_timeslot_{timeslot}.png",
        dpi=300
    )
    plt.close()


save_barcode(timeslots, list_occupation_values_toA , "TimeSlots", "% de Ocupación",  f"Sentido {to_A}", "Ocupación del bus por franja horaria", f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/occupation_per_timeslot_toA.png")

save_barcode(timeslots, list_occupation_values_toB , "TimeSlots", "% de Ocupación",  f"Sentido {to_B}", "Ocupación del bus por franja horaria", f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/occupation_per_timeslot_toB.png")

save_barcode(timeslots, list_occupation , "TimeSlots", "% de Ocupación",  "Datos Generales", "Ocupación del bus por franja horaria",
             f"{os.getcwd()}/{sim_dir}/PLOTS/general/occupation_per_timeslot_general.png")



stops_list_toA = [int(data) for data in stops_list_toA]
stops_list_toB = [int(data) for data in stops_list_toB]



json_stops_info_toA = {}
json_stops_info_toB = {}


for stopcode in stops_list_toA:
    #obtain the data from that stop and extract per timeslots its value
    list_per_ts_per_stop = []
    json_stops_info_toA[f"{stopcode}"] = {}

    data_stopcode = data_toA[data_toA["stop_num"] == stopcode]

    json_stops_info_toA[f"{stopcode}"]["Occupation_percentage_per_timeslot"] = {}

    json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"] = {}

    if stopcode == stops_list_toA[-1]:
        for timeslot in timeslots:
            data_for_occupation = data_stopcode[data_stopcode["departure_timeslot"] == timeslot]
            actual_percentage = (data_for_occupation["dropoffs"].mean()/MAX_CAPACITY)*100
            list_per_ts_per_stop.append((actual_percentage, data_for_occupation["dropoffs"],0, 0,data_for_occupation["dropoffs"].mean()))
            json_stops_info_toA[f"{stopcode}"]["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot] = {}
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["boards"] = 0
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["unable_boards"] = 0
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["dropoffs"] = data_for_occupation["dropoffs"].mean()



        save_barcode(timeslots, [data[0] for data in list_per_ts_per_stop] , "TimeSlots", "% de Ocupación",  f"Stop {stopcode}", "Ocupación media por franja horaria de los autobuses", f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/stops/occupation_per_timeslot_{stopcode}.png")

    else:

        for timeslot in timeslots:
            data_per_ts_per_stop = data_stopcode[data_stopcode["timeslot"] == timeslot]
            data_for_occupation = data_stopcode[data_stopcode["departure_timeslot"] == timeslot]

            actual_percentage = (data_for_occupation["occupation"].mean()/MAX_CAPACITY)*100
            list_per_ts_per_stop.append((actual_percentage, data_for_occupation["occupation"], data_per_ts_per_stop["boards"].mean(), data_per_ts_per_stop["residual_boards"].mean(), data_per_ts_per_stop["dropoffs"].mean()))
            json_stops_info_toA[f"{stopcode}"]["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot] = {}
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["boards"] = data_per_ts_per_stop["boards"].mean()
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["unable_boards"] = data_per_ts_per_stop["residual_boards"].mean()
            json_stops_info_toA[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["dropoffs"] = data_per_ts_per_stop["dropoffs"].mean()

        save_barcode(timeslots, [data[0] for data in list_per_ts_per_stop] , "TimeSlots", "% de Ocupación",  f"Stop {stopcode}", "Ocupación media por franja horaria de los autobuses", f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/stops/occupation_per_timeslot_{stopcode}.png")

    json_stops_info_toA[f"{stopcode}"]["Occupation_percentage"] = np.nanmean([data[0] for data in list_per_ts_per_stop])
    json_stops_info_toA[f"{stopcode}"]["mean_boards"] = np.nanmean([data[2] for data in list_per_ts_per_stop])
    json_stops_info_toA[f"{stopcode}"]["unable_boards"] = np.nanmean([data[3] for data in list_per_ts_per_stop])
    json_stops_info_toA[f"{stopcode}"]["mean_dropoffs"] = np.nanmean([data[4] for data in list_per_ts_per_stop])




    #Important KPI. Theoretical vs Real Distribution of Occupation per Timeslot per Stop
    for iter_ts in range(0, (timeslots[-1] - timeslots[0]) + 1):
        #Very important. Lets compare now the distribution of occupation in that stop VS the theoreticall distribution obtained in the statistical part
        normal_sim, vars_sim, mean_sim, std_sim = is_normal_simplified(list_per_ts_per_stop[iter_ts][1].tolist())

        #now, obtain the ts corresponding to this iteration
        timeslot = timeslots[iter_ts]
        #obtain the mean and std coirresponmding to this stop and this ts
        data_stop = known_occupation_values_toA[known_occupation_values_toA["Stop"] == stopcode]
        mean_known = data_stop[f"Mean_{timeslot}"].iloc[0]
        std_known = data_stop[f"std_{timeslot}"].iloc[0]

        compute_and_save_distribution_comparasion(vars_sim, mean_known, std_known, "to_A", stopcode, timeslot, normal_sim)


    #Per stop. Compute the mean time of awaital per passenger(Normal and per timeslot)

        #first normal mean time of awaital
    data_passengers_in_stop = joint_dataframe_passengers[joint_dataframe_passengers["stop_num"] == stopcode]
    mean_time_awaital_passenger = np.nanmean(
    [t for data in data_passengers_in_stop["list_passengers_time"] for t in data]
    )

    json_stops_info_toA[f"{stopcode}"]["Mean_await_time_general"] = mean_time_awaital_passenger

    json_stops_info_toA[f"{stopcode}"]["Mean_await_time_per_timeslot"] = {}

    for timeslot in timeslots:
        data_passengers_timeslotted = data_passengers_in_stop[data_passengers_in_stop["timeslot"] == timeslot]
        mean_time_awaital_passenger_timeslotted = np.nanmean(
        [t for data in data_passengers_timeslotted["list_passengers_time"] for t in data]
        )
        json_stops_info_toA[f"{stopcode}"]["Mean_await_time_per_timeslot"][timeslot] = mean_time_awaital_passenger_timeslotted



for stopcode in stops_list_toB:
    #obtain the data from that stop and extract per timeslots its value
    list_per_ts_per_stop = []

    json_stops_info_toB[f"{stopcode}"] = {}
    json_stops_info_toB[f"{stopcode}"]["Occupation_percentage_per_timeslot"] = {}


    json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"] = {}

    data_stopcode = data_toB[data_toB["stop_num"] == stopcode]
    if stopcode == stops_list_toB[-1]:
        for timeslot in timeslots:
            data_for_occupation = data_stopcode[data_stopcode["departure_timeslot"] == timeslot]
            actual_percentage = (data_for_occupation["dropoffs"].mean()/MAX_CAPACITY)*100
            list_per_ts_per_stop.append((actual_percentage, data_for_occupation["dropoffs"],0, 0,data_for_occupation["dropoffs"].mean()))
            json_stops_info_toB[f"{stopcode}"]["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot] = {}
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["boards"] = 0
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["unable_boards"] = 0
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["dropoffs"] = data_for_occupation["dropoffs"].mean()

        save_barcode(timeslots, [data[0] for data in list_per_ts_per_stop] , "TimeSlots", "% de Ocupación",  f"Stop {stopcode}", "Ocupación media por franja horaria de los autobuses", f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/stops/occupation_per_timeslot_{stopcode}.png")
    else:
        for timeslot in timeslots:
            data_per_ts_per_stop = data_stopcode[data_stopcode["timeslot"] == timeslot]
            data_for_occupation = data_stopcode[data_stopcode["departure_timeslot"] == timeslot]

            actual_percentage = (data_for_occupation["occupation"].mean()/MAX_CAPACITY)*100
            list_per_ts_per_stop.append((actual_percentage, data_for_occupation["occupation"], data_per_ts_per_stop["boards"].mean(), data_per_ts_per_stop["residual_boards"].mean(), data_per_ts_per_stop["dropoffs"].mean()))
            json_stops_info_toB[f"{stopcode}"]["Occupation_percentage_per_timeslot"][timeslot] = actual_percentage
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot] = {}
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["boards"] = data_per_ts_per_stop["boards"].mean()
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["unable_boards"] = data_per_ts_per_stop["residual_boards"].mean()
            json_stops_info_toB[f"{stopcode}"]["Board_dropoff_per_timeslot"][timeslot]["dropoffs"] = data_per_ts_per_stop["dropoffs"].mean()

        save_barcode(timeslots, [data[0] for data in list_per_ts_per_stop] , "TimeSlots", "% de Ocupación",  f"Stop {stopcode}", "Ocupación media por franja horaria de los autobuses", f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/stops/occupation_per_timeslot_{stopcode}.png")


    json_stops_info_toB[f"{stopcode}"]["Occupation_percentage"] = np.nanmean([data[0] for data in list_per_ts_per_stop])
    json_stops_info_toB[f"{stopcode}"]["Occupation_percentage"] = np.nanmean([data[0] for data in list_per_ts_per_stop])
    json_stops_info_toB[f"{stopcode}"]["mean_boards"] = np.nanmean([data[2] for data in list_per_ts_per_stop])
    json_stops_info_toB[f"{stopcode}"]["unable_boards"] = np.nanmean([data[3] for data in list_per_ts_per_stop])
    json_stops_info_toB[f"{stopcode}"]["mean_dropoffs"] = np.nanmean([data[4] for data in list_per_ts_per_stop])



    #Important KPI. Theoretical vs Real Distribution of Occupation per Timeslot per Stop
    for iter_ts in range(0, ((timeslots[-1] - timeslots[0]) + 1)):
        #Very important. Lets compare now the distribution of occupation in that stop VS the theoreticall distribution obtained in the statistical part
        normal_sim, vars_sim, mean_sim, std_sim = is_normal_simplified(list_per_ts_per_stop[iter_ts][1].tolist())

        #now, obtain the ts corresponding to this iteration
        timeslot = timeslots[iter_ts]
        #obtain the mean and std coirresponmding to this stop and this ts
        data_stop = known_occupation_values_toB[known_occupation_values_toB["Stop"] == stopcode]
        mean_known = data_stop[f"Mean_{timeslot}"].iloc[0]
        std_known = data_stop[f"std_{timeslot}"].iloc[0]

        compute_and_save_distribution_comparasion(vars_sim, mean_known, std_known, "to_B", stopcode, timeslot, normal_sim)



        #Per stop. Compute the mean time of awaital per passenger(Normal and per timeslot)

        #first normal mean time of awaital
    data_passengers_in_stop = joint_dataframe_passengers[joint_dataframe_passengers["stop_num"] == stopcode]
    mean_time_awaital_passenger = np.nanmean(
    [t for data in data_passengers_in_stop["list_passengers_time"] for t in data]
    )

    json_stops_info_toB[f"{stopcode}"]["Mean_await_time_general"] = mean_time_awaital_passenger

    json_stops_info_toB[f"{stopcode}"]["Mean_await_time_per_timeslot"] = {}

    for timeslot in timeslots:
        data_passengers_timeslotted = data_passengers_in_stop[data_passengers_in_stop["timeslot"] == timeslot]
        mean_time_awaital_passenger_timeslotted = np.nanmean(
        [t for data in data_passengers_timeslotted["list_passengers_time"] for t in data]
        )
        json_stops_info_toB[f"{stopcode}"]["Mean_await_time_per_timeslot"][timeslot] = mean_time_awaital_passenger_timeslotted

#Now occupation per physical bus
unique_bus = joint_dataframe_results["bus_code"].unique()


input_json_route = f"{os.getcwd()}/{sim_dir}/includes/INPUTS/final_input.json"

with open(input_json_route, "r") as f:
    input_json = json.load(f)

new_bus_json_data = {}


for bus in unique_bus:

    trip_occupation_percentage = 0

    data_per_bus = joint_dataframe_results[joint_dataframe_results["bus_code"] == bus]
    events_per_bus = joint_dataframe_events[joint_dataframe_events["bus_code"] == bus]

    unique_trips = data_per_bus['travels_completed'].unique()
    unique_trips = [int(data) for data in unique_trips]

    new_bus_json_data[f"{bus}"] = {}








    #Loop over each trip
    for trip in unique_trips:

        events_per_unique_trip =events_per_bus[events_per_bus["travels_completed"] == trip]

        total_percentage_of_delays_per_trip = (len(events_per_unique_trip)/N_SIMS)*100
        mean_delay_in_minutes_per_trip = (pd.Series([time_to_seconds(data, True) for data in events_per_unique_trip["time_event"]]) - pd.Series([time_to_seconds(data, False) for data in events_per_unique_trip["param_event_1"]])).mean()



        data_inputs = input_json[str(bus)][trip]

        data_simulation_per_trip = data_per_bus[data_per_bus['travels_completed'] == trip]
        trip_occupation_percentage = (data_simulation_per_trip["occupation"].mean()/MAX_CAPACITY)*100

        events_per_trip_per_bus = events_per_bus[events_per_bus['travels_completed'] == trip]

        mean_time_of_trip = 0
        #Extract the mean ocupation for saving the plot

        list_mean_values = []
        direction = ""
        if int(data_inputs[0]) == stops_list_toA[0]:
            direction = "to_A"

            #extract the mean estimated time. Calculating the mean arrival time to stop stops_list_toA[-1] and the mean departure time from stops_list_toA[-1]
            data_per_trip_last_stop = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toA[-1]]
            time_per_last_stop = data_per_trip_last_stop["current_time"]
            time_per_last_stop = [time_to_seconds(data, True) for data in time_per_last_stop]
            data_per_trip_first_stop = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toA[0]]
            time_per_first_stop = data_per_trip_first_stop["current_time"]
            time_per_first_stop = [time_to_seconds(data, True) for data in time_per_first_stop]
            mean_time_of_trip = sum(time_per_last_stop)/len(time_per_last_stop) - sum(time_per_first_stop)/len(time_per_first_stop)


            data_top_regularity_interval = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toA[-2]]
            time_top_regularity_interval = data_top_regularity_interval["current_time"]
            time_top_regularity_interval = [time_to_seconds(data, True) for data in time_top_regularity_interval]
            data_bottom_regularity_interval = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toA[1]]
            time_bottom_regularity_interval = data_bottom_regularity_interval["current_time"]
            time_bottom_regularity_interval = [time_to_seconds(data, True) for data in time_bottom_regularity_interval]

            regularity_interval = np.nanmean(time_top_regularity_interval) - np.nanmean(time_bottom_regularity_interval)
            timeslot_trip = data_per_trip_last_stop["timeslot"].iloc[0]
            if timeslot_trip > 23:
                timeslot_trip = 23
            regularity_value = regularity_calc(regularity_toA[timeslot_trip],regularity_interval, True)
            regularity_global.append(regularity_value)

            for stop in stops_list_toA:
                data_per_trip_per_stop = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stop]
                if stop != stops_list_toA[-1]:
                    list_mean_values.append( (data_per_trip_per_stop["occupation"].mean()/MAX_CAPACITY)*100)
                else:
                    list_mean_values.append( (data_per_trip_per_stop["dropoffs"].mean()/MAX_CAPACITY)*100)


            save_barcode(stops_list_toA, list_mean_values , f"Paradas en sentido {to_A}", "% de Ocupación",  f"Ocupación del viaje nº: {trip}", f"Ocupación del autobús por parada para el bus: {bus} con salida estimada {data_inputs[1]}", f"{os.getcwd()}/{sim_dir}/PLOTS/buses/mean_occupation_per_stop_toA_{bus}_{trip}.png")




        else:
            direction = "toB"
            #extract the mean estimated time. Calculating the mean arrival time to stop stops_list_toA[-1] and the mean departure time from stops_list_toA[-1]
            data_per_trip_last_stop = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toB[-1]]
            time_per_last_stop = data_per_trip_last_stop["current_time"]
            time_per_last_stop = [time_to_seconds(data, True) for data in time_per_last_stop]
            data_per_trip_first_stop = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toB[0]]
            time_per_first_stop = data_per_trip_first_stop["current_time"]
            time_per_first_stop = [time_to_seconds(data, True) for data in time_per_first_stop]
            mean_time_of_trip = sum(time_per_last_stop)/len(time_per_last_stop) - sum(time_per_first_stop)/len(time_per_first_stop)


            data_top_regularity_interval = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toB[-2]]
            time_top_regularity_interval = data_top_regularity_interval["current_time"]
            time_top_regularity_interval = [time_to_seconds(data, True) for data in time_top_regularity_interval]
            data_bottom_regularity_interval = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stops_list_toB[1]]
            time_bottom_regularity_interval = data_bottom_regularity_interval["current_time"]
            time_bottom_regularity_interval = [time_to_seconds(data, True) for data in time_bottom_regularity_interval]

            regularity_interval = np.nanmean(time_top_regularity_interval) - np.nanmean(time_bottom_regularity_interval)
            timeslot_trip = data_per_trip_last_stop["timeslot"].iloc[0]
            if timeslot_trip > 23:
                timeslot_trip = 23
            regularity_value = regularity_calc(regularity_toB[timeslot_trip],regularity_interval, True)
            regularity_global.append(regularity_value)





            for stop in stops_list_toB:
                data_per_trip_per_stop = data_simulation_per_trip[data_simulation_per_trip["stop_num"] == stop]
                if stop != stops_list_toB[-1]:
                    list_mean_values.append( (data_per_trip_per_stop["occupation"].mean()/MAX_CAPACITY)*100)
                else:
                    list_mean_values.append( (data_per_trip_per_stop["dropoffs"].mean()/MAX_CAPACITY)*100)

            save_barcode(stops_list_toB, list_mean_values , f"Paradas en sentido {to_B}", "% de ocupación",  f"Ocupación del viaje nº: {trip}", f"Ocupación del autobús por parada para el bus: {bus} con salida estimada {data_inputs[1]}", f"{os.getcwd()}/{sim_dir}/PLOTS/buses/mean_occupation_per_stop_toB_{bus}_{trip}.png")


        #Now data_inputs will act as the key for the data for that specific trip. The data will be. Mean % of occupation. (Mean % of occupation per stop(indicating direction)) Mean %of delays and Mean minutes of delay in case it exists.
        new_bus_json_data[f"{bus}"][f"{data_inputs[0]}-{data_inputs[1]}"] = {"Mean_Occupation_Percentage": trip_occupation_percentage, "Direction": direction, "Mean_time_of_trip": mean_time_of_trip, "Percentage_sims_delay_departure": total_percentage_of_delays_per_trip, "Mean_Minutes_departure_delay" : mean_delay_in_minutes_per_trip, "Regularity_value": regularity_value}




#Time between stops.
json_stops_info_toA["times_stops"] = {}
counter = 0
for stop in stops_list_toA[1:]:

    json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"] = {}

    #first, select all the instances from results which contains the stop_code 'stop'
    data_stop = joint_dataframe_results[joint_dataframe_results["stop_num"] == stop]
    data_stop = data_stop[data_stop["direction"] == "toA"]

    #the general value would be the mean of that column
    json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"]["general_time"] = data_stop["time_between_stops"].mean()



    json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"]["time_per_timeslot"] = {}
    json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"]["expected_time_per_timeslot"] = {}

    times_known = known_times_stops_toA[known_times_stops_toA["StopsCodes"] == f"{stops_list_toA[counter]}-{stop}"]

    expected_times = []

    #now iterate for every timeslot to obtain its val
    for timeslot in timeslots:
        data_stop_per_timeslot = data_stop[data_stop["timeslot"] == timeslot]["time_between_stops"]
        json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"]["time_per_timeslot"][timeslot] = data_stop_per_timeslot.mean()

        normal_sim, var_sim, mean_sim, std_sim = is_normal_simplified(data_stop_per_timeslot.tolist())

        mean_known = times_known[f"Mean_{timeslot}"].iloc[0]
        std_known = times_known[f"Std_{timeslot}"].iloc[0]

        expected_times.append(mean_known)
        json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"]["expected_time_per_timeslot"][timeslot] = mean_known

        compute_and_save_distribution_comparasion_times(var_sim, mean_known, std_known, "to_A", [stops_list_toA[counter],stop], timeslot, normal_sim)



    json_stops_info_toA["times_stops"][f"{stops_list_toA[counter]}-{stop}"]["expected_time"] = np.mean(expected_times)

    counter += 1


json_stops_info_toB["times_stops"] = {}
counter = 0
for stop in stops_list_toB[1:]:

    json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"] = {}

    #first, select all the instances from results which contains the stop_code 'stop'
    data_stop = joint_dataframe_results[joint_dataframe_results["stop_num"] == stop]
    data_stop = data_stop[data_stop["direction"] == "toB"]

    #the general value would be the mean of that column
    json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"]["general_time"] = data_stop["time_between_stops"].mean()

    json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"]["time_per_timeslot"] = {}
    json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"]["expected_time_per_timeslot"] = {}



    times_known = known_times_stops_toB[known_times_stops_toB["StopsCodes"] == f"{stops_list_toB[counter]}-{stop}"]

    expected_times = []

    #now iterate for every timeslot to obtain its val
    for timeslot in timeslots:
        data_stop_per_timeslot = data_stop[data_stop["timeslot"] == timeslot]["time_between_stops"]
        json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"]["time_per_timeslot"][timeslot] = data_stop_per_timeslot.mean()

        normal_sim, var_sim, mean_sim, std_sim = is_normal_simplified(data_stop_per_timeslot.tolist())

        mean_known = times_known[f"Mean_{timeslot}"].iloc[0]
        std_known = times_known[f"Std_{timeslot}"].iloc[0]
        expected_times.append(mean_known)        
        json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"]["expected_time_per_timeslot"][timeslot] = mean_known

        compute_and_save_distribution_comparasion_times(var_sim, mean_known, std_known, "to_B", [stops_list_toB[counter],stop], timeslot, normal_sim)

    json_stops_info_toB["times_stops"][f"{stops_list_toB[counter]}-{stop}"]["expected_time"] = np.mean(expected_times)

    counter += 1



json_output_general_info["Regularity_value"] = np.nanmean(regularity_global)



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
    json.dump(sanitize_for_json(new_bus_json_data), f,indent=4)

with open(f"{os.getcwd()}/{sim_dir}/PLOTS/json_output_general_info.json", "w") as f:
    json.dump(sanitize_for_json(json_output_general_info), f,indent=4)

with open(f"{os.getcwd()}/{sim_dir}/PLOTS/to_A/general_info_toA.json", "w") as f:
    json.dump(sanitize_for_json(json_stops_info_toA), f,indent=4)

with open(f"{os.getcwd()}/{sim_dir}/PLOTS/to_B/general_info_toB.json", "w") as f:
    json.dump(sanitize_for_json(json_stops_info_toB), f,indent=4)