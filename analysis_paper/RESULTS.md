# RESULTS — análisis de datos para la sección «Data analysis methodology» (E01)

Todo el código está en `analysis_paper/scripts/` (se ejecuta en este orden: `t0_t1.py`, `t2.py`, `fits.py`, `t3_t7.py`, `t4_t5.py`, `t8_t9.py`, `t10_heavy.py`, `t10.py`, `build_results.py`). No se ha modificado el pipeline ni los datos. Tablas en `tables/`, figuras (PDF vectorial) y CSV de cada figura en `figures/`.

## Resumen ejecutivo (leer primero)

1. **Corte de ocupación.** Todo este informe usa `Occupation < 80` (el corte pedido y el que dice el artículo). **Ojo:** la función del repositorio (`DATOS/src/generate_gaussian.py:477`) usa `< 75`, y son los resultados con 75, no con 80, los que reproducen *exactamente* las cifras publicadas: con `<75` salen 90,60 % (subidas toA), 94,39 % y 88,60 % (ocupación) y 95,49 % (tiempos toA) y los tipos de distribución de subidas coinciden en 475/475 combinaciones con `DATOS/src/input_data_E01_toA.csv`/`_toB.csv`; con `<80` salen 90,98 %, 94,74 %, 87,28 % y 95,86 %, y los tipos coinciden en 469/475. Es decir, el artículo y el simulador parecen calibrados con `<75`. Las cifras de bajadas y de tiempos toB (93,61 %, 90,91 %, 90,43 %) no cambian con el corte.
2. **Defectos del notebook que afectan a cifras del artículo:**
   - En `final_analysis_board_dropoff.ipynb` (celdas 6 y 8, `if is_normal or neg_bin or geom:`) las variables `neg_bin` y `geom` son *diccionarios*, siempre verdaderos. Las 19 franjas de la parada terminal 2646 (toA) y 5727 (toB) cuentan como «no rechazadas» sin serlo. Con `<75` (que reproduce lo publicado) el 90,60 % de subidas hacia Cibeles es (222+19)/266; con `<80` es (223+19)/266 = 90,98 %, y con el resultado real de 2646 sería **90,23 %** (240/266). Las cifras de bajadas (93,61 % y 90,91 %) tienen la misma estructura (+19 combinaciones). El código que las generó **no está en el repositorio** (en la celda final el bloque de bajadas está comentado).
   - La normalidad de los conteos se contrasta con asimetría/curtosis (`fussion_gauss.py:40`), una prueba muy permisiva; el test de dispersión rechaza equidispersión en el **98,7 %** de las combinaciones de subidas y el **95,1 %** de bajadas.
   - En 245 de 1.016 combinaciones MAD = 0 y `remove_outliers_mad` no elimina nada.
   - `test_negative_binomial` devuelve NaN (y por tanto «rechazada») en 133 combinaciones y `test_geometric` en 180 de 1016, por errores de implementación del agrupamiento y de los grados de libertad (Tarea 6.1). Corregirlos cambia la distribución elegida en 7–12 de 940 combinaciones (0,7–1,3 %); ver Tarea 6.1.
   - Las bajadas del simulador *actual* no usan normal/NB/geométrica sino beta-binomial/binomial (`DATOS/src/alighting_params_*.csv`, `DROPOFFS_BETA.ipynb`). Las cifras de bajadas del artículo describen un ajuste anterior.
   - Los rechazos de la validación de ocupación **no** se concentran solo en la última franja: 24 de 44 están en las paradas terminales (2646/5727), que el texto dice excluir (la tabla las incluye: N=285 y 228).
3. **Cifras del texto que no se confirman:** «un registro eliminado cada dos días por parada» (da 0,92 registros por día y parada; Tarea 1.4); reparto 62,4/23,9/13,7 % (da 62,2/24,5/13,3 % mezclando subidas y bajadas con el conjunto de paradas del notebook; solo subidas: 56,4/32,4/11,2 %; Tarea 3.4). **Se confirman:** −4,4 % de bajadas de menos (da −4,39 %, Tarea 4.2), horas punta (8 h y 18 h) y, con matices (ver punto 1), la tabla de no rechazo: con `<80` las filas de bajadas y de tiempos toB coinciden, pero no las de subidas, ocupación ni tiempos toA.

---

## Tarea 0. Estructura de los CSV y enlace entre paradas

**Cómo:** `scripts/t0_t1.py` (lectura con `pd.read_csv` de cada CSV; filtro por `Direction`). Datos: `DATOS/data/E01_toA/NEW` (15 CSV, uno por parada) y `DATOS/data/E01_toB` (12 CSV).

**0.1 Columnas.** Los 15 CSV de toA comparten un único esquema; los 12 de toB, también (mismo esquema que toA). Son 25 columnas; pandas renombra las repetidas con `.1`:
`TripId, IdExternal, EventDate, EventTime, TimeSlot, Line, Direction, LogicVehicle, Weekday, DayType, Season, FreeDay` (**tabla de salidas desde terminal**: fecha, hora y franja de salida de la expedición) + `TripId.1, Stop, IdExternal.1, EventDate.1, EventTime.1, TimeSlot.1, TemperatureMax, TemperatureMin, RainProbMin, RainProbMax, Board, DropOff, Occupation` (**tabla de llegadas a parada**). Es decir, **el enlace ya está reconstruido en cada CSV** (una fila = una visita a una parada con los datos de salida de su expedición). Cada CSV contiene ambos sentidos; hay que filtrar por `Direction` (2 = toA, 1 = toB), como hace `clean_dataframe`. Las paradas terminales (2646, 5727) aparecen en ambas carpetas.

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

**0.2 Identificador y orden.** Identificador de expedición: `TripId` (idéntico a `TripId.1` en el 100 % de filas). **No hay columna con el orden de la parada**. Lo obtengo de las listas fijas del modelo, `GAMA/src/TEST_MOBILITY/models/mobility_performance.gaml:195` (`stopNums_toA`) y `:197` (`stopNums_toB`): toA = 2646, 562, 4090, 4188, 5939, 3995, 3991, 3903, 2539, 2535, 1929, 4032, 5360, 82, 5727; toB = 5727, 81, 1167, 2538, 3929, 3990, 3994, 5938, 4187, 2964, 649, 2646 (las mismas listas están en `analysis_time_between_stops.ipynb`, celdas 2 y 17). La hora de llegada crece con ese orden en el 99,2 % (toA) y 98,8 % (toB) de las expediciones, lo que valida el orden. **Las tareas 4, 5 y 9 son por tanto factibles.** Solo ~52 % (toA) y ~51 % (toB) de las expediciones de días normales tienen las 15/12 paradas registradas («completas»); las tareas 4.x se limitan a esas.

**0.3 Occupation.** **Viene registrada** en los datos (columna `Occupation`); el artículo dice que la calcula el pipeline, pero no he encontrado ningún paso del pipeline que la recalcule. Coincide con «ocupación de la parada anterior + Board − DropOff» en el **97,4–97,5 % (toA)** y **96,1–96,5 % (toB)** de los pares de paradas consecutivas (99,1–99,7 % si se trunca el cálculo a 0). En la primera parada de la expedición, `Occupation = Board − DropOff` solo en el 26–28 % de las visitas (la ocupación incluye pasajeros que siguen a bordo del servicio anterior; ver Tarea 4.6).

**0.4 DayType.** Los laborables son `DayType == "LA"` (los demás: `SA` sábados, `FE` domingos y festivos). `clean_dataframe_advanced(data, "LA")` se llama en: `final_analysis_board_dropoff.ipynb` celda 3 (línea 180 del .ipynb, toA) y celda 7 (línea 870, toB); `analisis_board_dropoff.ipynb` (líneas 85 y 314); `analisis_board_dropoff_toB.ipynb` (líneas 138 y 877); `analysis_time_between_stops.ipynb` (líneas 48 y 1435). En el ajuste de ocupación el filtro está dentro de la función: `analisis_ALL_OCCUPATION.ipynb` línea 45 ss. (`generate_gaussian_per_slot_all_days`: `DayType == "LA"` y `FreeDay == 0`) y `generate_gaussian.py:364-366`. `expected_kpi_extractor.ipynb` (línea 89) tiene una tercera versión de `clean_dataframe` con `<= 80` para los KPI.

**0.5 Dónde se aplica cada limpieza.** Definiciones en `DATOS/src/generate_gaussian.py:475` (`clean_dataframe`) y `:483` (`clean_dataframe_advanced`).
- **Subidas y bajadas:** ambas funciones, en este orden (`final_analysis_board_dropoff.ipynb` líneas 174 y 180; toB 864 y 870). Por tanto `clean_dataframe` también descarta por `Occupation` los registros de subidas/bajadas.
- **Tiempos de viaje:** ambas (`analysis_time_between_stops.ipynb` líneas 47–48 y 1434–1435).
- **Referencia de ocupación:** solo `clean_dataframe` (`analisis_ALL_OCCUPATION.ipynb` líneas 408 y 697); el filtro de días normales lo hace la función de ajuste (`LA` y `FreeDay==0`, más un `Occupation <= 80` redundante).
- **Ventana de fechas:** ambas carpetas cubren exactamente el mismo conjunto de fechas (2025-07-01 a 2026-02-23, 238 fechas): ver tabla arriba.

---

## Tarea 1. Tamaños muestrales y limpieza

**Cómo:** `scripts/t0_t1.py`. Días normales = `DayType=="LA"` y `FreeDay==0` (nivel de día; `DayType` y `FreeDay` son constantes por fecha). La «visita» es una fila del CSV. «Registros eliminados» = los que no pasan las condiciones de `clean_dataframe`/`clean_dataframe_advanced` (conteos por condición calculados con las mismas comparaciones; condiciones solapadas se cuentan en cada una y se da el total de únicos). La cota de ocupación es `Occupation < 80` (`clean_dataframe` con el corte del pipeline original; `common.py` define esa versión sin tocar el repositorio).

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

