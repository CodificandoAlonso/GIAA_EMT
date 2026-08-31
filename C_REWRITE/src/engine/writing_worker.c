#include "engine/writing_worker.h"


#define IOBUF_SZ (4u << 20)

static void outq_push(worker_thread_params *w, outq_t *q, void *rows, size_t n) {
    size_t pos = atomic_fetch_add_explicit(&q->head, 1, memory_order_relaxed);
    if (pos >= q->cap) {
        fprintf(stderr, "outq overflow: pos=%zu cap=%zu\n", pos, q->cap);
        abort();
    }
    cell_t *c = &q->cells[pos];
    c->rows = rows;
    c->n    = n;
    atomic_store_explicit(&c->ready, 1, memory_order_release);

    atomic_fetch_add_explicit(&w->published, 1, memory_order_release);
    pthread_mutex_lock(&w->wmutex);
    pthread_cond_signal(&w->wcond);
    pthread_mutex_unlock(&w->wmutex);
}


static int outq_init(outq_t *q, size_t cap, const char *path,
                     write_fn_t fn, const char *header) {
    q->cells = calloc(cap, sizeof *q->cells);      /* ready = 0 */
    if (!q->cells) return -1;

    q->out = fopen(path, "w");
    if (!q->out) { free(q->cells); q->cells = NULL; return -1; }

    q->iobuf = malloc(IOBUF_SZ);
    if (q->iobuf) setvbuf(q->out, q->iobuf, _IOFBF, IOBUF_SZ);

    q->cap = cap;
    q->write_fn = fn;
    atomic_init(&q->head, 0);

    if (header) fputs(header, q->out);
    return 0;
}


static void outq_destroy(outq_t *q) {
    if (q->out) {
        if (fclose(q->out) != 0) perror("fclose");   /* flush failure lands here */
        q->out = NULL;
    }
    free(q->iobuf); q->iobuf = NULL;                 /* only after fclose */
    free(q->cells); q->cells = NULL;
}


/* drains one queue as far as it can; returns cells consumed */
static size_t drain(outq_t *q, size_t *tail) {
    size_t did = 0;
    for (;;) {
        if (*tail >= q->cap) break;
        cell_t *c = &q->cells[*tail];
        if (atomic_load_explicit(&c->ready, memory_order_acquire) != 1) break;
        q->write_fn(q->out, c->rows, c->n);
        free(c->rows);
        c->rows = NULL;
        (*tail)++;
        did++;
    }
    return did;
}


void writer_loop(worker_thread_params *w) {
    size_t t_res = 0, t_pas = 0, t_ano = 0;   /* private, non-atomic */
    size_t consumed = 0;

    for (;;) {
        size_t did = drain(&w->results,    &t_res)
                   + drain(&w->passengers, &t_pas)
                   + drain(&w->anomalies,  &t_ano);
        if (did) { consumed += did; continue; }   /* stay hot */

        pthread_mutex_lock(&w->wmutex);
        while (atomic_load_explicit(&w->published, memory_order_acquire) == consumed &&
               !atomic_load_explicit(&w->done, memory_order_acquire))
            pthread_cond_wait(&w->wcond, &w->wmutex);
        int finished = atomic_load_explicit(&w->done, memory_order_acquire) &&
                       atomic_load_explicit(&w->published, memory_order_acquire) == consumed;
        pthread_mutex_unlock(&w->wmutex);

        if (finished) break;
    }

    if (fflush(w->results.out) || fflush(w->passengers.out) || fflush(w->anomalies.out))
        perror("fflush");
}


static void *writer_thread_main(void *arg) {
    writer_loop((worker_thread_params *)arg);
    return NULL;
}


int init_worker_workspace(worker_thread_params *w,
                          size_t cap_results,
                          size_t cap_passengers,
                          size_t cap_anomalies) {
    atomic_init(&w->published, 0);
    atomic_init(&w->done, 0);
    pthread_mutex_init(&w->wmutex, NULL);
    pthread_cond_init(&w->wcond, NULL);

    if (outq_init(&w->results, cap_results, OUTPUT_RESULTS,
                write_results, "sim,bus,trip,stop,dir,slot,dep_slot,boards,residual,dropoffs,occup,travel_time\n") != 0) goto fail0;
    if (outq_init(&w->passengers, cap_passengers, OUTPUT_PASSENGERS,
                write_passengers, "sim,bus,trip,stop,slot,time,generation_times\n") != 0) goto fail1;
    if (outq_init(&w->anomalies, cap_anomalies, OUTPUT_ANOMALIES,
                write_anomalies, "sim,bus,trip,dir,stop,slot,event,time,expected_dep,delay_min\n") != 0) goto fail2;

    if (pthread_create(&w->writer_tid, NULL, writer_thread_main, w) != 0) goto fail3;
    return 0;


    fail3: outq_destroy(&w->anomalies);
    fail2: outq_destroy(&w->passengers);
    fail1: outq_destroy(&w->results);
    fail0: pthread_cond_destroy(&w->wcond);
        pthread_mutex_destroy(&w->wmutex);
        return -1;
}

void destroy_worker_workspace(worker_thread_params *w) {
    pthread_mutex_lock(&w->wmutex);
    atomic_store_explicit(&w->done, 1, memory_order_release);
    pthread_cond_signal(&w->wcond);
    pthread_mutex_unlock(&w->wmutex);

    pthread_join(w->writer_tid, NULL);

    outq_destroy(&w->results);
    outq_destroy(&w->passengers);
    outq_destroy(&w->anomalies);
    pthread_cond_destroy(&w->wcond);
    pthread_mutex_destroy(&w->wmutex);
}


/* typed wrappers so callers can't pass the wrong queue */
void push_results(worker_thread_params *w, results_row *r, size_t n)
    { outq_push(w, &w->results, r, n); }
void push_passengers(worker_thread_params *w, passengers_row *r, size_t n)
    { outq_push(w, &w->passengers, r, n); }
void push_anomalies(worker_thread_params *w, anomaly_row *r, size_t n)
    { outq_push(w, &w->anomalies, r, n); }