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
        
        if (inline_data[i] == ',' || inline_data[i] == '\n'|| inline_data[i] == '\0'){

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
            matrix->route_stops_a[index_stop].stop_distributions[(byte)2* (new_row.time_slot - (byte)5) + (byte)new_row.type] = new_row;
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
            matrix->route_stops_b[index_stop].stop_distributions[(byte)2* (new_row.time_slot - (byte)5) + (byte)new_row.type] = new_row;
        }
    }

    free(inline_data);
    fclose(fd_toB);

    return matrix;
}



input_data_times clean_inline_times_row(char *inline_data){

    /**
     *There is a line per stop. And its ordered in the following schema.
     *First of all, the first field is the stops combination. This will work by, once ending
     *the stop interaction, the stop will fetch the data by
     *filtering per that specific stop, so the stop_code inthe input_data_times_row field
     *should correspond with the first value only
     *Then, is mean std per every timeslot. The value of storage will be, mean will be 
     *the pair and the odd will be std, all of that advancing timeslots
     *when finding a pair
     */


    size_t stop_parsing_counter = 0;

    u16 stop_code = 0;
    
    //if we consider a maximum of 16 bytes for the XXXX-YYYY stop-stop combo.
    for (size_t i = 0; i < 16; i++) {

        if (inline_data[i] == '-') {
            break;
        }

        if (inline_data[i] >= '0' && inline_data[i] <= '9') {
            stop_code = stop_code * 10 +
                        (u16)(inline_data[i] - '0');
        }
    }

    size_t starting_point = stop_parsing_counter + 1;

    size_t copied_bytes = 0;

    byte timeslot = 5;

    //create and allocate input_data_times.

    input_data_times line_input_data_times = {0};


    bool odd = false;

    input_data_times_row aux_row = {0};

    aux_row.distro.kind = DIST_NORMAL;
    aux_row.distro.random = sample_normal;
    aux_row.stop_code = stop_code;
    aux_row.time_slot = timeslot;

    //auxiliar for the params of the struct
    double param1, param2 = 0.0;
    for (size_t i=stop_parsing_counter; i< 1024; i++){

        if (inline_data[i] == ',' || inline_data[i] == '\0' || inline_data[i] == '\n'){
            //need to figure out which param are we. For that, we check the odd t/f. if odd F, we are in mean. If odd T we are in std and save
            //Full distro. Also store it in the line_input_data_times. When odd T reached and line saved, move TS ++.
            if (!odd){
                param1 = strtod(inline_data + starting_point, NULL);
                aux_row.distro.value1 = param1;
                odd = true;
                starting_point = i + 1;
                copied_bytes = 0;
            }else{
                param2 = strtod(inline_data + starting_point, NULL);
                aux_row.distro.value2 = param2;

                //Once done, saved into the line_input_data_times.
                line_input_data_times.times_distributions[timeslot -5] = aux_row;
                aux_row.time_slot = timeslot++;
                odd = false;
                starting_point = i + 1;
                copied_bytes = 0;
            }

            if (inline_data[i] == '\0' || inline_data[i] == '\n'){
                break;
            }
        }else{
            copied_bytes ++;
        }
    }
    return line_input_data_times;
}

const input_times_matrix *load_and_map_route_times_from_csv(
const char *route_direction_a,
const char *route_direction_b){

    u16 counter = 0;

    input_times_matrix *matrix = malloc(sizeof(input_times_matrix));

     if (matrix == NULL) {
        return NULL;
    }

    *matrix = (input_times_matrix){0};

    input_data_times new_row;

    char *inline_data = malloc(sizeof(char)*1024);

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
    while (fgets(inline_data, sizeof(char)*1024, fd_toA)){
        if (counter == 0){ counter++;}
        else{
            new_row = clean_inline_times_row(inline_data);

            size_t index_stop = stop_mapper_toA(new_row.times_distributions[0].stop_code);

            if (index_stop == SIZE_MAX) {
                fprintf(stderr,
                        "Error: stop code %u"
                        " not found in direction A\n",
                        new_row.times_distributions[0].stop_code);
                free(inline_data);
                fclose(fd_toA);
                free(matrix);
                return NULL;
            }

            matrix->route_stops_a[index_stop] = new_row;
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

    while (fgets(inline_data, sizeof(char)*1024, fd_toB)){
        if (counter == 0){ counter++;}
        else{
            new_row = clean_inline_times_row(inline_data);
            size_t index_stop = stop_mapper_toB(new_row.times_distributions[0].stop_code);

            if (index_stop == SIZE_MAX) {
                fprintf(stderr,
                        "Error: stop code %u"
                        " not found in direction B\n",
                        (unsigned int)new_row.times_distributions[0].stop_code);
                free(inline_data);
                fclose(fd_toB);
                free(matrix);
                return NULL;
            }
            matrix->route_stops_b[index_stop] = new_row;
        }
    }

    free(inline_data);
    fclose(fd_toB);

    return matrix;

}