#### Variantes por condición (registros / (días × paradas)), días normales

| direction | condition (alone) | records | days*stops | records per day-stop |
|---|---|---|---|---|
| toA | Occupation<0 | 1016 | 2370 | 0.4287 |
| toA | Occupation>=80 | 843 | 2370 | 0.3557 |
| toA | Board/DropOff <0 or >=80 | 30 | 2370 | 0.0127 |
| toB | Occupation<0 | 1547 | 1896 | 0.8159 |
| toB | Occupation>=80 | 479 | 1896 | 0.2526 |
| toB | Board/DropOff <0 or >=80 | 24 | 1896 | 0.0127 |

**1.4 Conclusión.** Registros eliminados / (días × paradas) = **0,92** (toA+toB), es decir un registro eliminado por parada cada **1,09 días**. **No se confirma «un registro cada dos días» (0,5)**; ninguna de las variantes por condición lo da (la más cercana, `Occupation<0` sola, da ≈0,6). Si el cálculo del texto usó otro denominador (p. ej. los 238 días de la ventana, que da 0,93) tampoco coincide.

**Notas 1.5.** Subidas: n = número de días en que la parada tiene algún registro limpio (152–158), porque el pipeline suma por día y franja y añade 0 si ese día no hubo autobús (`final_analysis_board_dropoff.ipynb` celda 3: bucle `for day in unique_days` con `list_boards.append(sum(...))`). Bajadas: una por llegada de autobús; ocupación: una por visita (franja de salida); tiempos de viaje: pares de visitas de la misma expedición en paradas consecutivas con ambas llegadas en la misma franja. Las combinaciones con 0 observaciones en toB (franja 5) son las que no tienen servicio a esa hora.

---

## Tarea 2. Perfil de carga por parada

**Cómo:** `scripts/t2.py`, sobre datos tras `clean_dataframe` + `clean_dataframe_advanced("LA")` (`cleaned(d)` en `common.py`). Franja = `TimeSlot.1` (momento de servicio) para las tres magnitudes; la ocupación es el campo registrado tras la parada.

Peak hour (slot = hour of service, TimeSlot.1) by mean total boardings per normal day: toA **8**, toB **18**.

Top-4 hours toA:

| direction | slot | mean_total_boardings_per_day |
|---|---|---|
| toA | 8 | 421.5 |
| toA | 7 | 398.8 |
| toA | 17 | 345.5 |
| toA | 18 | 337.0 |

Top-4 hours toB:

| direction | slot | mean_total_boardings_per_day |
|---|---|---|
| toB | 18 | 397.6 |
| toB | 15 | 380.1 |
| toB | 19 | 373.1 |
| toB | 14 | 368.5 |

Paper claim: 7-9 h towards Cibeles, after 17 h towards La Peseta -> matches: toA yes, toB yes.

| direction | slot | stop | order | n_visits | board_mean | board_q25 | board_q75 | dropoff_mean | dropoff_q25 | dropoff_q75 | occ_mean | occ_q25 | occ_q75 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| toA | 8 | 2646 | 1 | 754 | 10.1 | 5.0 | 13.0 | 0.0 | 0.0 | 0.0 | 8.7 | 4.0 | 11.0 |
| toA | 8 | 562 | 2 | 824 | 4.5 | 2.0 | 6.0 | 0.2 | 0.0 | 0.0 | 13.1 | 8.0 | 16.0 |
| toA | 8 | 4090 | 3 | 816 | 6.4 | 3.0 | 8.0 | 2.2 | 0.0 | 1.2 | 17.2 | 11.0 | 22.0 |
| toA | 8 | 4188 | 4 | 817 | 1.2 | 0.0 | 2.0 | 0.8 | 0.0 | 1.0 | 18.0 | 12.0 | 23.0 |
| toA | 8 | 5939 | 5 | 853 | 2.7 | 1.0 | 4.0 | 0.2 | 0.0 | 0.0 | 20.6 | 14.0 | 26.0 |
| toA | 8 | 3995 | 6 | 844 | 17.2 | 11.0 | 22.0 | 0.9 | 0.0 | 1.0 | 37.3 | 27.0 | 48.0 |
| toA | 8 | 3991 | 7 | 861 | 6.9 | 4.0 | 9.0 | 0.9 | 0.0 | 1.0 | 43.1 | 31.0 | 56.0 |
| toA | 8 | 3903 | 8 | 875 | 10.0 | 6.0 | 13.0 | 7.8 | 3.0 | 11.0 | 45.4 | 33.0 | 58.0 |
| toA | 8 | 2539 | 9 | 861 | 7.7 | 4.0 | 11.0 | 2.9 | 1.0 | 4.0 | 49.8 | 38.0 | 64.0 |
| toA | 8 | 2535 | 10 | 865 | 4.6 | 2.0 | 6.0 | 2.6 | 1.0 | 4.0 | 52.8 | 43.0 | 66.0 |
| toA | 8 | 1929 | 11 | 868 | 3.1 | 1.0 | 4.2 | 4.2 | 2.0 | 6.0 | 52.8 | 44.0 | 64.0 |
| toA | 8 | 4032 | 12 | 843 | 1.1 | 0.0 | 2.0 | 4.4 | 2.0 | 6.0 | 50.0 | 41.0 | 61.0 |
| toA | 8 | 5360 | 13 | 853 | 2.0 | 0.0 | 3.0 | 11.7 | 8.0 | 15.0 | 40.7 | 32.0 | 51.0 |
| toA | 8 | 82 | 14 | 826 | 1.7 | 0.0 | 2.0 | 13.4 | 10.0 | 17.0 | 29.2 | 22.0 | 36.0 |
| toA | 8 | 5727 | 15 | 726 | 0.2 | 0.0 | 0.0 | 26.6 | 20.0 | 34.0 | 4.4 | 0.0 | 6.0 |
| toB | 18 | 5727 | 1 | 680 | 26.6 | 16.8 | 37.0 | 0.1 | 0.0 | 0.0 | 25.7 | 16.8 | 36.0 |
| toB | 18 | 81 | 2 | 662 | 20.1 | 13.0 | 27.0 | 0.8 | 0.0 | 1.0 | 47.2 | 34.0 | 63.0 |
| toB | 18 | 1167 | 3 | 596 | 9.5 | 4.0 | 14.0 | 0.7 | 0.0 | 1.0 | 54.7 | 42.0 | 69.0 |
| toB | 18 | 2538 | 4 | 699 | 4.5 | 2.0 | 6.0 | 7.8 | 5.0 | 10.0 | 50.6 | 39.0 | 64.0 |
| toB | 18 | 3929 | 5 | 689 | 17.5 | 11.0 | 23.0 | 15.2 | 10.0 | 20.0 | 51.7 | 42.0 | 64.0 |
| toB | 18 | 3990 | 6 | 717 | 3.3 | 1.0 | 5.0 | 5.8 | 4.0 | 8.0 | 48.0 | 38.0 | 61.0 |
| toB | 18 | 3994 | 7 | 714 | 5.3 | 2.0 | 8.0 | 10.3 | 7.0 | 14.0 | 43.1 | 31.0 | 55.0 |
| toB | 18 | 5938 | 8 | 709 | 0.4 | 0.0 | 0.0 | 2.3 | 1.0 | 3.0 | 41.0 | 29.0 | 53.0 |
| toB | 18 | 4187 | 9 | 698 | 4.9 | 1.0 | 7.0 | 28.1 | 17.0 | 37.8 | 17.6 | 12.0 | 23.0 |
| toB | 18 | 2964 | 10 | 715 | 0.4 | 0.0 | 0.0 | 4.8 | 3.0 | 7.0 | 12.8 | 7.0 | 17.5 |
| toB | 18 | 649 | 11 | 747 | 0.1 | 0.0 | 0.0 | 2.6 | 1.0 | 4.0 | 10.0 | 5.0 | 14.0 |
| toB | 18 | 2646 | 12 | 744 | 0.5 | 0.0 | 0.0 | 7.1 | 4.0 | 10.0 | 3.5 | 0.0 | 5.0 |

**Figuras:** `figures/fig_load_profile.pdf` (página completa, 17 cm, datos en `fig_load_profile_data.csv`/`tables/t2_peak_stop_profile.csv`) y `figures/fig_hourly_profile.pdf` (1 columna, 8,5 cm, datos en `fig_hourly_profile_data.csv`). Sin título; cada panel lleva una etiqueta corta con el sentido y la hora punta (se puede quitar si el pie de LaTeX lo cubre). Paleta Okabe–Ito, tipografía serif de 8 pt. **Observación:** en el panel de toA la ocupación en la parada terminal 5727 (4,4 pasajeros tras la parada) y en 2646 es poco fiable (Tarea 4.6).

---

## Tarea 3. Dispersión de los conteos

**Cómo:** `scripts/fits.py` y `scripts/t3_t7.py`. Reutiliza `remove_outliers_mad`, `is_normal_simplified`, `test_negative_binomial`, `test_geometric` y `select_by_aic` (cargadas literalmente de `final_analysis_board_dropoff.ipynb` celda 4 y de `fussion_gauss.py`). Conjunto de paradas como en el notebook: bucle principal (sin 2646 ni 5727) más la terminal de origen para subidas (2646 en toA, 5727 en toB) y la terminal de destino para bajadas (5727 en toA, 2646 en toB). Datos: subidas = suma diaria por parada y franja (`TimeSlot.1`), bajadas = valor por llegada, tras MAD. Test de dispersión: (n−1)·s²/x̄ frente a χ²(n−1), bilateral, α = 0,05; s² con ddof=1. Se excluyen las combinaciones con n<2 o media 0.

