#pragma once

#include<stdio.h>
#include<stdlib.h>
#include<utils/utils.h>

#define INIT_CAPACITY 8


typedef struct Agent Agent;





typedef enum PROTOCOL_TYPE {
    REQUEST = 0,
    QUERY_IF = 1,
    QUERY_REF = 2
} PROTOCOL_TYPE;


typedef enum MESSAGE_TYPE {
    request = 0,
    query = 1,
    agree = 2,
    refuse = 3,
    inform = 4,
}MESSAGE_TYPE;



typedef struct message {
    Agent *sender;
    Agent *receiver;
    PROTOCOL_TYPE protocol_type;
    MESSAGE_TYPE message_type;
    void *payload;
}message;



typedef struct inbox {
    message *messages;
    size_t head;
    size_t size;
    size_t capacity;
}inbox;


/**
 * @brief auxiliar function to init any given inbox. Sub-calld
 * by init_inbox
 */
void init_specific_inbox(inbox *ib);

/**
 * @brief function to init all inboxes in an agent. It only requires the agent struct,
 * and will init the inboxes required by the simulation specified.
 */
void init_inbox(Agent *agent, MESSAGE_TYPE *message_types, size_t n);




message *read_specific_message_FIFO(inbox *ib);


/**
 * @brief function that given an agent struct and the message type reads the inbox
 * corresponding to the message type and returns the message corresponding with FIFO
 * importance.
 * @returns the pointer to the concrete first message or
 * @returns NULL
 */
message *read_message_FIFO(Agent *agent, MESSAGE_TYPE message_type);



/**
 * @brief get the message full of its contents and put it in the corresponding
 * inbox.
 */
void send_message(message *message);


/**
* @brief The *messages inbox needs re-capacitation. It should first,
* alloc memory for the new array doubling capacity.
* Then, starting from head until size is reached, copying the elements into
* the new array.
* Lastly, restarts head to 0, capacity to its double, and freed the remaining
* memspace. For last, update the starting pointer into *messages
*/
void handle_specific_inbox_expansion (inbox *ib);



void destroy_specific_inbox(inbox *ib);

/**
 * @brief function call to destroy all inboxes created in a given agent.
 */
void destroy_inbox(Agent *agent, MESSAGE_TYPE *message_types, size_t n);


/**
 * @brief Once read the relevant content from a message, this function
 * cleans up the memory allocated for the payload for each message, so each
 * agent obtain the required abstraction of not knowing how its handle.
 * The idea is that the ownership of the pointer relies on the agent *receiver.
 */
void cleanup_message(message *message);