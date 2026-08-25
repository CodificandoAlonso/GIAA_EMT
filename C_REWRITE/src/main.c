#include <stdio.h>
#include <stdlib.h>

#include "io/json_parser.h"
#include "agents/bus/bus.h"
#include "utils/utils.h"


static const char *direction_to_string(direction dir)
{
    switch (dir) {
        case CIBELES:
            return "CIBELES";

        case LA_PESETA:
            return "LA_PESETA";

        default:
            return "UNKNOWN";
    }
}


int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input.json>\n", argv[0]);
        return EXIT_FAILURE;
    }

    /*
     * Parse JSON.
     */
    const input_data_buses *input = load_input_from_json(argv[1]);

    printf("========================================\n");
    printf("Creating bus agents: %zu\n", input->number_of_buses);
    printf("========================================\n\n");


    /*
     * Create one bus agent per parsed bus.
     */
    bus **buses = calloc(input->number_of_buses, sizeof(*buses));

    if (!buses) {
        perror("calloc buses");
        return EXIT_FAILURE;
    }


    for (size_t i = 0; i < input->number_of_buses; i++) {

        const data_bus *data = &input->input_buses[i];

        /*
         * Create the bus agent.
         *
         * The parser already owns headway_bus_times.
         * create_bus() stores that pointer directly in the bus.
         */
        buses[i] = create_bus(
            data->bus_code,
            0,                              // Initial stop for now
            data->initial_direction,
            data->headway_bus_times,
            data->headways_length
        );

        if (!buses[i]) {
            fprintf(stderr,
                    "ERROR: Could not create bus %u\n",
                    data->bus_code);

            /*
             * Cleanup already-created buses.
             */
            for (size_t j = 0; j < i; j++) {
                buses[j]->agent.cleanup(buses[j]);
                free(buses[j]);
            }

            free(buses);
            return EXIT_FAILURE;
        }


        /*
         * Check personalized fields.
         */
        printf("Bus %u\n", buses[i]->bus_code);

        printf("  Expected bus code:       %u\n",
               data->bus_code);

        printf("  Actual bus code:         %u\n",
               buses[i]->bus_code);

        printf("  Direction:               %s\n",
               direction_to_string(buses[i]->bus_direction));

        printf("  Headways scheduled:      %u\n",
               buses[i]->travels_scheduled);

        printf("  Headways pointer:        %p\n",
               (void *)buses[i]->headway_times);

        printf("  Max occupancy:           %u\n",
               buses[i]->max_occupancy);

        printf("  State:                   %d\n",
               buses[i]->state);

        printf("  Inbox count:             %zu\n",
               buses[i]->agent.inboxes_numbers);

        printf("  Results index:            %zu\n",
               buses[i]->results_idx);


        /*
         * Verify the important personalization.
         */
        int ok = 1;

        if (buses[i]->bus_code != data->bus_code)
            ok = 0;

        if (buses[i]->bus_direction != data->initial_direction)
            ok = 0;

        if (buses[i]->headway_times != data->headway_bus_times)
            ok = 0;

        if (buses[i]->travels_scheduled != data->headways_length)
            ok = 0;

        if (buses[i]->max_occupancy != MAX_OCCUPANCY)
            ok = 0;

        if (buses[i]->state != waiting_headway)
            ok = 0;

        if (buses[i]->agent.inboxes_numbers != BUS_INBOXES_NUMBER)
            ok = 0;

        if (buses[i]->agent.message_types != BUS_MESSAGE_TYPES)
            ok = 0;

        if (buses[i]->agent.startup_agent != startup_bus_agent)
            ok = 0;

        if (buses[i]->agent.update_in_sim != update_bus_in_sim)
            ok = 0;

        if (buses[i]->agent.cleanup != cleanup_bus)
            ok = 0;


        if (ok)
            printf("  RESULT:                 OK\n");
        else
            printf("  RESULT:                 FAILED\n");


        /*
         * Print the actual headways as an additional sanity check.
         */
        printf("  Headways:\n");

        for (size_t j = 0; j < buses[i]->travels_scheduled; j++) {

            printf("    [%zu] %s - %u seconds\n",
                   j,
                   direction_to_string(
                       buses[i]->headway_times[j].bus_direction
                   ),
                   buses[i]->headway_times[j].departure_time);
        }

        printf("\n");
    }


    /*
     * Cleanup.
     *
     * IMPORTANT:
     *
     * The bus agents now own headway_times because create_bus()
     * stores the parser's pointer directly.
     *
     * Therefore:
     *
     *     DO NOT free input->input_buses[i].headway_bus_times
     *
     * separately.
     *
     * We free it through each bus instead.
     */
    for (size_t i = 0; i < input->number_of_buses; i++) {

        free(buses[i]->headway_times);

        /*
         * cleanup_bus() is currently empty, but call it through
         * the generic Agent interface to test the inheritance setup.
         */
        buses[i]->agent.cleanup(buses[i]);

        free(buses[i]);
    }

    free(buses);

    /*
     * The parser allocated these structures.
     *
     * input->input_buses itself can now be freed because the
     * headway pointers have already been freed above.
     */
    free(input->input_buses);
    free((void *)input);

    return EXIT_SUCCESS;
}