### 3.1-3.3 Dispersion index (boardings per stop-hour, alightings per bus arrival; after MAD removal)

| direction | variable | n_combinations | pct_reject_overdisp | pct_reject_underdisp | disp_median | disp_q25 | disp_q75 | pct_disp_gt1 | pct_reject_equidisp_total |
|---|---|---|---|---|---|---|---|---|---|
| toA | alightings | 266 | 94.36 | 0.00 | 1.78 | 1.38 | 2.37 | 98.12 | 94.36 |
| toA | boardings | 266 | 98.87 | 0.00 | 3.37 | 2.24 | 5.55 | 100.00 | 98.87 |
| toB | alightings | 199 | 95.98 | 0.00 | 1.82 | 1.43 | 2.55 | 98.99 | 95.98 |
| toB | boardings | 199 | 98.49 | 0.00 | 3.40 | 2.07 | 7.24 | 98.99 | 98.49 |

Combinations excluded (n<2 or mean=0, test undefined):

| direction | variable | excluded_combos(n<2 or mean=0) |
|---|---|---|
| toB | alightings | 10 |
| toB | boardings | 10 |

By variable (both directions pooled):

| variable | n | pct_over | pct_under | disp_med |
|---|---|---|---|---|
| alightings | 465 | 95.05 | 0.00 | 1.81 |
| boardings | 465 | 98.71 | 0.00 | 3.38 |

### 3.4 Selected distributions (paper: normal 62.4 %, NB 23.9 %, geometric 13.7 %)

| direction | variable | n_cells | n_normal | n_negbin | n_geom | pct_normal | pct_negbin | pct_geom |
|---|---|---|---|---|---|---|---|---|
| all | all | 940 | 585 | 230 | 125 | 62.2 | 24.5 | 13.3 |
| toA | alightings | 266 | 172 | 51 | 43 | 64.7 | 19.2 | 16.2 |
| toA | boardings | 266 | 159 | 87 | 20 | 59.8 | 32.7 | 7.5 |
| toB | alightings | 199 | 145 | 25 | 29 | 72.9 | 12.6 | 14.6 |
| toB | boardings | 209 | 109 | 67 | 33 | 52.2 | 32.1 | 15.8 |
| all | alightings | 465 | 317 | 76 | 72 | 68.2 | 16.3 | 15.5 |
| all | boardings | 475 | 268 | 154 | 53 | 56.4 | 32.4 | 11.2 |
| toA | all | 532 | 331 | 138 | 63 | 62.2 | 25.9 | 11.8 |
| toB | all | 408 | 254 | 92 | 62 | 62.3 | 22.5 | 15.2 |

Cells where all three candidates were rejected (lowest-AIC fallback):

| direction | variable | sum | size |
|---|---|---|---|
| toA | alightings | 18 | 266 |
| toA | boardings | 26 | 266 |
| toB | alightings | 19 | 209 |
| toB | boardings | 27 | 209 |



**Lectura:** la equidispersión se rechaza casi siempre y siempre por sobredispersión; ninguna combinación infradispersa. Mediana del índice: 3,4 (subidas) y 1,8 (bajadas). Esto contrasta con la selección de la normal en ~62 % de los casos y se explica porque el test de normalidad usado (asimetría/curtosis) es permisivo (Tarea 6.1).

---

## Tarea 4. Balance de subidas y bajadas

**Cómo:** `scripts/t4_t5.py`. Una expedición es «completa» si tiene todas las paradas del sentido. Subconjuntos: S0 todas las visitas de días normales sin limpiar; S1 visitas que pasan la limpieza (expediciones parciales); S2 expediciones completas sin limpiar; **S3 expediciones completas en las que ninguna visita es eliminada por la limpieza del pipeline (`Occupation<80`)**. Ocupación acumulada = suma acumulada de Board − DropOff desde 0 a lo largo del orden de paradas. Diferencia por expedición = subidas − bajadas.

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

**Respuestas:**
- **4.2** Con `Occupation<80` (S3, con terminales): **−4,39 %** total (toA −5,03 %, toB −3,68 %): **confirma el «4,4 % de bajadas de menos»**. Sin limpiar (S0/S2) las sumas están dominadas por valores absurdos de las columnas (millones de pasajeros) y no son interpretables.
- **4.3** Mediana por expedición (S3, con terminales): +3 (toA) y +2 (toB) subidas más que bajadas; 70,5 % (toA) y 64,6 % (toB) de las expediciones tienen más subidas que bajadas.
- **4.4** Ocupación calculada en la última parada (S3): mediana 3 (toA) y 2 (toB), media 3,6 y 2,5, rango −58…75 y −49…93. La ocupación registrada en la última parada tiene mediana 1.
- **4.5** Antes de la limpieza, la ocupación acumulada se vuelve negativa en alguna parada en el **22,2 % (toA)** y **28,3 % (toB)** de las expediciones completas; con la ocupación *registrada*, en el 2,3 % y 5,5 % de todas las expediciones. Tras la limpieza, la acumulada sigue siendo negativa en 21,9 % y 25,9 %: la limpieza elimina valores absurdos pero no la deriva.
- **4.6** **El desequilibrio agregado depende de incluir las terminales**: sin ellas sale **−19,3 % (toA) y +20,5 % (toB)** (S3), de signo opuesto en cada sentido, frente a −5,0 % y −3,7 % con ellas. Las terminales concentran las mayores magnitudes (toA, subconjunto S3 con `Occupation<80`: ver `tables/t4_per_stop_net.csv`), así que no se puede atribuir el −4,4 % a las terminales ni al resto de la ruta por separado con estos datos. En la parada de origen, `Occupation = Board − DropOff` solo en el 26–28 % de las visitas (Tarea 0.3), coherente con el comentario del artículo sobre el cambio de expedición mal registrado.

---

## Tarea 5. Relación entre bajadas y carga

**Cómo:** `scripts/t4_t5.py`. Carga a la llegada = `Occupation` de la parada anterior de la misma expedición (visitas consecutivas, ambas tras la limpieza). Franja = `TimeSlot.1`. Correlaciones con `scipy.stats.pearsonr/spearmanr` por combinación parada×franja con n≥3 y varianza no nula; «significativa positiva» = p<0,05 y r>0 (sin corrección por comparaciones múltiples).

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

**Lectura:** las bajadas están **fuertemente ligadas a la carga**: correlación mediana 0,40 (toA) y 0,53 (toB), positiva y significativa en el 92 % y 95 % de las combinaciones. Esto choca con el supuesto del simulador de que las bajadas se sortean por llegada **independientemente de la carga** (artículo, sección 3.2). La fracción que baja varía mucho por parada (≈2–5 % en las paradas iniciales, ≈24–53 % en las paradas de intercambio, ≈100 % en la terminal final). Nota: en las paradas terminales la fracción puede superar 1 (la carga a la llegada registrada es menor que las bajadas).

---

## Tarea 6. Detalles metodológicos (lectura del código)

Referencias a `.ipynb` con la línea del JSON y la celda. Salvo indicación, las funciones están en `DATOS/src/final_analysis_board_dropoff.ipynb` celda 4.

**6.1 Tests de bondad de ajuste.**
- **Normal:** *no* es chi-cuadrado. `is_normal_simplified` (`DATOS/src/fussion_gauss.py:40-72`) es un test de asimetría y curtosis: z = asimetría/√(6/n) y curtosis exceso/√(24/n); con n<50 se acepta si |z|≤1,96; con 50≤n<300 si |z|≤3,29; con n≥300 se abandonan los z y se acepta si |asimetría|≤2 y |curtosis exceso|+3≤7 (umbrales absolutos, sin nivel de significación). Parámetros: media muestral y desviación típica poblacional (`central_moment(·,2)`, ddof=0) en el test; `select_by_aic` usa media y desviación ddof=1. `test_normal_chi2` (línea 327) está definida pero **no se llama** en ninguna celda.
- **Binomial negativa:** `test_negative_binomial` (línea 279): chi-cuadrado de Pearson, α=0,05, parámetros por **método de momentos** (p = media/varianza, r = media·p/(1−p)); si varianza ≤ media se rechaza directamente. Clases: cada valor entero distinto observado; esperados = n·pmf. Agrupamiento: los valores con esperado <5 se juntan en **una sola clase final** (se añade siempre, aunque esté vacía). Grados de libertad: clases − 1 − 2 (mín. 1). **Fallo detectado:** si todos los esperados son ≥5 la clase final queda con 0/0, el estadístico es NaN y `p_value > alpha` es falso: la candidata se rechaza. Ocurre en 133 de 1016 combinaciones. Ejemplos impresos y efecto de corregirlo: sección «6.1 bis» más abajo.
- **Geométrica:** `test_geometric` (línea 232): chi-cuadrado, α=0,05, **máxima verosimilitud** (p = 1/(1+media)), clases = valores distintos, esperados n·(1−p)^k·p, agrupamiento de esperados <5 en una clase (solo si existe alguna), gl = clases − 1 − 1. **Fallo detectado:** si tras agrupar quedan ≤2 clases (p. ej. todas con esperado <5, o solo valores 0 y 1) gl ≤ 0 y el p-valor es NaN (se rechaza): 180 de 1016 combinaciones.
- Las clases no incluyen los enteros no observados entre medias, por lo que la distribución esperada no suma n.

