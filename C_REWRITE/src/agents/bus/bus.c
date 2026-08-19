#include "agents/bus/bus.h"
#include "utils/utils.h"
#include "agents/generic/agents.h"
#include<stdio.h>
#include<stdlib.h>



bus *create_bus(u16 stop_code, direction direction,
                headway_times *headway_departures, byte travels_scheduled)
    {
        bus *bus = calloc(1, sizeof(*bus));

        if (!bus) {
            return NULL;
        }

        bus->stop = stop_code;
        bus->bus_direction = direction;
        bus->headway_times = headway_departures;
        bus->travels_scheduled = travels_scheduled;

        bus->agent.startup_agent = startup_bus_agent;
        bus->agent.update_in_sim = update_bus_in_sim;
        bus->agent.cleanup = cleanup_bus;

        bus->agent.startup_agent(bus);

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



void update_bus_in_sim(void *self, void *sim_params){
    bus *bus = self;

    simulation_params *sim_params = (simulation_params *)sim_params;

    switch (bus->state){

        case waiting_headway:{
            if (sim_params->global_clock >= bus->headway_times[bus->travels_completed].departure_time){
                bus->state = moving;
                bus->departure_timeslot = sim_params->timeslot;
                //Here should infer the specific mean time between stops via random
                //param of the distribution specified.
            }
        }

        case stopped: {
            switch(bus->stopped_state){
                case arrived: {
                    //Starts comms with stop agent. Move to waiting_stop_answer

                    bus->stopped_state = waiting_stop_answer;
                    //Here the break is mandatory to save cycles, cause in this iter
                    //the stop never will have answered
                    break;
                }
                case waiting_stop_answer:{

                    break;
                }
                

                //not sure
                //case waiting_stop_validation:{}


                case wait_extra_time:{
                    //if ();
                }
            }

        }

        case moving: {
            //if ()

        }

    }

}

void cleanup_bus(void *self){

    
}

