// *Really* minimal PCG32 code / (c) 2014 M.E. O'Neill / pcg-random.org
// Licensed under Apache License 2.0 (NO WARRANTY, etc. see website)


//Copied minimal RNG generator out of https://www.pcg-random.org/index.html


#include "RNG.h"
#include "math/math_utils.h"




RNG *RNG_init(uint64_t state, uint64_t inc){

    RNG *rng_ret = malloc(sizeof(RNG));


    if (rng_ret == NULL) {
        return NULL;
    }

    rng_ret->state = 0U;
    rng_ret->inc = (inc << 1u) | 1u;

    pcg32_random_r(rng_ret);

    rng_ret->state += state;

    pcg32_random_r(rng_ret);

    return rng_ret;
}



void RNG_destroy(RNG* rng_gen){
    free(rng_gen);
}


uint32_t pcg32_random_r(RNG* rng)
{
    uint64_t oldstate = rng->state;
    // Advance internal state
    rng->state = oldstate * 6364136223846793005ULL + (rng->inc|1);
    // Calculate output function (XSH RR), uses old state for max ILP
    uint32_t xorshifted = ((oldstate >> 18u) ^ oldstate) >> 27u;
    uint32_t rot = oldstate >> 59u;
    return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));
}


double rng_uniform(uint32_t rng_sample){return ((double)rng_sample + 0.5) /MAX_32;}