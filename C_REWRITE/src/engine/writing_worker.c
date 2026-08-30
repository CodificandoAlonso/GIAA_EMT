#include "engine/writing_worker.h"
#include "utils/utils.h"

#include<stdio.h>
#include<stdlib.h>






#define OUTPUT_RESULTS "ruta"

#define OUTPUT_PASSENGERS "ruta"

#define OUTPUT_ANOMALIES "ruta"











void init_worker_workspace(worker_thread_params *thread_params){


    FILE *FD_results = fopen(OUTPUT_RESULTS,"w");

    if (!FD_results){
        perror("Error opening results file descriptor\n");
        exit(-3);
    }

    FILE *FD_passengers = fopen(OUTPUT_PASSENGERS,"w");

    if (!FD_passengers){
        perror("Error opening passengers file descriptor\n");
        exit(-3);
    }

    FILE *FD_anomalies = fopen(OUTPUT_ANOMALIES,"w");

    if (!FD_anomalies){
        perror("Error opening anomalies file descriptor\n");
        exit(-3);
    }
    

    
}