**6.2 AIC** (`select_by_aic`, línea 499; `study_abnormal`, línea 422): AIC = −2·log-verosimilitud + 2k con k = 1 (geométrica, línea 543), 2 (binomial negativa, línea 531) y 2 (normal, línea 519). Log-verosimilitud: geométrica `log((1−p)^x·p)` con MLE; binomial negativa `nbinom.logpmf` con **parámetros por momentos** (no MLE); normal `norm.logpdf` (una densidad, no una masa) con σ ddof=1. El AIC de la normal (densidad) y el de las discretas (masa) no son estrictamente comparables. Entre las candidatas no rechazadas gana el AIC mínimo; si las tres se rechazan se evalúan las tres y se elige igualmente el mínimo (`study_abnormal`). Resultado de esa rama: 27+26 combinaciones de subidas y 18+19 de bajadas (Tarea 3.4).

**6.3 Normal → conteo.**
- GAML (`GAMA/src/TEST_MOBILITY/models/mobility_performance.gaml`): `sample_distribution` (línea 133) devuelve `max(0.0, gauss(μ,σ))` (línea 136), es decir **recorta a 0 primero**. Para bajadas, `infer_dropoffs` (línea 160) aplica después `int(floor(...))` (**trunca**; no redondea). Para subidas el valor (tasa horaria) se usa como `float` sin redondear (líneas 853, 857, 865).
- C (`C_REWRITE/src/`): `sample_normal` (`math/distributions/normal.c:29`) devuelve μ+σ·Z **sin recortar**; en bajadas (`engine/simulation.c:55-58`) se recorta a [0, `MAX_OCCUPANCY`=80] y luego `(u16)ret_val` trunca (mismo orden que GAML, con cota superior añadida). Para subidas la tasa sale de `.random(...)` sin recorte en `simulation.c:187-192, 215-220, 261, 292` y entra en `linear_conservative_reconstruction` (`math/math_utils.c:7-57`), que interpola linealmente sin recortar; **en C no hay recorte a 0 de las tasas de subida** (ni en `sample_normal` ni en la reconstrucción), a diferencia del GAML, que sí recorta (`max(0.0, …)`).
- Nota (regla 5): el GAML del repositorio lee `../includes/INPUTS/old_input_data_E01_toA.csv` (línea 181); esos ficheros están en `BASE_DATA/`, no en `GAMA/.../INPUTS/`, donde hay `input_data_E01_*.csv` (solo subidas, sin columna `DataType`) y `alighting_params_*.csv` (beta-binomial). No he podido determinar con cuál se ejecutó el artículo.

**6.4 MAD** (`remove_outliers_mad`, línea 391): umbral **3** (`threshold=3`) y **sí se aplica la constante 1,4826** (`mad_scaled = 1.4826 * mad`, línea 410); se elimina lo que cumple |x − mediana|/(1,4826·MAD) > 3. Si MAD = 0 la función devuelve los datos sin tocarlos: ocurre en 245 de 1.016 combinaciones (24 %), en conteos con muchos valores repetidos. (Para ocupación y tiempos de viaje se usa otro método, ESD generalizado, `estimate_outliers`, `generate_gaussian.py:195`.)

**6.5 Capacidad.** El simulador usa **80** pasajeros: `mobility_performance.gaml:1191` (`int max_passengers <- 80;`, comentario «All buses have the same maximum capacity») y `C_REWRITE/src/agents/bus/bus.h:14` (`#define MAX_OCCUPANCY 80`); es un valor fijado en el código (no hay fuente de datos en el repositorio). Con el corte `Occupation < 80` **la limpieza elimina todas las visitas con ocupación ≥ capacidad**. Visitas eliminadas por `Occupation ≥ 80` (sobre las visitas de días normales que pasan el resto de filtros):

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

De las 832 visitas eliminadas en toA, **151 tienen exactamente 80**; de las 470 de toB, **55** (el resto supera 80). El desglose por franja está en la tabla anterior y en `tables/t6_5_removed_by_occupation_cut.csv` (también con la definición de franja de servicio). La franja 5 y las franjas punta de la mañana en toA (5–7 h) concentran los mayores porcentajes (1,2–1,9 %).

**6.6 Franjas.** Son horarias, de 5 a 23 (19 franjas): `timeslot = [5,…,23]` (`final_analysis_board_dropoff.ipynb` celda 3) y en el simulador `TimeSlot <- 5 + int(total_minutes / 60)` (`mobility_performance.gaml:799`). En los datos `TimeSlot` es la hora de `EventTime` y `TimeSlot.1` la hora de `EventTime.1` (comprobado: 100 % de coincidencia). **Entradas** (subidas, bajadas, tiempos): franja del momento de servicio, `TimeSlot.1` (`final_analysis_board_dropoff.ipynb` líneas 191 y 881; `analysis_time_between_stops.ipynb` líneas 1216-1217 (toA) y 1476-1477 (toB)). **Referencia de validación** (ocupación): franja de salida desde terminal, `TimeSlot` (`generate_gaussian.py:296, 407, 442` y `analisis_ALL_OCCUPATION.ipynb`, función de la línea 45). Ambas definiciones confirmadas.

### 6.1 bis. Casos con p-valor NaN y efecto de corregirlos (`scripts/nan_and_bug.py`)

Las réplicas impresas de los dos tests coinciden con `test_negative_binomial` y `test_geometric` en las 1.016 combinaciones. Corrección aplicada: no crear la clase final vacía (la clase agrupada solo se añade si algún esperado es <5) y exigir al menos 1 grado de libertad; si gl<1 el test no es aplicable y el candidato se mantiene o se descarta (dos políticas).

Replica check: 0 of 1016 cells differ between the printed-detail replica and the pipeline functions.

### 2.a Negative binomial: NaN p-value (all expected >= 5 -> empty final class, 0/0)

**NB, toA, alightings, stop 562, slot 14**
- n = 722 (after MAD); mean = 0.152; var = 0.154
- observed values (sorted, first 40): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ...
- classes (unique values): [0, 1, 2]
- observed frequencies:    [621, 92, 9]
- expected frequencies:    [620.56, 93.36, 7.61]
- pooled observed / expected (as built by the function): [621, 92, 9, 0] / [620.56, 93.36, 7.61, 0.0]
- degrees of freedom = 1; statistic = nan; p-value = nan
- `p_value > alpha` -> False  => candidate treated as REJECTED

**NB, toB, alightings, stop 649, slot 6**
- n = 350 (after MAD); mean = 1.489; var = 1.763
- observed values (sorted, first 40): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ...
- classes (unique values): [0, 1, 2, 3, 4, 5]
- observed frequencies:    [103, 88, 81, 50, 19, 9]
- expected frequencies:    [89.29, 112.2, 79.24, 41.42, 17.85, 6.71]
- pooled observed / expected (as built by the function): [103, 88, 81, 50, 19, 9, 0] / [89.29, 112.2, 79.24, 41.42, 17.85, 6.71, 0.0]
- degrees of freedom = 4; statistic = nan; p-value = nan
- `p_value > alpha` -> False  => candidate treated as REJECTED

### 2.b Geometric: NaN p-value (df <= 0)

**Geometric, toA, boardings, stop 562, slot 5**
- n = 158 (after MAD); mean = 31.589; var = 176.193
- observed values (sorted, first 40): [0, 0, 0, 0, 0, 0, 0, 5, 6, 6, 8, 10, 11, 11, 11, 12, 12, 12, 13, 13, 15, 16, 16, 16, 18, 18, 18, 19, 20, 21, 21, 21, 22, 23, 23, 24, 24, 24, 25, 25] ...
- classes (unique values): [0.0, 5.0, 6.0, 8.0, 10.0, 11.0, 12.0, 13.0, 15.0, 16.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 54.0, 55.0, 56.0, 58.0]
- observed frequencies:    [7, 1, 2, 1, 1, 3, 3, 2, 1, 3, 3, 1, 1, 3, 1, 2, 3, 4, 6, 6, 7, 4, 2, 7, 1, 5, 5, 6, 4, 3, 5, 4, 3, 3, 6, 9, 2, 7, 6, 5, 1, 2, 1, 2, 1, 1, 1, 1]
- expected frequencies:    [4.85, 4.15, 4.02, 3.78, 3.55, 3.44, 3.34, 3.23, 3.04, 2.94, 2.77, 2.68, 2.6, 2.52, 2.44, 2.37, 2.29, 2.22, 2.16, 2.09, 2.03, 1.96, 1.9, 1.84, 1.79, 1.73, 1.68, 1.63, 1.58, 1.53, 1.48, 1.44, 1.39, 1.35, 1.31, 1.27, 1.23, 1.19, 1.16, 1.12, 1.09, 1.05, 1.02, 0.99, 0.9, 0.87, 0.85, 0.8]
- pooled observed / expected (as built by the function): [158] / [98.67]
- degrees of freedom = -1; statistic = 35.676680835016484; p-value = nan
- `p_value > alpha` -> False  => candidate treated as REJECTED

**Geometric, toA, alightings, stop 562, slot 5**
- n = 354 (after MAD); mean = 0.006; var = 0.006
- observed values (sorted, first 40): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ...
- classes (unique values): [0.0, 1.0]
- observed frequencies:    [352, 2]
- expected frequencies:    [352.01, 1.98]
- pooled observed / expected (as built by the function): [352, 2] / [352.01, 1.98]
- degrees of freedom = 0; statistic = 0.00025428054703856095; p-value = nan
- `p_value > alpha` -> False  => candidate treated as REJECTED

**Geometric, toB, boardings, stop 81, slot 5**
- n = 158 (after MAD); mean = 0.000; var = 0.000
- observed values (sorted, first 40): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ...
- classes (unique values): [0.0]
- observed frequencies:    [158]
- expected frequencies:    [158.0]
- pooled observed / expected (as built by the function): [158] / [158.0]
- degrees of freedom = -1; statistic = 0.0; p-value = nan
- `p_value > alpha` -> False  => candidate treated as REJECTED

### 2.c Effect of correcting the two tests on the distribution selection (cells of the notebook stop set)

