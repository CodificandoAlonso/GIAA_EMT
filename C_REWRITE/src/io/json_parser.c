#include "io/json_parser.h"
#include<stdlib.h>
#include<stdio.h>





const input_data_buses *load_input_from_json(char *filename){
    

    FILE *fd_json = fopen(filename, "r");
    if (!fd_json){
        perror("Error opening json file\n");
        exit(-2);
    }


    char *input_line = malloc(256);

    if (!input_line){
        perror("Error allocating in json read\n");
        exit(-3);
    }


    while (fgets(input_line, 256, fd_json)){
        
    }

}