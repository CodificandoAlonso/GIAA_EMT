#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<math.h>

#include "agents/stop/stop.h"
#include "utils/utils.h"
#include "agents/generic/agents.h"
#include "engine/simulation.h"



stop *create_stop(u16 stop_code){

    stop *new_stop = calloc(1,sizeof(stop));

    if (!new_stop){
        perror("Error allocating memory for new stop agent\n");
        exit(-3);
    }

    new_stop->stop_code = stop_code;

    new_stop->agent.startup_agent = startup_stop_agent;
    new_stop->agent.update_in_sim = update_stop_in_sim;
    new_stop->agent.cleanup = cleanup_stop;
    new_stop->passengers_idx = 0;
    new_stop->agent.startup_agent(new_stop);
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

    passengers_row *buffer_passengers = malloc(sizeof(passengers_row) *BASE_PASSENGERS_BUFFER_MAX_SIZE);
    if (!buffer_passengers){
        fprintf(stderr, "Error at stop %u startup allocating memory for passengers buffer log\n", stop->stop_code);
        exit(-3);
    }

    stop->buffer_passengers = buffer_passengers;
    stop->max_allocated_buffer_size = BASE_PASSENGERS_BUFFER_MAX_SIZE;

    stop->agent.message_types = STOP_MESSAGE_TYPES;
    stop->agent.inboxes_numbers = (size_t)STOP_INBOXES_NUMBER;

    init_inbox(&stop->agent, stop->agent.message_types, stop->agent.inboxes_numbers);
}




u32 *crop_time_of_passengers(stop *stop, size_t len_to_crop){


    //Uopdate this piece of code. Not optimal yet. This type of code HAS to be optimal

    if (len_to_crop == stop->number_of_passengers){
        u32 *new_passengers_time_array = malloc(sizeof(u32)*BASE_PASSENGERS_MAX_SIZE);
        if (!new_passengers_time_array){
            perror("Error allocating new memory for passengers not in stop\n");
            exit(-3);
        }
        //free old memory
        free(stop->passengers_time_of_creation);
        stop->number_of_passengers = 0;
        return new_passengers_time_array;
    }
    u32 *new_passengers_time_array = malloc(sizeof(u32)* (stop->number_of_passengers - len_to_crop));

    if (!new_passengers_time_array){
        perror("Error allocating new memory for passengers not in stop\n");
        exit(-3);
    }

    // 'crop' the first len_to_crop elements as they left the stop. That implies copy from len to crop to passengers
    // to the new array;
    size_t i = 0;
    for (size_t idx = len_to_crop; idx < stop->number_of_passengers; idx ++){
        new_passengers_time_array[i++] = stop->passengers_time_of_creation[idx];
    }
    free(stop->passengers_time_of_creation);
    stop->number_of_passengers -= (u16)len_to_crop;
    return new_passengers_time_array;
}

void process_and_save_passengers_row(stop *stop, u16 factual_boards, u16 bus_code, byte travels_completed, const global_simulation_parameters *sim_params){

    if (factual_boards > (size_t)stop->number_of_passengers){
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
    .generation_times = malloc(sizeof(u32) * factual_boards)
    };
    if (!new_pass_row.generation_times) {
    perror("Error allocating generation times");
    exit(-3);
    }
    memcpy(new_pass_row.generation_times, stop->passengers_time_of_creation, sizeof(u32)*factual_boards);

    stop->passengers_time_of_creation = crop_time_of_passengers(stop, factual_boards);

}




void update_stop_in_sim(void *self, const global_simulation_parameters *sim_params){

    stop *stop = self;

    switch (stop->stop_state){

        case passengers_custody:{

            //This case is globally updated. The reason why, is that the stop agent itself
            //cannot be the one dictating when the passengers are generated inself. It actually
            //comes from an environmental update, dictate by the world.
            break;
        }
        case interaction_with_bus:{
            switch (stop->interaction_state){

                case initial_conversation:{
                    message *query_message = read_specific_message_FIFO(
                            &stop->agent.queries
                    );
                    if (query_message){
                        if (strcmp((char *)query_message->payload, "Bus arrived to stop") != 0){
                            fprintf(stderr,"Performative unknown message %s in query stop mailbox\n",
                            (char *)query_message->payload);
                            exit(-4);
                        }
                        cleanup_message(query_message);

                        //Infer dropoffs. It invoices a global action handler from the sim, because
                        //the drpoff knowledge cannot be into the agent own's beliefs or knowkledge.

                        message *answer_back_agree_message = calloc(1, sizeof(message));
                        message *answer_back_inform_message = calloc(1, sizeof(message));

                        answer_back_agree_message->message_type = agree;
                        answer_back_agree_message->protocol_type = QUERY_REF;
                        answer_back_agree_message->sender = &stop->agent;
                        answer_back_agree_message->receiver = query_message->receiver;
                        answer_back_agree_message->payload = (void *)"Here is the passengers information";
                        
                        send_message(answer_back_agree_message);


                        answer_back_inform_message->message_type = inform;
                        answer_back_inform_message->protocol_type = QUERY_REF;
                        answer_back_inform_message->sender = &stop->agent;
                        answer_back_inform_message->receiver = query_message->receiver;

                        //tmp
                        u16 boards = 0, dropoffs = 0;
                        u16 payload[2] = {boards,dropoffs};
                        answer_back_inform_message->payload = (void *)payload;           
                        send_message(answer_back_inform_message);

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
                        u16 factual_boards = payload->passengers_boarded;

                        cleanup_char_and_num_message(req_message);



                        message *answer_back_agree_message = calloc(1, sizeof(message));
                        message *answer_back_inform_message = calloc(1, sizeof(message));

                        answer_back_agree_message->message_type = agree;
                        answer_back_agree_message->protocol_type = QUERY_REF;
                        answer_back_agree_message->sender = &stop->agent;
                        answer_back_agree_message->receiver = req_message->receiver;
                        answer_back_agree_message->payload = (void *)"Ok";
                        
                        send_message(answer_back_agree_message);


                        //Compare factual_boards with passengers in stop. Save the passengers_buffer
                        //info with the necesarry info associated and change state to passegners_custody
                        process_and_save_passengers_row(stop, factual_boards, sim_params);

                        answer_back_inform_message->message_type = inform;
                        answer_back_inform_message->protocol_type = QUERY_REF;
                        answer_back_inform_message->sender = &stop->agent;
                        answer_back_inform_message->receiver = req_message->receiver;
                        answer_back_agree_message->payload = (void *)"Done";

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


void cleanup_stop(void *self){}