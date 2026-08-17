#pragma once
#include <stdint.h>

typedef uint8_t byte;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


typedef volatile u32 reg32;



char *extract_data_range (char *buffer, size_t start, size_t end);