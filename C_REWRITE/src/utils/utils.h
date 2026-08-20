#pragma once
#include <stdint.h>
#include <stddef.h>

typedef uint8_t byte;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


typedef volatile u32 reg32;


typedef enum {
    CIBELES = 0,
    LA_PESETA = 1
} direction;


typedef struct headway_times{
    u32 departure_time;
    direction bus_direction;
} headway_times;

char *extract_data_range (char *buffer, size_t start, size_t end);