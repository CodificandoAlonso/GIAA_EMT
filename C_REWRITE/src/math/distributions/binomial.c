#include <math.h>
#include "math/math_utils.h"
#include "math/distributions/generic/generic_distro.h"


/**
 * @brief Samples a random value from a binomial distribution using 
 * BINV algorithm
 *
 * The specified params are sampled via void * conversion to a fixed distribution
 * sample parameters
 *
 * @param binomial_distribution Pointer to the binomial
 *                            distribution structure.
 * @param random_gen Pointer to the RNG structure.
 *
 * @param N value of N given.
 * @return The sampled uint32 value.
 */
double sample_binomial(
    void *parameters
){

    distribution_sampling_parameters *binomial_params = parameters;

    distribution *binomial_distro = binomial_params->self;

    RNG *random_gen = binomial_params->random_gen;

    u32 N = binomial_params->N;


    if (binomial_distro->value1 <= 0.0 || binomial_distro->value1 > 1.0) return 0.0;


    if (binomial_distro->value1 > 0.5) {
        distribution inv_distro = { .value1 = 1.0 - binomial_distro->value1 };
        distribution_sampling_parameters inv_params = {
            .self = &inv_distro,
            .random_gen = random_gen,
            .N = N
        };
        return (double)N - sample_binomial(&inv_params);
    }


    // ASsign q = 1 - p.
    double q = 1 - binomial_distro->value1;


    double s = binomial_distro->value1 / q;

    double a = (N + 1)*s;

    double r = pow(q, N);

    if (r <= 0.0){
        //WIth central limit theorem, in this case, it converges to a Normal

        double mu = N * binomial_distro->value1;

        double sigma = sqrt(mu*(1 - binomial_distro->value1));

        uint32_t new_gen = pcg32_random_r(random_gen);

        double u1 = rng_uniform(new_gen);

        new_gen = pcg32_random_r(random_gen);

        double u2 = rng_uniform(new_gen);

        double Z = sqrt(-2*log(u1))*cos(2*PI*u2);

        return round(mu + sigma*Z);
    }


    //OBtain u ~ U(0,1)
    uint32_t new_gen = pcg32_random_r(random_gen);

    double u = rng_uniform(new_gen);

    double x = 0;
    const double max_x = (double)N;
    while (u > r && x < max_x){

        u = u -r;
        x += 1.0;

        r = ((a /x) -s)*r;

        if (r <= 0.0) break;
    }
    return x;

}