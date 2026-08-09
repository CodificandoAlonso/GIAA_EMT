#pragma once
#include "math/random/RNG.h"

typedef struct distribution distribution;

typedef enum {
    DIST_NORMAL,
    DIST_NEGBIN,
    DIST_GEOMETRIC,
} dist_kind;

struct distribution{
    dist_kind kind;
    double value1;
    double value2;
    double (*random) (distribution *self, RNG *random_gen);
};

/*
static inline double random(const distribution *d, RNG *rng)
{
    switch (d->kind) {
        case DIST_NORMAL: return sample_normal(d, rng);
        case DIST_NEGBIN: return sample_negbin(d, rng);
        case DIST_GEOMETRIC: return sample_geometric(d, rng);
        default:          return 0.0;
    }
}
*/
