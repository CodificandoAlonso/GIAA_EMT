#include "agents/bus/bus.h"
#include "utils/utils.h"
#include "agents/generic/agents.h"
#include "engine/simulation.h"
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
        bus.ending_service = false;
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



byte update_bus_occupancy(bus *bus, byte boards, byte dropoffs){

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


void save_results_row(bus *bus, byte pass_to_board, byte pass_to_dropoff, byte residual_boards,
                      const global_simulation_parameters *sim_params){
    bus->buffer_results[bus->results_idx] = (results_row){
        sim_params->simulation_id,
        bus->bus_code,
        bus->travels_completed,
        bus->stop,
        bus->bus_direction,
        sim_params->timeslot,
        bus->departure_timeslot,
        (pass_to_board - residual_boards),
        pass_to_dropoff,
        residual_boards,
        bus->occupation,
        bus->time_travelled
    };
    bus->results_idx ++;
}


void request_to_update_stop(bus *bus, byte expected_boards, byte unable_boards){

}


void update_bus_in_sim(void *self, const global_simulation_parameters *sim_params){
    bus *bus = self;

    switch (bus->state){

        case waiting_headway:{
            if (sim_params->global_clock >= bus->headway_times[bus->travels_completed].departure_time){
                
                bus->departure_timeslot = sim_params->timeslot;

                //Bus state moves into moving, fo the bus to communicate with the first stop.
                bus->state = moving;
                bus->expected_navigation_arrival = sim_params->global_clock;

                //Here should infer the specific mean time between stops via random
                //param of the distribution specified.
            }
        }

        case moving: {
            if (sim_params->global_clock >= bus->expected_navigation_arrival){
                bus->state = stopped;
                bus->stopped_state = arrived;

                /*
                 *here should see if here is when advancing stops reachjed counter, or is it done
                 * after finishing the comms with the stop. Prob after. Should see also
                 * how stops are stored. So, with all those stuff, starts the communications with it.
                 * Also, todo: later on, check the dying-condition for finished shifts.
                 */

                
                
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

                                byte pass_to_board = ((byte *)inform_stop->payload)[0];
                                byte pass_to_dropoff = ((byte *)inform_stop->payload)[1];
                                cleanup_message(inform_stop);
                                byte residual_boards = update_bus_occupancy(bus,
                                                    pass_to_board, pass_to_dropoff);
                                save_results_row(bus, pass_to_board, pass_to_dropoff, residual_boards,
                                                    sim_params);
                                
                                request_to_update_stop(bus, pass_to_board, residual_boards);
                                bus->stopped_state = waiting_stop_validation;

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
                         * Once here, before moving and breaking, this should check and update if last stop,
                         if last shift, and so, so the bus can execute ending code or not.
                        */




                        bus->state = moving;
                        break;
                    }
                }
            }
        }
    }
}




void reset_bus(void *self){

}

void cleanup_bus(void *self){

    
}

