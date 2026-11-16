First date: **2025-07-01**, last date: **2026-02-23**. (n days = 238)

| category | n_days |
|---|---|
| normal | 158 |
| weekend (Sat/Sun) | 68 |
| public holiday (Mon-Fri) | 7 |
| free-fare working day | 5 |
| TOTAL | 238 |

Precedence: weekend > holiday > free fare. Note: all Sundays carry DayType FE; Saturdays DayType SA; holidays falling Mon-Fri are FE; FreeDay=1 occurs only in LA days.

Normal days (DayType=LA & FreeDay=0): **158** (toA: 158, toB: 158).


| direction | trips_normal_days | visits_normal_days | trips_after_cleaning | visits_after_cleaning | trips_all_days | visits_all_days | n_stops |
|---|---|---|---|---|---|---|---|
| toA | 12951 | 170944 | 12932 | 169074 | 18029 | 236940 | 15 |
| toB | 12860 | 135618 | 12845 | 133578 | 17864 | 187116 | 12 |

| direction | scope | condition | n_records | pct | N_total |
|---|---|---|---|---|---|
| toA | all records of direction | Occupation < 0 | 1470 | 0.6204 | 236940 |
| toA | all records of direction | Occupation >= 80 | 1348 | 0.5689 | 236940 |
| toA | all records of direction | Board < 0 | 1 | 0.0004 | 236940 |
| toA | all records of direction | DropOff < 0 | 12 | 0.0051 | 236940 |
| toA | all records of direction | Board >= 80 | 24 | 0.0101 | 236940 |
| toA | all records of direction | DropOff >= 80 | 28 | 0.0118 | 236940 |
| toA | normal-day records | Occupation < 0 | 1016 | 0.5943 | 170944 |
| toA | normal-day records | Occupation >= 80 | 843 | 0.4931 | 170944 |
| toA | normal-day records | Board < 0 | 1 | 0.0006 | 170944 |
| toA | normal-day records | DropOff < 0 | 10 | 0.0058 | 170944 |
| toA | normal-day records | Board >= 80 | 14 | 0.0082 | 170944 |
| toA | normal-day records | DropOff >= 80 | 15 | 0.0088 | 170944 |
| toB | all records of direction | Occupation < 0 | 2328 | 1.2441 | 187116 |
| toB | all records of direction | Occupation >= 80 | 756 | 0.4040 | 187116 |
| toB | all records of direction | Board < 0 | 0 | 0.0000 | 187116 |
| toB | all records of direction | DropOff < 0 | 16 | 0.0086 | 187116 |
| toB | all records of direction | Board >= 80 | 20 | 0.0107 | 187116 |
| toB | all records of direction | DropOff >= 80 | 10 | 0.0053 | 187116 |
| toB | normal-day records | Occupation < 0 | 1547 | 1.1407 | 135618 |
| toB | normal-day records | Occupation >= 80 | 479 | 0.3532 | 135618 |
| toB | normal-day records | Board < 0 | 0 | 0.0000 | 135618 |
| toB | normal-day records | DropOff < 0 | 12 | 0.0088 | 135618 |
| toB | normal-day records | Board >= 80 | 12 | 0.0088 | 135618 |
| toB | normal-day records | DropOff >= 80 | 4 | 0.0029 | 135618 |

| direction | scope | N_total | unique_removed | pct |
|---|---|---|---|---|
| toA | all records of direction | 236940 | 2846 | 1.2011 |
| toA | normal-day records | 170944 | 1870 | 1.0939 |
| toB | all records of direction | 187116 | 3106 | 1.6599 |
| toB | normal-day records | 135618 | 2040 | 1.5042 |

| direction | cleaning | removed_records | normal_days | stops | removed/(days*stops) | inverse (days per removed record) |
|---|---|---|---|---|---|---|
| toA | Occ<80 | 1870 | 158 | 15 | 0.7890 | 1.2674 |
| toB | Occ<80 | 2040 | 158 | 12 | 1.0759 | 0.9294 |
| both | Occ<80 | 3910 | 158 | 27 | 0.9165 | 1.0910 |

| direction | variable | n_combinations | min | median | max |
|---|---|---|---|---|---|
| toA | alightings (per bus arrival) | 285 | 15 | 622.0 | 875 |
| toA | boardings (per stop-hour, day sums) | 285 | 152 | 158.0 | 158 |
| toA | occupation (per visit, departure slot) | 285 | 3 | 631.0 | 894 |
| toA | travel times (per segment, both arrivals in slot) | 266 | 9 | 571.0 | 836 |
| toB | alightings (per bus arrival) | 228 | 0 | 624.5 | 818 |
| toB | boardings (per stop-hour, day sums) | 228 | 152 | 158.0 | 158 |
| toB | occupation (per visit, departure slot) | 228 | 3 | 609.5 | 883 |
| toB | travel times (per segment, both arrivals in slot) | 209 | 0 | 550.0 | 772 |

| direction | variable | slots_with_fewest_obs |
|---|---|---|
| toA | alightings (per bus arrival) | slot 5 (median n=207), slot 23 (median n=234), slot 22 (median n=438) |
| toA | boardings (per stop-hour, day sums) | slot 5 (median n=158), slot 6 (median n=158), slot 7 (median n=158) |
| toA | occupation (per visit, departure slot) | slot 23 (median n=111), slot 5 (median n=349), slot 22 (median n=395) |
| toA | travel times (per segment, both arrivals in slot) | slot 5 (median n=186), slot 23 (median n=231), slot 22 (median n=401) |
| toB | alightings (per bus arrival) | slot 5 (median n=0), slot 23 (median n=384), slot 6 (median n=422) |
| toB | boardings (per stop-hour, day sums) | slot 5 (median n=158), slot 6 (median n=158), slot 7 (median n=158) |
| toB | occupation (per visit, departure slot) | slot 5 (median n=118), slot 23 (median n=224), slot 22 (median n=458) |
| toB | travel times (per segment, both arrivals in slot) | slot 5 (median n=0), slot 23 (median n=372), slot 6 (median n=406) |

Combinations with zero observations:

| direction | variable | combinations_with_0_obs |
|---|---|---|
| toB | alightings (per bus arrival) | 10 |
| toB | travel times (per segment, both arrivals in slot) | 11 |