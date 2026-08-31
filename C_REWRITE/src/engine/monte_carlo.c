#include<stdatomic.h>
#include "pthread.h"
#include "engine/monte_carlo.h"
#include "config/config.h"
#include "engine/simulation.h"







//for calling. atomic_fetch_add(&sim_id_counter, 1);





int run_monte_carlo_replicas(const global_inmutable_params *global_input_params){

    _Atomic size_t next_sim;

    atomic_init(&next_sim, 0);
    //first things first, cereate dedicated thread pool array.

    pthread_t array_threads[N_THREADS];

    sim_context threads_array[N_THREADS];

    pthread_t worker_thread;


    worker_thread_params worker_thread_parameters = {0};

    //init worker params :).
    size_t cap_results    = 2 * (12 * 1000) + 1024;   /* 25,024 */
    size_t cap_passengers = 2 * (25 * 1000) + 1024;   /* 51,024 */
    size_t cap_anomalies  = 2 * (12 * 1000) + 1024;   /* 25,024 */

    if (init_worker_workspace(&worker_thread_parameters,cap_results, cap_passengers, cap_anomalies) < 0){
        perror("Error creating worker workspace\n");
        return -2;
    }

    for (size_t i = 0; i< N_THREADS; i++){
        threads_array[i] = startup_thread_parameters(global_input_params, 1433, i);
        threads_array[i].next_sim = &next_sim;
        threads_array[i].writter = &worker_thread_parameters;
        
        if (pthread_create(&array_threads[i], NULL, replica_worker, (void *)&threads_array[i]) != 0){
            perror("Error creating thread\n");
            exit(-2);
        }
    }

    for (size_t i = 0; i< N_THREADS; i++){
        pthread_join(array_threads[i],NULL);
    }

    destroy_worker_workspace(&worker_thread_parameters); 

    return 0;
}






