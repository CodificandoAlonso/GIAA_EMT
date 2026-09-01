#include "agents/bus/bus.h"
#include "utils/utils.h"
#include "agents/generic/agents.h"
#include "engine/simulation.h"
#include "math/math_utils.h"
#include<stdio.h>
#include<stdlib.h>
#include <string.h>
#include<math.h>


bus create_bus(u16 bus_code, u16 stop_code, direction direction,
                const headway_times *headway_departures, byte travels_scheduled)
    {
        bus bus = {0};

        bus.bus_code = bus_code;
        bus.stop = stop_code;
        bus.bus_direction = direction;
        bus.headway_times = headway_departures;
        bus.travels_scheduled = travels_scheduled;
        bus.agent.startup_agent = startup_bus_agent;
        bus.agent.update_in_sim = update_bus_in_sim;
        bus.agent.cleanup = cleanup_bus;
        bus.agent.reset_agent = reset_bus;
        bus.results_idx = 0;
        bus.anomalies_idx = 0;
        bus.ending_service = false;

        bus.anomalies_allocated = BASE_BUFFER_ANOMALIES_SIZE;
        bus.results_allocated = BASE_BUFFER_RESULTS_SIZE;

        bus.agent.startup_agent(&bus);
        return bus;
    }




void startup_bus_agent(void *self){
    bus *bus = self;

    bus->max_occupancy = MAX_OCCUPANCY;

    bus->state = waiting_headway;
    
    bus->agent.message_types = BUS_MESSAGE_TYPES;
    bus->agent.inboxes_numbers = (size_t)BUS_INBOXES_NUMBER;

    init_inbox(&bus->agent, bus->agent.message_types, bus->agent.inboxes_numbers);
}



u16 update_bus_occupancy(bus *bus, u16 boards, u16 dropoffs){

    //first apply droppoffs.
    if (dropoffs > bus->occupation)
        bus->occupation = 0;
    else
        bus->occupation -= dropoffs;

    //now, apply boards.

    if ((boards + bus->occupation) > bus->max_occupancy ){
        byte residual_boards = (boards + bus->occupation) - bus->max_occupancy;
        bus->occupation = bus->max_occupancy;
        return residual_boards;
    }
    bus->occupation += boards;
    return 0;
}


void save_results_row(bus *bus, u16 pass_to_board, u16 pass_to_dropoff, u16 residual_boards,
                      const sim_context *sim_params){
    
    if (bus->results_idx == bus->results_allocated){
        //realloc twice.
        results_row *realloc_res = realloc(bus->buffer_results, bus->results_allocated*2*sizeof(results_row));
        if (!realloc_res){
            perror("Error reallocating memory for results realloqued\n");
            exit(-3);
        }
        bus->results_allocated *= 2;
        bus->buffer_results = realloc_res;
    }
    
                        
    bus->buffer_results[bus->results_idx] = (results_row){
        sim_params->simulation_id,
        bus->bus_code,
        bus->travels_completed,
        bus->stop,
        bus->bus_direction,
        sim_params->global_clock,
        sim_params->timeslot,
        bus->departure_timeslot,
        (pass_to_board - residual_boards),
        residual_boards,
        pass_to_dropoff,
        bus->occupation,
        bus->time_travelled
    };
    bus->results_idx ++;
}


void save_last_row(bus *bus, const sim_context *sim_params){

    if (bus->results_idx == bus->results_allocated){
        //realloc twice.
        results_row *realloc_res = realloc(bus->buffer_results, bus->results_allocated*2*sizeof(results_row));
        if (!realloc_res){
            perror("Error reallocating memory for results realloqued\n");
            exit(-3);
        }
        bus->results_allocated *= 2;
        bus->buffer_results = realloc_res;
    }
    bus->buffer_results[bus->results_idx] = (results_row){
        sim_params->simulation_id,
        bus->bus_code,
        bus->travels_completed,
        bus->stop,
        bus->bus_direction,
        sim_params->global_clock,
        sim_params->timeslot,
        bus->departure_timeslot,
        0,
        0,
        bus->occupation,
        0,
        bus->time_travelled
    };
    bus->results_idx ++;
}


