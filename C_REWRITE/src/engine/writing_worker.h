#pragma once
#include "io/csv_parser.h"
#include "utils/utils.h"




typedef struct worker_thread_params {
    FILE *fd_results;

    FILE *fd_passengers;

    FILE *fd_anomalies;

    
    
}worker_thread_params;



void init_worker_workspace(worker_thread_params *thread_params);