#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>

#include "math/distributions/generic/generic_distro.h"
#include "math/distributions/normal.h"
#include "math/distributions/geometrical.h"
#include "math/distributions/negbin.h"
#include "math/random/RNG.h"

#define NUM_THREADS 3
#define SAMPLES_PER_THREAD 1000

#define OUTPUT_DIRECTORY "data"


typedef struct {
    int thread_id;
    RNG *rng;
    distribution *dist;
} ThreadData;


void *generate_samples(void *arg)
{
    ThreadData *data = (ThreadData *)arg;

    char filename[256];

    snprintf(
        filename,
        sizeof(filename),
        OUTPUT_DIRECTORY "/samples_thread_%d.txt",
        data->thread_id
    );

    FILE *file = fopen(filename, "w");

    if (file == NULL) {
        perror("Error opening output file");
        return NULL;
    }

    for (int i = 0; i < SAMPLES_PER_THREAD; i++) {

        double value = data->dist->random(
            data->dist,
            data->rng
        );

        fprintf(file, "%.10f\n", value);
    }

    fclose(file);
    
    return NULL;
}


int main(void)
{
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];

    /*
     * Normal distribution:
     *
     * X ~ N(mu, sigma^2)
     *
     * mu    = 25
     * sigma = 10
     */
    distribution negbin = {
        .value1 = 3.3691608217435576,
        .value2 = 0.4576085966669701,
        .random = sample_negbin
    };


    RNG *rngs[NUM_THREADS];


    /*
     * Create one independent RNG for each thread.
     */
    for (int i = 0; i < NUM_THREADS; i++) {

        uint64_t seed = 12345ULL + (uint64_t)i;
        uint64_t stream = (uint64_t)i;

        rngs[i] = RNG_init(seed, stream);

        if (rngs[i] == NULL) {
            fprintf(
                stderr,
                "Failed to initialize RNG %d\n",
                i
            );

            return EXIT_FAILURE;
        }


        thread_data[i].thread_id = i;
        thread_data[i].rng = rngs[i];
        thread_data[i].dist = &negbin;


        int result = pthread_create(
            &threads[i],
            NULL,
            generate_samples,
            &thread_data[i]
        );

        if (result != 0) {

            fprintf(
                stderr,
                "Failed to create thread %d\n",
                i
            );

            for (int j = 0; j <= i; j++) {
                RNG_destroy(rngs[j]);
            }

            return EXIT_FAILURE;
        }
    }


    /*
     * Wait for all threads to finish.
     */
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }


    /*
     * Free the RNGs.
     */
    for (int i = 0; i < NUM_THREADS; i++) {
        RNG_destroy(rngs[i]);
    }


    printf(
        "Generated %d samples per thread (%d total).\n",
        SAMPLES_PER_THREAD,
        NUM_THREADS * SAMPLES_PER_THREAD
    );

    return EXIT_SUCCESS;
}