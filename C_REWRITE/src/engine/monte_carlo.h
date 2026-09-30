#pragma once
#include<stdatomic.h>
#include "utils/utils.h"
#include "semaphore.h"




typedef struct global_inmutable_params global_inmutable_params;



int run_monte_carlo_replicas(const global_inmutable_params *global_input_params, u64 seed);








