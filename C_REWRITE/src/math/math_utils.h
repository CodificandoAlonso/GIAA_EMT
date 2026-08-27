#pragma once
#include "utils/utils.h"

#include<math.h>

#define MAX_32 4294967296.0

static const double EULER = 2.71828182845904523536;

static const double PI    = 3.14159265358979323846;



void linear_conservative_reconstruction(double *linear_arr,
double value_first_tram, double value_second_tram, u32 step);