void save_anomaly_row(bus *bus, u32 delay, const sim_context *sim_params){

    //check if needs reallocation.
    if (bus->anomalies_idx == bus->anomalies_allocated){
        bus->anomalies_allocated *= 2;
        anomaly_row *new_anomalies = realloc(bus->buffer_anomalies,
             sizeof(anomaly_row) * bus->anomalies_allocated);
        
        if (!new_anomalies){
            perror("Erorr reallocating memory for anomalies row\n");
            exit(-3);
        }
        bus->buffer_anomalies = new_anomalies;
    }
    bus->buffer_anomalies[bus->anomalies_idx++] = (anomaly_row){
        .sim_identifier = sim_params->simulation_id,
        .bus_code = bus->bus_code,
        .travels_completed = bus->travels_completed,
        .direction = bus->bus_direction,
        .stopcode = bus->stop,
        .timeslot = sim_params->timeslot,
        .event_type = "DELAY",
        .current_time = sim_params->global_clock,
        .expected_departure = bus->headway_times[bus->travels_completed].departure_time,
        .minutes_of_delay = (byte)delay
    };

}


void request_to_update_stop(bus *bus, u16 expected_boards, u16 unable_boards){
    message *new_message = malloc(sizeof(message));

    if (!new_message){
        perror("Error allocating memory for new message\n");
        exit(-3);
    }

    char_and_num *payload = malloc(sizeof(char_and_num));

    payload->bus_code = bus->bus_code;
    payload->message = "Update passengers. I boarded";
    payload->passengers_boarded = expected_boards - unable_boards;
    payload->travels_completed = bus->travels_completed;

    new_message->sender = &bus->agent;
    new_message->message_type = request;
    new_message->protocol_type = REQUEST;
    new_message->receiver = &bus->stop_reached->agent;
    new_message->payload = (void *)payload;
    new_message->payload_owned = true;
    send_message(new_message);
}



void process_extra_time_at_stop(bus *bus, u16 boards,
     u16 dropoffs, const sim_context *sim_params){

    //Simply. the boarding and dropoff process are consider parallel.

    //The extra time should be processed if, counting max number of cycles the bus
    //takes to process all the info at stop. Counting from when it arrives.
    //at cycle 0 starts comms with stop. Expected in cycle 1 have first answer.
    //At cycle 2 having second answer. That means 2 cycles. The system should
    //first take a time_per_passenger, def will be 5s and process the
    //First the max between boards and dropoffs. Then, the max between 
    //That value *time_per_passenger and 2*STEP. Define the bus->extra_time_in_stop
    //as the time the bus is "allowed" to leave the stop.

    byte max_val = max(boards, dropoffs);
    
    u32 extra_time = (u32)(max_val* TIME_PER_PASSENGER);

    if (extra_time  > 2*sim_params->step){
        bus->extra_time_awaital = sim_params->global_clock + extra_time;
    }else{
        bus->extra_time_awaital = sim_params->global_clock;
    }
}


void ending_bus_service(bus *bus, const sim_context *sim_params){

    //When ending, just put its results info and anomalies info into the buffer, and thats it.
    push_results(sim_params->writter, bus->buffer_results, bus->results_idx);
    push_anomalies(sim_params->writter, bus->buffer_anomalies, bus->anomalies_idx);
}

