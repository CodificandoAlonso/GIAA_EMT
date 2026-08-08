#pragma once
#include "math/random/RNG.h"
#include "math/distributions/generic/generic_distro.h"

double sample_negbin(distribution *negbin_distribution, RNG *random_num);