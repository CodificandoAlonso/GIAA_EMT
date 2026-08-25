#pragma once

#include <stdint.h>

#include "math/distributions/generic/generic_distro.h"
#include "utils/utils.h"


#define N_TIMESLOTS 19
#define MAX_DIRECTION_LEN 16
#define N_STOP_DATA (N_TIMESLOTS * 2)


/*
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 ********************************************  INPUT CSV DECLARATIONS *********************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 */


/**
 * @brief Identifies whether a distribution corresponds to passengers boarding
 *        or dropping off at a stop.
 */
typedef enum {
    BOARD = 0,
    DROPOFF = 1
} data_type;


/**
 * @brief Represents one parsed row of the input CSV.
 *
 * Each row contains the stop, time slot, passenger flow type and the
 * probability distribution associated with that combination.
 */
typedef struct input_data_stop_row {
    u16 stop_code;
    byte time_slot;
    data_type type;
    distribution distro;
} input_data_stop_row;


/**
 * @brief Stores all distribution data associated with a single stop.
 *
 * The 38 entries correspond to 19 time slots with two possible types
 * per time slot: BOARD and DROPOFF.
 */
typedef struct input_data_stop {
    input_data_stop_row stop_distributions[N_STOP_DATA];
} input_data_stop;


/**
 * @brief Stores the distribution data for all stops in both route directions.
 *
 * The stops are stored contiguously for each direction, allowing direct
 * indexed access after mapping a stop code to its corresponding index.
 */
typedef struct input_data_matrix {
    input_data_stop route_stops_a[MAX_DIRECTION_LEN];
    input_data_stop route_stops_b[MAX_DIRECTION_LEN];
} input_data_matrix;


/**
 * @brief Parses a single CSV line into an input_data_stop_row structure.
 *
 * @param inline_data Null-terminated string containing one CSV row.
 *
 * @return Parsed input_data_stop_row containing the stop code, time slot,
 *         passenger flow type and distribution parameters.
 */
input_data_stop_row clean_inline_row(char *inline_data);


/**
 * @brief Loads and maps the input CSV files for both route directions.
 *
 * Each stop code is mapped to a fixed array index, while each time slot
 * and passenger flow type is mapped to a fixed position within the stop.
 *
 * @param route_direction_a Path to the CSV file corresponding to direction A.
 * @param route_direction_b Path to the CSV file corresponding to direction B.
 *
 * @return Pointer to the populated input_data_matrix, or NULL if the data
 *         could not be loaded.
 *
 * @note The returned matrix is allocated dynamically and must be freed
 *       by the caller when it is no longer needed.
 */
const input_data_matrix *
load_and_map_route_data_from_csv(
    const char *route_direction_a,
    const char *route_direction_b
);





/**
 * @brief Maps a direction A stop code to its corresponding array index.
 *
 * @param stopcode Stop code to map.
 *
 * @return Zero-based index of the stop within route_stops_a, or SIZE_MAX
 *         if the stop code is not recognized.
 */
static inline size_t stop_mapper_toA(u16 stopcode)
{
    switch (stopcode) {
        case 4090: return 0;
        case 2539: return 1;
        case 3903: return 2;
        case 82:   return 3;
        case 5360: return 4;
        case 5939: return 5;
        case 4032: return 6;
        case 3991: return 7;
        case 3995: return 8;
        case 4188: return 9;
        case 2535: return 10;
        case 562:  return 11;
        case 1929: return 12;
        case 2646: return 13;
        case 5727: return 14;
        default:   return SIZE_MAX;
    }
}


/**
 * @brief Maps a direction B stop code to its corresponding array index.
 *
 * @param stopcode Stop code to map.
 *
 * @return Zero-based index of the stop within route_stops_b, or SIZE_MAX
 *         if the stop code is not recognized.
 */
static inline size_t stop_mapper_toB(u16 stopcode)
{
    switch (stopcode) {
        case 1167: return 0;
        case 2964: return 1;
        case 4187: return 2;
        case 5938: return 3;
        case 649:  return 4;
        case 3994: return 5;
        case 81:   return 6;
        case 3990: return 7;
        case 2538: return 8;
        case 3929: return 9;
        case 2646: return 13;
        case 5727: return 14;
        default:   return SIZE_MAX;
    }
}






