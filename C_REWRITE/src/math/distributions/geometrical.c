#include <math.h>
#include "math/math_utils.h"
#include "math/distributions/generic/generic_distro.h"

/**
 * @brief Function to sample a random value given a geometrical distribution parameter and a random number generator. It uses the closed form 
 * inverse transformation
 * @param geometrical_distribution pointer to a typedefstruct of type distribution. As its stablished this method will be called .random
 * @param random_gen pointer to a RNG structure that contains the random generator methods.
 * @return The double value sampled.
 */
double sample_geometrical(distribution *geometrical_distribution, RNG *random_gen){

    uint32_t new_gen = pcg32_random_r(random_gen);

    double u = rng_uniform(new_gen);

    return floor((log(u)/log(1 - geometrical_distribution->value1)));
}