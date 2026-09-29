#include <math.h>
#include "math/math_utils.h"
#include "math/distributions/generic/generic_distro.h"

/**
 * @brief Function to sample a random value given a normal distribution parameters and a random number generator. It uses the box muller approach.
 * @param normal_distribution pointer to a typedefstruct of type distribution. As its stablished this method will be called .random
 * @param random_gen pointer to a RNG structure that contains the random generator methods.
 * @return The double value sampled.
 */
double sample_normal(void *parameters){

    distribution_sampling_parameters *normal_params = parameters;

    distribution *normal_distribution = normal_params->self;

    RNG *random_gen = normal_params->random_gen;

    uint32_t new_gen = pcg32_random_r(random_gen);

    double u1 = rng_uniform(new_gen);

    new_gen = pcg32_random_r(random_gen);

    double u2 = rng_uniform(new_gen);

    double Z = sqrt(-2*log(u1))*cos(2*PI*u2);

    return (normal_distribution->value1 + normal_distribution->value2 * Z);
}