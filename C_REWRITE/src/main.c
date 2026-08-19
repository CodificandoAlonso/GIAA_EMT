#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <assert.h>

#include "comms/fipa.h"
#include "agents/generic/agents.h"


/* ******************************************************************
 * TEST PAYLOAD
 * ******************************************************************/

typedef struct {
    uint64_t id;
    uint32_t sender_id;
    uint32_t receiver_id;
} TestPayload;


/* ******************************************************************
 * MESSAGE HELPERS
 * ******************************************************************/

static message make_message(
    Agent *sender,
    Agent *receiver,
    MESSAGE_TYPE type,
    PROTOCOL_TYPE protocol,
    uint64_t id
){
    TestPayload *payload = malloc(sizeof(TestPayload));

    assert(payload != NULL);

    payload->id = id;
    payload->sender_id = (uint32_t)(uintptr_t)sender;
    payload->receiver_id = (uint32_t)(uintptr_t)receiver;

    message msg = {
        .sender = sender,
        .receiver = receiver,
        .protocol_type = protocol,
        .message_type = type,
        .payload = payload
    };

    return msg;
}


/*
 * The payload is owned by the message once send_message()
 * has been called. Therefore, do NOT free it before reading
 * the message from the inbox.
 */
static void destroy_message_payload(message *msg)
{
    free(msg->payload);
    msg->payload = NULL;
}


/* ******************************************************************
 * TEST 1
 *
 * Single inbox.
 *
 * - Only REQUEST inbox is initialized.
 * - Send 100000 messages.
 * - Forces multiple expansions.
 * - Read everything back.
 * - Verify FIFO ordering.
 * ******************************************************************/

static void test_single_inbox_expansion(void)
{
    printf("\n========================================\n");
    printf("TEST 1: Single inbox + expansion\n");
    printf("========================================\n");

    Agent agent = {0};

    MESSAGE_TYPE types[] = {
        request
    };

    init_inbox(&agent, types, 1);

    const size_t N = 100000;

    printf("Sending %zu REQUEST messages...\n", N);

    for (size_t i = 0; i < N; i++) {

        message msg = make_message(
            &agent,
            &agent,
            request,
            REQUEST,
            i
        );

        send_message(&msg);

        /*
         * IMPORTANT:
         *
         * Do NOT free msg.payload here.
         *
         * send_message() performs a shallow copy of message,
         * so the inbox now owns the pointer.
         */
    }

    printf("Final capacity: %zu\n", agent.requests.capacity);
    printf("Final size:     %zu\n", agent.requests.size);

    assert(agent.requests.size == N);
    assert(agent.requests.capacity >= N);

    printf("Reading messages FIFO...\n");

    for (size_t i = 0; i < N; i++) {

        message *msg =
            read_message_FIFO(&agent, request);

        assert(msg != NULL);
        assert(msg->message_type == request);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == i);

        destroy_message_payload(msg);
    }

    assert(agent.requests.size == 0);

    assert(
        read_message_FIFO(&agent, request) == NULL
    );

    printf("PASS\n");

    destroy_inbox(&agent, types, 1);
}


/* ******************************************************************
 * TEST 2
 *
 * Circular buffer wrap-around.
 *
 * Fill buffer.
 * Read some messages.
 * Push more messages.
 *
 * This forces writes to wrap around to the beginning
 * of the physical array.
 * ******************************************************************/

static void test_fifo_wraparound(void)
{
    printf("\n========================================\n");
    printf("TEST 2: FIFO circular wrap-around\n");
    printf("========================================\n");

    Agent agent = {0};

    MESSAGE_TYPE types[] = {
        request
    };

    init_inbox(&agent, types, 1);

    /*
     * Initial capacity = 8.
     */

    for (size_t i = 0; i < 8; i++) {

        message msg = make_message(
            &agent,
            &agent,
            request,
            REQUEST,
            i
        );

        send_message(&msg);
    }

    assert(agent.requests.size == 8);

    /*
     * Read first five messages.
     *
     * Expected:
     *
     * 0 1 2 3 4
     */

    for (size_t i = 0; i < 5; i++) {

        message *msg =
            read_message_FIFO(&agent, request);

        assert(msg != NULL);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == i);

        destroy_message_payload(msg);
    }

    assert(agent.requests.size == 3);

    /*
     * Push five more.
     *
     * Expected FIFO order now:
     *
     * 5 6 7 8 9 10 11 12
     */

    for (size_t i = 8; i < 13; i++) {

        message msg = make_message(
            &agent,
            &agent,
            request,
            REQUEST,
            i
        );

        send_message(&msg);
    }

    assert(agent.requests.size == 8);

    /*
     * Read everything.
     */

    for (size_t expected = 5; expected < 13; expected++) {

        message *msg =
            read_message_FIFO(&agent, request);

        assert(msg != NULL);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == expected);

        destroy_message_payload(msg);
    }

    assert(agent.requests.size == 0);

    printf("PASS\n");

    destroy_inbox(&agent, types, 1);
}


