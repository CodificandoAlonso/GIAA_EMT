#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<math.h>

#include "agents/stop/stop.h"
#include "comms/fipa.h"
#include "utils/utils.h"
#include "agents/generic/agents.h"
#include "engine/simulation.h"



stop create_stop(u16 stop_code){

    stop new_stop = {0};

    new_stop.stop_code = stop_code;

    new_stop.agent.startup_agent = startup_stop_agent;
    new_stop.agent.update_in_sim = update_stop_in_sim;
    new_stop.agent.cleanup = cleanup_stop;
    new_stop.agent.reset_agent = reset_stop;
    new_stop.passengers_idx = 0;
    new_stop.agent.startup_agent(&new_stop);
    return new_stop;
}


void startup_stop_agent(void *self){
    stop *stop = self;

    stop->stop_state = passengers_custody;
    
    u32 *passengers_timearray = malloc(sizeof(u32)*BASE_PASSENGERS_MAX_SIZE);
    if (!passengers_timearray){
        fprintf(stderr, "Error at stop %u startup allocating memory for passengers timearray\n", stop->stop_code);
        exit(-3);
    }
    stop->passengers_time_of_creation = passengers_timearray;
    stop->allocation_len_passengers = BASE_PASSENGERS_MAX_SIZE;

    stop->max_allocated_buffer_size = BASE_PASSENGERS_BUFFER_MAX_SIZE;

    stop->agent.message_types = STOP_MESSAGE_TYPES;
    stop->agent.inboxes_numbers = (size_t)STOP_INBOXES_NUMBER;

    init_inbox(&stop->agent, stop->agent.message_types, stop->agent.inboxes_numbers);
}




void crop_time_of_passengers(stop *stop, size_t len_to_crop){


    if (len_to_crop == stop->number_of_passengers){
        stop->number_of_passengers = 0;
        return;
    }

    // 'crop' the first len_to_crop elements as they left the stop. That implies copy from len to crop to passengers
    // to the init of the array;
    size_t remaining = stop->number_of_passengers - len_to_crop;

    memmove(stop->passengers_time_of_creation, stop->passengers_time_of_creation + len_to_crop,
                sizeof(u32) * remaining);

    stop->number_of_passengers -= len_to_crop;
}

void process_and_save_passengers_row(stop *stop, byte factual_boards, u16 bus_code,
     byte travels_completed, const sim_context  *sim_params){

    if (factual_boards == 0) {
    return;
    }
    if ((u16)factual_boards > stop->number_of_passengers){
        perror("Error at passengers comparaison. Factual boards cannot be bigger than passengers \
            on stop\n");
        exit(-8);
    }

    if (stop->max_allocated_buffer_size == stop->passengers_idx){
        //In that case needed to reallocate.
        stop->max_allocated_buffer_size *= 2;
        passengers_row *new_buffer = realloc(stop->buffer_passengers, sizeof(passengers_row) *stop->max_allocated_buffer_size);
        if (!new_buffer){
            perror("Error re-allocating new memory for buffer passnegers\n");
            exit(-3);
        }
        stop->buffer_passengers = new_buffer;
    }
    passengers_row new_pass_row = {
    .sim_identifier = sim_params->simulation_id,
    .bus_code = bus_code,
    .travels_completed = travels_completed,
    .stopcode = stop->stop_code,
    .timeslot = sim_params->timeslot,
    .current_time = sim_params->global_clock,
    .n_generation_times = factual_boards
    };

    memcpy(new_pass_row.generation_times, stop->passengers_time_of_creation, sizeof(u32)*factual_boards);

    crop_time_of_passengers(stop, factual_boards);
    
    stop->buffer_passengers[stop->passengers_idx++] = new_pass_row;
}




