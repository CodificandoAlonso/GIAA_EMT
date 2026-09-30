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
#include "engine/writing_worker.h"

typedef struct distribution_chosen_params {
    double actual_value;
    double next_value;
}distribution_chosen_params;




typedef struct global_inmutable_params{
    const input_data_matrix *const stops_data_distributions;
    const stops_list *const stops_list_data;
    const input_data_buses *const input_data_buses;
    const input_times_matrix *const stops_times_distributions;
}global_inmutable_params;




typedef struct sim_context {
    /* ---- set once per thread, never reset ---- */
    const global_inmutable_params *global_params;
    RNG                        *random_generator;
    u64                         initial_seed;
    worker_thread_params          *writter;        /* the three output queues */
    _Atomic size_t                *next_sim;   /* shared claim counter */

    bus    *buses;      size_t buses_size;
    stop   *stops;      size_t stops_size;
    stop  **stops_toA;
    stop  **stops_toB;
    double **array_passengers_gen;
    distribution_chosen_params *random_gen_params;

    /* ---- reset at the start of every replica ---- */
    u16  simulation_id;
    u32  global_clock;
    u32  step;
    byte timeslot;
} sim_context;



u16 infer_dropoffs(u16 stop, 
sim_context *sim_params, u32 occupation);


u32 return_next_time_to_stop(u16 stop, 
sim_context *sim_params, direction direction);



void generate_passengers_in_stops(sim_context *sim_params);

void start_pass_gen_arrays(sim_context *sim_params);

void update_pass_gen_arrays(sim_context *sim_params);


void update_globals(sim_context *sim_params);

/**
 * @brief Auxiliary simulation.h function to update the timeslot variable based
 * on the global_clock param
 */
void update_time(sim_context *sim_params);


void *replica_worker(void *arg);

void start_simulation(sim_context *simulation_variables);


void delete_agents(sim_context *simulation_variables);

void restart_agents(sim_context *simulation_variables, u64 seed);

/**
 * @brief function called before starting up the monte carlo replicas
 * in order to create and startup the necesary agents for the sims.
 * Also startup the rng seed generator
 */
sim_context startup_thread_parameters(
const global_inmutable_params *global_params,u64 seed,
    u64 stream);

void run_simulation_thread(sim_context *simulation_init_variables,
    u16 id);