/* ******************************************************************
 * TEST 3
 *
 * Agent using ALL five FIPA inboxes.
 *
 * Send messages to every inbox in an interleaved fashion.
 *
 * Each inbox must maintain its own independent FIFO.
 * ******************************************************************/

static void test_all_inboxes(void)
{
    printf("\n========================================\n");
    printf("TEST 3: Agent with all inboxes\n");
    printf("========================================\n");

    Agent agent = {0};

    MESSAGE_TYPE types[] = {
        request,
        query,
        agree,
        refuse,
        inform
    };

    init_inbox(&agent, types, 5);

    const size_t N = 10000;

    MESSAGE_TYPE all_types[] = {
        request,
        query,
        agree,
        refuse,
        inform
    };

    PROTOCOL_TYPE protocols[] = {
        REQUEST,
        QUERY_IF,
        QUERY_IF,
        QUERY_REF,
        REQUEST
    };

    /*
     * Send 10000 messages to each inbox.
     *
     * Messages are interleaved:
     *
     * REQUEST 0
     * QUERY 0
     * AGREE 0
     * REFUSE 0
     * INFORM 0
     * REQUEST 1
     * QUERY 1
     * ...
     */

    for (size_t i = 0; i < N; i++) {

        for (size_t t = 0; t < 5; t++) {

            message msg = make_message(
                &agent,
                &agent,
                all_types[t],
                protocols[t],
                i
            );

            send_message(&msg);
        }
    }

    /*
     * Every inbox should contain N messages.
     */

    assert(agent.requests.size == N);
    assert(agent.queries.size  == N);
    assert(agent.agrees.size   == N);
    assert(agent.refuses.size  == N);
    assert(agent.informs.size  == N);

    /*
     * Read every inbox and verify FIFO ordering.
     */

    for (size_t t = 0; t < 5; t++) {

        for (size_t i = 0; i < N; i++) {

            message *msg =
                read_message_FIFO(
                    &agent,
                    all_types[t]
                );

            assert(msg != NULL);
            assert(msg->message_type == all_types[t]);

            TestPayload *payload = msg->payload;

            assert(payload != NULL);
            assert(payload->id == i);

            destroy_message_payload(msg);
        }
    }

    assert(agent.requests.size == 0);
    assert(agent.queries.size  == 0);
    assert(agent.agrees.size   == 0);
    assert(agent.refuses.size  == 0);
    assert(agent.informs.size  == 0);

    printf("PASS\n");

    destroy_inbox(&agent, types, 5);
}


/* ******************************************************************
 * TEST 4
 *
 * Multiple agents.
 *
 * A only accepts REQUEST + INFORM.
 * B accepts all message types.
 * C only accepts QUERY + AGREE.
 *
 * Communication:
 *
 * A -> B : REQUEST
 * B -> A : INFORM
 * C -> B : QUERY
 * A -> C : AGREE
 * ******************************************************************/

static void test_multi_agent_communication(void)
{
    printf("\n========================================\n");
    printf("TEST 4: Multi-agent communication\n");
    printf("========================================\n");

    Agent A = {0};
    Agent B = {0};
    Agent C = {0};

    MESSAGE_TYPE A_types[] = {
        request,
        inform
    };

    MESSAGE_TYPE B_types[] = {
        request,
        query,
        agree,
        refuse,
        inform
    };

    MESSAGE_TYPE C_types[] = {
        query,
        agree
    };

    init_inbox(&A, A_types, 2);
    init_inbox(&B, B_types, 5);
    init_inbox(&C, C_types, 2);

    /*
     * A -> B
     */

    for (size_t i = 0; i < 1000; i++) {

        message msg = make_message(
            &A,
            &B,
            request,
            REQUEST,
            i
        );

        send_message(&msg);
    }

    /*
     * B -> A
     */

    for (size_t i = 0; i < 500; i++) {

        message msg = make_message(
            &B,
            &A,
            inform,
            REQUEST,
            i
        );

        send_message(&msg);
    }

    /*
     * C -> B
     */

    for (size_t i = 0; i < 750; i++) {

        message msg = make_message(
            &C,
            &B,
            query,
            QUERY_IF,
            i
        );

        send_message(&msg);
    }

    /*
     * A -> C
     */

    for (size_t i = 0; i < 250; i++) {

        message msg = make_message(
            &A,
            &C,
            agree,
            QUERY_IF,
            i
        );

        send_message(&msg);
    }

    /*
     * Verify inbox sizes.
     */

    assert(B.requests.size == 1000);
    assert(A.informs.size  == 500);
    assert(B.queries.size  == 750);
    assert(C.agrees.size   == 250);

    /*
     * B REQUESTS
     */

    for (size_t i = 0; i < 1000; i++) {

        message *msg =
            read_message_FIFO(&B, request);

        assert(msg != NULL);
        assert(msg->sender == &A);
        assert(msg->receiver == &B);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == i);

        destroy_message_payload(msg);
    }

    /*
     * A INFORMS
     */

    for (size_t i = 0; i < 500; i++) {

        message *msg =
            read_message_FIFO(&A, inform);

        assert(msg != NULL);
        assert(msg->sender == &B);
        assert(msg->receiver == &A);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == i);

        destroy_message_payload(msg);
    }

    /*
     * B QUERIES
     */

    for (size_t i = 0; i < 750; i++) {

        message *msg =
            read_message_FIFO(&B, query);

        assert(msg != NULL);
        assert(msg->sender == &C);
        assert(msg->receiver == &B);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == i);

        destroy_message_payload(msg);
    }

    /*
     * C AGREES
     */

    for (size_t i = 0; i < 250; i++) {

        message *msg =
            read_message_FIFO(&C, agree);

        assert(msg != NULL);
        assert(msg->sender == &A);
        assert(msg->receiver == &C);

        TestPayload *payload = msg->payload;

        assert(payload != NULL);
        assert(payload->id == i);

        destroy_message_payload(msg);
    }

    printf("PASS\n");

    destroy_inbox(&A, A_types, 2);
    destroy_inbox(&B, B_types, 5);
    destroy_inbox(&C, C_types, 2);
}


