### 4.2 / 4.6 Aggregate imbalance = sum(alightings)/sum(boardings) - 1 (paper: -4.4 %)

| direction | subset | terminals | n_trips | n_visits | sum_boardings | sum_alightings | imbalance_%_(alightings/boardings-1) |
|---|---|---|---|---|---|---|---|
| both | S0 raw, all normal-day visits | with terminals | 25811 | 306562 | -753206277 | -775799606 | 3.00 |
| toA | S0 raw, all normal-day visits | with terminals | 12951 | 170944 | -754640240 | -776354941 | 2.88 |
| toB | S0 raw, all normal-day visits | with terminals | 12860 | 135618 | 1433963 | 555335 | -61.27 |
| both | S0 raw, all normal-day visits | without terminals | 25232 | 263456 | -753499498 | -776055586 | 2.99 |
| toA | S0 raw, all normal-day visits | without terminals | 12643 | 149741 | -754723841 | -776537010 | 2.89 |
| toB | S0 raw, all normal-day visits | without terminals | 12589 | 113715 | 1224343 | 481424 | -60.68 |
| both | S1 pipeline-cleaned visits (partial trips allowed) | with terminals | 25777 | 302652 | 1522034 | 1455368 | -4.38 |
| toA | S1 pipeline-cleaned visits (partial trips allowed) | with terminals | 12932 | 169074 | 797297 | 742371 | -6.89 |
| toB | S1 pipeline-cleaned visits (partial trips allowed) | with terminals | 12845 | 133578 | 724737 | 712997 | -1.62 |
| both | S1 pipeline-cleaned visits (partial trips allowed) | without terminals | 25163 | 259657 | 1230327 | 1200694 | -2.41 |
| toA | S1 pipeline-cleaned visits (partial trips allowed) | without terminals | 12615 | 147930 | 714180 | 561321 | -21.40 |
| toB | S1 pipeline-cleaned visits (partial trips allowed) | without terminals | 12548 | 111727 | 516147 | 639373 | 23.87 |
| both | S2 complete trips, raw | with terminals | 13437 | 181656 | 1430699 | 558150 | -60.99 |
| toA | S2 complete trips, raw | with terminals | 6804 | 102060 | 501892 | 565631 | 12.70 |
| toB | S2 complete trips, raw | with terminals | 6633 | 79596 | 928807 | -7481 | -100.81 |
| both | S2 complete trips, raw | without terminals | 13437 | 154782 | 1243890 | 395944 | -68.17 |
| toA | S2 complete trips, raw | without terminals | 6804 | 88452 | 444415 | 449742 | 1.20 |
| toB | S2 complete trips, raw | without terminals | 6633 | 66330 | 799475 | -53798 | -106.73 |
| both | S3 complete trips with no visit removed by cleaning | with terminals | 12850 | 174009 | 895406 | 856113 | -4.39 |
| toA | S3 complete trips with no visit removed by cleaning | with terminals | 6603 | 99045 | 471182 | 447486 | -5.03 |
| toB | S3 complete trips with no visit removed by cleaning | with terminals | 6247 | 74964 | 424224 | 408627 | -3.68 |
| both | S3 complete trips with no visit removed by cleaning | without terminals | 12850 | 148309 | 718593 | 700389 | -2.53 |
| toA | S3 complete trips with no visit removed by cleaning | without terminals | 6603 | 85839 | 416368 | 336104 | -19.28 |
| toB | S3 complete trips with no visit removed by cleaning | without terminals | 6247 | 62470 | 302225 | 364285 | 20.53 |

### 4.1/4.3 Per-expedition balance (diff = boardings - alightings; subset S3)

| direction | subset | terminals | n_trips | diff_median | diff_q25 | diff_q75 | diff_mean | %trips boards>alightings | %trips equal | %trips boards<alightings | rel_imbalance_median_% | rel_q25_% | rel_q75_% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| toA | S3 | with terminals | 6603 | 3.00 | 0.00 | 6.00 | 3.59 | 70.47 | 7.68 | 21.85 | -4.26 | -8.62 | 0.00 |
| toA | S3 | without terminals | 6603 | 11.00 | 5.00 | 18.00 | 12.16 | 91.70 | 2.26 | 6.04 | -18.52 | -26.92 | -10.34 |
| toB | S3 | with terminals | 6247 | 2.00 | -1.00 | 5.00 | 2.50 | 64.61 | 9.54 | 25.85 | -3.23 | -7.52 | 1.05 |
| toB | S3 | without terminals | 6247 | -8.00 | -16.00 | -2.00 | -9.93 | 14.29 | 3.92 | 81.78 | 17.35 | 5.12 | 34.44 |

