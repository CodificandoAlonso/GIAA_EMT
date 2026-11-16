
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
