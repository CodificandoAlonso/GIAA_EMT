#include<stdlib.h>
#include<stdio.h>
#include<stdint.h>
#include "utils/utils.h"
#include "math/distributions/geometrical.h"
#include "math/distributions/negbin.h"
#include "math/distributions/normal.h"
#include "csv_parser.h"
#include<stdbool.h>




input_data_stop_row clean_inline_row (char *inline_data){
    input_data_stop_row new_row = {0};

    int param_counter = 0;

    size_t copied_bytes = 0;

    size_t starting_point = 0;


    //auxiliar for the params of the struct
    u16 stopcode = 0;
    byte timeslot = 0;
    double param1, param2 = 0.0;
    for (size_t i=0; i< 256; i++){
        
        if (inline_data[i] == ',' || inline_data[i] == '\n'){

            //If enters here, the number of copied bytes represent the number of bytes needed to parse,
            //starting from starting_point.

            switch(param_counter){
                case 0: //STOPCODE

                
                    for (size_t j = starting_point; j < starting_point + copied_bytes; j ++){
                        stopcode = stopcode * 10 + (inline_data[j] - '0');
                    }
                    new_row.stop_code = stopcode;
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;

                case 1: //TIMESLOT
                    
                    
                    for (size_t j = starting_point; j < starting_point + copied_bytes; j ++){
                        timeslot = timeslot * 10 + (inline_data[j] - '0');
                    }
                    new_row.time_slot = timeslot;
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                case 2: //BOARD / DROPOFF

                    //Compare the string with the character Board or DropOff.
                    //Easy, just check copied_bytes, if 5 == Board, else DropOff

                    if (copied_bytes == 5){
                        new_row.type = BOARD;
                    }else{new_row.type = DROPOFF;}

                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                
                case 3: // DISTRIBUTION TYPE
                    
                    //Same scenario as before, depending on length we have one type or another
                    if (copied_bytes == 6){ //NORMAL
                        new_row.distro.kind = DIST_NORMAL;
                        new_row.distro.random = sample_normal;
                    }else if (copied_bytes == 11){ //GEOMETRICAL
                        new_row.distro.kind = DIST_GEOMETRIC;
                        new_row.distro.random = sample_geometrical;
                    } else{//NEGBIN
                        new_row.distro.kind = DIST_NEGBIN;
                        new_row.distro.random = sample_negbin;
                    }
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                case 4: //PARAM1
                    //First param scenario
                    param1 = strtod(inline_data + starting_point, NULL);
                    new_row.distro.value1 = param1;
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                case 5: //PARAM2
                    //Second param scenario
                    param2 = strtod(inline_data + starting_point, NULL);
                    new_row.distro.value2 = param2;
                return new_row;
            } 
        }
        else{
            copied_bytes ++;
        }
    }
    perror("Error parsing line, exiting\n");
    exit(-4);
}



const input_data_matrix *load_and_map_route_data_from_csv(const char *route_direction_a, const  char *route_direction_b){


    u16 counter = 0;

    input_data_matrix *matrix = malloc(sizeof(input_data_matrix));

     if (matrix == NULL) {
        return NULL;
    }

    *matrix = (input_data_matrix){0};

    input_data_stop_row new_row;

    char *inline_data = malloc(sizeof(char)*256);

    if (inline_data == NULL) {
        free(matrix);
        return NULL;
    }

    FILE* fd_toA = fopen(route_direction_a, "r");

    if (fd_toA == NULL) {
        free(inline_data);
        free(matrix);
        return NULL;
    }
    while (fgets(inline_data, sizeof(char)*256, fd_toA)){
        if (counter == 0){ counter++;}
        else{
            new_row = clean_inline_row(inline_data);
            size_t index_stop = stop_mapper_toA(new_row.stop_code);


        if (index_stop == SIZE_MAX) {
            return NULL;
        }
            matrix->route_stops_a[index_stop].stop_distributions[2* (new_row.time_slot - 5) + new_row.type] = new_row;
        }
    }
    fclose(fd_toA);

    FILE* fd_toB = fopen(route_direction_b, "r");

    if (fd_toB == NULL) {
        free(inline_data);
        free(matrix);
        return NULL;
    }

    counter = 0;

    while (fgets(inline_data, sizeof(char)*256, fd_toB)){
        if (counter == 0){ counter++;}
        else{
            new_row = clean_inline_row(inline_data);
            size_t index_stop = stop_mapper_toB(new_row.stop_code);

            if (index_stop == SIZE_MAX) {
            return NULL;
            }
            matrix->route_stops_b[index_stop].stop_distributions[2* (new_row.time_slot - 5) + new_row.type] = new_row;
        }
    }

    free(inline_data);
    fclose(fd_toB);

    return matrix;
}