Correction: no empty final class (the pooled class is added only if some expected < 5); at least 1 degree of freedom is required, otherwise the test is not applicable and the candidate is either kept or discarded (two policies).

| policy | cells | selection_changes | nb_verdict_changes | geom_verdict_changes | pct_selection_changes |
|---|---|---|---|---|---|
| untestable -> not rejected | 940 | 12 | 8 | 136 | 1.28 |
| untestable -> rejected | 940 | 7 | 20 | 0 | 0.74 |

| policy | direction | variable | cells | selection_changes | nb_verdict_changes | geom_verdict_changes | any_pass_changes |
|---|---|---|---|---|---|---|---|
| untestable -> not rejected | toA | alightings | 266 | 7 | 6 | 3 | 2 |
| untestable -> not rejected | toA | boardings | 266 | 2 | 0 | 63 | 1 |
| untestable -> not rejected | toB | alightings | 199 | 2 | 1 | 1 | 0 |
| untestable -> not rejected | toB | boardings | 209 | 1 | 1 | 69 | 12 |
| untestable -> rejected | toA | alightings | 266 | 5 | 6 | 0 | 0 |
| untestable -> rejected | toA | boardings | 266 | 0 | 0 | 0 | 0 |
| untestable -> rejected | toB | alightings | 199 | 1 | 1 | 0 | 0 |
| untestable -> rejected | toB | boardings | 209 | 1 | 13 | 0 | 11 |

Transitions (policy 'not rejected'):

| chosen_original | chosen_corrected | n |
|---|---|---|
| GEOMETRICAL | NEGATIVE BINOMIAL | 3 |
| NEGATIVE BINOMIAL | GEOMETRICAL | 1 |
| NORMAL | GEOMETRICAL | 4 |
| NORMAL | NEGATIVE BINOMIAL | 4 |

Transitions (policy 'rejected'):

| chosen_original | chosen_corrected | n |
|---|---|---|
| GEOMETRICAL | NEGATIVE BINOMIAL | 1 |
| NEGATIVE BINOMIAL | GEOMETRICAL | 2 |
| NORMAL | NEGATIVE BINOMIAL | 4 |

### Celda con `if is_normal or neg_bin or geom:` y valor de `neg_bin` y `geom` en una combinación terminal (`scripts/nan_and_bug.py`)

```
#Subir boards de la parada 2646

stop = 2646
data_stop = final_dataframe[final_dataframe["Stop"] == 2646]
_init_stop_counters(stop)

counter_stop_2646_parameters = 0
stop_normal_boards  = 0
stop_normal_dropoffs = 0

for timeslot in timeslots:
    data_boards = data_stop[f"instances_boards_{timeslot}"].iloc[0]
    print(data_boards)
    cleaned_boards, _ = remove_outliers_mad(data_boards)
    is_normal, _, mean, std = is_normal_simplified(cleaned_boards)
    neg_bin = test_negative_binomial(cleaned_boards)
    geom    = test_geometric(cleaned_boards)

    chosen = select_by_aic(
        cleaned_boards,
        candidates_mask={'NORMAL': is_normal, 'NEGATIVE BINOMIAL': neg_bin['is_negbin'], 'GEOMETRICAL': geom['is_geometric']},
        stop=stop, timeslot=timeslot,
        dataframe=dataframe_simulation
    )
    _record('Board', stop, timeslot, chosen)

    if is_normal or neg_bin or geom:
        global_normal_boards += 1
        stop_normal_boards += 1

    counter_parameters += 1
    counter_stop_2646_parameters += 1




with open ("input_data_E01_toA.csv", "w", encoding="utf-8") as f:
    dataframe_simulation.to_csv(f, index=False)

==== same pattern in cell 8 (toB, stop 5727) ====

stop 2646 toA, slot 5: n=158
  is_normal = np.False_  (type bool)
  neg_bin   = {'is_negbin': False, 'reason': 'too few valid bins', 'statistic': 0, 'p_value': 0, 'p_hat': 0, 'r_hat': 0}
  type(neg_bin) = dict, bool(neg_bin) = True
  geom      = {'statistic': np.float64(469.3049779038333), 'p_value': np.float64(nan), 'p_hat': np.float64(0.5429553264604811), 'is_geometric': np.False_, 'df': 0}
  type(geom) = dict, bool(geom) = True
  (is_normal or neg_bin or geom) = {'is_negbin': False, 'reason': 'too few valid bins', 'statistic': 0, 'p_value': 0, 'p_hat': 0, 'r_hat': 0} -> bool True
  real verdicts: neg_bin['is_negbin'] = False, geom['is_geometric'] = False

stop 2646 toA, slot 8: n=157
  is_normal = np.True_  (type bool)
  neg_bin   = {'is_negbin': False, 'reason': 'too few valid bins', 'statistic': 0, 'p_value': 0, 'p_hat': 0, 'r_hat': 0}
  type(neg_bin) = dict, bool(neg_bin) = True
  geom      = {'statistic': np.float64(31.500029643289416), 'p_value': np.float64(nan), 'p_hat': np.float64(0.020780939774983454), 'is_geometric': np.False_, 'df': -1}
  type(geom) = dict, bool(geom) = True
  (is_normal or neg_bin or geom) = np.True_ -> bool True
  real verdicts: neg_bin['is_negbin'] = False, geom['is_geometric'] = False
```

---

## Tarea 7. Efecto de la eliminación de outliers en las colas

**Cómo:** `scripts/fits.py` y `scripts/t3_t7.py` (`remove_outliers_mad`; percentiles con `np.percentile`, interpolación lineal, sobre los mismos datos antes y después).

### 7.1 Observations removed by the MAD rule (threshold 3, scaling 1.4826)

| direction | variable | n_obs_before | n_removed_by_MAD | pct_removed | cells_with_any_removal | n_cells |
|---|---|---|---|---|---|---|
| toA | alightings | 158734 | 2638 | 1.662 | 183 | 266 |
| toA | boardings | 42028 | 581 | 1.382 | 169 | 266 |
| toB | alightings | 122390 | 1892 | 1.546 | 149 | 209 |
| toB | boardings | 32908 | 420 | 1.276 | 108 | 209 |
| all | alightings | 281124 | 4530 | 1.611 | 332 | 475 |
| all | boardings | 74936 | 1001 | 1.336 | 277 | 475 |
| all | all | 356060 | 5531 | 1.553 | 609 | 950 |

### 7.2 Relative change of tail percentiles after MAD removal ((after-before)/before)

| direction | variable | percentile | n_cells_(before>0) | median_rel_diff_% | min_rel_diff_% | max_abs_rel_diff_% | cells_with_cut |
|---|---|---|---|---|---|---|---|
| toA | alightings | 90 | 261 | 0.00 | -28.57 | 28.57 | 83 |
| toA | alightings | 95 | 264 | 0.00 | -41.18 | 41.18 | 124 |
| toA | alightings | 99 | 265 | -10.00 | -61.48 | 61.48 | 174 |
| toA | boardings | 90 | 265 | 0.00 | -50.00 | 50.00 | 113 |
| toA | boardings | 95 | 266 | -0.73 | -50.00 | 50.00 | 142 |
| toA | boardings | 99 | 266 | -4.91 | -76.53 | 76.53 | 166 |
| toB | alightings | 90 | 199 | 0.00 | -33.33 | 33.33 | 66 |
| toB | alightings | 95 | 199 | 0.00 | -41.18 | 41.18 | 97 |
| toB | alightings | 99 | 199 | -7.69 | -55.56 | 55.56 | 131 |
| toB | boardings | 90 | 192 | 0.00 | -50.00 | 50.00 | 85 |
| toB | boardings | 95 | 197 | 0.00 | -47.19 | 47.19 | 92 |
| toB | boardings | 99 | 198 | -2.73 | -63.64 | 63.64 | 106 |

### 7.3 Combinations with the largest cut of the 99th percentile

| direction | variable | stop | slot | n_raw | n_mad_removed | p99_before | p99_after | rel99 |
|---|---|---|---|---|---|---|---|---|
| toA | boardings | 82 | 16 | 158 | 8 | 38.35 | 9.00 | -0.77 |
| toB | boardings | 3990 | 22 | 158 | 10 | 11.00 | 4.00 | -0.64 |
| toA | boardings | 82 | 21 | 158 | 10 | 13.44 | 5.00 | -0.63 |
| toA | alightings | 3991 | 23 | 235 | 12 | 12.98 | 5.00 | -0.61 |
| toB | boardings | 2964 | 15 | 158 | 19 | 10.00 | 4.00 | -0.60 |
| toB | boardings | 3994 | 22 | 158 | 11 | 11.86 | 5.00 | -0.58 |
| toB | boardings | 2964 | 16 | 158 | 22 | 21.29 | 9.00 | -0.58 |
| toA | boardings | 2646 | 23 | 158 | 6 | 10.58 | 4.49 | -0.58 |
| toB | alightings | 5938 | 6 | 406 | 16 | 9.00 | 4.00 | -0.56 |
| toA | boardings | 4032 | 11 | 158 | 19 | 13.15 | 6.00 | -0.54 |
| toB | alightings | 649 | 23 | 420 | 42 | 10.00 | 5.00 | -0.50 |
| toB | alightings | 2964 | 8 | 746 | 67 | 24.00 | 12.00 | -0.50 |
| toA | alightings | 4188 | 14 | 730 | 64 | 11.00 | 6.00 | -0.45 |
| toB | alightings | 2964 | 23 | 425 | 27 | 12.76 | 7.00 | -0.45 |
| toA | alightings | 4090 | 15 | 692 | 47 | 9.09 | 5.00 | -0.45 |
| toA | alightings | 3991 | 14 | 768 | 29 | 9.00 | 5.00 | -0.44 |

