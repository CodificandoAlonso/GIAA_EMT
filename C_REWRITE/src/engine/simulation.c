#include "engine/simulation.h"
#include "math/math_utils.h"
#include<stdbool.h>



u16 infer_dropoffs(u16 stop, global_simulation_parameters *sim_params){

    if (stop == 2646 || stop == 5727) {
        return MAX_OCCUPANCY;
    }

    const input_data_stop_row *distro;

    /*
     * For non-terminal stops, determine which route direction
     * contains this stop.
     */
    size_t idx = stop_mapper_toA(stop);

    if (idx != SIZE_MAX) {
        distro = get_distribution_per_timeslot_toA(
            sim_params->global_params->stops_data_distributions,
            stop,
            sim_params->timeslot,
            DROPOFF
        );
    } else {
        distro = get_distribution_per_timeslot_toB(
            sim_params->global_params->stops_data_distributions,
            stop,
            sim_params->timeslot,
            DROPOFF
        );
    }

    if (distro == NULL) {
        fprintf(stderr,
                "No dropoff distribution for stop %u, timeslot %u\n",
                stop,
                sim_params->timeslot);
        exit(-1);
    }

    return (u16)distro->distro.random(
        &distro->distro,
        sim_params->random_generator
    );
}



u32 return_next_time_to_stop(u16 stop, global_simulation_parameters *sim_params, direction direction){

    //Need to obtain the double value coresponding to the combo stop
    //and sim_params->timeslot. then, use
    //The utils.h double_sec_to_u32_sec() to transform and return the u32 val.

    const input_data_times_row *distribution;


    if (direction == CIBELES) {
        distribution = get_distribution_per_timeslot_times_toA(
            sim_params->global_params->stops_times_distributions,
            stop,
            sim_params->timeslot
        );
    } else {
        distribution = get_distribution_per_timeslot_times_toB(
            sim_params->global_params->stops_times_distributions,
            stop,
            sim_params->timeslot
        );
    }

    if (distribution == NULL) {
        fprintf(stderr,
                "No travel-time distribution for stop %u, timeslot %u\n",
                stop,
                sim_params->timeslot);
        exit(-1);
    }

    double time = distribution->distro.random(
        &distribution->distro,
        sim_params->random_generator
    );

    return sim_params->global_clock + (u32)round(time);
}



void generate_passengers_in_stops(global_simulation_parameters *sim_params){

    //Calculate index to access. Should be the remainder of the operation
    // global_clock % 3600

    size_t index_to_add = (sim_params->global_clock % 3600) / sim_params->step;

    for (size_t i = 0; i < sim_params->stops_size; i++){
        //get stop reference.

        stop *stop_agent = &sim_params->stops[i];

        stop_agent->passengers_generating += 
        sim_params->array_passengers_gen[i][index_to_add];

        //Cast to a tmp int
        int passengers_in_int = (int)stop_agent->passengers_generating;
        if (passengers_in_int >= 1){

            //First, we need to check if adding this passengers results in overflow due to the 
            //allocation len passengers. In that case, first, passengers_time_of_creation
            //Should be realloc'ed.

            if (passengers_in_int + stop_agent->number_of_passengers > stop_agent->allocation_len_passengers){
                
                size_t required =
                stop_agent->number_of_passengers + (size_t)passengers_in_int;

                if (required > stop_agent->allocation_len_passengers) {

                    size_t new_capacity = stop_agent->allocation_len_passengers;

                    while (new_capacity < required) {
                        new_capacity *= 2;
                    }
                    stop_agent->allocation_len_passengers = new_capacity;
                }
                u32 *new_arr = realloc(stop_agent->passengers_time_of_creation,
                     sizeof(u32)*stop_agent->allocation_len_passengers);
                    
                if (!new_arr){
                    perror("Error reallocating u32 array of times of passenger_creations\n");
                    exit(-3);
                }
                stop_agent->passengers_time_of_creation = new_arr;
            }

            for (int i = 0; i < passengers_in_int; i++){
                stop_agent->passengers_time_of_creation[stop_agent->number_of_passengers++] = sim_params->global_clock;
            }
            stop_agent->passengers_generating -= (double)passengers_in_int;
        }
    }   

}