void update_bus_in_sim(void *self, const sim_context *sim_params){
    bus *bus = self;

    switch (bus->state){

        case waiting_headway:{
            if (sim_params->global_clock >= bus->headway_times[bus->travels_completed].departure_time){
                
                bus->departure_timeslot = sim_params->timeslot;

                //Bus state moves into moving, fo the bus to communicate with the first stop.
                bus->state = moving;
                bus->expected_navigation_arrival = sim_params->global_clock;

            } else {break;}
        }

        case moving: {
            if (sim_params->global_clock >= bus->expected_navigation_arrival){

                //First, Check if last stop of the direction's route. If so, handle it :).
                if (bus->bus_direction == CIBELES){
                    if (bus->stops_reached == sim_params->global_params->stops_list_data->size_toA - 1){
                        //Process the shift change.
                        if (bus->travels_completed +1 == bus->travels_scheduled){
                            save_last_row(bus, sim_params);
                            bus->ending_service = true;

                            //call the ending_bus_function.
                            ending_bus_service(bus, sim_params);
                            break;
                        }

                        save_last_row(bus, sim_params);
                        bus->occupation = 0;
                        bus->stops_reached = 0;
                        bus->travels_completed ++;
                        //update headway start.
                        bus->bus_direction = bus->headway_times[bus->travels_completed].bus_direction;
                        if (bus->bus_direction == CIBELES){
                            bus->stop = sim_params->global_params->stops_list_data->stopcodes_toA[0];
                        } else{
                            bus->stop = sim_params->global_params->stops_list_data->stopcodes_toB[0];
                        }

                        bus->state = waiting_headway;
                        //Check if the bus is delayed. If so, save_anomaly_row.

                        if (bus->headway_times[bus->travels_completed].departure_time < sim_params->global_clock){
                            //Calculate the delay in seconds;
                            u32 delay = sim_params->global_clock -
                            bus->headway_times[bus->travels_completed].departure_time;
                            save_anomaly_row(bus, delay, sim_params);
                        }
                        break;
                    }
                } else{
                    if (bus->stops_reached == sim_params->global_params->stops_list_data->size_toB -1){
                        if (bus->travels_completed +1 == bus->travels_scheduled){
                            save_last_row(bus, sim_params);
                            bus->ending_service = true;
                            ending_bus_service(bus, sim_params);
                            break;
                        }

                        save_last_row(bus, sim_params);
                        bus->occupation = 0;
                        bus->stops_reached = 0;
                        bus->travels_completed ++;
                        //update headway start.
                        bus->bus_direction = bus->headway_times[bus->travels_completed].bus_direction;
                        bus->state = waiting_headway;
                        bus->time_travelled = 0;

                        //Check if the bus is delayed. If so, save_anomaly_row.

                        if (bus->headway_times[bus->travels_completed].departure_time < sim_params->global_clock){
                            //Calculate the delay in seconds;
                            u32 delay = sim_params->global_clock -
                            bus->headway_times[bus->travels_completed].departure_time;
                            save_anomaly_row(bus, delay, sim_params);
                        }
                        break;
                    }
                }

                bus->state = stopped;
                bus->stopped_state = arrived;    
                
                //No break for intentional fall through to stopped
            }else{
                //as the stopping condition is not met, just breaks and exit the loop.
                break;
            }
        }

        case stopped: {
            switch(bus->stopped_state){
                case arrived: {
                    //Starts comms with stop agent. 
                    if (bus->bus_direction == CIBELES){
                        bus->stop_reached = sim_params->stops_toA[bus->stops_reached];
                    }else{
                        bus->stop_reached = sim_params->stops_toB[bus->stops_reached];
                    }


                    message *new_message = malloc(sizeof(message));

                    if (!new_message){
                        perror("Error allocating memory for new message\n");
                        exit(-3);
                    }
                    new_message->sender = &bus->agent;
                    new_message->message_type = query;
                    new_message->protocol_type = QUERY_IF;
                    new_message->receiver = &bus->stop_reached->agent;
                    new_message->payload = (void *)"Bus arrived to stop";
                    new_message->payload_owned = false;
                    send_message(new_message);

                    //Move to waiting_stop_answer
                    bus->stopped_state = waiting_stop_answer;
                    
                    //Here the break is mandatory to save cycles, cause in this iter
                    //the stop never will have answered
                    break;
                }
                case waiting_stop_answer:{

                    message *agree_stop = read_message_FIFO(
                                &bus->agent, agree);
                    if (agree_stop){
                        //if agree, read payload and free check inform
                        if (strcmp((const char *)agree_stop->payload, 
                            "Here is the passengers information") == 0){

                            //first cleanup the memory.
                            cleanup_message(agree_stop);

                            //Then reads the inform
                            message *inform_stop = read_message_FIFO(
                                &bus->agent, inform);

                            if (inform_stop){
                                //If both messages received, means the comm works. Process boards
                                //and dropoffs information and update state

                                const u16 *p = inform_stop->payload;
                                u16 pass_to_board   = p[0];
                                u16 pass_to_dropoff = p[1];
                                cleanup_message(inform_stop);
                                u16 residual_boards = update_bus_occupancy(bus,
                                                    pass_to_board, pass_to_dropoff);
                                save_results_row(bus, pass_to_board, pass_to_dropoff, residual_boards,
                                                    sim_params);
                                
                                request_to_update_stop(bus, pass_to_board, residual_boards);
                                bus->stopped_state = waiting_stop_validation;
                                
                                //infer the extra time based on the number of boards and driopoffs.
                                process_extra_time_at_stop(bus, 
                                    pass_to_board - residual_boards, pass_to_dropoff,
                                    sim_params);

                                
                            }else{
                                perror("Error in bus->stop request passengers communication\n");
                                exit(-2);
                            }
                        }else{
                            fprintf(stderr, "Unknown message %s\n", (char *)agree_stop->payload);
                            free(agree_stop->payload);
                            exit(-3);
                        }
                    }
                    break;
                }
                case waiting_stop_validation:{
                    message *agree_message = read_message_FIFO(
                                &bus->agent, agree);
                    if (agree_message){
                        
                        if (strcmp((const char *)agree_message->payload, "Ok") == 0){

                            cleanup_message(agree_message);

                            message *inform_message = read_message_FIFO(
                                    &bus->agent, inform);
                            
                            if (inform_message){
                                if (strcmp((const char *)inform_message->payload, "Done") == 0){
                                    cleanup_message(inform_message);
                                    bus->stopped_state = wait_extra_time;
                                    
                                }else{
                                    fprintf(stderr, "Unknown message %s\n", (char *)inform_message->payload);
                                    free(inform_message->payload);
                                    exit(-3);
                                }
                            }else{
                               perror("Error in bus->stop request update passengers info communication\n");
                               exit(-2); 
                            }
                            
                        }
                    }else{
                        //if no message yet, weird but can happen. exit and no checjk of wait extra time
                        break;
                    }

                    //Intentional fall through to check wait extra time, cause might be zero and saves us 
                    //a wasted cycle.

                }
                case wait_extra_time:{
                    if (sim_params->global_clock >= bus->extra_time_awaital){
                        /*
                         * Once here, before moving and breaking, it should infer the next stop's arrival time.
                        */
                        
                        bus->expected_navigation_arrival = 
                        return_next_time_to_stop(bus->stop_reached->stop_code,
                            sim_params, bus->bus_direction);

                        bus->time_travelled = bus->expected_navigation_arrival - sim_params->global_clock;
                        
                        bus->stops_reached ++;

                        if (bus->bus_direction == CIBELES){
                            bus->stop = sim_params->global_params->stops_list_data->stopcodes_toA[bus->stops_reached];
                        } else{
                            bus->stop = sim_params->global_params->stops_list_data->stopcodes_toB[bus->stops_reached];
                        }

                        bus->state = moving;
                        break;
                    }
                }     

            }
        }
    }
}




