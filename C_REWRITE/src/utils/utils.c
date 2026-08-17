#include<stdio.h>
#include<stdlib.h>
#include<stdint.h>
#include "utils/utils.h"


char *extract_data_range (char *buffer, size_t start, size_t len){

    char* ret_char = malloc(len +1);

    size_t counter = 0;
    for (size_t i = start; i < start + len; i++){
        ret_char[counter] = buffer[i];
        counter ++;
    }
    ret_char[len] = '\0';
    return ret_char;
}