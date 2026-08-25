#pragma once


#include<stdio.h>
#include<stdlib.h>
#include<utils/utils.h>
#include "comms/fipa.h"




typedef enum MESSAGE_TYPE MESSAGE_TYPE;
typedef struct inbox inbox;

typedef struct global_simulation_parameters global_simulation_parameters;


/**
 * @brief generic agent structure. It holds the basics for defining an agent.
 * Based on the GAMA agents models for bus transit simulation.
 */
typedef struct Agent {

    /* generic FIPA queues. All agents should have the same queues. for reference
     * inbox REQUESTS, QUERIES, AGREES, INFORMS, REFUSES for now on. No need to have more, 
     * as the bus transit sim only requires those five.
     */
    inbox requests;
    inbox queries;
    inbox agrees;
    inbox refuses;
    inbox informs;

    const MESSAGE_TYPE *message_types;
    size_t inboxes_numbers;

    void (* startup_agent) (void *self);
    void (*update_in_sim) (void *self, const global_simulation_parameters *sim_params);
    void (*cleanup) (void *self);
    
} Agent;