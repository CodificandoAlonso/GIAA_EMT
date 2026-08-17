#include<stdlib.h>
#include<stdio.h>
#include<stdint.h>
#include "utils/utils.h"
#include "csv_parser.h"
#include<stdbool.h>





input_data_stop_row clean_inline_row (char *inline_data){
    input_data_stop_row new_row = {0};

    int param_counter = 0;

    bool writable = false;

    size_t copied_bytes = 0;

    size_t starting_point = 0;
    for (size_t i=0; i< 256; i++){
        
        if (inline_data[i] == ',' || inline_data[i] == '\n'){

            //If enters here, the number of copied bytes represent the number of bytes needed to parse,
            //starting from starting_point.

            //char *data_to_save = extract_data_range(inline_data, starting_point, copied_bytes);

            switch(param_counter){
                case 0:

                    u16 stopcode = 0;

                    for (size_t j = starting_point; j < starting_point + copied_bytes; j ++){
                        stopcode = stopcode * 10 + (inline_data[j] - '0');
                    }
                    new_row.stop_code = stopcode;
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;

                case 1:
                    
                    byte timeslot = 0;
                    
                    for (size_t j = starting_point; j < starting_point + copied_bytes; j ++){
                        timeslot = timeslot * 10 + (inline_data[j] - '0');
                    }
                    new_row.time_slot = timeslot;
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                case 2:

                    //Compare the string with the character Board or DropOff.
                    //Easy, just check copied_bytes, if 5 == Board, else DropOff

                    if (copied_bytes == 5){
                        new_row.type = BOARD;
                    }else{new_row.type = DROPOFF;}
                    
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                
                case 3:


                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                case 4:
                    
                    starting_point = i + 1;
                    copied_bytes = 0;
                    param_counter ++;
                    break;
                case 5:

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



const input_data_matrix *load_and_map_route_data_from_csv(char *route_direction_a, char *route_direction_b){

    FILE* fd_toA = fopen(route_direction_a, "r");

    u16 counter = 0;
    char *inline_data = malloc(sizeof(char)*256);
    while (fgets(inline_data, sizeof(char)*256, fd_toA)){
        if (counter == 0){ counter++;}
        else{
            input_data_stop_row new_row = clean_inline_row(inline_data);
            counter ++;
        }
    }
    free(inline_data);
    fclose(fd_toA);

}


const input_data_stop *get_stop_data(input_data_matrix *matrix, u16 stopcode){

}


const input_data_stop_row *get_distribution_per_timeslot(input_data_stop *stop_info, u16 stopcode, byte timeslot, data_type type){

}



const size_t stop_mapper_toA(u16 stopcode, input_data_matrix *matrix){

    for (size_t index = 0; index < MAX_DIRECTION_LEN; index ++){
        if (matrix->route_stops_a[index].stop_distributions[0].stop_code == stopcode){
            return index;
        }
    }
    return -1;

}

const size_t stop_mapper_toB(u16 stopcode, input_data_matrix *matrix){
    for (size_t index = 0; index < MAX_DIRECTION_LEN; index ++){
        if (matrix->route_stops_b[index].stop_distributions[0].stop_code == stopcode){
            return index;
        }
    }
    return -1;
    
}