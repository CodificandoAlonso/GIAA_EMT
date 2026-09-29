#pragma once
#include "math/random/RNG.h"
#include "math/distributions/generic/generic_distro.h"


double aux_sample_binomial(u32 N, double p, RNG *random_gen);

double sample_betabinomial(void *parameters);