#pragma once
#include <stdatomic.h>
#include <stdalign.h>
#include <stdio.h>
#include <pthread.h>
#include "io/csv_parser.h"
#include "utils/utils.h"


typedef void (*write_fn_t)(FILE *out, const void *rows, size_t n);

typedef struct {
    _Atomic int  ready;
    void        *rows;
    size_t       n;
} cell_t;

typedef struct {
    cell_t     *cells;
    size_t      cap;
    FILE       *out;
    char       *iobuf;        /* setvbuf block — must outlive the FILE* */
    write_fn_t  write_fn;
    alignas(64) _Atomic size_t head;
} outq_t;

typedef struct {
    outq_t results, passengers, anomalies;

    pthread_t        writer_tid;
    pthread_mutex_t  wmutex;
    pthread_cond_t   wcond;

    alignas(64) _Atomic size_t published;
    alignas(64) _Atomic int    done;
} worker_thread_params;





static void outq_push(worker_thread_params *w, outq_t *q, void *rows, size_t n);


static int outq_init(outq_t *q, size_t cap, const char *path,
                     write_fn_t fn, const char *header);

static void outq_destroy(outq_t *q);


static size_t drain(outq_t *q, size_t *tail);


static void writer_loop(worker_thread_params *w);


static void *writer_thread_main(void *arg);

int  init_worker_workspace(worker_thread_params *w,
                           size_t cap_results,
                           size_t cap_passengers,
                           size_t cap_anomalies);
void destroy_worker_workspace(worker_thread_params *w);



/* typed wrappers so callers can't pass the wrong queue */
void push_results(worker_thread_params *w, results_row *r, size_t n);

void push_passengers(worker_thread_params *w, passengers_row *r, size_t n);

void push_anomalies(worker_thread_params *w, anomaly_row *r, size_t n);