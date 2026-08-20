#include "comms/fipa.h"
#include "utils/utils.h"
#include "agents/generic/agents.h"
#include<stdio.h>
#include<stdlib.h>




void init_specific_inbox(inbox *ib){
    ib->capacity = INIT_CAPACITY;
    ib->size = 0;
    ib->head = 0;
    ib->messages = malloc(sizeof(message)*ib->capacity);
    if (!ib->messages){
        perror("ERROR CREATING MALLOC'ED INBOX\n");
        exit(-3);
    }
}



void init_inbox(Agent *agent, MESSAGE_TYPE *message_types, size_t n){

    for (size_t i=0; i < n; i++){
        switch (message_types[i]){
            case request:
                init_specific_inbox(&agent->requests);
                break;
            case query:
                init_specific_inbox(&agent->queries);
                break;
            case agree:
                init_specific_inbox(&agent->agrees);        
                break;
            case refuse:
                init_specific_inbox(&agent->refuses);
                break;
            case inform:
                init_specific_inbox(&agent->informs);
                break;
        }
    }
}




message *read_specific_message_FIFO(inbox *ib){
    if (ib->size == 0)
        return NULL;
    message *ret_message = &ib->messages[ib->head];
    ib->head = (ib->head + 1) % ib->capacity;
    ib->size --;

    return ret_message;
}





message *read_message_FIFO(Agent *agent, MESSAGE_TYPE message_type){
    switch (message_type){
        case request:
            return read_specific_message_FIFO(&agent->requests);
        case query:
            return read_specific_message_FIFO(&agent->queries);
        case agree:
            return read_specific_message_FIFO(&agent->agrees);
        case refuse:
            return read_specific_message_FIFO(&agent->refuses);
        case inform:
            return read_specific_message_FIFO(&agent->informs);
    }
    return NULL;
}

void inbox_push(inbox *ib, message *msg)
{
    if (ib->size == ib->capacity)
        handle_specific_inbox_expansion(ib);

    size_t index = (ib->head + ib->size) % ib->capacity;

    ib->messages[index] = *msg;
    ib->size++;
}



void send_message(message *msg){
    switch (msg->message_type){
        case request:
            inbox_push(&msg->receiver->requests, msg);
            break;
        case query:
            inbox_push(&msg->receiver->queries, msg);
            break;
        case agree:
            inbox_push(&msg->receiver->agrees, msg);
            break;
        case refuse:
            inbox_push(&msg->receiver->refuses, msg);
            break;
        case inform:
            inbox_push(&msg->receiver->informs, msg);
            break;
    }
    free(msg);
}



void handle_specific_inbox_expansion (inbox *ib){
    message *new_array = malloc(sizeof(message) *2*ib->capacity);
    if (!new_array){
        perror("Error reasigning request memory\n");
        exit(-5);
    }
    for (size_t i = 0; i< ib->size; i ++){
        size_t old_idx = (ib->head + i)
                            % ib->capacity;
        
        new_array[i] = ib->messages[old_idx];
    }
    free(ib->messages);
    ib->messages = new_array;
    ib->head = 0;
    ib->capacity *= 2;
}


void destroy_specific_inbox(inbox *ib){
    free(ib->messages);
    ib->size = 0;
    ib->capacity = 0;
    ib->head = 0;
}


void destroy_inbox(Agent *agent, MESSAGE_TYPE *message_types, size_t n){
    for (size_t i=0; i < n; i++){
        switch (message_types[i]){
            case request:
                destroy_specific_inbox(&agent->requests);
                break;
            case query:
                destroy_specific_inbox(&agent->queries);
                break;
            case agree:
                destroy_specific_inbox(&agent->agrees);
                break;
            case refuse:
                destroy_specific_inbox(&agent->refuses);
                break;
            case inform:
                destroy_specific_inbox(&agent->informs);
                break;
        }
    }
}




void cleanup_message(message *message){
    free(message->payload);
    message->payload = NULL;
}