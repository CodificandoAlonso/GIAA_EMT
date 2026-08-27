#include "engine/simulation.h"
#include<stdbool.h>





void update_globals(global_simulation_parameters *sim_params,
const global_inmutable_params * global_params){


    
}



void update_time(global_simulation_parameters *sim_params){}




void start_simulation(global_simulation_parameters *simulation_variables, 
const global_inmutable_params * global_params){

    bool ending = false;

    while(!ending){
    
    ending = true;
    //First, check ending condition
    for (size_t n = 0; n < simulation_variables->buses_size; n ++){
        if (!simulation_variables->buses[n].ending_service){ending=false;break;}
    }
    if (ending){break;}

    //update globals
    update_globals(simulation_variables, global_params);


    //If not, update buses, same loop again, but its in the order of 12/13 ~~~~ times, so no super unoptimal
    for (size_t n = 0; n < simulation_variables->buses_size; n ++){
        if (!simulation_variables->buses[n].ending_service){
            simulation_variables->buses[n].agent.update_in_sim((void *)&simulation_variables->buses[n], simulation_variables);
        }
    }

    //update stops
    for (size_t n = 0; n < simulation_variables->stops_size; n ++){
        simulation_variables->stops[n].agent.update_in_sim((void *)&simulation_variables->stops[n], simulation_variables);
    }

    //lastly, update time :)
    update_time(simulation_variables);
    }
}















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
    thread_sim_vars->buses = buses;

    //j i c
    thread_sim_vars->buses_size = 0;
    thread_sim_vars->stops_size = 0;

    for (size_t n = 0; n < global_params->input_data_buses->number_of_buses; n ++){

        thread_sim_vars->buses[thread_sim_vars->buses_size++] = create_bus(
            global_params->input_data_buses->input_buses[n].bus_code,
            global_params->input_data_buses->input_buses[n].stop_code,
            global_params->input_data_buses->input_buses[n].initial_direction,
            global_params->input_data_buses->input_buses[n].headway_bus_times,
            global_params->input_data_buses->input_buses[n].headways_length);;
    }



    //startup stop agents.
    size_t number_of_stops =
    global_params->stops_list_data->size_toA +
    global_params->stops_list_data->size_toB -
    2;
    //allocating memory
    stop *stops = malloc(sizeof(stop)*number_of_stops);

    if (!stops){
        perror("Error allocating memory for stops agents\n");
        exit(-3);
    }
    thread_sim_vars->stops = stops;
    

    stop **stops_toA = malloc(sizeof(stop *)*global_params->stops_list_data->size_toA);

    if (!stops_toA){
        perror("Error allocating memory for agent stop's array of memdirs for toA dir\n");
        exit(-3);
    }

    thread_sim_vars->stops_toA = stops_toA;

    stop **stops_toB = malloc(sizeof(stop *)*global_params->stops_list_data->size_toB);

    if (!stops_toB){
        perror("Error allocating memory for agent stop's array of memdirs for toB dir\n");
        exit(-3);
    }

    thread_sim_vars->stops_toB = stops_toB;


    //create agents out of the txt parsed file

    //first, toA agents.
    for (size_t idx = 0; idx < global_params->stops_list_data->size_toA; idx ++){

        //Create the agent and save in the general stop array
        thread_sim_vars->stops[thread_sim_vars->stops_size] =create_stop(
            global_params->stops_list_data->stopcodes_toA[idx]);
        
        size_t mapped_idx = stop_mapper_toA(global_params->stops_list_data->stopcodes_toA[idx]);

        stops_toA[mapped_idx] = &thread_sim_vars->stops[thread_sim_vars->stops_size ++];
    }

    //for toB agents, we need to make a distinction, as stop agents for 5727 and 2646 are already
    //created. We need to obtain the & of the agent and paste it where it belongs in the toB array
    size_t idx_2646_toA = stop_mapper_toA(2646);
    size_t idx_2646_toB = stop_mapper_toB(2646);
    size_t idx_5727_toA = stop_mapper_toA(5727);
    size_t idx_5727_toB = stop_mapper_toB(5727);

    stops_toB[idx_2646_toB] = thread_sim_vars->stops_toA[idx_2646_toA];
    stops_toB[idx_5727_toB] = thread_sim_vars->stops_toA[idx_5727_toA];


    //Loop' the rest
    for (size_t idx = 0; idx < global_params->stops_list_data->size_toB; idx ++){
        
        if (global_params->stops_list_data->stopcodes_toB[idx] != 2646 && global_params->stops_list_data->stopcodes_toB[idx] != 5727){
            
            //Create the agent and save in the general stop array
            thread_sim_vars->stops[thread_sim_vars->stops_size] =create_stop(
                global_params->stops_list_data->stopcodes_toB[idx]);
            

            size_t mapped_idx = stop_mapper_toB(global_params->stops_list_data->stopcodes_toB[idx]);

            stops_toB[mapped_idx] = &thread_sim_vars->stops[thread_sim_vars->stops_size++];
        }
    }

    return thread_sim_vars;
}



void restart_agents(simulation_variables *simulation_variables){

}

void *run_simulation_thread(simulation_variables *simulation_init_variables, 
const global_inmutable_params * global_params){



    //if agents are already created, call restart agents, if not, init them
    if (simulation_init_variables->buses_size > 0 && simulation_init_variables->stops_size > 0){
        restart_agents(simulation_init_variables);
    }


    //start the global simulation parameters.
    global_simulation_parameters *sim_params = malloc(sizeof(global_simulation_parameters));

    if(!sim_params){
        perror("Error allocating memory for global simulation parameters\n");
        exit(-3);
    }

    //params

    sim_params->simulation_id = simulation_init_variables->simulation_id;

    sim_params->global_clock = timechar_to_u32_seconds("05:00", 5);

    sim_params->timeslot = 5;

    //RN HARDCODDED. SHOULD BE .ENVED
    sim_params->step = 2;

    sim_params->random_generator = simulation_init_variables->random_generator;

    //agents
    sim_params->buses_size = simulation_init_variables->buses_size;
    sim_params->buses = simulation_init_variables->buses;
    sim_params->stops_size = simulation_init_variables->stops_size;
    sim_params->stops = simulation_init_variables->stops;
    sim_params->stops_toA = simulation_init_variables->stops_toA;
    sim_params->stops_toB = simulation_init_variables->stops_toB;



    //Once the global params are set, with all the agents initialized, this is simply 2 function calls and
    //a check. First, update environment, second, update agents, and check ending condition. Thats it.

    //All of this is done by run_smiulation thread. Once finished, it must specify to montecarlo that the thread
    //has finished so it can rerun again.
    start_simulation(sim_params, global_params);

    //Indicate montecarlo.c that it has ended
    return 0;
}