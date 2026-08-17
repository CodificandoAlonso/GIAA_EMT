#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#include "io/csv_parser.h"


#define ITERATIONS 100000000ULL


/*
 * Prevent the compiler from optimizing the benchmark result away.
 */
static volatile uintptr_t benchmark_sink;


/*
 * Return elapsed nanoseconds between two timestamps.
 */
static uint64_t elapsed_ns(
    const struct timespec *start,
    const struct timespec *end
)
{
    return (uint64_t)(end->tv_sec - start->tv_sec) * 1000000000ULL
         + (uint64_t)(end->tv_nsec - start->tv_nsec);
}


static void benchmark_stop_mapper(void)
{
    const u16 stopcodes[] = {
        4090, 2539, 3903, 82,
        5360, 5939, 4032, 3991,
        3995, 4188, 2535, 562,
        1929, 2646, 5727
    };

    const size_t n = sizeof(stopcodes) / sizeof(stopcodes[0]);

    uintptr_t accumulator = 0;

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (uint64_t i = 0; i < ITERATIONS; ++i) {

        u16 stopcode = stopcodes[i % n];

        accumulator += stop_mapper_toA(stopcode);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    benchmark_sink = accumulator;

    uint64_t elapsed = elapsed_ns(&start, &end);

    printf(
        "stop_mapper_toA:\n"
        "  total: %.3f ms\n"
        "  per lookup: %.3f ns\n"
        "  sink: %lu\n\n",
        (double)elapsed / 1e6,
        (double)elapsed / (double)ITERATIONS,
        (unsigned long)benchmark_sink
    );
}


static void benchmark_distribution_lookup(
    const input_data_matrix *matrix
)
{
    const u16 stopcodes[] = {
        4090, 2539, 3903, 82,
        5360, 5939, 4032, 3991,
        3995, 4188, 2535, 562,
        1929, 2646, 5727
    };

    const size_t n = sizeof(stopcodes) / sizeof(stopcodes[0]);

    uintptr_t accumulator = 0;

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (uint64_t i = 0; i < ITERATIONS; ++i) {

        u16 stopcode = stopcodes[i % n];

        byte timeslot = (byte)(5 + (i % N_TIMESLOTS));

        data_type type = (data_type)(i & 1U);

        const input_data_stop_row *row =
            get_distribution_per_timeslot_toA(
                matrix,
                stopcode,
                timeslot,
                type
            );

        /*
         * Read something from the result so the compiler cannot
         * simply eliminate the lookup.
         */
        accumulator += row->stop_code;
        accumulator += row->time_slot;
        accumulator += (uintptr_t)row->type;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    benchmark_sink = accumulator;

    uint64_t elapsed = elapsed_ns(&start, &end);

    printf(
        "get_distribution_per_timeslot_toA:\n"
        "  total: %.3f ms\n"
        "  per lookup: %.3f ns\n"
        "  sink: %lu\n\n",
        (double)elapsed / 1e6,
        (double)elapsed / (double)ITERATIONS,
        (unsigned long)benchmark_sink
    );
}


static void benchmark_stop_lookup(
    const input_data_matrix *matrix
)
{
    const u16 stopcodes[] = {
        4090, 2539, 3903, 82,
        5360, 5939, 4032, 3991,
        3995, 4188, 2535, 562,
        1929, 2646, 5727
    };

    const size_t n = sizeof(stopcodes) / sizeof(stopcodes[0]);

    uintptr_t accumulator = 0;

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (uint64_t i = 0; i < ITERATIONS; ++i) {

        u16 stopcode = stopcodes[i % n];

        const input_data_stop *stop =
            get_stop_data_toA(matrix, stopcode);

        accumulator += stop->stop_distributions[0].stop_code;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    benchmark_sink = accumulator;

    uint64_t elapsed = elapsed_ns(&start, &end);

    printf(
        "get_stop_data_toA:\n"
        "  total: %.3f ms\n"
        "  per lookup: %.3f ns\n"
        "  sink: %lu\n\n",
        (double)elapsed / 1e6,
        (double)elapsed / (double)ITERATIONS,
        (unsigned long)benchmark_sink
    );
}


static void benchmark_direct_pointer(
    const input_data_stop *stop
)
{
    uintptr_t accumulator = 0;

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (uint64_t i = 0; i < ITERATIONS; ++i) {

        byte timeslot = (byte)(5 + (i % N_TIMESLOTS));

        data_type type = (data_type)(i & 1U);

        const input_data_stop_row *row =
            &stop->stop_distributions[
                2 * (timeslot - 5) + type
            ];

        accumulator += row->stop_code;
        accumulator += row->time_slot;
        accumulator += (uintptr_t)row->type;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    benchmark_sink = accumulator;

    uint64_t elapsed = elapsed_ns(&start, &end);

    printf(
        "DIRECT POINTER:\n"
        "  total: %.3f ms\n"
        "  per lookup: %.3f ns\n"
        "  sink: %lu\n\n",
        (double)elapsed / 1e6,
        (double)elapsed / (double)ITERATIONS,
        (unsigned long)benchmark_sink
    );
}


int main(void)
{
    printf("========================================\n");
    printf(" C DATA ACCESS MICROBENCHMARK\n");
    printf(" Iterations: %llu\n", ITERATIONS);
    printf("========================================\n\n");

    /*
     * We don't need the CSV for the structural benchmark.
     * Allocate and initialize the matrix so that the memory exists
     * exactly as it will during the simulation.
     */
    input_data_matrix *matrix =
        malloc(sizeof(input_data_matrix));

    if (matrix == NULL) {
        perror("malloc");
        return EXIT_FAILURE;
    }

    /*
     * Initialize the matrix.
     */
    *matrix = (input_data_matrix){0};

    /*
     * Put identifiable data in every slot.
     */
    for (size_t stop = 0; stop < MAX_DIRECTION_LEN; ++stop) {

        for (size_t slot = 0; slot < N_STOP_DATA; ++slot) {

            matrix->route_stops_a[stop]
                .stop_distributions[slot]
                .stop_code = (u16)stop;

            matrix->route_stops_a[stop]
                .stop_distributions[slot]
                .time_slot = (byte)(slot / 2);

            matrix->route_stops_a[stop]
                .stop_distributions[slot]
                .type = (data_type)(slot & 1U);
        }
    }

    /*
     * The actual stop used for the direct-pointer benchmark.
     *
     * Stopcode 4090 maps to index 0.
     */
    const input_data_stop *stop =
        &matrix->route_stops_a[stop_mapper_toA(4090)];

    /*
     * Warm-up.
     *
     * This makes sure the relevant code/data has been executed
     * before measuring.
     */
    benchmark_sink = 0;

    for (uint64_t i = 0; i < 1000000ULL; ++i) {
        benchmark_sink +=
            stop_mapper_toA(4090);
    }

    printf("Running benchmarks...\n\n");

    benchmark_stop_mapper();

    benchmark_stop_lookup(matrix);

    benchmark_distribution_lookup(matrix);

    benchmark_direct_pointer(stop);

    free(matrix);

    return EXIT_SUCCESS;
}