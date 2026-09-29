#pragma once

/* All values come from -D flags emitted by the Makefile (ENV_CFLAGS).
 * Building outside the Makefile is a hard error by design. */

#if !defined(CSV_DISTRIBUTION_BOARDS_A) || !defined(CSV_DISTRIBUTION_BOARDS_B) || \
    !defined(CSV_DISTRIBUTION_DROPOFFS_A) || !defined(CSV_DISTRIBUTION_DROPOFFS_B) || \
    !defined(CSV_TIMES_A)        || !defined(CSV_TIMES_B)        || \
    !defined(BUSES_JSON)         || !defined(STOPS_TXT)          || \
    !defined(OUTPUT_RESULTS)     || !defined(OUTPUT_PASSENGERS)  || \
    !defined(OUTPUT_ANOMALIES)   || !defined(OUT_DIR)
#  error "Path macros missing — build with the Makefile (make / make debug / make release)"
#endif

#if !defined(TIME_PER_PASSENGER) || !defined(STEP) || \
    !defined(N_THREADS) || !defined(N_WORKERS) || !defined(N_SIMS)
#  error "Numeric config macros missing — build with the Makefile"
#endif

#include <stddef.h>

/* ---- paths ---- */
#define PATH_DISTRIBUTION_BOARDS_A  CSV_DISTRIBUTION_BOARDS_A
#define PATH_DISTRIBUTION_BOARDS_B CSV_DISTRIBUTION_BOARDS_B
#define PATH_DISTRIBUTION_DROPOFFS_A  CSV_DISTRIBUTION_DROPOFFS_A
#define PATH_DISTRIBUTION_DROPOFFS_B CSV_DISTRIBUTION_DROPOFFS_B
#define PATH_TIMES_A         CSV_TIMES_A
#define PATH_TIMES_B         CSV_TIMES_B
#define PATH_BUSES_JSON      BUSES_JSON
#define PATH_STOPS_TXT       STOPS_TXT
#define PATH_RESULTS         OUTPUT_RESULTS
#define PATH_PASSENGERS      OUTPUT_PASSENGERS
#define PATH_ANOMALIES       OUTPUT_ANOMALIES
#define PATH_OUT_DIR         OUT_DIR

/* ---- numeric config ---- */
enum {
    CFG_TIME_PER_PASSENGER = TIME_PER_PASSENGER,
    CFG_STEP               = STEP,
    CFG_N_THREADS          = N_THREADS,
    CFG_N_WORKERS          = N_WORKERS,
    CFG_N_SIMS             = N_SIMS,
    CGF_MAX_OCCUPANCY      = MAX_OCCUPANCY
};

/* size_t forms, to keep -Wconversion quiet at call sites */
#define CFG_N_THREADS_SZ ((size_t)CFG_N_THREADS)
#define CFG_N_SIMS_SZ    ((size_t)CFG_N_SIMS)

/* Fails at compile time if someone sets a nonsense value in .env */
_Static_assert(CFG_N_THREADS > 0,  "N_THREADS must be > 0");
_Static_assert(CFG_N_WORKERS == 1, "writer design assumes exactly one writer thread");
_Static_assert(CFG_N_SIMS    > 0,  "N_SIMS must be > 0");
_Static_assert(CFG_STEP      > 0,  "STEP must be > 0");


int mkdir_p(const char *path);

/* Creates OUT_DIR if absent; returns 0 on success, -1 on failure. */
int config_ensure_outdir(const char *path);