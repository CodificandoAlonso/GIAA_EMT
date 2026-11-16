Slot = departure slot of the expedition (reference definition, `TimeSlot`). Occupation is the recorded occupancy after the stop.

### By direction

| direction | state | threshold | n_visits | n_at_threshold | pct |
|---|---|---|---|---|---|
| toA | A before upper cut | occ>=80 (capacity) | 169906 | 832 | 0.490 |
| toA | A before upper cut | occ>=72 (90% of capacity) | 169906 | 3460 | 2.036 |
| toA | B after Occupation<80 | occ>=80 (capacity) | 169074 | 0 | 0.000 |
| toA | B after Occupation<80 | occ>=72 (90% of capacity) | 169074 | 2628 | 1.554 |
| toB | A before upper cut | occ>=80 (capacity) | 134048 | 470 | 0.351 |
| toB | A before upper cut | occ>=72 (90% of capacity) | 134048 | 2057 | 1.535 |
| toB | B after Occupation<80 | occ>=80 (capacity) | 133578 | 0 | 0.000 |
| toB | B after Occupation<80 | occ>=72 (90% of capacity) | 133578 | 1587 | 1.188 |

### By slot, state A, share of visits >=80 and >=72 (90% capacity). States B/C in `tables/t8_by_slot.csv`

| direction | slot | occ>=72 (90% of capacity) | occ>=80 (capacity) |
|---|---|---|---|
| toA | 5 | 6.67 | 1.89 |
| toA | 6 | 7.18 | 1.75 |
| toA | 7 | 5.62 | 1.20 |
| toA | 8 | 2.73 | 0.55 |
| toA | 9 | 0.95 | 0.11 |
| toA | 10 | 0.55 | 0.06 |
| toA | 11 | 0.50 | 0.06 |
| toA | 12 | 0.51 | 0.07 |
| toA | 13 | 0.45 | 0.10 |
| toA | 14 | 0.63 | 0.19 |
| toA | 15 | 0.91 | 0.28 |
| toA | 16 | 1.07 | 0.25 |
| toA | 17 | 2.14 | 0.65 |
| toA | 18 | 2.07 | 0.58 |
| toA | 19 | 1.37 | 0.31 |
| toA | 20 | 1.03 | 0.25 |
| toA | 21 | 1.74 | 0.33 |
| toA | 22 | 1.45 | 0.64 |
| toA | 23 | 0.06 | 0.06 |
| toB | 5 | 2.06 | 1.92 |
| toB | 6 | 0.00 | 0.00 |
| toB | 7 | 0.63 | 0.39 |
| toB | 8 | 0.78 | 0.51 |
| toB | 9 | 0.06 | 0.00 |
| toB | 10 | 0.03 | 0.00 |
| toB | 11 | 0.21 | 0.06 |
| toB | 12 | 0.30 | 0.01 |
| toB | 13 | 1.00 | 0.30 |
| toB | 14 | 2.85 | 0.50 |
| toB | 15 | 3.09 | 0.59 |
| toB | 16 | 1.78 | 0.25 |
| toB | 17 | 2.82 | 0.33 |
| toB | 18 | 3.85 | 0.68 |
| toB | 19 | 2.46 | 0.39 |
| toB | 20 | 1.57 | 0.21 |
| toB | 21 | 1.80 | 0.48 |
| toB | 22 | 1.28 | 0.80 |
| toB | 23 | 0.66 | 0.41 |

### By stop (state A, >=80 and >=72) 

