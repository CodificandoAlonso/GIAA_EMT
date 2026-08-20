#pragma once
#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include "math/random/RNG.h"
#include "utils/utils.h"
#include "io/csv_parser.h"
#include "io/txt_parser.h"
#include "agents/generic/agents.h"
#include "agents/bus/bus.h"
#include "agents/stop/stop.h"
#include "agents/passenger/passenger.h"




typedef struct simulation_variables{
    RNG *random_generator;
    u16 simulation_id;
}simulation_variables;


typedef struct global_inmutable_params{
    const input_data_matrix *const stops_data_distributions;
    const stops_list *const stops_list_data;
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








void *run_simulation_thread(simulation_variables *simulation_init_variables, 
                            const global_inmutable_params * global_params);