/**
 * @brief Retrieves the distribution data for a stop in route direction A.
 *
 * The stop code is mapped to its static stop index and the time slot/type
 * pair is mapped to the corresponding entry in the stop's data array.
 *
 * @param matrix Pointer to the input data matrix.
 * @param stopcode Stop code to retrieve.
 * @param timeslot Time slot associated with the requested distribution.
 * @param type Passenger flow type, either BOARD or DROPOFF.
 *
 * @return Pointer to the corresponding input_data_stop_row.
 */
static inline const input_data_stop_row *
get_distribution_per_timeslot_toA(
    const input_data_matrix *matrix,
    u16 stopcode,
    byte timeslot,
    data_type type
)
{
    size_t index = stop_mapper_toA(stopcode);


    if (index == SIZE_MAX) {
        return NULL;
    }

    return &matrix->route_stops_a[index]
        .stop_distributions[(byte)2 * (timeslot - (byte)5) + (byte)type];
}


/**
 * @brief Retrieves the distribution data for a stop in route direction B.
 *
 * The stop code is mapped to its static stop index and the time slot/type
 * pair is mapped to the corresponding entry in the stop's data array.
 *
 * @param matrix Pointer to the input data matrix.
 * @param stopcode Stop code to retrieve.
 * @param timeslot Time slot associated with the requested distribution.
 * @param type Passenger flow type, either BOARD or DROPOFF.
 *
 * @return Pointer to the corresponding input_data_stop_row.
 */
static inline const input_data_stop_row *
get_distribution_per_timeslot_toB(
    const input_data_matrix *matrix,
    u16 stopcode,
    byte timeslot,
    data_type type
)
{
    size_t index = stop_mapper_toB(stopcode);

    if (index == SIZE_MAX) {
    return NULL;
    }
    return &matrix->route_stops_b[index]
        .stop_distributions[(byte)2 * (timeslot - (byte)5) + (byte)type];
}


/**
 * @brief Retrieves the data associated with a stop code.
 *
 * @param matrix Pointer to the input data matrix.
 * @param stopcode Stop code to search for.
 *
 * @return Pointer to the corresponding input_data_stop, or NULL if the
 *         stop code is not present.
 */
static inline const input_data_stop *
get_stop_data_toA(
    const input_data_matrix *matrix,
    u16 stopcode
){
    size_t index = stop_mapper_toA(stopcode);

    if (index == SIZE_MAX) {
        return NULL;
    }
     return &matrix->route_stops_a[index];
}


/**
 * @brief Retrieves the data associated with a stop code.
 *
 * @param matrix Pointer to the input data matrix.
 * @param stopcode Stop code to search for.
 *
 * @return Pointer to the corresponding input_data_stop, or NULL if the
 *         stop code is not present.
 */
static inline const input_data_stop *
get_stop_data_toB(
    const input_data_matrix *matrix,
    u16 stopcode
){
    size_t index = stop_mapper_toB(stopcode);


    if (index == SIZE_MAX) {
        return NULL;
    }
     return &matrix->route_stops_b[index];
}





/*
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************** OUTPUT CSV DECLARATIONS *********************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 */



 typedef struct results_row{
    u16 sim_identifier;
    u16 bus_code;
    byte travels_completed;
    u16 stopcode;
    direction direction;
    byte timeslot;
    byte departure_timeslot;
    byte boards;
    byte residual_boards;
    byte dropoffs;
    byte occupation;
    u32 time_travelled;
}results_row;

typedef struct anomaly_row{
    u16 sim_identifier;
    u16 bus_code;
    byte travels_completed;
    direction direction;
    u16 stopcode;
    byte timeslot;
    char *event_type;
    u32 current_time;
    u32 expected_departure;
    byte minutes_of_delay;
}anomaly_row;


typedef struct passengers_row {
    u16 sim_identifier;
    u16 bus_code;
    byte travels_completed;
    u16 stopcode;
    byte timeslot;
    u32 current_time;
    u32 *generation_times;
}passengers_row;