void update_stop_in_sim(void *self, const sim_context  *sim_params){

    stop *stop = self;

    switch (stop->stop_state){

        case passengers_custody:{
            //This case is globally updated. The reason why, is that the stop agent itself
            //cannot be the one dictating when the passengers are generated inself. It actually
            //comes from an environmental update, dictate by the world.

            if (stop->agent.queries.size > 0) {
                stop->stop_state = interaction_with_bus;
                stop->interaction_state = initial_conversation;
            }else {break;}
            // } else if (stop->agent.requests.size > 0) {
            //     stop->stop_state = interaction_with_bus;
            //     stop->interaction_state = last_conversation;
            // } else break;

        }
        case interaction_with_bus:{
            switch (stop->interaction_state){

                case initial_conversation:{
                    message *query_message = read_specific_message_FIFO(
                            &stop->agent.queries
                    );
                    if (query_message){
                        char_and_occ *payload_recv = (char_and_occ *)query_message->payload;

                        if (strcmp(payload_recv->message, "Bus arrived to stop") != 0){
                            fprintf(stderr,"Performative unknown message %s in query stop mailbox\n",
                            (char *)query_message->payload);
                            exit(-4);
                        }
                        u32 bus_occupation = payload_recv->occupation;
                        cleanup_char_and_occ_message(query_message);

                        //Infer dropoffs. It invoices a global action handler from the sim, because
                        //the drpoff knowledge cannot be into the agent own's beliefs or knowkledge.
                        u16 dropoffs = infer_dropoffs(stop->stop_code, sim_params, bus_occupation);
                        
                        message *answer_back_agree_message = calloc(1, sizeof(message));
                        message *answer_back_inform_message = calloc(1, sizeof(message));

                        answer_back_agree_message->message_type = agree;
                        answer_back_agree_message->protocol_type = QUERY_REF;
                        answer_back_agree_message->sender = &stop->agent;
                        answer_back_agree_message->receiver = query_message->sender;
                        answer_back_agree_message->payload = (void *)"Here is the passengers information";
                        answer_back_agree_message->payload_owned = false;

                        send_message(answer_back_agree_message);


                        answer_back_inform_message->message_type = inform;
                        answer_back_inform_message->protocol_type = QUERY_REF;
                        answer_back_inform_message->sender = &stop->agent;
                        answer_back_inform_message->receiver = query_message->sender;


                        u16 *payload = malloc(sizeof(u16)*2);

                        if (!payload){
                            perror("error allocating memory for payload stop-bus answer inform\n");
                            exit(-3);
                        }
                        payload[0] = stop->number_of_passengers;
                        payload[1] = dropoffs;
                        answer_back_inform_message->payload = (void *)payload;
                        answer_back_inform_message->payload_owned = true;      
                        send_message(answer_back_inform_message);

                        stop->interaction_state = last_conversation;
                        break;
                    }else{
                        break;
                    }
                    break;
                }
                case last_conversation:{
                    message *req_message = read_specific_message_FIFO(
                            &stop->agent.requests
                    );
                    if (req_message){

                        char_and_num *payload = req_message->payload;

                        if (strcmp(payload->message, "Update passengers. I boarded") != 0){
                            fprintf(stderr,"Performative unknown message %s in req stop mailbox\n",
                            (char *)req_message->payload);
                            exit(-4);
                        }
                        byte factual_boards = payload->passengers_boarded;
                        byte travels_completed = payload->travels_completed;
                        u16 bus_code = payload->bus_code;

                        cleanup_char_and_num_message(req_message);



                        message *answer_back_agree_message = calloc(1, sizeof(message));
                        message *answer_back_inform_message = calloc(1, sizeof(message));

                        answer_back_agree_message->message_type = agree;
                        answer_back_agree_message->protocol_type = QUERY_REF;
                        answer_back_agree_message->sender = &stop->agent;
                        answer_back_agree_message->receiver = req_message->sender;
                        answer_back_agree_message->payload = (void *)"Ok";
                        answer_back_agree_message->payload_owned = false;
                        send_message(answer_back_agree_message);


                        //Compare factual_boards with passengers in stop. Save the passengers_buffer
                        //info with the necesarry info associated and change state to passegners_custody
                        process_and_save_passengers_row(stop, factual_boards,bus_code, travels_completed,
                         sim_params);

                        answer_back_inform_message->message_type = inform;
                        answer_back_inform_message->protocol_type = QUERY_REF;
                        answer_back_inform_message->sender = &stop->agent;
                        answer_back_inform_message->receiver = req_message->sender;
                        answer_back_inform_message->payload = (void *)"Done";
                        answer_back_inform_message->payload_owned = false;

                        send_message(answer_back_inform_message);
                        stop->stop_state = passengers_custody;
                        break;
                    }else{
                        break;
                    }
                    break;
                }
            }
        }
    }
}


void reset_stop(void *self){
    stop *stop = self;
    reset_inbox(&stop->agent, STOP_MESSAGE_TYPES, STOP_INBOXES_NUMBER);

    stop->number_of_passengers = 0;
    stop->passengers_generating = 0.0;
    stop->stop_state = passengers_custody;
    stop->passengers_idx = 0;

    //malloc memory for buffer paswsengers again.
    passengers_row *buffer_passengers = malloc(sizeof(passengers_row) *stop->max_allocated_buffer_size);
    if (!buffer_passengers){
        fprintf(stderr, "Error at stop %u startup allocating memory for passengers buffer log\n", stop->stop_code);
        exit(-3);
    }

    stop->buffer_passengers = buffer_passengers;

}



void cleanup_stop(void *self){
    //Needs to, cleanup all stuff that relies on the stop agent. That means.

    //Cleanup the inboxes mem allocation.
    stop *stop = self;
    destroy_inbox(&stop->agent, STOP_MESSAGE_TYPES, STOP_INBOXES_NUMBER);
    
    free(stop->passengers_time_of_creation);
    stop->passengers_time_of_creation = NULL;

    // free(stop->buffer_passengers);
    // stop->buffer_passengers = NULL;
}