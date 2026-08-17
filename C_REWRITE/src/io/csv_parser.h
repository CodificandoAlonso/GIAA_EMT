#pragma once
#include<stdint.h>
#include "math/distributions/generic/generic_distro.h"
#define N_TIMESLOTS 19
#define MAX_DIRECTION_LEN 16
#include "utils/utils.h"




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
 * @brief enum type for recognizing boards and dropoffs distr types
 */
 typedef enum {
    BOARD = 0,
    DROPOFF = 1
 } data_type;


/**
 * @brief struct that represents a row of the input csv for each stop distribution type for boarding and droppoff
 */
typedef struct input_data_stop_row{
    u16 stop_code;
    byte time_slot;
    data_type type;
    distribution distro;
} input_data_stop_row;


/**
 * @brief struct that represents a group of rows representing the stop
 */
typedef struct input_data_stop{
    input_data_stop_row stop_distributions[38];
} input_data_stop;

/**
 * @brief struct that represents a group of stops for each direction representing the route
 */
typedef struct input_data_matrix{
    input_data_stop route_stops_a[MAX_DIRECTION_LEN];
    input_data_stop route_stops_b[MAX_DIRECTION_LEN];
} input_data_matrix;

/**
 * @brief Auxiliar function that receives a static 256b char pointer and resolves the content giving back a struct
 * of type input_data_stop_row
 */
input_data_stop_row clean_inline_row(char *inline_data);



const input_data_matrix *load_and_map_route_data_from_csv(char *route_direction_a, char *route_direction_b);


const input_data_stop *get_stop_data(input_data_matrix *matrix, u16 stopcode);


const input_data_stop_row *get_distribution_per_timeslot(input_data_stop *stop_info, u16 stopcode, byte timeslot, data_type type);



const size_t stop_mapper_toA(u16 stopcode, input_data_matrix *matrix);


const size_t stop_mapper_toB(u16 stopcode, input_data_matrix *matrix);



/*
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************** OUTPUT CSV DECLARATIONS *********************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 ******************************************************************************************************************
 */
