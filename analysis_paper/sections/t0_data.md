| direction | n_csv | n_distinct_schemas | columns |
|---|---|---|---|
| toA | 15 | 1 | TripId, IdExternal, EventDate, EventTime, TimeSlot, Line, Direction, LogicVehicle, Weekday, DayType, Season, FreeDay, TripId.1, Stop, IdExternal.1, EventDate.1, EventTime.1, TimeSlot.1, TemperatureMax, TemperatureMin, RainProbMin, RainProbMax, Board, DropOff, Occupation |
| toB | 12 | 1 | TripId, IdExternal, EventDate, EventTime, TimeSlot, Line, Direction, LogicVehicle, Weekday, DayType, Season, FreeDay, TripId.1, Stop, IdExternal.1, EventDate.1, EventTime.1, TimeSlot.1, TemperatureMax, TemperatureMin, RainProbMin, RainProbMax, Board, DropOff, Occupation |

| direction | share_TripId==TripId.1 | share_trips_with_arrival_time_increasing_in_stop_order | n_trips |
|---|---|---|---|
| toA | 1.0000 | 0.9920 | 18029 |
| toB | 1.0000 | 0.9878 | 17864 |

| direction | subset | n_consecutive_pairs | % Occ == prevOcc+Board-DropOff | % same, calc clipped at 0 | n_first_stop_visits | % first stop: Occ == Board-DropOff |
|---|---|---|---|---|---|---|
| toA | raw (all visits of direction) | 215266 | 97.44 | 99.11 | 14539 | 26.25 |
| toA | cleaned (pipeline, normal days) | 153123 | 97.55 | 99.72 | 10336 | 27.48 |
| toB | raw (all visits of direction) | 164085 | 96.06 | 98.33 | 14581 | 28.44 |
| toB | cleaned (pipeline, normal days) | 116428 | 96.55 | 99.63 | 11132 | 28.29 |

| direction | first_date | last_date | n_distinct_dates |
|---|---|---|---|
| toA | 2025-07-01 | 2026-02-23 | 238 |
| toB | 2025-07-01 | 2026-02-23 | 238 |


Set of dates identical in both folders: **True**