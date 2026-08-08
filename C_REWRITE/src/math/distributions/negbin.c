#include <math.h>
#include "math/math_utils.h"
#include "math/distributions/generic/generic_distro.h"

/**
 * @brief Samples a random value from a negative binomial distribution
 *        using a Gamma-Poisson mixture.
 *
 * The negative binomial is parameterized by:
 *   value1 = r : shape parameter
 *   value2 = p : probability parameter
 *
 * The sampling procedure is:
 *
 *   lambda ~ Gamma(r, beta)
 *   X | lambda ~ Poisson(lambda)
 *
 * where:
 *
 *   beta = p / (1 - p)
 *
 * The Gamma distribution is sampled using the Marsaglia-Tsang
 * method. For r < 1, the shape-augmentation method is used:
 *
 *   Gamma(r) = Gamma(r + 1) * U^(1/r)
 *
 * @param negbin_distribution Pointer to the negative binomial
 *                            distribution structure.
 * @param random_gen Pointer to the RNG structure.
 *
 * @return The sampled uint32 value.
 */
double sample_negbin(
    distribution *negbin_distribution,
    RNG *random_gen
)
{
    double r = negbin_distribution->value1;
    double p = negbin_distribution->value2;

    /* Gamma rate parameter */
    double beta = p / (1.0 - p);

    /*
     * Marsaglia-Tsang requires a Gamma shape >= 1.
     *
     * If r < 1, generate:
     *
     *   Gamma(r) = Gamma(r + 1) * U^(1/r)
     */
    double gamma_shape = r;
    double correction = 1.0;

    if (r < 1.0)
    {
        gamma_shape = r + 1.0;

        uint32_t new_gen = pcg32_random_r(random_gen);
        double u = rng_uniform(new_gen);

        correction = pow(u, 1.0 / r);
    }

    /*
     * Marsaglia-Tsang Gamma sampler
     */
    double d = gamma_shape - 1.0 / 3.0;
    double c = 1.0 / sqrt(9.0 * d);

    double gamma_sample;

    while (1)
    {
        uint32_t new_gen = pcg32_random_r(random_gen);
        double u1 = rng_uniform(new_gen);

        new_gen = pcg32_random_r(random_gen);
        double u2 = rng_uniform(new_gen);

        /* Standard normal using Box-Muller */
        double Z =
            sqrt(-2.0 * log(u1))
            * cos(2.0 * PI * u2);

        double x = 1.0 + c * Z;

        if (x <= 0.0)
            continue;

        double v = x * x * x;

        new_gen = pcg32_random_r(random_gen);
        double u3 = rng_uniform(new_gen);

        /*
         * Marsaglia-Tsang acceptance condition
         */
        if (u3 < 1.0 - 0.0331 * Z * Z * Z * Z)
        {
            gamma_sample = d * v;
            break;
        }

        if (log(u3) <
            0.5 * Z * Z +
            d * (1.0 - v + log(v)))
        {
            gamma_sample = d * v;
            break;
        }
    }

    /*
     * Convert Gamma(shape, 1) to Gamma(shape, rate = beta)
     * and apply the r < 1 correction if necessary.
     */
    double lambda = (gamma_sample * correction) / beta;


    /*
     * Poisson sampler (Knuth's algorithm)
     */
    double L = exp(-lambda);

    uint32_t k = 0;
    double product = 1.0;

    do
    {
        k++;

        uint32_t new_gen = pcg32_random_r(random_gen);
        double u = rng_uniform(new_gen);

        product *= u;

    } while (product > L);

    return (double)k - 1;
}