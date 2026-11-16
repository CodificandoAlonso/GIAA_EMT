### 5.2 Correlation between alightings and arrival load per (stop, service slot)

| direction | n_combinations | pearson_median | q25 | q75 | %sig_positive | %sig_negative | spearman_median | q25  | q75  | %sig_positive  | %sig_negative  |
|---|---|---|---|---|---|---|---|---|---|---|---|
| toA | 266 | 0.404 | 0.216 | 0.622 | 91.729 | 0.000 | 0.409 | 0.207 | 0.638 | 88.722 | 0.000 |
| toB | 201 | 0.529 | 0.305 | 0.619 | 95.025 | 0.000 | 0.535 | 0.354 | 0.628 | 95.522 | 0.000 |

Restricted to combinations with n >= 30:

| direction | n_combinations | pearson_median | %sig_pos_pearson | spearman_median | %sig_pos_spearman |
|---|---|---|---|---|---|
| toA | 265 | 0.405 | 92.075 | 0.409 | 89.057 |
| toB | 198 | 0.527 | 95.455 | 0.533 | 95.960 |

### 5.3 Fraction of the arriving load that alights (alightings/load)

| direction | stop | order | n_visits_(load>0) | frac_mean | frac_q25 | frac_median | frac_q75 |
|---|---|---|---|---|---|---|---|
| toA | 82 | 14 | 11379 | 0.377 | 0.273 | 0.357 | 0.458 |
| toA | 562 | 2 | 8439 | 0.044 | 0.000 | 0.000 | 0.000 |
| toA | 1929 | 11 | 11392 | 0.072 | 0.023 | 0.058 | 0.100 |
| toA | 2535 | 10 | 11066 | 0.052 | 0.000 | 0.038 | 0.073 |
| toA | 2539 | 9 | 10756 | 0.061 | 0.000 | 0.043 | 0.087 |
| toA | 3903 | 8 | 11014 | 0.260 | 0.136 | 0.240 | 0.357 |
| toA | 3991 | 7 | 11055 | 0.055 | 0.000 | 0.037 | 0.083 |
| toA | 3995 | 6 | 10711 | 0.091 | 0.000 | 0.071 | 0.137 |
| toA | 4032 | 12 | 11561 | 0.104 | 0.048 | 0.088 | 0.136 |
| toA | 4090 | 3 | 10341 | 0.071 | 0.000 | 0.000 | 0.095 |
| toA | 4188 | 4 | 10503 | 0.239 | 0.031 | 0.188 | 0.375 |
| toA | 5360 | 13 | 11585 | 0.277 | 0.192 | 0.263 | 0.344 |
| toA | 5727 | 15 | 10250 | 0.984 | 0.773 | 0.917 | 1.077 |
| toA | 5939 | 5 | 10608 | 0.015 | 0.000 | 0.000 | 0.000 |
| toA | ALL | 0 | 150660 | 0.193 | 0.000 | 0.083 | 0.250 |
| toB | 81 | 2 | 10041 | 0.039 | 0.000 | 0.000 | 0.043 |
| toB | 649 | 11 | 10630 | 0.248 | 0.083 | 0.200 | 0.350 |
| toB | 1167 | 3 | 8839 | 0.019 | 0.000 | 0.000 | 0.027 |
| toB | 2538 | 4 | 9044 | 0.137 | 0.083 | 0.130 | 0.182 |
| toB | 2646 | 12 | 9277 | 1.099 | 0.600 | 0.857 | 1.250 |
| toB | 2964 | 10 | 10741 | 0.334 | 0.186 | 0.300 | 0.438 |
| toB | 3929 | 5 | 11082 | 0.339 | 0.250 | 0.324 | 0.409 |
| toB | 3990 | 6 | 11242 | 0.131 | 0.071 | 0.120 | 0.176 |
| toB | 3994 | 7 | 11374 | 0.270 | 0.176 | 0.254 | 0.345 |
| toB | 4187 | 9 | 11059 | 0.534 | 0.371 | 0.553 | 0.708 |
| toB | 5938 | 8 | 11407 | 0.085 | 0.000 | 0.060 | 0.118 |
| toB | ALL | 0 | 114736 | 0.291 | 0.053 | 0.185 | 0.381 |

### 5.4 Per-expedition correlation of cumulative boardings and alightings along the route

| direction | n_complete_trips | n_with_defined_corr | median | q25 | q75 | mean |
|---|---|---|---|---|---|---|
| toA | 6603 | 6599 | 0.789 | 0.728 | 0.835 | 0.776 |
| toB | 6247 | 6241 | 0.815 | 0.766 | 0.856 | 0.806 |

### 5.5 Visit-level CSV: `tables/t5_visits.csv` (269551 rows; first stop excluded, load = recorded Occupation of the previous stop of the same trip, only consecutive visits both surviving cleaning).