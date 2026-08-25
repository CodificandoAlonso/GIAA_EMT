#pragma once
#include "utils/utils.h"



typedef struct data_bus{
    u16 bus_code;
    direction initial_direction;
    headway_times *headway_bus_times;
    size_t headways_length;
}data_bus;



typedef struct input_data_buses{
    data_bus *input_buses;
    size_t number_of_buses;
}input_data_buses;



const input_data_buses *load_input_from_json(char *filename);