/* ******************************************************************
 * TEST 5
 *
 * Reading from an empty inbox.
 * ******************************************************************/

static void test_empty_inbox(void)
{
    printf("\n========================================\n");
    printf("TEST 5: Empty inbox\n");
    printf("========================================\n");

    Agent agent = {0};

    MESSAGE_TYPE types[] = {
        request
    };

    init_inbox(&agent, types, 1);

    assert(agent.requests.size == 0);

    message *msg =
        read_message_FIFO(&agent, request);

    assert(msg == NULL);

    printf("PASS\n");

    destroy_inbox(&agent, types, 1);
}


/* ******************************************************************
 * TEST 6
 *
 * Mixed long-running stress test.
 *
 * Continuously:
 *
 * A -> B : REQUEST
 * B -> A : INFORM
 *
 * while periodically reading messages.
 *
 * This produces:
 *
 * - repeated wrap-around
 * - repeated expansion
 * - repeated shrinking of size
 * - independent queues
 * ******************************************************************/

static void test_mixed_stress(void)
{
    printf("\n========================================\n");
    printf("TEST 6: Mixed stress test\n");
    printf("========================================\n");

    Agent A = {0};
    Agent B = {0};

    MESSAGE_TYPE A_types[] = {
        request,
        inform
    };

    MESSAGE_TYPE B_types[] = {
        request,
        query,
        agree,
        refuse,
        inform
    };

    init_inbox(&A, A_types, 2);
    init_inbox(&B, B_types, 5);

    const size_t ITERATIONS = 100000;

    size_t request_id = 0;
    size_t inform_id = 0;

    for (size_t i = 0; i < ITERATIONS; i++) {

        /*
         * A -> B REQUEST
         */

        message msg1 = make_message(
            &A,
            &B,
            request,
            REQUEST,
            request_id++
        );

        send_message(&msg1);


        /*
         * B -> A INFORM
         */

        message msg2 = make_message(
            &B,
            &A,
            inform,
            REQUEST,
            inform_id++
        );

        send_message(&msg2);


        /*
         * Periodically consume B REQUEST.
         */

        if (i % 3 == 0) {

            message *received =
                read_message_FIFO(&B, request);

            if (received != NULL) {

                destroy_message_payload(received);
            }
        }


        /*
         * Periodically consume A INFORM.
         */

        if (i % 5 == 0) {

            message *received =
                read_message_FIFO(&A, inform);

            if (received != NULL) {

                destroy_message_payload(received);
            }
        }
    }

    /*
     * Drain remaining B REQUEST messages.
     */

    message *msg;

    while ((msg = read_message_FIFO(&B, request)) != NULL) {
        destroy_message_payload(msg);
    }

    /*
     * Drain remaining A INFORM messages.
     */

    while ((msg = read_message_FIFO(&A, inform)) != NULL) {
        destroy_message_payload(msg);
    }

    assert(A.informs.size == 0);
    assert(B.requests.size == 0);

    printf("PASS\n");

    destroy_inbox(&A, A_types, 2);
    destroy_inbox(&B, B_types, 5);
}


/* ******************************************************************
 * MAIN
 * ******************************************************************/

int main(void)
{
    printf("\n");
    printf("========================================\n");
    printf(" FIPA INBOX STRESS TEST\n");
    printf("========================================\n");

    test_single_inbox_expansion();

    test_fifo_wraparound();

    test_all_inboxes();

    test_multi_agent_communication();

    test_empty_inbox();

    test_mixed_stress();

    printf("\n");
    printf("========================================\n");
    printf(" ALL TESTS PASSED\n");
    printf("========================================\n");

    return EXIT_SUCCESS;
}