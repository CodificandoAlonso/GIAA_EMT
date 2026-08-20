#pragma once

#include<stdio.h>
#include<stdlib.h>
#include<utils/utils.h>
#include<stdbool.h>
#include "comms/fipa.h"
#include "agents/generic/agents.h"
#include "io/csv_parser.h"
#include "utils/utils.h"


typedef struct simulation_params simulation_params;




typedef enum {
    passengers_custody = 0,
    interaction_with_bus = 1
} STOP_STATE;



static const MESSAGE_TYPE STOP_MESSAGE_TYPES[] = {
    request,
    query
};

#define STOP_INBOXES_NUMBER 2




typedef struct stop{
    Agent *agent;




}stop;