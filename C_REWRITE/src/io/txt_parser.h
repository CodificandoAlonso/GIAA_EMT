#pragma once

#include<stdio.h>
#include<stdlib.h>

#include "utils/utils.h"
#include "io/csv_parser.h"


typedef struct stops_list{
    //u16 stopcode[2][MAX_DIRECTION_LEN];
    size_t size_toA;
    u16 *stopcodes_toA;
    size_t size_toB;
    u16 *stopcodes_toB;
}stops_list;




const stops_list *load_stops(char *route_to_file);
