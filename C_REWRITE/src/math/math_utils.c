#include "math/math_utils.h"
#include <stdlib.h>
#include <stdio.h>



void linear_conservative_reconstruction(double *linear_arr, double value_first_tram,
double value_second_tram, u32 step){


    // Validate step before using it in modulo/division.
    if (step == 0 || 3600 % step != 0) {
        fprintf(
            stderr,
            "Error in linear conservative reconstruction: "
            "step must be a non-zero divisor of 3600\n"
        );
        exit(EXIT_FAILURE);
    }

    size_t tram_parts = 3600 / step;

    // The caller must provide enough memory.
    if (linear_arr == NULL) {
        fprintf(
            stderr,
            "Error in linear conservative reconstruction: "
            "linear_arr is NULL\n"
        );
        exit(EXIT_FAILURE);
    }

    // Only one part: no interpolation is necessary.
    if (tram_parts == 1) {
        linear_arr[0] = value_first_tram;
        return;
    }



    //extract the second value addition per tram part.
    double second_tram_part = value_second_tram /tram_parts;


    double y_intercept = 0, slope = 0;

    y_intercept = (2* value_first_tram / tram_parts) - second_tram_part;

    slope = (second_tram_part - y_intercept) / (tram_parts -1);

    for(size_t i = 0; i < tram_parts; i++){
        linear_arr[i] = slope * i + y_intercept;
    }
}