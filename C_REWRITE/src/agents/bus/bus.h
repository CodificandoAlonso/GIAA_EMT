#pragma once

#include<stdio.h>
#include<stdlib.h>
#include<utils/utils.h>
#include<stdbool.h>
#include "comms/fipa.h"
#include "agents/generic/agents.h"
#include "io/csv_parser.h"
#include "utils/utils.h"

#define MAX_OCCUPANCY 80

typedef struct simulation_params simulation_params;




typedef enum {
    stopped = 0,
    moving = 1,
    waiting_headway = 2
} BUS_STATE;

typedef enum {
    arrived = 0,
    waiting_stop_answer = 1,
    waiting_stop_validation = 2,
    wait_extra_time = 3,
} BUS_STOPPED_STATE;

static const MESSAGE_TYPE BUS_MESSAGE_TYPES[] = {
    request,
    query,
    agree,
    inform
};

#define BUS_INBOXES_NUMBER 4


//todo, maybe put this into the json_parser.h
typedef struct headway_times{
    u32 departure_time;
    direction bus_direction;
} headway_times;


typedef struct bus {

    //Inherit general agent capacities
    Agent agent;

    //stopcode for referencing itself
    u16 stop;

    //For debugging. Later on can be erased
    char *stop_name;

    //enum to know whether its moving towards
    direction bus_direction;

    //seconds passed from 00:00. utils.h include a layout for changing and parsing
    //seconds to either hh:mm or hh:mm:ss and vice versa.
    u32 departure_time;

    //array of fixed headway times for the expected departures from the bus
    //and the direction they face
    headway_times *headway_times;

    //Inside state of the bus. Obtained via the bachelor thesis documentation about
    //simulation modeling
    BUS_STATE state;


    BUS_STOPPED_STATE stopped_state;

    //variable to know how many stops has the bus reached.
    byte stops_reached;

    //variable to know how many passengers are in a stop.
    byte occupation;

    //in each stop save scope of how many passengers board
    byte boards;

    //in each stop save scope of how many passengers dropped off
    byte dropoffs;

    //in each stop save scope of how many passengers werent able to dropoff.
    byte residual_boards;

    //variable to define the maximum bus capacity.
    byte max_occupancy;

    //variable to save scope of how many headways has finished
    byte travels_completed;
    
    //variable to check the ending condition.
    byte travels_scheduled;

    //variable to know at which time given the distro value, when the bus will change
    //state from moving to stopped
    u32 expected_navigation_arrival;

    //variable scope for being able to know at which TimeSlot the bus starts
    //headway
    byte departure_timeslot;
    
} bus;


bus *create_bus(u16 stop_code, direction direction,
                headway_times *headway_departures, byte travels_scheduled);


void startup_bus_agent(void *self);


void update_bus_in_sim(void *self, void *sim_params);


void cleanup_bus(void *self);