void reset_bus(void *self){

    bus *bus = self;

    bus->state = waiting_headway;

    bus->stopped_state = arrived;

    reset_inbox(&bus->agent, BUS_MESSAGE_TYPES, BUS_INBOXES_NUMBER);

    bus->occupation = 0;

    bus->anomalies_idx = 0;
    bus->results_idx = 0;

    //qallocate new mem.

    //jit.
    bus->buffer_results = NULL;
    bus->buffer_anomalies = NULL;

    //allocate memory for both results array and anomalies one.
    results_row *reserverd_results = malloc(sizeof(results_row)* bus->results_allocated);

    if (!reserverd_results){
        perror("Error allocating mem for results buffer in bus agent creation\n");
        exit(-3);
    }

    anomaly_row *reserverd_anomalies = malloc(sizeof(anomaly_row)* bus->anomalies_allocated);

    if (!reserverd_anomalies){
        perror("Error allocating mem for anomalies buffer in bus agent creation\n");
        exit(-3);
    }

    bus->buffer_anomalies = reserverd_anomalies;
    bus->buffer_results = reserverd_results;





    bus->stops_reached = 0;

    bus->travels_completed = 0;

    bus->ending_service = false;

    bus->stop_reached = NULL;
    bus->expected_navigation_arrival = 0;
    bus->departure_timeslot = 0;
    bus->time_travelled = 0;
    bus->extra_time_awaital = 0;
}




void cleanup_bus(void *self){

    //Needs to, cleanup all stuff that relies on the bus agent. That means.

    //Cleanup the inboxes mem allocation.
    bus *bus = self;
    destroy_inbox(&bus->agent, BUS_MESSAGE_TYPES, BUS_INBOXES_NUMBER);
    
    bus->stop_reached = NULL;

    bus->headway_times = NULL;


    // free(bus->buffer_anomalies);
    // bus->buffer_anomalies = NULL;

    // free(bus->buffer_results);
    // bus->buffer_results = NULL;
}