| direction | threshold | stop | order | n_visits | n_at_threshold | pct |
|---|---|---|---|---|---|---|
| toA | occ>=72 (90% of capacity) | 2646 | 1 | 10341 | 5 | 0.05 |
| toA | occ>=80 (capacity) | 2646 | 1 | 10341 | 5 | 0.05 |
| toA | occ>=72 (90% of capacity) | 562 | 2 | 11047 | 6 | 0.05 |
| toA | occ>=80 (capacity) | 562 | 2 | 11047 | 5 | 0.05 |
| toA | occ>=72 (90% of capacity) | 4090 | 3 | 11037 | 6 | 0.05 |
| toA | occ>=80 (capacity) | 4090 | 3 | 11037 | 5 | 0.05 |
| toA | occ>=72 (90% of capacity) | 4188 | 4 | 10817 | 47 | 0.43 |
| toA | occ>=80 (capacity) | 4188 | 4 | 10817 | 8 | 0.07 |
| toA | occ>=72 (90% of capacity) | 5939 | 5 | 11008 | 84 | 0.76 |
| toA | occ>=80 (capacity) | 5939 | 5 | 11008 | 8 | 0.07 |
| toA | occ>=72 (90% of capacity) | 3995 | 6 | 11291 | 196 | 1.74 |
| toA | occ>=80 (capacity) | 3995 | 6 | 11291 | 20 | 0.18 |
| toA | occ>=72 (90% of capacity) | 3991 | 7 | 11368 | 311 | 2.74 |
| toA | occ>=80 (capacity) | 3991 | 7 | 11368 | 41 | 0.36 |
| toA | occ>=72 (90% of capacity) | 3903 | 8 | 11370 | 419 | 3.69 |
| toA | occ>=80 (capacity) | 3903 | 8 | 11370 | 92 | 0.81 |
| toA | occ>=72 (90% of capacity) | 2539 | 9 | 11507 | 655 | 5.69 |
| toA | occ>=80 (capacity) | 2539 | 9 | 11507 | 147 | 1.28 |
| toA | occ>=72 (90% of capacity) | 2535 | 10 | 11812 | 712 | 6.03 |
| toA | occ>=80 (capacity) | 2535 | 10 | 11812 | 169 | 1.43 |
| toA | occ>=72 (90% of capacity) | 1929 | 11 | 11936 | 593 | 4.97 |
| toA | occ>=80 (capacity) | 1929 | 11 | 11936 | 150 | 1.26 |
| toA | occ>=72 (90% of capacity) | 4032 | 12 | 11985 | 301 | 2.51 |
| toA | occ>=80 (capacity) | 4032 | 12 | 11985 | 74 | 0.62 |
| toA | occ>=72 (90% of capacity) | 5360 | 13 | 11879 | 55 | 0.46 |
| toA | occ>=80 (capacity) | 5360 | 13 | 11879 | 38 | 0.32 |
| toA | occ>=72 (90% of capacity) | 82 | 14 | 11666 | 36 | 0.31 |
| toA | occ>=80 (capacity) | 82 | 14 | 11666 | 36 | 0.31 |
| toA | occ>=72 (90% of capacity) | 5727 | 15 | 10842 | 34 | 0.31 |
| toA | occ>=80 (capacity) | 5727 | 15 | 10842 | 34 | 0.31 |
| toB | occ>=72 (90% of capacity) | 5727 | 1 | 11138 | 9 | 0.08 |
| toB | occ>=80 (capacity) | 5727 | 1 | 11138 | 6 | 0.05 |
| toB | occ>=72 (90% of capacity) | 81 | 2 | 11125 | 292 | 2.62 |
| toB | occ>=80 (capacity) | 81 | 2 | 11125 | 22 | 0.20 |
| toB | occ>=72 (90% of capacity) | 1167 | 3 | 9273 | 668 | 7.20 |
| toB | occ>=80 (capacity) | 1167 | 3 | 9273 | 71 | 0.77 |
| toB | occ>=72 (90% of capacity) | 2538 | 4 | 11406 | 335 | 2.94 |
| toB | occ>=80 (capacity) | 2538 | 4 | 11406 | 53 | 0.46 |
| toB | occ>=72 (90% of capacity) | 3929 | 5 | 11464 | 254 | 2.22 |
| toB | occ>=80 (capacity) | 3929 | 5 | 11464 | 66 | 0.58 |
| toB | occ>=72 (90% of capacity) | 3990 | 6 | 11735 | 158 | 1.35 |
| toB | occ>=80 (capacity) | 3990 | 6 | 11735 | 47 | 0.40 |
| toB | occ>=72 (90% of capacity) | 3994 | 7 | 11744 | 116 | 0.99 |
| toB | occ>=80 (capacity) | 3994 | 7 | 11744 | 40 | 0.34 |
| toB | occ>=72 (90% of capacity) | 5938 | 8 | 11623 | 93 | 0.80 |
| toB | occ>=80 (capacity) | 5938 | 8 | 11623 | 40 | 0.34 |
| toB | occ>=72 (90% of capacity) | 4187 | 9 | 11344 | 34 | 0.30 |
| toB | occ>=80 (capacity) | 4187 | 9 | 11344 | 33 | 0.29 |
| toB | occ>=72 (90% of capacity) | 2964 | 10 | 11204 | 34 | 0.30 |
| toB | occ>=80 (capacity) | 2964 | 10 | 11204 | 33 | 0.29 |
| toB | occ>=72 (90% of capacity) | 649 | 11 | 11247 | 35 | 0.31 |
| toB | occ>=80 (capacity) | 649 | 11 | 11247 | 33 | 0.29 |
| toB | occ>=72 (90% of capacity) | 2646 | 12 | 10745 | 29 | 0.27 |
| toB | occ>=80 (capacity) | 2646 | 12 | 10745 | 26 | 0.24 |

