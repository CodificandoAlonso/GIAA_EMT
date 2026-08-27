#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

#include "math/math_utils.h"

int main(void)
{
    double value_first_tram = 33.45;
    double value_second_tram = 200.0;
    u32 step = 2;

    size_t tram_parts = 3600 / step;

    printf("========================================\n");
    printf("Linear Conservative Reconstruction Test\n");
    printf("========================================\n");

    printf("First tram value  : %.2f\n", value_first_tram);
    printf("Second tram value : %.2f\n", value_second_tram);
    printf("Step              : %" PRIu32 " seconds\n", step);
    printf("Number of parts   : %zu\n\n", tram_parts);

    /*
     * Allocate the output array on the heap.
     */
    double *linear_arr = malloc(sizeof(double) * tram_parts);

    if (linear_arr == NULL) {
        perror("Error allocating linear_arr");
        return EXIT_FAILURE;
    }

    /*
     * Fill the allocated array.
     */
    linear_conservative_reconstruction(
        linear_arr,
        value_first_tram,
        value_second_tram,
        step
    );

    /*
     * Print the reconstructed values.
     */
    printf("Reconstructed values:\n");

    for (size_t i = 0; i < tram_parts; ++i) {
        printf(
            "  [%zu] = %.10f\n",
            i,
            linear_arr[i]
        );
    }

    /*
     * Cleanup.
     */
    free(linear_arr);

    return EXIT_SUCCESS;
}