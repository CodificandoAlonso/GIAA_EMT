#include<stdlib.h>
#include<stdio.h>
#include<string.h>
#include <ctype.h>
#include <inttypes.h>
#include "io/json_parser.h"
#include "utils/utils.h"




const input_data_buses *load_input_from_json(char *filename){
    
    FILE *fd_json = fopen(filename, "r");
    if (!fd_json){
        perror("Error opening json file\n");
        exit(-2);
    }


    char *input_char = malloc(1);

    if (!input_char){
        perror("Error allocating char reader in json read\n");

        fclose(fd_json);
        exit(-3);
    }

    char *input_file = malloc(256);
    if (!input_file){
        perror("Error allocating char *stream in json read\n");
        free(input_char);
        fclose(fd_json);
        exit(-3);
    }


    size_t index = 0;
    size_t max_index = 256;
    //First loop. Remove \n's and make a plain array.   
    while (fread(input_char,1,1, fd_json)){
        if (index == max_index - 1){
            max_index = max_index * 2;
            char *tmp = realloc(input_file, max_index);

            if (!tmp) {
                perror("Error reallocating char *stream in json read\n");
                free(input_file);
                free(input_char);
                fclose(fd_json);
                exit(-3);
            }
            input_file = tmp;
        }
        if (!isspace((unsigned char)*input_char) && *input_char != '"'){
            input_file[index++] = *input_char;
        }
    }
    input_file[index] = '\0';
    fclose(fd_json);
    free(input_char);


    //now, with the stream cleanse completed, parse it into the defined stryuct in the .h file.
    
    byte scope = 0;


    size_t scope1_start = 0, scope1_len = 0;


    size_t scope3_start = 0, scope3_len = 0;

    u16 bus_code = 0;

    //This will be parsed with a scope system. Scope one means reading the bus_code,
    //scope 2 means we are inside the first list of tuples, Each tuple represent
    //the headway. Each headway as a tuple will be a scope 3 characteristic, but the scope
    //2 will maintain the init and close of this scope 3 tuples.
    //For each scope 3 tuples, each one will be parsed as a headway_times struct


    //The return struct now is a temporal struct
    input_data_buses temporal_input_buses = {0};

    size_t max_bus_number = 16;

    //assign memory up to 16 buses. If more, realloc that chunk of data.
    temporal_input_buses.input_buses = malloc(sizeof(data_bus)*max_bus_number);

    if (!temporal_input_buses.input_buses){
        perror("Error assigning memory for input buses temporal aray\n");
        exit(-3);
    }

    headway_times temporal_headway_struct = {0};


    size_t max_headway_length = 16;

    headway_times *temporal_headways_array = malloc(sizeof(headway_times) * max_headway_length);

    if (!temporal_headways_array){
        perror("Error assigning memory for a specific bus temporal array\n");
        exit(-3);
    }

    //for knowing in each scope2->scope1 reduction how many headways got parsed. Also 
    //to realloc in case the max 16 gets topped.
    size_t temporal_headway_length = 0;

    //For the final memory allocation in the specific return struct, or to realloc memory in case 16
    //gets topped
    size_t number_of_buses = 0;

    for (size_t i = 0; i< index; i++){
        if (input_file[i] == '{'){
            scope ++;
            scope1_start = i + 1;
            scope1_len = 0;
            continue;
        }

        switch (scope){

            case 1:{
                //Processing the characters, either "XXXX", with XXXX being the bus id, 
                //the char ':', or the char
                // [ -> that implies an augment of scope, or the one ']' indicating scope reduction.
                //also, it can process a comma ','. here just advances the scope1_start and restarts the
                //scope1_len.
                //Finally, if } detected, it will be the last character so exit the switch case and thats it :)

                //Elevate scope.
                if (input_file[i] == '['){
                    scope ++;
                    break;
                }

                if (input_file[i] == ':'){
                    bus_code = char_to_u16(input_file + scope1_start, scope1_len);
                    break;
                }
                
                if (input_file[i] == ','){
                    //If enters here, means a scope2 ended and it needs to transition to the next bus information.
                    //so its like moving from scope 0 to scope 1. just define start and length.
                    scope1_start = i + 1;
                    scope1_len = 0;
                    break;
                }
                if (input_file[i] == '}'){
                    //If enters here. Json ended. So. All the information is saved in a temporal input
                    //data buses with max_bus_numbers length of .input_buses. So, for the final
                    //path here just breaks. The next iter will be outside the for loop
                    scope --;
                    break;
                }
                scope1_len ++;
                break;
            }


            case 2:{

                //Here there is several options. If '[' detected -> scope moves to 3 (treat the headway
                // tuple). If it encounters a comma, all the tmp headway struct parsed by scope3 gets
                // saved in the scope2_headway_idx index of the scope1_bus_struct corresponding.

                if (input_file[i] == '['){
                    scope ++;
                    scope3_start = i +1;
                    scope3_len = 0;
                    break;
                }

                if (input_file[i] == ','){
                    //if it enters here. The scope3 has happened and saved, so here just move on
                    //and continue :);
                    break;
                }
                if (input_file[i] == ']'){

                    //Here means the headways info correponding the bus_code has ended and its stored
                    //in the temporal_hedways_array. Now, this will realloc that array into a
                    //limited chunk corresponding the factual length and store in the temporal
                    //bus array.

                    if (number_of_buses == max_bus_number){
                        max_bus_number *= 2;
                        data_bus *tmp_input = realloc(temporal_input_buses.input_buses,
                                        sizeof(data_bus)*max_bus_number);
                        
                        if (!tmp_input){
                            perror("Error reallocati ng memory in expansion due to max number of buses reached\n");
                            free(temporal_headways_array);
                            
                            free(input_file);
                            exit(-3);
                        }
                        temporal_input_buses.input_buses = tmp_input;
                    }

                    temporal_input_buses.input_buses[number_of_buses].bus_code = bus_code;
                    temporal_input_buses.input_buses[number_of_buses].initial_direction = 
                                                                temporal_headways_array[0].bus_direction;
                    
                    if (temporal_headways_array[0].bus_direction == CIBELES){
                        temporal_input_buses.input_buses[number_of_buses].stop_code = 2646;
                    }else{
                        temporal_input_buses.input_buses[number_of_buses].stop_code = 5727;
                    }
                                                                
                    headway_times *temporal_new_chunk = realloc(temporal_headways_array,
                                            sizeof(headway_times) *temporal_headway_length);
                    
                    if (!temporal_new_chunk){
                        perror("Error reallocating memoray for bus headway_times saving into its appropiate length\n");
                        exit(-3);
                    }
                    temporal_input_buses.input_buses[number_of_buses].headway_bus_times = temporal_new_chunk;
                    temporal_input_buses.input_buses[number_of_buses].headways_length = temporal_headway_length;
                    temporal_headway_length = 0;
                    max_headway_length = 16;
                    number_of_buses ++;
                    temporal_headways_array = malloc(sizeof(headway_times) * max_headway_length);

                    if (!temporal_headways_array){
                        perror("Error assigning memory for temporal headways array in scope 2 ending\n");
                        free(temporal_input_buses.input_buses);
                        free(input_file);
                        exit(-3);
                    }
                    scope --;
                    break;
                }
            break; 
            }

            case 3:{
                //This scope will process the headway tuple parsing. The key here is, once it
                //finds a comma ',' parse the previous part. this will be the stopcode where
                //the bus starts. Once saved, it will move the scope3_start so the departure time
                //gets parsed right. The departuretime will be parsed once reaching the ']'.
                //after that, a scope reduction will happen.

                if (input_file[i] == ','){

                    u16 stopcode = char_to_u16(input_file + scope3_start, scope3_len);

                    //two possibilities. either 2646 or 5727. Else FOR NOW IS FAILURE.
                    if (stopcode == 2646){
                        temporal_headway_struct.bus_direction = CIBELES;
                    }else if (stopcode == 5727){
                        temporal_headway_struct.bus_direction = LA_PESETA;                       
                    } else{
                        fprintf(stderr, "Undefined stopcode %" PRIu16 " for json parsing\n", stopcode);
                        free(temporal_headways_array);
                        free(temporal_input_buses.input_buses);
                        free(input_file);
                        exit(-7);
                    }
                    scope3_start = i +1;
                    scope3_len = 0;
                    break;
                }
                if (input_file[i] == ']'){
                    temporal_headway_struct.departure_time = timechar_to_u32_seconds(
                                    input_file + scope3_start, scope3_len);

                    if (temporal_headway_length == max_headway_length){
                        max_headway_length *=2;

                        headway_times *tmp_headways = realloc(temporal_headways_array,
                                        sizeof(headway_times)*max_headway_length);
                        
                        if (!tmp_headways){
                            perror("Error reallocating memory for temporal struct headways in json parsing\n");
                            free(temporal_input_buses.input_buses);
                            free(input_file);
                            exit(-3);
                        }
                        temporal_headways_array = tmp_headways;
                    }
                    temporal_headways_array[temporal_headway_length] = temporal_headway_struct;
                    temporal_headway_length ++;
                    temporal_headway_struct = (headway_times){0};
                    scope --;
                    break;
                }
                //If no check matches, just advance the len
                scope3_len ++;
            }
        } 
    }

    //Outside of the for loop. We need to move the temporal to the definitive.

    input_data_buses *return_data_buses = malloc(sizeof(input_data_buses));
    if (!return_data_buses){
        perror("Error assigning memory for input data vbuses struct\n");
        exit(-3);
    }

    data_bus *final_data_bus = realloc(temporal_input_buses.input_buses,
                        sizeof(data_bus) *number_of_buses);
    
    if (!final_data_bus){
        perror("Error allocating final memory for json parse returtn\n");
        free(temporal_headways_array);
        exit(-3);
    }
    return_data_buses->input_buses = final_data_bus;
    return_data_buses->number_of_buses = number_of_buses;

    free(temporal_headways_array);
    free(input_file);
    return return_data_buses;
}