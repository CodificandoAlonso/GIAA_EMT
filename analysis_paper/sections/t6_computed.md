| direction | n_visits_before_cut | removed (Occ>=80) | pct | exactly 80 | > 80 |
|---|---|---|---|---|---|
| toA | 169906 | 832 | 0.490 | 151 | 681 |
| toB | 134048 | 470 | 0.351 | 55 | 415 |

Visits removed by `Occupation >= 80`, with how many have exactly 80, per direction and slot (departure-slot definition; the service-slot version is in `tables/t6_5_removed_by_occupation_cut.csv`):

| direction | slot | n_visits_before_cut | removed_by_Occ>=80 | of_which_exactly_80 | of_which_>80 | pct_removed |
|---|---|---|---|---|---|---|
| toA | 5 | 4933 | 93 | 17 | 76 | 1.89 |
| toA | 6 | 9480 | 166 | 31 | 135 | 1.75 |
| toA | 7 | 12954 | 156 | 34 | 122 | 1.20 |
| toA | 8 | 11648 | 64 | 12 | 52 | 0.55 |
| toA | 9 | 9280 | 10 | 2 | 8 | 0.11 |
| toA | 10 | 8223 | 5 | 2 | 3 | 0.06 |
| toA | 11 | 8319 | 5 | 5 | 0 | 0.06 |
| toA | 12 | 10040 | 7 | 1 | 6 | 0.07 |
| toA | 13 | 10757 | 11 | 4 | 7 | 0.10 |
| toA | 14 | 10179 | 19 | 7 | 12 | 0.19 |
| toA | 15 | 10960 | 31 | 1 | 30 | 0.28 |
| toA | 16 | 11189 | 28 | 4 | 24 | 0.25 |
| toA | 17 | 10688 | 70 | 14 | 56 | 0.65 |
| toA | 18 | 9940 | 58 | 8 | 50 | 0.58 |
| toA | 19 | 9123 | 28 | 1 | 27 | 0.31 |
| toA | 20 | 8061 | 20 | 5 | 15 | 0.25 |
| toA | 21 | 6648 | 22 | 2 | 20 | 0.33 |
| toA | 22 | 5932 | 38 | 1 | 37 | 0.64 |
| toA | 23 | 1552 | 1 | 0 | 1 | 0.06 |
| toB | 5 | 1409 | 27 | 0 | 27 | 1.92 |
| toB | 6 | 5887 | 0 | 0 | 0 | 0.00 |
| toB | 7 | 9319 | 36 | 1 | 35 | 0.39 |
| toB | 8 | 8551 | 44 | 0 | 44 | 0.51 |
| toB | 9 | 6714 | 0 | 0 | 0 | 0.00 |
| toB | 10 | 7069 | 0 | 0 | 0 | 0.00 |
| toB | 11 | 6717 | 4 | 0 | 4 | 0.06 |
| toB | 12 | 6773 | 1 | 1 | 0 | 0.01 |
| toB | 13 | 7598 | 23 | 1 | 22 | 0.30 |
| toB | 14 | 9995 | 50 | 5 | 45 | 0.50 |
| toB | 15 | 8710 | 51 | 12 | 39 | 0.59 |
| toB | 16 | 8919 | 22 | 3 | 19 | 0.25 |
| toB | 17 | 8959 | 30 | 8 | 22 | 0.33 |
| toB | 18 | 7972 | 54 | 11 | 43 | 0.68 |
| toB | 19 | 8277 | 32 | 7 | 25 | 0.39 |
| toB | 20 | 7622 | 16 | 2 | 14 | 0.21 |
| toB | 21 | 5888 | 28 | 0 | 28 | 0.48 |
| toB | 22 | 5228 | 42 | 3 | 39 | 0.80 |
| toB | 23 | 2441 | 10 | 1 | 9 | 0.41 |

Slot definitions check on the data:

| direction | % TimeSlot == hour(EventTime) (terminal departure) | % TimeSlot.1 == hour(EventTime.1) (stop arrival) | n_visits |
|---|---|---|---|
| toA | 100.000 | 100.000 | 236940 |
| toB | 100.000 | 100.000 | 187116 |