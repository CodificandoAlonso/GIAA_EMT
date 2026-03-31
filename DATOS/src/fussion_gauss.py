
import math



from math import sqrt

from math import log

from math import exp


def bhattacharyya_distance(mean_1, mean_2, std_1, std_2):
    return 0.25*((mean_1 -mean_2)**2/(std_1**2 + std_2**2)) + 0.5*(log((std_1**2 + std_2**2)/(2*(std_1 * std_2))))





def bhattacharyya_coefficient(mean_1, mean_2, std_1, std_2):
    return (sqrt(2*(std_1*std_2/(std_1**2 + std_2**2))))*exp(-(((mean_1 -mean_2)**2)/(4*(std_1**2 + std_2**2))))


import numpy as np



def central_moment(x, r):
    mean = np.mean(x)
    return sum((xi - mean) ** r for xi in x) / len(x)


def kurtosis(x):
    return (central_moment(x, 4) / central_moment(x, 2) ** 2) -3

def skewness(x):
    return central_moment(x, 3) / central_moment(x, 2)**(3/2)


def is_normal_simplified(variables:list):


    if len(variables) == 0:
        return np.bool(False), [], 0, 0

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

    mean = np.mean(variables)
    std_dev = math.sqrt(central_moment(variables, 2))
    z_skew = skew / se_skew
    z_kurt = kurt / se_kurt

    if z_crit != "False":
        approx_normal = (abs(z_skew) <= z_crit) and (abs(z_kurt) <= z_crit)

    else:
        approx_normal = (abs(skew) <= 2) and (abs(kurt) + 3 <= 7)

    return approx_normal, variables, mean, std_dev