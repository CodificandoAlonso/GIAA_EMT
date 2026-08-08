#pragma once
#include "math/random/RNG.h"

typedef struct distribution distribution;

struct distribution{
    double value1;
    double value2;
    double (*random) (distribution *self, RNG *random_gen);
};
