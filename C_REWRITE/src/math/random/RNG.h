// *Really* minimal PCG32 code / (c) 2014 M.E. O'Neill / pcg-random.org
// Licensed under Apache License 2.0 (NO WARRANTY, etc. see website)


//Copied minimal RNG generator out of https://www.pcg-random.org/index.html


#pragma once

#include<stdlib.h>
#include<stdio.h>
#include<stdint.h>

typedef struct RNG RNG;

struct RNG{ uint64_t state;  uint64_t inc;};


RNG* RNG_init(uint64_t state, uint64_t inc);

void RNG_destroy(RNG *rng_gen);

uint32_t pcg32_random_r (RNG *rng);

double rng_uniform(uint32_t rng_sample);