**Lectura:** la regla elimina ≈1,5 % de las observaciones (1,3 % en subidas, 1,6 % en bajadas); el p99 baja en mediana un 2,7–10 % según variable y sentido, hasta un 77 % en la combinación más afectada (toA, subidas, parada 82, 16 h: p99 38,35 → 9). Los percentiles 90 y 95 apenas cambian en mediana. Detalle completo por combinación en `tables/t7_tail_per_combination.csv`.

---

## Tarea 8. Visitas a capacidad y censura de la demanda

**Cómo:** `scripts/t8_t9.py`. Capacidad = 80 (Tarea 6.5); umbral del 90 % = 72. Dos estados: **A** antes del corte superior de ocupación (todos los demás filtros del pipeline aplicados); **B** tras `Occupation<80`. En B el porcentaje a capacidad es 0 por construcción; el indicador sólo es medible en A. Franja = `TimeSlot` (salida; referencia de validación); versiones por `TimeSlot.1` se pueden obtener con el mismo script cambiando la columna.

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

**Lectura:** antes del corte, el **0,49 % (toA) y 0,35 % (toB)** de las visitas están a capacidad (≥80) y el 2,0 % y 1,5 % al ≥90 %. Se concentran en las franjas de 5–8 h de toA (hasta 1,9 % a capacidad en la franja 5) y en 14–18 h de toB (≥72 en el 1,8–3,9 %). En esos momentos pudo haber pasajeros que no subieron y que el APC no registra; el recorte de la limpieza elimina esas visitas del ajuste de la ocupación, por lo que **el indicador de visitas a capacidad del simulador no es contrastable con los datos limpios**.

---

## Tarea 9. Franjas de entrada frente a franjas de referencia

**Cómo:** `scripts/t8_t9.py`. Por visita (tras la limpieza): `TimeSlot` (salida) frente a `TimeSlot.1` (servicio). Figura (1 col.): `figures/fig_slot_mismatch.pdf`, datos `figures/fig_slot_mismatch_data.csv`.

Visit-level comparison of `TimeSlot` (terminal departure) vs `TimeSlot.1` (service/arrival), pipeline-cleaned normal-day visits.

| direction | n_visits | n_mismatch | pct_mismatch |
|---|---|---|---|
| toA | 169074 | 64585 | 38.20 |
| toB | 133578 | 53916 | 40.36 |

| direction | stop | order | n_visits | n_mismatch | pct_mismatch |
|---|---|---|---|---|---|
| toA | 2646 | 1 | 10336 | 30 | 0.29 |
| toA | 562 | 2 | 11042 | 1280 | 11.59 |
| toA | 4090 | 3 | 11032 | 1640 | 14.87 |
| toA | 4188 | 4 | 10809 | 2233 | 20.66 |
| toA | 5939 | 5 | 11000 | 2889 | 26.26 |
| toA | 3995 | 6 | 11271 | 3424 | 30.38 |
| toA | 3991 | 7 | 11327 | 3845 | 33.95 |
| toA | 3903 | 8 | 11278 | 4132 | 36.64 |
| toA | 2539 | 9 | 11360 | 4693 | 41.31 |
| toA | 2535 | 10 | 11643 | 5408 | 46.45 |
| toA | 1929 | 11 | 11786 | 6058 | 51.40 |
| toA | 4032 | 12 | 11911 | 6787 | 56.98 |
| toA | 5360 | 13 | 11841 | 7176 | 60.60 |
| toA | 82 | 14 | 11630 | 7464 | 64.18 |
| toA | 5727 | 15 | 10808 | 7526 | 69.63 |
| toB | 5727 | 1 | 11132 | 38 | 0.34 |
| toB | 81 | 2 | 11103 | 2289 | 20.62 |
| toB | 1167 | 3 | 9202 | 2160 | 23.47 |
| toB | 2538 | 4 | 11353 | 3585 | 31.58 |
| toB | 3929 | 5 | 11398 | 4146 | 36.37 |
| toB | 3990 | 6 | 11688 | 4623 | 39.55 |
| toB | 3994 | 7 | 11704 | 5046 | 43.11 |
| toB | 5938 | 8 | 11583 | 5489 | 47.39 |
| toB | 4187 | 9 | 11311 | 6092 | 53.86 |
| toB | 2964 | 10 | 11171 | 6571 | 58.82 |
| toB | 649 | 11 | 11214 | 6987 | 62.31 |
| toB | 2646 | 12 | 10719 | 6890 | 64.28 |

Correlation of mismatch with stop order: toA: 0.996, toB: 0.974

By departure slot:

| direction | departure_slot | n_visits | pct_mismatch |
|---|---|---|---|
| toA | 5 | 4840 | 36.36 |
| toA | 6 | 9314 | 42.86 |
| toA | 7 | 12798 | 43.22 |
| toA | 8 | 11584 | 39.61 |
| toA | 9 | 9270 | 43.05 |
| toA | 10 | 8218 | 40.65 |
| toA | 11 | 8314 | 31.13 |
| toA | 12 | 10033 | 41.08 |
| toA | 13 | 10746 | 43.86 |
| toA | 14 | 10160 | 33.63 |
| toA | 15 | 10929 | 34.87 |
| toA | 16 | 11161 | 38.16 |
| toA | 17 | 10618 | 37.37 |
| toA | 18 | 9882 | 39.40 |
| toA | 19 | 9095 | 36.78 |
| toA | 20 | 8041 | 36.04 |
| toA | 21 | 6626 | 36.78 |
| toA | 22 | 5894 | 32.68 |
| toA | 23 | 1551 | 0.26 |
| toB | 5 | 1382 | 91.53 |
| toB | 6 | 5887 | 33.34 |
| toB | 7 | 9283 | 39.29 |
| toB | 8 | 8507 | 37.86 |
| toB | 9 | 6714 | 35.88 |
| toB | 10 | 7069 | 40.40 |
| toB | 11 | 6713 | 41.46 |
| toB | 12 | 6772 | 38.63 |
| toB | 13 | 7575 | 37.24 |
| toB | 14 | 9945 | 45.59 |
| toB | 15 | 8659 | 44.98 |
| toB | 16 | 8897 | 40.20 |
| toB | 17 | 8929 | 46.52 |
| toB | 18 | 7918 | 46.68 |
| toB | 19 | 8245 | 39.54 |
| toB | 20 | 7606 | 41.72 |
| toB | 21 | 5860 | 36.54 |
| toB | 22 | 5186 | 35.65 |
| toB | 23 | 2431 | 2.30 |

**Lectura:** las dos franjas difieren en el **38,2 % (toA) y 40,4 % (toB)** de las visitas; en la primera parada ≈0,3 % y crece a lo largo del recorrido hasta ≈64 % en la última parada de toB (correlación con el orden de parada 0,996 en toA y 0,974 en toB).

---

## Tarea 10. Tabla de no rechazo

**Cómo:** subidas y bajadas: `scripts/fits.py` (+ `t10.py`), mismo procedimiento que el notebook (MAD → tres contrastes → no rechazada si alguna de las tres no se rechaza; `final_analysis_board_dropoff.ipynb` celdas 5 y 8). Ocupación: función `generate_gaussian_per_slot_all_days` cargada literalmente de `analisis_ALL_OCCUPATION.ipynb` (celda 2) y ejecutada por fichero de parada tras `clean_dataframe` (`scripts/t10_heavy.py`). Tiempos de viaje: lógica de `analysis_time_between_stops.ipynb` celda 14 (pares de visitas por `TripId`, diferencia de `EventTime.1`, `is_normal_simplified`, y si falla ESD con hasta 20 outliers y nueva prueba), con `estimate_outliers` de `generate_gaussian.py:195`. Los tiempos de viaje no se usan MAD sino ESD. Test binomial de la proporción frente a 0,95 (`scipy.stats.binomtest`, bilateral) con **intervalo de Wilson al 95 %**. Los N cuentan combinaciones que no son independientes (misma parada o franja), por lo que los p-valores son orientativos.

### 10.1/10.2 Recomputed table vs paper

| variable | direction | paper_% | recomputed_% | k | N | match |
|---|---|---|---|---|---|---|
| boardings | toA | 90.60 | 90.98 | 242 | 266 | False |
| boardings | toB | 87.56 | 87.08 | 182 | 209 | False |
| alightings | toA | 93.61 | 93.61 | 249 | 266 | True |
| alightings | toB | 90.91 | 90.91 | 190 | 209 | True |
| travel times | toA | 95.49 | 95.86 | 255 | 266 | False |
| travel times | toB | 90.43 | 90.43 | 189 | 209 | True |
| occupation | toA | 94.39 | 94.74 | 270 | 285 | False |
| occupation | toB | 88.60 | 87.28 | 199 | 228 | False |

### 10.3 Binomial test against 0.95 and Wilson 95 % CI (all variants)

