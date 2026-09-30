#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

#include "math/math_utils.h"
#include "config/config.h"
#include "io/csv_parser.h"
#include "io/json_parser.h"
#include "io/txt_parser.h"
#include "engine/simulation.h"
#include "engine/monte_carlo.h"





int main(void)
{
    




    //REad and see if MASTER_SEED IS SET.

    char *MASTER_SEED = getenv("MASTER_SEED");

    if (MASTER_SEED == NULL){
        perror("Error: MASTER_SEED ENV not declared in binary scope's execution\n");
        exit(-1);
    }

    u64 master_seed = strtoul(MASTER_SEED, NULL, 10);


    //construct the inputs as parsed by the data.

    //distribution data as an input_data_matrix
    const input_data_matrix *const stops_data_distributions =
    load_and_map_route_data_from_csv(CSV_DISTRIBUTION_BOARDS_A,
                                    CSV_DISTRIBUTION_BOARDS_B,
                                    CSV_DISTRIBUTION_DROPOFFS_A,
                                    CSV_DISTRIBUTION_DROPOFFS_B);

    //stop list from the ttx as a stops_list
    const stops_list *const stops_list_data = load_stops(STOPS_TXT);

    //input buses as a json
    const input_data_buses *const input_buses = load_input_from_json(
        BUSES_JSON);

    //times between stops as a input_times_matrix.
    const input_times_matrix *const stops_times_distributions = 
    load_and_map_route_times_from_csv(CSV_TIMES_A, CSV_TIMES_B);

    const global_inmutable_params global_input_params =
    (global_inmutable_params){
        .stops_data_distributions = stops_data_distributions,
        .stops_list_data = stops_list_data,
        .input_data_buses = input_buses,
        .stops_times_distributions = stops_times_distributions
    };

     if (config_ensure_outdir(OUT_DIR) < 0){
        perror("Error creating output results csv file\n");
        exit(-1);
    }

    run_monte_carlo_replicas(&global_input_params, master_seed);

    free((void *)stops_data_distributions);

    free(global_input_params.stops_list_data->stopcodes_toA);
    free(global_input_params.stops_list_data->stopcodes_toB);

    free((void *)stops_list_data);

    for (size_t i = 0; i < input_buses->number_of_buses; i++){
        free(input_buses->input_buses[i].headway_bus_times);
    }
    free(input_buses->input_buses);
    free((void *)input_buses);
    free((void *)stops_times_distributions);
    return 0;
}