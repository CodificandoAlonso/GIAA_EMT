import numpy as np

import matplotlib as plt

import pandas as pd






# Cogemos un dataset entero. Lo partimos por franjas horarias. Para cada franja horaria tenemos que comprobar su hipotesis de normalidad. Con su hipotesis
# de normalidad seremos capaces de generar una gaussiana con media y std las que sean. Esas gaussianas habrá que ver si se pueden apilar en vez de franja
# a franja en alguna que otra franja, con el fin de no tener que actualizar las gaussianas hora a hora


# A tener en cuenta: Lo que analizamos a la hora de calcular la gaussiana es la ocupacion que lleva el autobus al paso por esa parada. Es como tomar una foto
# del instante del paso. Habrá que tener en cuenta realmente para "cada parada" el número de gente que se sube y que se baja, porque eso tmb se modela. Ahora
# mismo se tiene en cuenta de forma pasiva puesto que el valor de ocupacion en teoria es el ocupacion anterior + subidos - bajados.

#La cosa es como tener en cuenta eso. se puede tener como un ratio de generacion de personas por hora. **DE MOMENTO**. Se calculan para cada franja horaria el número de personas
# que suben y bajan. Porque eso realmente es lo que se tiene que modelar. al final, si sigues la ruta del bus ese ratio se deberia ir cumpliendo.



#CODIGO EXPORTADO DE NOTEBOOK PARA OUTLIERS
import math
from math import sqrt
from scipy.stats import t as t_student


def calculate_lambda(iter_value, n_elems, significance_level: float = 0.05):
    """

    :param iter_value: the iteration i in which calculate the associate lambda
    :param significance_level:
    :param n_elems:
    :return: The lambda value for that iteration
    """
    calculate_p = 1 - (significance_level / (2*(n_elems - iter_value +1)))

    t_p_v = t_student.ppf(calculate_p, (n_elems - iter_value - 1))

    return ((n_elems - iter_value) * t_p_v)/sqrt((n_elems - iter_value - 1 + t_p_v*t_p_v)* (n_elems - iter_value + 1))


def calc_r_value(element, variables):
    """
    Function to calculate the R value of a data given the sample it belongs
    :param element: The element to calculate the R value of
    :param variables: The complete sample to evaluate mean and sample standard deviation
    :return: The r value for that element
    """


    mean = np.mean(variables)
    s = sqrt(sum((xi - mean) ** 2 for xi in variables) / (len(variables) -1))
    return abs(element - mean)/s



def extract_r_parameters(variables: list, r:int):
    """

    :param variables:
    :param r:
    :return:
    """

    #variables = np.array(variables)
    r_parameters = []
    variables_as_dict = {}

    for iteration in range(r):

        for variable in variables:
            variables_as_dict[variable] = calc_r_value(variable, variables)


        item, max_r = 0, 0
        for key,value in variables_as_dict.items():
            if value > max_r:
                max_r = value
                item = key
        r_parameters.append((item, max_r))
        #print(f"DEBUG voy a eliminar {item} con {max_r}")

        variables.remove(item)
        variables_as_dict = {}

    return r_parameters

def estimate_outliers(variables:list, outliers_hipotesis: int, significance_level: float = 0.05):
    """

    :param variables:
    :param outliers_hipotesis:
    :param significance_level:
    :return:
    """
    r_parameters = extract_r_parameters(variables, outliers_hipotesis)

    #FOR THE FORMATTED EXIT
    print(f"H_0:\tThere are No outliers")
    print(f"H_a:\tThere are up to {outliers_hipotesis} outliers in the data")
    print(f"\nSignificance level : {significance_level}")
    print(f"Critical Region: Reject H_0 if R_i > Critical value")
    print(f"\nSummary Table for EDC Test")
    print(f"-----------------------------------------------------------")
    print(f" Exact              Test                        Critical")
    print(f"Number of           Statistic                   Value, λ ")
    print(f"Outliers, i         Value, R_i                     5%")
    print(f"-----------------------------------------------------------")

    for iteration in range(outliers_hipotesis):
        iteration_value = calculate_lambda(iteration, len(variables))

        print(f"\t{iteration + 1}\t\t\t{r_parameters[iteration][1]}\t\t\t{iteration_value}") if iteration_value >= r_parameters[iteration][1] else print(f"\t{iteration + 1}\t\t\t{r_parameters[iteration][1]}\t\t\t{iteration_value} *")

    return r_parameters





#CODIGO EXPORTADO DE NOTEBOOK PARA TEST DE NORMALIDAD. modificado para que devuelva valores de media y std
def central_moment(x, r):
    mean = np.mean(x)
    return sum((xi - mean) ** r for xi in x) / len(x)


def kurtosis(x):
    return (central_moment(x, 4) / central_moment(x, 2) ** 2) -3

def skewness(x):
    return central_moment(x, 3) / central_moment(x, 2)**(3/2)