### 4.4 Occupation computed at the last stop (cumulative Board-DropOff from 0); ideal value 0

| direction | subset | n_trips | computed_occ_last_mean | median | q25 | q75 | mean_abs | min | max | recorded_Occ_last_median | rec_q25 | rec_q75 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| toA | complete trips, raw | 6804 | -9.37 | 3.00 | 0.00 | 7.00 | 46.58 | -184717 | 94723 | 2.00 | 0.00 | 5.00 |
| toA | complete trips, cleaned (S3) | 6603 | 3.59 | 3.00 | 0.00 | 6.00 | 5.07 | -58 | 75 | 1.00 | 0.00 | 5.00 |
| toB | complete trips, raw | 6633 | 141.16 | 2.00 | -1.00 | 5.00 | 143.26 | -60 | 498673 | 1.00 | 0.00 | 4.00 |
| toB | complete trips, cleaned (S3) | 6247 | 2.50 | 2.00 | -1.00 | 5.00 | 4.21 | -49 | 93 | 1.00 | 0.00 | 4.00 |

### 4.5 Share of expeditions where occupancy turns negative at some stop

| direction | n_complete_trips_raw | %trips cumulative occupancy <0 at some stop (raw, complete trips) | %trips recorded Occupation<0 at some stop (raw, complete trips) | n_all_normal_day_trips | %trips recorded Occupation<0 at some stop (all trips, raw) | n_trips_S3 | %trips cumulative<0 after cleaning (S3) |
|---|---|---|---|---|---|---|---|
| toA | 6804 | 22.22 | 1.09 | 12951 | 2.29 | 6603 | 21.87 |
| toB | 6633 | 28.25 | 4.48 | 12860 | 5.47 | 6247 | 25.87 |

### 4.6 Net boardings-alightings per stop (S3); terminals are the first and last row of each direction

| direction | order | Stop | n | boards | drops | net |
|---|---|---|---|---|---|---|
| toA | 1 | 2646 | 6603 | 54219 | 35 | 54184 |
| toA | 2 | 562 | 6603 | 29129 | 1215 | 27914 |
| toA | 3 | 4090 | 6603 | 30753 | 4884 | 25869 |
| toA | 4 | 4188 | 6603 | 100286 | 23780 | 76506 |
| toA | 5 | 5939 | 6603 | 15191 | 2189 | 13002 |
| toA | 6 | 3995 | 6603 | 65858 | 18650 | 47208 |
| toA | 7 | 3991 | 6603 | 30033 | 13627 | 16406 |
| toA | 8 | 3903 | 6603 | 62083 | 67791 | -5708 |
| toA | 9 | 2539 | 6603 | 32710 | 14074 | 18636 |
| toA | 10 | 2535 | 6603 | 19300 | 12799 | 6501 |
| toA | 11 | 1929 | 6603 | 14176 | 18431 | -4255 |
| toA | 12 | 4032 | 6603 | 4697 | 26158 | -21461 |
| toA | 13 | 5360 | 6603 | 6850 | 64232 | -57382 |
| toA | 14 | 82 | 6603 | 5302 | 68274 | -62972 |
| toA | 15 | 5727 | 6603 | 595 | 111347 | -110752 |
| toB | 1 | 5727 | 6247 | 121723 | 231 | 121492 |
| toB | 2 | 81 | 6247 | 99020 | 3160 | 95860 |
| toB | 3 | 1167 | 6247 | 59208 | 3100 | 56108 |
| toB | 4 | 2538 | 6247 | 21548 | 35767 | -14219 |
| toB | 5 | 3929 | 6247 | 67290 | 83591 | -16301 |
| toB | 6 | 3990 | 6247 | 12157 | 29752 | -17595 |
| toB | 7 | 3994 | 6247 | 18868 | 55078 | -36210 |
| toB | 8 | 5938 | 6247 | 1511 | 13078 | -11567 |
| toB | 9 | 4187 | 6247 | 19180 | 96449 | -77269 |
| toB | 10 | 2964 | 6247 | 3101 | 28590 | -25489 |
| toB | 11 | 649 | 6247 | 342 | 15720 | -15378 |
| toB | 12 | 2646 | 6247 | 276 | 44111 | -43835 |