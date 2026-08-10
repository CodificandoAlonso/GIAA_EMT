#include<stdlib.h>
#include<stdio.h>
#include<stdint.h>
#include "utils/utils.h"
#include "csv_parser.h"





const input_data_matrix *load_and_map_route_data_from_csv(char *route_direction_a, char *route_direction_b){

    FILE* fd_toA = fopen(route_direction_a, "r");


    char *data;

    while (fread(data,sizeof(char),1, fd_toA) >= 0){
        if (data == '\0'){
            break;
        }


    }

}


const input_data_stop *get_stop_data(input_data_matrix *matrix, u16 stopcode){

}


const input_data_stop_row *get_distribution_per_timeslot(input_data_stop *stop_info, u16 stopcode, byte timeslot, data_type type){

}



const size_t stop_mapper_toA(u16 stopcode, input_data_matrix *matrix){

    for (size_t index = 0; index < MAX_DIRECTION_LEN; index ++){
        if (matrix->route_stops_a[index]->stop_distributions[0].stop_code == stopcode){
            return index;
        }
    }
    return -1;

}

const size_t stop_mapper_toB(u16 stopcode, input_data_matrix *matrix){
    for (size_t index = 0; index < MAX_DIRECTION_LEN; index ++){
        if (matrix->route_stops_b[index]->stop_distributions[0].stop_code == stopcode){
            return index;
        }
    }
    return -1;
    
}