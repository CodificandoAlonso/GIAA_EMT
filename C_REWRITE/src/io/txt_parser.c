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


    size_t direction = 0;
    size_t index = 0;
    while (fgets(line, 256, fd_input)){

        //auxiliar variables.
        size_t start = 0, actual_read = 0;


        for (size_t i = 0; i<256; i++){

            if (line[i] == ',' || line[i] == '\n' | line[i] == '\0'){

                u16 stop_code = 0;

                for(size_t j = start; j < start + actual_read; j++){
                    stop_code = 10*stop_code + (line[j] - '0');
                }
                global_stops_list->stopcode[direction][index] = stop_code;
                start = i + 1;
                actual_read = 0;
                index ++;

                if (line[i] == '\n'){
                    direction ++;
                    index = 0;
                    break;
                }

                if (line[i] == '\0'){
                    break;
                }


            }else{actual_read++;}
        }
    }
    fclose(fd_input);
    free(line);
        
    return global_stops_list;
}