def general_behaviour(skew_value, kurt_value):
    return_statement = ""
    if skew_value == 0:
        if kurt_value == 0:
            return_statement += "\t-Distribución Normal perfecta"
        else:
            return_statement += "\t-Distribución Normal con simetría perfecta, pero valor de kurtosis que indica:\n"
            return_statement += "\t-Distribución leptocúrtica" if kurt_value > 0 else "\t-Distribución platicúrtica"
    else:
        if kurt_value == 0:
            return_statement += "\t-Distribución Normal con kurtosis perfecta, pero valor de skewness que indica:\n"
            return_statement += "\t-Distribución con cola más grande en el lado derecho" if skew_value > 0 else "\t-Distribución con cola más grande en el lado izquierdo"
    if skew_value > 0:
        if kurt_value > 0:
            return_statement += "\t-Cola derecha más grande que izquierda\n\t-Distribución leptocúrtica(picos más altos de lo normal)"
        else:
            return_statement += "\t-Cola derecha más grande que izquierda\n\t-Distribución platicúrtica(distribución más achatada de lo normal)"
    else:
        if kurt_value > 0:
            return_statement += "\t-Cola izquierda más grande que derecha\n\t-Distribución leptocúrtica(picos más altos de lo normal)"
        else:
            return_statement += "\t-Cola izquierda más grande que derecha\n\t-Distribución platicúrtica(distribución más achatada de lo normal)"
    return return_statement


def is_normal_modified(dataset: pd.DataFrame, day: str, timeslot: int, variable: str):


    variables_daily = dataset[dataset["Weekday"] == day]
    variables_timeslot = variables_daily[variables_daily["TimeSlot"] == timeslot]

    variables = variables_timeslot[variable]

    if len(variables) < 50: #CASO Z score 1.96
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

    mean = np.mean(variables)
    std_dev = math.sqrt(central_moment(variables, 2))
    z_skew = skew / se_skew
    z_kurt = kurt / se_kurt

    if z_crit != "False":
        approx_normal = (abs(z_skew) <= z_crit) and (abs(z_kurt) <= z_crit)
        print(f"-Para {n} valores, con valor skewness: {skew} y kurtosis: {kurt}, \n\n"
          f"-Con valores de SE, SE_skewness: {se_skew}, SE_kurtosis: {se_kurt}, \n\n"
          f"-Se obtienen los siguientes valores de Z; Z_skew: {z_skew} y Z_kurtosis: {z_kurt}, \n\n"
          f"-Se concluye por lo tanto que la hipótesis de que la distribución es normal es: {approx_normal}\n\n"
          f"La distribución presenta una media:  {mean} y una desviación estandar σ: {std_dev}\n\n"
          f"-El comportamiento general de esta distribución es:\n{general_behaviour(skew, kurt)}")

    else:
        approx_normal = (abs(skew) <= 2) and (abs(kurt) + 3 <= 7) #para muestras grandes de Z > 300 no se utilizan los errores, sino valores absolutos  de medida
        print(f"-Para {n} valores, con valor skewness: {skew} y kurtosis: {kurt}, \n\n"
              f"-Con valores de SE, SE_skewness: {se_skew}, SE_kurtosis: {se_kurt}, \n\n"
              f"-Se concluye por lo tanto que la hipótesis de que la distribución es normal es: {approx_normal}\n\n"
              f"La distribución presenta una media:  {mean} y una desviación estandar σ: {std_dev}\n\n"
              f"-El comportamiento general de esta distribución es:\n{general_behaviour(skew, kurt)}")

    return approx_normal, variables






def generate_gaussian_per_slot_daily(dataframeinput: pd.DataFrame, param_to_gauss: str):
    """

    :param dataframeinput:
    :param param_to_gauss:
    :return new_dataframe:
    """


    #FUERA CASOS MAL MEDIDOS
    dataframe = dataframeinput[dataframeinput["Occupation"] <= 65]
    dataframe = dataframe[dataframe["Occupation"] >= 0]



    #TRABAJAMOS SOBRE SOLO LABORABLES SIN GRATUIDAD
    dataframe = dataframe[dataframe["DayType"] == "LA"]

    dataframe = dataframe[dataframe["FreeDay"] == 0]


    #VAMOS A TRABAJAR DIA A DIA
    daytype = ["L", "M", "X", "J", "V"]
    timeslot = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]


    #Inittialy column day to specify L, M, X, J, V
    columns = ["day"]

    #For each timeslot t add columns Mean_t, std_t and IsNormal_t
    for time in timeslot:
        strvar = f"Mean_{time}"
        columns.append(strvar)
        strvar = f"std_{time}"
        columns.append(strvar)
        strvar = f"IsNormal_{time}"
        columns.append(strvar)

    #generate df
    new_dataframe = pd.DataFrame(columns=columns)


    #aux
    tuple_array = []

    #loop for each day and timeslot
    for day in daytype:

        #only daily darta
        data_daily = dataframe[dataframe["Weekday"] == day]

        for time in timeslot:

            #Filter by timeslot
            data_per_timeslot = data_daily[data_daily["TimeSlot"] == time]

            #calculate normal hypothesis
            gauss_hypothesis, nothing  = is_normal_modified(pd.DataFrame(data_per_timeslot), day, time, param_to_gauss)

            #save in a 5 tuple
            five_tuple = (day, time, np.mean(data_per_timeslot[param_to_gauss]), sqrt(central_moment(data_per_timeslot[param_to_gauss], 2)), gauss_hypothesis)

            #add to aux daily
            tuple_array.append(five_tuple)

        #select only the new added(For each day select the daily)
        select_day= [tuple for tuple in tuple_array if tuple[0] == day]

        #add to df
        select_day = np.array(select_day)
        row_data = np.concatenate([[select_day[0, 0]], select_day[:, 2:5].flatten()])
        new_dataframe.loc[len(new_dataframe)] = row_data


    return new_dataframe