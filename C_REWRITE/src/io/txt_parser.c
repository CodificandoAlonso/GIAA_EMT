#include "io/txt_parser.h"



const stops_list *load_stops(char *route_to_file){

    
    FILE *fd_input = fopen(route_to_file, "r");


    if (!fd_input){
        perror("Error opening file txt\n");
        exit(-6);
    }

    char *line = malloc(256);
    if (!line){
        perror("Error allocating memory in file txt code\n");
        exit(-4);        
    }

    stops_list *global_stops_list = malloc(sizeof(stops_list));
    if (!global_stops_list)
        return NULL;

    global_stops_list->size_toA = 0;
    global_stops_list->size_toB = 0;

    //alloc'ed space for each direction array

    u16 *allocated_toA = malloc(sizeof(u16)*MAX_DIRECTION_LEN);
    if (!allocated_toA){
        perror("Error allocating memory for toA direction array of stopcodes\n");
        exit(-3);
    }
    global_stops_list->stopcodes_toA = allocated_toA;

    u16 *allocated_toB = malloc(sizeof(u16)*MAX_DIRECTION_LEN);
    if (!allocated_toB){
        perror("Error allocating memory for toB direction array of stopcodes\n");
        exit(-3);
    }
    global_stops_list->stopcodes_toB = allocated_toB;

    size_t direction = 0;
    size_t index = 0;
    while (fgets(line, 256, fd_input)){

        //auxiliar variables.
        size_t start = 0, actual_read = 0;


        for (size_t i = 0; i<256; i++){

            if (line[i] == ',' || line[i] == '\n' || line[i] == '\0'){

                u16 stop_code = 0;

                for(size_t j = start; j < start + actual_read; j++){
                    stop_code = 10*stop_code + (line[j] - '0');
                }

                
                if (direction == 0){
                    //Case toA.
                    global_stops_list->stopcodes_toA[index] = stop_code;
                    start = i + 1;
                    actual_read = 0;
                    index ++;
                }else{
                    //Case toB.
                    global_stops_list->stopcodes_toB[index] = stop_code;
                    start = i + 1;
                    actual_read = 0;
                    index ++;
                }                

                if (line[i] == '\n'){
                    direction ++;
                    global_stops_list->size_toA = index;
                    index = 0;
                    break;
                }

                if (line[i] == '\0'){
                    global_stops_list->size_toB = index;
                    break;
                }


            }else{actual_read++;}
        }
    }
    fclose(fd_input);
    free(line);
        
    return global_stops_list;
}