| variable | direction | variant | n_not_rejected | N | pct_not_rejected | wilson95_low | wilson95_high | binom_test_p_vs_0.95 | note |
|---|---|---|---|---|---|---|---|---|---|
| boardings | toA | as published (terminal counted as always non-rejected) | 242 | 266 | 90.977 | 86.926 | 93.862 | 0.007 | reproduces paper |
| boardings | toA | corrected (terminal with its real test result) | 240 | 266 | 90.226 | 86.064 | 93.242 | 0.001 |  |
| boardings | toA | main-loop stops only (terminals excluded) | 223 | 247 | 90.283 | 85.950 | 93.383 | 0.002 |  |
| boardings | toB | as published (terminal counted as always non-rejected) | 182 | 209 | 87.081 | 81.857 | 90.968 | 0.000 | reproduces paper |
| boardings | toB | corrected (terminal with its real test result) | 182 | 209 | 87.081 | 81.857 | 90.968 | 0.000 |  |
| boardings | toB | main-loop stops only (terminals excluded) | 163 | 190 | 85.789 | 80.114 | 90.046 | 0.000 |  |
| alightings | toA | as published (terminal counted as always non-rejected) | 249 | 266 | 93.609 | 90.005 | 95.972 | 0.322 | reproduces paper |
| alightings | toA | corrected (terminal with its real test result) | 248 | 266 | 93.233 | 89.558 | 95.677 | 0.202 |  |
| alightings | toA | main-loop stops only (terminals excluded) | 230 | 247 | 93.117 | 89.255 | 95.659 | 0.186 |  |
| alightings | toB | as published (terminal counted as always non-rejected) | 190 | 209 | 90.909 | 86.239 | 94.103 | 0.011 | reproduces paper |
| alightings | toB | corrected (terminal with its real test result) | 190 | 209 | 90.909 | 86.239 | 94.103 | 0.011 |  |
| alightings | toB | main-loop stops only (terminals excluded) | 171 | 190 | 90.000 | 84.910 | 93.504 | 0.004 |  |
| occupation | toA | all stops incl. terminals (as published) | 270 | 285 | 94.737 | 91.499 | 96.785 | 0.786 | reproduces paper |
| occupation | toA | terminals excluded (as the text states) | 241 | 247 | 97.571 | 94.803 | 98.882 | 0.077 |  |
| travel times | toA | as published | 255 | 266 | 95.865 | 92.748 | 97.675 | 0.672 | reproduces paper |
| travel times | toA | combinations with n>0 only | 255 | 266 | 95.865 | 92.748 | 97.675 | 0.672 |  |
| occupation | toB | all stops incl. terminals (as published) | 199 | 228 | 87.281 | 82.330 | 90.996 | 0.000 | reproduces paper |
| occupation | toB | terminals excluded (as the text states) | 176 | 190 | 92.632 | 88.013 | 95.560 | 0.133 |  |
| travel times | toB | as published | 189 | 209 | 90.431 | 85.682 | 93.720 | 0.006 | reproduces paper |
| travel times | toB | combinations with n>0 only | 189 | 198 | 95.455 | 91.588 | 97.590 | 1.000 |  |

### 10.4 Occupation, non-rejection by slot (both directions)

| slot | N | n_not_rejected | pct | n_rejected |
|---|---|---|---|---|
| 5.0 | 27.0 | 22.0 | 81.5 | 5.0 |
| 6.0 | 27.0 | 25.0 | 92.6 | 2.0 |
| 7.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 8.0 | 27.0 | 24.0 | 88.9 | 3.0 |
| 9.0 | 27.0 | 25.0 | 92.6 | 2.0 |
| 10.0 | 27.0 | 25.0 | 92.6 | 2.0 |
| 11.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 12.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 13.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 14.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 15.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 16.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 17.0 | 27.0 | 27.0 | 100.0 | 0.0 |
| 18.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 19.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 20.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 21.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 22.0 | 27.0 | 26.0 | 96.3 | 1.0 |
| 23.0 | 27.0 | 9.0 | 33.3 | 18.0 |

By direction and slot (only slots with any rejection):

| direction | slot | N | n_not_rejected | pct |
|---|---|---|---|---|
| toA | 6 | 15 | 14 | 93.3 |
| toA | 7 | 15 | 14 | 93.3 |
| toA | 8 | 15 | 13 | 86.7 |
| toA | 9 | 15 | 14 | 93.3 |
| toA | 10 | 15 | 14 | 93.3 |
| toA | 13 | 15 | 14 | 93.3 |
| toA | 14 | 15 | 14 | 93.3 |
| toA | 23 | 15 | 8 | 53.3 |
| toB | 5 | 12 | 7 | 58.3 |
| toB | 6 | 12 | 11 | 91.7 |
| toB | 8 | 12 | 11 | 91.7 |
| toB | 9 | 12 | 11 | 91.7 |
| toB | 10 | 12 | 11 | 91.7 |
| toB | 11 | 12 | 11 | 91.7 |
| toB | 12 | 12 | 11 | 91.7 |
| toB | 15 | 12 | 11 | 91.7 |
| toB | 16 | 12 | 11 | 91.7 |
| toB | 18 | 12 | 11 | 91.7 |
| toB | 19 | 12 | 11 | 91.7 |
| toB | 20 | 12 | 11 | 91.7 |
| toB | 21 | 12 | 11 | 91.7 |
| toB | 22 | 12 | 11 | 91.7 |
| toB | 23 | 12 | 1 | 8.3 |

All rejected occupation combinations:

| direction | stop | slot | n |
|---|---|---|---|
| toA | 5727 | 6 | 620 |
| toA | 5727 | 7 | 829 |
| toA | 2646 | 8 | 745 |
| toA | 5727 | 8 | 562 |
| toA | 5727 | 9 | 526 |
| toA | 5727 | 10 | 538 |
| toA | 5727 | 13 | 709 |
| toA | 5727 | 14 | 664 |
| toA | 2535 | 23 | 111 |
| toA | 2539 | 23 | 109 |
| toA | 2646 | 23 | 108 |
| toA | 3903 | 23 | 111 |
| toA | 3995 | 23 | 111 |
| toA | 4090 | 23 | 110 |
| toA | 562 | 23 | 109 |
| toB | 2646 | 5 | 120 |
| toB | 3929 | 5 | 118 |
| toB | 3990 | 5 | 118 |
| toB | 3994 | 5 | 118 |
| toB | 5938 | 5 | 118 |
| toB | 2646 | 6 | 512 |
| toB | 2646 | 8 | 691 |
| toB | 2646 | 9 | 587 |
| toB | 2646 | 10 | 614 |
| toB | 2646 | 11 | 574 |
| toB | 2646 | 12 | 573 |
| toB | 2646 | 15 | 752 |
| toB | 2646 | 16 | 755 |
| toB | 2646 | 18 | 666 |
| toB | 2646 | 19 | 568 |
| toB | 2646 | 20 | 503 |
| toB | 2646 | 21 | 412 |
| toB | 2646 | 22 | 217 |
| toB | 1167 | 23 | 186 |
| toB | 2538 | 23 | 231 |
| toB | 2964 | 23 | 216 |
| toB | 3929 | 23 | 229 |
| toB | 3990 | 23 | 231 |
| toB | 3994 | 23 | 227 |
| toB | 4187 | 23 | 220 |
| toB | 5727 | 23 | 216 |
| toB | 5938 | 23 | 225 |
| toB | 649 | 23 | 210 |
| toB | 81 | 23 | 224 |

Share of all occupation rejections falling in slot 23: **40.9%** (18 of 44); slot 23 holds 5.3% of the combinations.

Desglose de los 44 rechazos de ocupación: 16 en la franja 23 de paradas no terminales, 24 en paradas terminales (2646 y 5727, cualquier franja) y 4 en otras combinaciones. Sin terminales (punto 4 de la revisión): 241/247 = 97,57 % (toA) y 176/190 = 92,63 % (toB).

**Lectura:**
- **10.1/10.2** Las ocho cifras coinciden con el artículo y con N = 266/209 (subidas y bajadas toA/toB y tiempos), 285/228 (ocupación).
- **10.3** Frente a 0,95: subidas (ambos sentidos), bajadas hacia La Peseta y ocupación hacia La Peseta quedan **significativamente por debajo** (p<0,05); bajadas hacia Cibeles, ocupación hacia Cibeles y tiempos hacia Cibeles son compatibles con 0,95. Tiempos hacia La Peseta (90,43 %, p=0,006) también por debajo, pero con las 11 combinaciones sin servicio de la franja 5 incluidas en N (sin ellas 95,45 %).
- **Matiz del bug:** las filas «as published» de subidas y bajadas incluyen 19 combinaciones terminales contadas como no rechazadas por el fallo de `if is_normal or neg_bin or geom`. Con el resultado real, las subidas hacia Cibeles son 90,23 % (240/266).
- **10.4** Los rechazos de ocupación se concentran en la franja 23 (33 % de no rechazo; 18 de 44 rechazos) **y** en las paradas terminales (ver desglose arriba): no es sólo un efecto de la última franja.

---

## Archivos generados

- `tables/`: un CSV por tabla (prefijo `tN_`); `tables/fits_per_combination.csv` con el ajuste de cada combinación (parada, franja, n, media, varianza, índice de dispersión, resultados de cada contraste, distribución elegida, percentiles antes/después).
- `figures/`: `fig_load_profile.pdf`, `fig_hourly_profile.pdf`, `fig_slot_mismatch.pdf` y los CSV `fig_*_data.csv` (también `fig_occupation_nonrejection_by_slot_data.csv`).
- `tables/t5_visits.csv`: base visita a visita para la figura de dispersión de la Tarea 5.5.

## Archivos o datos no encontrados (regla 5)

- Código que generó las cifras de bajadas 93,61 % y 90,91 %: no está en `DATOS/src/` (en `final_analysis_board_dropoff.ipynb` el bloque de bajadas está comentado en las celdas 5 y 8; `analisis_board_dropoff*.ipynb` usan una cascada con ESD y dan 97,17 %/95,00 %). Reconstruido con el mismo procedimiento de subidas, coincide.
- `dropoff_analyzer.ipynb` está vacío (0 bytes).
- El origen del valor 80 de capacidad (¿dato de EMT?) no está documentado en el repositorio.
- No se ha identificado qué `input_data` leyó el GAML para el artículo (`old_input_data_E01_*.csv` en `BASE_DATA/`).

## Tabla final de cifras del artículo