void start_pass_gen_arrays(global_simulation_parameters *sim_params){

    //as its start, we assume Init ts 5 and next 6.

    //Wyhat whe need to do. For each stop, take for boardings only. Take tjhe 5th ts and obtain a rand. And for 
    //Ts6 same. then apply luinear conservative reconstrtuction and save tuat in the double.
    size_t size_toA = sim_params->global_params->stops_list_data->size_toA;
    for (size_t i = 0; i < sim_params->global_params->stops_list_data->size_toA; i++ ){
        //Only apply to all of toA besides 5727. 5727's boards will be handled by toB
        if (sim_params->global_params->stops_list_data->stopcodes_toA[i] != 5727){
            double actual_param = sim_params->global_params->stops_data_distributions->route_stops_a[i]
            .stop_distributions[0].distro.random(
                    &sim_params->global_params->stops_data_distributions->route_stops_a[i]
                    .stop_distributions[0].distro, sim_params->random_generator);

            double next_param = sim_params->global_params->stops_data_distributions->route_stops_a[i]
            .stop_distributions[2].distro.random(
                    &sim_params->global_params->stops_data_distributions->route_stops_a[i].
                    stop_distributions[2].distro, sim_params->random_generator);
            

            size_t agent_idx = (size_t)(sim_params->stops_toA[i] -
            sim_params->stops);

            sim_params->random_gen_params[agent_idx] = 
            (distribution_chosen_params){
                .actual_value =actual_param,
                .next_value=next_param};

            linear_conservative_reconstruction(sim_params->array_passengers_gen[agent_idx],
                actual_param, next_param, sim_params->step);
        }
    }
    size_t size_toB = sim_params->global_params->stops_list_data->size_toB;
    for (size_t i = 0; i < size_toB; i++){
        //Only apply to all of toA besides 2646. 2646's boards were handled by toA
        if (sim_params->global_params->stops_list_data->stopcodes_toB[i] != 2646){

            double actual_param = sim_params->global_params->stops_data_distributions->route_stops_b[i]
            .stop_distributions[0].distro.random(
                    &sim_params->global_params->stops_data_distributions->route_stops_b[i]
                    .stop_distributions[0].distro, sim_params->random_generator);

            double next_param = sim_params->global_params->stops_data_distributions->route_stops_b[i]
            .stop_distributions[2].distro.random(
                    &sim_params->global_params->stops_data_distributions->route_stops_b[i].
                    stop_distributions[2].distro, sim_params->random_generator);

            size_t agent_idx = (size_t)(sim_params->stops_toB[i] -
            sim_params->stops);
            
            sim_params->random_gen_params[agent_idx] = 
            (distribution_chosen_params){
                .actual_value =actual_param,
                .next_value=next_param};

            linear_conservative_reconstruction(sim_params->array_passengers_gen[agent_idx],
                actual_param, next_param, sim_params->step);
        }
    }
}


void update_pass_gen_arrays(global_simulation_parameters *sim_params){


    //The formula for the choosen value will be, accesing index 2*((TS +1) - 5).
    //As actual is already in the random gen params.

    size_t size_toA = sim_params->global_params->stops_list_data->size_toA;
    for (size_t i = 0; i < size_toA; i++ ){
        //Only apply to all of toA besides 5727. 5727's boards will be handled by toB
        if (sim_params->global_params->stops_list_data->stopcodes_toA[i] != 5727){


            size_t agent_idx = (size_t)(sim_params->stops_toA[i] -
            sim_params->stops);

            double actual_param = sim_params->random_gen_params[agent_idx].next_value;

            double next_param = sim_params->global_params->stops_data_distributions->route_stops_a[i]
            .stop_distributions[2*((sim_params->timeslot +1) - 5)].distro.random(
                    &sim_params->global_params->stops_data_distributions->route_stops_a[i].
                    stop_distributions[2*((sim_params->timeslot +1) - 5)].distro,
                     sim_params->random_generator);
            

            sim_params->random_gen_params[agent_idx] = 
            (distribution_chosen_params){
                .actual_value =actual_param,
                .next_value=next_param};

            linear_conservative_reconstruction(sim_params->array_passengers_gen[agent_idx],
                actual_param, next_param, sim_params->step);
        }
    }
    size_t size_toB = sim_params->global_params->stops_list_data->size_toB;
    for (size_t i = 0; i < size_toB; i++){
        //Only apply to all of toA besides 2646. 2646's boards were handled by toA
        if (sim_params->global_params->stops_list_data->stopcodes_toB[i] != 2646){

            size_t agent_idx = (size_t)(sim_params->stops_toB[i] -
            sim_params->stops);

            double actual_param = sim_params->random_gen_params[agent_idx].next_value;

            double next_param = sim_params->global_params->stops_data_distributions->route_stops_b[i]
            .stop_distributions[2*((sim_params->timeslot +1) - 5)].distro.random(
                    &sim_params->global_params->stops_data_distributions->route_stops_b[i].
                    stop_distributions[2*((sim_params->timeslot +1) - 5)].distro, 
                    sim_params->random_generator);
            

            sim_params->random_gen_params[agent_idx] = 
            (distribution_chosen_params){
                .actual_value =actual_param,
                .next_value=next_param};

            linear_conservative_reconstruction(sim_params->array_passengers_gen[agent_idx],
                actual_param, next_param, sim_params->step);
        }
    }

}

