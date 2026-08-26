#pragma once
#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#include "math/random/RNG.h"
#include "utils/utils.h"
#include "io/csv_parser.h"
#include "io/txt_parser.h"
#include "io/json_parser.h"
#include "agents/generic/agents.h"
#include "agents/bus/bus.h"
#include "agents/stop/stop.h"
#include "agents/passenger/passenger.h"




typedef struct simulation_variables{
    RNG *random_generator;
    u16 simulation_id;
    size_t buses_size;
    size_t stops_size;
    bus *buses;
    stop *stops;

}simulation_variables;


typedef struct global_inmutable_params{
    const input_data_matrix *const stops_data_distributions;
    const stops_list *const stops_list_data;
    const input_data_buses *const input_data_buses;
}global_inmutable_params;



typedef struct global_simulation_parameters{

    u16 simulation_id;


    u32 global_clock;


    u32 step;


    byte timeslot;


    u32 elapsed_time_per_passenger;


    bus *simulation_buses;


    stop *simulation_stops[2];


}global_simulation_parameters;




/**
 * @brief Auxiliary simulation.h function to update the timeslot variable based
 * on the global_clock param
 */
void update_time(global_simulation_parameters *sim_params);




void *start_simulation();



/**
 * @brief function called before starting up the monte carlo replicas
 * in order to create and startup the necesary agents for the sims.
 * Also startup the rng seed generator
 */
simulation_variables *startup_thread_parameters(const global_inmutable_params * global_params,u64 seed,
                          u64 stream);

void *run_simulation_thread(simulation_variables *simulation_init_variables, 
                            const global_inmutable_params * global_params);


