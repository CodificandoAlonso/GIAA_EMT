#pragma once
#include "utils/utils.h"

#include<math.h>

#define MAX_32 4294967296.0

static const double EULER = 2.71828182845904523536;

static const double PI    = 3.14159265358979323846;

// Source - https://stackoverflow.com/a/3437484
// Posted by David Titarenco, modified by community. See post 'Timeline' for change history
// Retrieved 2026-08-30, License - CC BY-SA 4.0

 #define max(a,b) \
   ({ __typeof__ (a) _a = (a); \
       __typeof__ (b) _b = (b); \
     _a > _b ? _a : _b; })

 #define min(a,b) \
   ({ __typeof__ (a) _a = (a); \
       __typeof__ (b) _b = (b); \
     _a < _b ? _a : _b; })



void linear_conservative_reconstruction(double *linear_arr,
double value_first_tram, double value_second_tram, u32 step);