void update_globals(global_simulation_parameters *sim_params){

    //First, it needs to check if its TS:00, that means a change in TimeSlot and an update
    //on the arrays for passengers generation.
    if (sim_params->global_clock % 3600 == 0){
        //Case 1. the sim just got started, that means global clock // 3600 == 5.
        if (sim_params->global_clock / 3600 == 5){
            //Here it should start the arrays. This is done by start_pass_gen_arrays
            start_pass_gen_arrays(sim_params);
        }else{
            sim_params->timeslot ++;
            update_pass_gen_arrays(sim_params);
        }
    }

    //Now, the system will, using the pass arrays stablished before, update the pass counter in each stop
    //agent, and if the result of the agent can be cropped to a value >1, "create" that n of passengers in the stop.
    generate_passengers_in_stops(sim_params);
}



void update_time(global_simulation_parameters *sim_params){
    sim_params->global_clock+= sim_params->step;
}




void start_simulation(global_simulation_parameters *simulation_variables){

    bool ending = false;

    while(!ending){
    
    ending = true;
    //First, check ending condition
    for (size_t n = 0; n < simulation_variables->buses_size; n ++){
        if (!simulation_variables->buses[n].ending_service){ending=false;break;}
    }
    if (ending){break;}

    //update globals
    update_globals(simulation_variables);


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


    //SUPER ULTRA MEGA HARDCODDED THIS CANNOT HAPPEN
    thread_sim_vars->step = 2;

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


    double **array_passengers = malloc(sizeof( double *)*number_of_stops);

    if (!array_passengers){
        perror("Error allocating emmory for array of generation data\n");
        exit(-3);
    }   
    thread_sim_vars->array_passengers_gen = array_passengers;

    for (size_t i = 0; i< number_of_stops; i++){
        double *array = malloc(sizeof(double)*(3600/thread_sim_vars->step));

        if (!array){
            perror("Error allocating emmory for concrete array of generation data\n");
            exit(-3); 
        }
        thread_sim_vars->array_passengers_gen[i] = array;
    }


    distribution_chosen_params *random_gen_params = calloc(number_of_stops, sizeof(distribution_chosen_params));

    if(!random_gen_params){
        perror("ERror allocating space for the choosen generation parameters\n");
        exit(-3);
    }

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

    sim_params->global_params = global_params;


    sim_params->return_next_time_to_stop = return_next_time_to_stop;

    sim_params->simulation_id = simulation_init_variables->simulation_id;

    sim_params->global_clock = timechar_to_u32_seconds("05:00", 5);

    sim_params->timeslot = 5;

    //RN HARDCODDED. SHOULD BE .ENVED
    sim_params->step = 2;

    sim_params->random_generator = simulation_init_variables->random_generator;

    sim_params->array_passengers_gen = simulation_init_variables->array_passengers_gen;

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
    start_simulation(sim_params);

    //Indicate montecarlo.c that it has ended
    return 0;
}