#pragma once
#include "utils/utils.h"



typedef struct data_bus{
    u16 bus_code;
    u16 initial_stop_code;
    headway_times *headway_bus_times;
}data_bus;



typedef struct input_data_buses{
    data_bus *input_buses;
}input_data_buses;



const input_data_buses *load_input_from_json(char *filename);