| Cifra | Valor recalculado | ¿Coincide con el texto? | Tarea |
|---|---|---|---|
| Registros eliminados por parada y día («uno cada dos días») | 0,92 por día y parada (1 cada 1,09 días) | **No** (el texto dice 0,5) | 1.4 |
| Umbral de ocupación de limpieza | el repositorio usa 75; las cifras publicadas se reproducen con 75, no con 80 | **No** (texto: 80) | Resumen / 10 |
| Normal seleccionada | 62,2 % (subidas+bajadas, N=940); solo subidas 56,4 % | **Aproximada** (texto 62,4 %) | 3.4 |
| Binomial negativa seleccionada | 24,5 % (solo subidas 32,4 %; bajadas 16,3 %) | **Aproximada** (texto 23,9 %) | 3.4 |
| Geométrica seleccionada | 13,3 % (solo subidas 11,2 %) | **Aproximada** (texto 13,7 %) | 3.4 |
| «BN más frecuente en subidas que en bajadas» | 32,4 % frente a 16,3 % | Sí | 3.4 |
| No rechazo subidas toA / toB | 90,98 % / 87,08 % (N 266 / 209) | **No con `<80`** (texto 90,60 / 87,56; coincide con `<75`). Incluye el fallo de terminal; real 90,23 % / 87,08 % | 10 |
| No rechazo bajadas toA / toB | 93,61 % / 90,91 % (N 266 / 209) | Sí (reconstruido; real 93,23 % / 90,91 %) | 10 |
| No rechazo tiempos de viaje toA / toB | 95,86 % / 90,43 % (N 266 / 209) | toB sí; toA **no con `<80`** (texto 95,49; coincide con `<75`) | 10 |
| No rechazo ocupación toA / toB | 94,74 % / 87,28 % (N 285 / 228; incluye terminales) | **No con `<80`** (texto 94,39 / 88,60; coincide con `<75`). Sin terminales: 97,57 % / 92,63 % | 10 |
| Rechazos de ocupación concentrados en la última franja | 40.9 % de los rechazos en la franja 23; 24 de 44 en paradas terminales | **Parcial** | 10.4 |
| Bajadas de menos (Σ bajadas / Σ subidas − 1) | −4,39 % (`Occ<80`, expediciones completas) | Sí (texto −4,4 %) | 4.2 |
| Hora punta toA / toB | 8 h / 18 h | Sí (7–9 h; después de las 17 h) | 2.1 |
| Días de la ventana / normales | 238 / 158 (68 fin de semana, 7 festivos, 5 de gratuidad); 2025-07-01 a 2026-02-23 | — (nuevo) | 1.1 |
| Visitas en días normales toA / toB | 170.944 / 135.618 (167.877 / 132.938 tras limpieza) | — (nuevo) | 1.2 |
| Expediciones en días normales toA / toB | 12.951 / 12.860 | — (nuevo) | 1.2 |
| Sobredispersión (rechazo de Poisson) subidas / bajadas | 98,7 % / 95,1 % | — (nuevo) | 3.2 |
| Índice de dispersión, mediana subidas / bajadas | 3,4 / 1,8 | — (nuevo) | 3.3 |
| Observaciones eliminadas por MAD | 1,55 % (subidas 1,34 %, bajadas 1,61 %) | — (nuevo) | 7.1 |
| Visitas a capacidad (≥80) antes del corte toA / toB | 0,49 % / 0,35 % | — (nuevo) | 8.1 |
| Visitas con franjas de entrada y referencia distintas toA / toB | 38,2 % / 40,4 % | — (nuevo; crece a lo largo del recorrido) | 9.2 |
| Correlación bajadas–carga (Pearson mediana) toA / toB | 0,40 / 0,53 (positiva significativa 92 % / 95 %) | — (nuevo; contradice independencia bajadas–carga) | 5.2 |
| Ocupación acumulada negativa en alguna parada (antes de limpiar) | 22,2 % / 28,3 % de las expediciones completas | — (nuevo) | 4.5 |

---

## Revisión 3. Origen del corte de ocupación y tabla final

**Archivos:** `BASE_DATA/old_input_data_E01_toA.csv` (532 filas) y `_toB.csv` (418): columnas `Stop, Timeslot, DataType (Board/DropOff), DistributionType, Param1, Param2`. Contienen subidas y bajadas, **no tiempos de viaje**; estos los lee el GAML de `GAMA/src/TEST_MOBILITY/includes/INPUTS/input_times_stops_to{A,B}.csv` (`mobility_performance.gaml:541-542`), con los que comparo los tiempos. Script: `scripts/compare_old_input.py`; detalle por combinación en `tables/t_old_input_comparison_detail.csv`. «Exacto» = mismo tipo y parámetros con tolerancia relativa 1e-6.

| variable | direction | cut | n_combinations_in_file | same_distribution_type | same_type_and_params |
|---|---|---|---|---|---|
| boardings | toA | 80 | 266 | 261 | 134 |
| boardings | toA | 75 | 266 | 266 | 266 |
| alightings | toA | 80 | 266 | 263 | 133 |
| alightings | toA | 75 | 266 | 266 | 266 |
| travel times | toA | 80 | 266 | 111 | 111 |
| travel times | toA | 75 | 266 | 266 | 266 |
| boardings | toB | 80 | 209 | 208 | 137 |
| boardings | toB | 75 | 209 | 209 | 209 |
| alightings | toB | 80 | 209 | 196 | 118 |
| alightings | toB | 75 | 209 | 199 | 199 |
| travel times | toB | 80 | 209 | 117 | 117 |
| travel times | toB | 75 | 209 | 209 | 209 |

**Conclusión: el corte es `Occupation < 75`.** Con 75 coinciden **todas** las combinaciones en subidas, bajadas y tiempos, en ambos sentidos, salvo 10 de bajadas toB de la franja 5, que el fichero rellena con `NORMAL, 0, 0` (sin datos) y que yo dejo vacías: equivalente. Con 80 coinciden en tipo entre 94 % y 100 % de subidas/bajadas pero en tipo y parámetros solo entre el 50 % y el 66 %, y en tiempos entre el 42 % y el 56 %. Además esto indica que **las bajadas de `old_input` sí salen del procedimiento MAD + 3 contrastes + AIC** (reproducido exactamente), aunque el código no esté en el repositorio.

**Historia de git.**
- `clean_dataframe` (`generate_gaussian.py:475-481`): `git log -L` la muestra **creada el 2026-01-05 (commit `4bd35443`, «Avances gordos como camiones») ya con `Occupation < 75`**; no cambia después (el commit `e8c42e39` de 2026-02-03 solo retoca el contexto). **Nunca fue 80 en ese archivo.** El 80 aparece en otros sitios: `Occupation <= 80` en línea 358 de `generate_gaussian.py`, en `analisis_ALL_OCCUPATION.ipynb`, `expected_kpi_extractor.ipynb` y en el texto del artículo.
- `old_input_data_E01_toA/toB.csv`: añadidos al repositorio el **2026-10-12 (commit `2c4f0f47`, «Committttt»)**, último commit el mismo; fecha de modificación del fichero 2026-10-13. Es la fecha de entrada en git, no de generación (los `input_data_E01_*.csv` equivalentes entran el 2026-02-10/11, commits `5048ed94` y `249bef8b`).

### Tabla de no rechazo final (corte 75, fallo de terminales corregido)

Subidas y bajadas: la terminal se evalúa con su resultado real (no «siempre no rechazada»). Ocupación: se da con todas las paradas (como en el artículo) y sin terminales (2646 y 5727). Test binomial frente a 0,95 e intervalo de Wilson al 95 %. Detalle y variantes: `tables/t10_nonrejection_table_cut75.csv`.

| Variable | Sentido | No rechazadas / N | % | IC Wilson 95 % | p (binomial vs 0,95) | Artículo |
|---|---|---|---|---|---|---|
| Subidas | Cibeles | 239 / 266 | 89,85 | 85,64–92,93 | 0,001 | 90,60 |
| Subidas | La Peseta | 183 / 209 | 87,56 | 82,40–91,37 | <0,001 | 87,56 |
| Bajadas | Cibeles | 248 / 266 | 93,23 | 89,56–95,68 | 0,20 | 93,61 |
| Bajadas | La Peseta | 190 / 209 | 90,91 | 86,24–94,10 | 0,011 | 90,91 |
| Tiempos de viaje | Cibeles | 254 / 266 | 95,49 | 92,28–97,40 | 0,89 | 95,49 |
| Tiempos de viaje | La Peseta | 189 / 209 | 90,43 | 85,68–93,72 | 0,006 | 90,43 |
| Ocupación, todas las paradas | Cibeles | 269 / 285 | 94,39 | 91,08–96,52 | 0,59 | 94,39 |
| Ocupación, todas las paradas | La Peseta | 202 / 228 | 88,60 | 83,82–92,10 | <0,001 | 88,60 |
| **Ocupación, sin terminales** | Cibeles | 240 / 247 | **97,17** | 94,27–98,62 | 0,14 | — |
| **Ocupación, sin terminales** | La Peseta | 179 / 190 | **94,21** | 89,93–96,74 | 0,62 | — |

Solo cambian respecto al artículo las subidas hacia Cibeles (90,60 → 89,85 %, el fallo de 2646) y las bajadas hacia Cibeles (93,61 → 93,23 %, terminal 5727 con 18/19 en lugar de 19/19). En bajadas hacia La Peseta la terminal corregida (2646) pasa 19/19, así que no cambia. Tiempos hacia La Peseta: 95,45 % (189/198) si se excluyen las 11 combinaciones sin servicio de la franja 5. Sin terminales, la ocupación es compatible con 0,95 en ambos sentidos; los rechazos restantes están sobre todo en la franja 23.

*Nota:* el resto de este informe (secciones anteriores) usa `<80` por petición; las tablas con corte 75 llevan el sufijo `_cut75`.
