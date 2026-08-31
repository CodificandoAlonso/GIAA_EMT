#pragma once

#include<stdio.h>
#include<stdlib.h>
#include<utils/utils.h>
#include<stdbool.h>
#include "comms/fipa.h"
#include "agents/generic/agents.h"
#include "io/csv_parser.h"
#include "utils/utils.h"
#include "agents/stop/stop.h"

#define MAX_OCCUPANCY 80

typedef struct global_simulation_parameters global_simulation_parameters;

#define BASE_BUFFER_RESULTS_SIZE 512

#define BASE_BUFFER_ANOMALIES_SIZE 512



typedef enum {
    stopped = 0,
    moving = 1,
    waiting_headway = 2
} BUS_STATE;


typedef enum {
    arrived = 0,
    waiting_stop_answer = 1,
    waiting_stop_validation = 2,
    wait_extra_time = 3
} BUS_STOPPED_STATE;

static const MESSAGE_TYPE BUS_MESSAGE_TYPES[] = {
    agree,
    inform
};

#define BUS_INBOXES_NUMBER 2



typedef struct bus {

    //Inherit general agent capacities
    Agent agent;

    //stopcode for referencing itself
    u16 bus_code;

    u16 stop;

    stop *stop_reached;

    //enum to know whether its moving towards
    direction bus_direction;

    //seconds passed from 00:00. utils.h include a layout for changing and parsing
    //seconds to either hh:mm or hh:mm:ss and vice versa.
    u32 departure_time;

    //array of fixed headway times for the expected departures from the bus
    //and the direction they face
    const headway_times *headway_times;

    //Inside state of the bus. Obtained via the bachelor thesis documentation about
    //simulation modeling
    BUS_STATE state;


    BUS_STOPPED_STATE stopped_state;

    //variable to know how many stops has the bus reached.
    byte stops_reached;

    //variable to know how many passengers are in a stop.
    byte occupation;


    //global time when the bus will leave the stop
    u32 extra_time_awaital;


    //variable to define the maximum bus capacity.
    byte max_occupancy;

    //variable to save scope of how many headways has finished
    byte travels_completed;
    
    //variable to check the ending condition.
    byte travels_scheduled;

    //variable to know at which time given the distro value, when the bus will change
    //state from moving to stopped
    u32 expected_navigation_arrival;

    //variable to save how much time the bus travels between specifi stops
    u32 time_travelled;

    //variable scope for being able to know at which TimeSlot the bus starts
    //headway
    byte departure_timeslot;

    //bool variable to know if it has ended service
    bool ending_service;

    size_t results_allocated;

    size_t results_idx;
    results_row *buffer_results;

    size_t anomalies_allocated;
    size_t anomalies_idx;
    anomaly_row *buffer_anomalies;


} bus;


bus create_bus(u16 bus_code, u16 stop_code, direction direction,
                const headway_times *headway_departures, byte travels_scheduled);


void startup_bus_agent(void *self);


/**
 * @brief auxiliary function to, given a bus and board/dropoffs value, update the value
 * of the occupancy based on the params and return the number of passengers not able
 * to actually board.
 * @param bus the bus reference to work with
 * @param boards number of passengers willing to be boarded
 * @param dropoffs number of passengers that will be dropped out of the bus
 * @return number of residual_boards not able to board due to occupancy constraints.
 */
u16 update_bus_occupancy(bus *bus, u16 boards, u16 dropoffs);


void save_results_row(bus *bus, u16 pass_to_board, u16 pass_to_dropoff, u16 residual_boards,
                      const sim_context *sim_params);


void save_last_row(bus *bus, const sim_context *sim_params);


void save_anomaly_row(bus *bus, u32 delay, const sim_context *sim_params);

/**
 * @brief auxiliary function to, when the infer of boarding disboarding porcess
 * is finished, comms back to the stop to indicate how many factual passengers
 * actually boarded.
 * @param bus bus reference.
 * @param expected_boards the total number of passebngers at the stop initially
 * @param unable_boards the number of passengers not able to board. If zero
 * the answer back is expected boards
 */
void request_to_update_stop(bus *bus, u16 expected_boards, u16 unable_boards);


void process_extra_time_at_stop(bus *bus, u16 boards,
     u16 dropoffs, const sim_context *sim_params);



void ending_bus_service(bus *bus, const sim_context *sim_params);


void update_bus_in_sim(void *self, const sim_context *sim_params);


void reset_bus(void *self);

void cleanup_bus(void *self);