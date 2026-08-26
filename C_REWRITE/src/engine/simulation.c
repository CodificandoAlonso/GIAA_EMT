#include "engine/simulation.h"


void update_time(global_simulation_parameters *sim_params);




void *start_simulation(){}















simulation_variables *startup_thread_parameters(const global_inmutable_params * global_params,u64 seed,
                          u64 stream){

    simulation_variables *thread_sim_vars = calloc(1, sizeof(simulation_variables));

    if (!thread_sim_vars){
        perror("Error allocating memory for thread sim params\n");
        exit(-3);
    }

    RNG *random_generator = RNG_init(seed, stream);

    if (!random_generator) {
        perror("Error allocating memory for random generator\n");
        exit(-3);
    }

    thread_sim_vars->random_generator = random_generator;

    //startup bus agents.

    //allocating memory
    bus *buses = malloc(sizeof(bus)*global_params->input_data_buses->number_of_buses);

    if (!buses){
        perror("Error allocating memory for buses creation\n");
        exit(-3);
    }

    //j i c
    thread_sim_vars->buses_size = 0;

    for (size_t n = 0; n < global_params->input_data_buses->number_of_buses; n ++){
        bus *new_bus = create_bus(global_params->input_data_buses->input_buses[n].bus_code,
        global_params->input_data_buses->input_buses[n].stop_code,
        global_params->input_data_buses->input_buses[n].initial_direction,
        global_params->input_data_buses->input_buses[n].headway_bus_times,
        global_params->input_data_buses->input_buses[n].headways_length);

        if (!new_bus){
            perror("Err9or creating bus agent");
            exit(-3);
        }

        thread_sim_vars->buses[thread_sim_vars->buses_size++] = *new_bus;
    }

    //startup stop agents.

    //allocating memory
    stop *stops = malloc(sizeof(stop)*MAX_DIRECTION_LEN*2);

    if (!stops){
        perror("Error allocating memory for stops agents\n");
        exit(-3);
    }

    
}



void *run_simulation_thread(simulation_variables *simulation_init_variables, 
const global_inmutable_params * global_params){

    //Once the global params are set.




}