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

u16 char_to_u16(const char *input, size_t n){
    u16 ret = 0;
    for (size_t i = 0; i< n; i++){
        ret = ret*10 + (input[i] - '0');
    }
    return ret;
}


u32 timechar_to_u32_seconds(const char *input, size_t n){


    u32 hours = 0;
    u32 minutes = 0;
    u32 seconds = 0;


    // 0 means reading hours, 1 means reading minutes, 2 means reading seconds.
    byte scope = 0;

    for (size_t i = 0; i< n; i++){

        if (input[i] == ':'){scope++;continue;}

        switch (scope){
            case 0:
                hours = hours*10 + (input[i] - '0');
                break;
            case 1:
                minutes = minutes*10 + (input[i] - '0');
                break;
            case 2:
                seconds = seconds *10  + (input[i] - '0');
                break;
        }
    }
    return hours*3600 + minutes*60 + seconds;
}