### 8.2 Stop-slot combinations with highest share of visits at capacity (state A, n>=30)

| direction | stop | order | slot | n_visits | n_at_threshold | pct |
|---|---|---|---|---|---|---|
| toA | 2539 | 9 | 5 | 352 | 25 | 7.10 |
| toA | 2535 | 10 | 5 | 353 | 25 | 7.08 |
| toA | 1929 | 11 | 5 | 352 | 23 | 6.53 |
| toA | 2535 | 10 | 6 | 656 | 35 | 5.34 |
| toA | 2539 | 9 | 6 | 648 | 30 | 4.63 |
| toA | 1929 | 11 | 6 | 655 | 30 | 4.58 |
| toA | 2535 | 10 | 7 | 892 | 36 | 4.04 |
| toA | 3903 | 8 | 6 | 648 | 25 | 3.86 |
| toA | 2539 | 9 | 7 | 880 | 29 | 3.30 |
| toB | 1167 | 3 | 15 | 627 | 18 | 2.87 |
| toA | 4032 | 12 | 5 | 354 | 10 | 2.82 |
| toA | 1929 | 11 | 7 | 895 | 25 | 2.79 |
| toB | 4187 | 9 | 5 | 120 | 3 | 2.50 |
| toB | 649 | 11 | 5 | 120 | 3 | 2.50 |
| toA | 3903 | 8 | 7 | 886 | 22 | 2.48 |

### >=90% of capacity, top combinations (state A, n>=30)

| direction | stop | order | slot | n_visits | n_at_threshold | pct |
|---|---|---|---|---|---|---|
| toA | 2535 | 10 | 5 | 353 | 88 | 24.93 |
| toA | 1929 | 11 | 5 | 352 | 84 | 23.86 |
| toA | 2539 | 9 | 5 | 352 | 83 | 23.58 |
| toA | 2535 | 10 | 6 | 656 | 143 | 21.80 |
| toA | 2539 | 9 | 6 | 648 | 133 | 20.52 |
| toA | 1929 | 11 | 6 | 655 | 121 | 18.47 |
| toA | 2535 | 10 | 7 | 892 | 153 | 17.15 |
| toA | 2539 | 9 | 7 | 880 | 149 | 16.93 |
| toA | 3903 | 8 | 6 | 648 | 107 | 16.51 |
| toB | 1167 | 3 | 15 | 627 | 101 | 16.11 |