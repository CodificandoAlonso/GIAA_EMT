#pragma once

#include<stdio.h>
#include<stdlib.h>
#include<utils/utils.h>
#include<stdbool.h>
#include "comms/fipa.h"
#include "agents/generic/agents.h"
#include "io/csv_parser.h"
#include "utils/utils.h"



typedef struct global_simulation_parameters global_simulation_parameters;


#define BASE_PASSENGERS_MAX_SIZE 32

#define BASE_PASSENGERS_BUFFER_MAX_SIZE 32


typedef enum {
    passengers_custody = 0,
    interaction_with_bus = 1
} STOP_STATE;

typedef enum {
    initial_conversation = 0,
    last_conversation = 1
} interaction_state;

static const MESSAGE_TYPE STOP_MESSAGE_TYPES[] = {
    request,
    query
};

#define STOP_INBOXES_NUMBER 2



/**
 * @brief struct defined to implement the abstraction of the agent stop defined
 * in the thesis. It extends from the base agent architecture, defining only 
 * the inboxes needed in the agent stop pre-defined.
 */
typedef struct stop{
    //Extend the agent
    Agent agent;

    //code for identification.
    u16 stop_code;


    u16 number_of_passengers;

    //Value to know how much the u32 array time_in_stop_per_passenger is allocated.
    size_t allocation_len_passengers;

    //array for buffering the time when each passenger was generated. If N passengers
    // (self.number_of_passengers) are generated and in custody, for each
    // i = 1,2,...N the index i -1 stores the moment of creation.
    u32 *passengers_time_of_creation;

    //enum type value for the internal state of the stop
    STOP_STATE stop_state;

    //enum type value for the internal state inside the interaction with bus'stop state.
    interaction_state interaction_state;

    //Size for knowing how much the array length is for the passengers buffer.
    size_t passengers_idx;


    size_t max_allocated_buffer_size;

    //actual array buffering the information about the time of awaital per passenger.
    passengers_row *buffer_passengers;
}stop;



/**
 * @brief function dedicate to instantiate an stop agent. Given the stop_code,
 * returns the full agent with its inboxes and stuff initialized
 * @param stop_code u16 identifier of the stop
 */
stop *create_stop(u16 stop_code);



/**
 * @brief extension of the startup function for a general agent.
 * @param self the pointer to the corresponding agent. Void because its attached
 * from general startup_func
 */
void startup_stop_agent(void *self);


/**
 * @brief auxiliar function that modifies the u32* array to crop
 * the passengers that left the stop.
 */
void crop_time_of_passengers(stop *stop, size_t len_to_crop);



/**
 * @brief auxiliar function to save in the buffer the info asociated with a specific
 * stop.
 * @param stop agent stop reference
 * @param factual_boards the number of actual passengers that boarded the bus.ç
 * @param bus_code bus reference to know which interaction bus-stop produced that casuistic.
 * @param sim_params reference to the global simulation parameters. needed to know the
 * general simulation time
 */
void process_and_save_passengers_row(stop *stop, byte factual_boards, u16 bus_code, byte travels_completed, const global_simulation_parameters *sim_params);




/**
 * @brief extension of the startup update function for a general agent.
 * In this case, it applies the logic to update the internal state of a given stop
 * agent.
 * @param self pointer to the agent. void because it extends from the general 
 * agent update_in_sim definition
 * @param sim_params reference to the global simulation params for knowuin
 */
void update_stop_in_sim(void *self, const global_simulation_parameters *sim_params);



void reset_stop(void *self);


/**
 * @brief extension of the cleanuo function for a general agent.
 * It resolves any memory conflicts or open heap allocations for no
 * memory leaks.
 * @param self the agent pointer to cleanup both its inboxes and the buffers arrays.
 * In general, all heap mem allocations.
 */
void cleanup_stop(void *self);