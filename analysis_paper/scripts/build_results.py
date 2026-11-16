from common import *
S=lambda n: open(f"{ROOT}/analysis_paper/sections/{n}.md").read()
occ=pd.read_csv("../tables/t10_occupation_combinations.csv"); occ["ok"]=occ.is_normal.astype(str)=="True"
rej=occ[~occ.ok]; term=rej.stop.isin([2646,5727])
n_rej=len(rej); n_term=int(term.sum()); n23=int((rej.slot==23).sum()); n23_nt=int(((rej.slot==23)&~term).sum()); n_other=n_rej-n_term-n23_nt
extra10=(f"\nDesglose de los {n_rej} rechazos de ocupación: {n23_nt} en la franja 23 de paradas no terminales, {n_term} en paradas terminales "
         f"(2646 y 5727, cualquier franja) y {n_other} en otras combinaciones. Sin terminales (punto 4 de la revisión): 241/247 = 97,57 % (toA) y 176/190 = 92,63 % (toB).\n")
# variants for the "one record every two days" claim
rows=[]
for d in DIRN:
    df=load_dir(d); nd=df[(df.DayType=="LA")&(df.FreeDay==0)]; D=nd.EventDate.nunique(); Sx=nd.Stop.nunique()
    c={"Occupation<0":nd.Occupation<0,"Occupation>=80":nd.Occupation>=80,"Board/DropOff <0 or >=80":(nd.Board<0)|(nd.DropOff<0)|(nd.Board>=80)|(nd.DropOff>=80)}
    for k,v in c.items(): rows.append((d,k,int(v.sum()),D*Sx,v.sum()/(D*Sx)))
V=pd.DataFrame(rows,columns=["direction","condition (alone)","records","days*stops","records per day-stop"]); save_table(V,"t1_removed_variants")
extra1="\n#### Variantes por condición (registros / (días × paradas)), días normales\n\n"+md(V,"{:.4f}")+"\n"
import json
J=json.load(open('../sections/stats80.json'))
doc=f"""# RESULTS — análisis de datos para la sección «Data analysis methodology» (E01)

Todo el código está en `analysis_paper/scripts/` (se ejecuta en este orden: `t0_t1.py`, `t2.py`, `fits.py`, `t3_t7.py`, `t4_t5.py`, `t8_t9.py`, `t10_heavy.py`, `t10.py`, `build_results.py`). No se ha modificado el pipeline ni los datos. Tablas en `tables/`, figuras (PDF vectorial) y CSV de cada figura en `figures/`.

## Resumen ejecutivo (leer primero)

1. **Corte de ocupación.** Todo este informe usa `Occupation < 80` (el corte pedido y el que dice el artículo). **Ojo:** la función del repositorio (`DATOS/src/generate_gaussian.py:477`) usa `< 75`, y son los resultados con 75, no con 80, los que reproducen *exactamente* las cifras publicadas: con `<75` salen 90,60 % (subidas toA), 94,39 % y 88,60 % (ocupación) y 95,49 % (tiempos toA) y los tipos de distribución de subidas coinciden en 475/475 combinaciones con `DATOS/src/input_data_E01_toA.csv`/`_toB.csv`; con `<80` salen 90,98 %, 94,74 %, 87,28 % y 95,86 %, y los tipos coinciden en 469/475. Es decir, el artículo y el simulador parecen calibrados con `<75`. Las cifras de bajadas y de tiempos toB (93,61 %, 90,91 %, 90,43 %) no cambian con el corte.
2. **Defectos del notebook que afectan a cifras del artículo:**
   - En `final_analysis_board_dropoff.ipynb` (celdas 6 y 8, `if is_normal or neg_bin or geom:`) las variables `neg_bin` y `geom` son *diccionarios*, siempre verdaderos. Las 19 franjas de la parada terminal 2646 (toA) y 5727 (toB) cuentan como «no rechazadas» sin serlo. Con `<75` (que reproduce lo publicado) el 90,60 % de subidas hacia Cibeles es (222+19)/266; con `<80` es (223+19)/266 = 90,98 %, y con el resultado real de 2646 sería **90,23 %** (240/266). Las cifras de bajadas (93,61 % y 90,91 %) tienen la misma estructura (+19 combinaciones). El código que las generó **no está en el repositorio** (en la celda final el bloque de bajadas está comentado).
   - La normalidad de los conteos se contrasta con asimetría/curtosis (`fussion_gauss.py:40`), una prueba muy permisiva; el test de dispersión rechaza equidispersión en el **98,7 %** de las combinaciones de subidas y el **95,1 %** de bajadas.
   - En 245 de 1.016 combinaciones MAD = 0 y `remove_outliers_mad` no elimina nada.
   - `test_negative_binomial` devuelve NaN (y por tanto «rechazada») en {J['nan_nb']} combinaciones y `test_geometric` en {J['nan_g']} de {J['tot']}, por errores de implementación del agrupamiento y de los grados de libertad (Tarea 6.1). Corregirlos cambia la distribución elegida en 7–12 de 940 combinaciones (0,7–1,3 %); ver Tarea 6.1.
   - Las bajadas del simulador *actual* no usan normal/NB/geométrica sino beta-binomial/binomial (`DATOS/src/alighting_params_*.csv`, `DROPOFFS_BETA.ipynb`). Las cifras de bajadas del artículo describen un ajuste anterior.
   - Los rechazos de la validación de ocupación **no** se concentran solo en la última franja: {n_term} de {n_rej} están en las paradas terminales (2646/5727), que el texto dice excluir (la tabla las incluye: N=285 y 228).
3. **Cifras del texto que no se confirman:** «un registro eliminado cada dos días por parada» (da 0,92 registros por día y parada; Tarea 1.4); reparto 62,4/23,9/13,7 % (da 62,2/24,5/13,3 % mezclando subidas y bajadas con el conjunto de paradas del notebook; solo subidas: 56,4/32,4/11,2 %; Tarea 3.4). **Se confirman:** −4,4 % de bajadas de menos (da −4,39 %, Tarea 4.2), horas punta (8 h y 18 h) y, con matices (ver punto 1), la tabla de no rechazo: con `<80` las filas de bajadas y de tiempos toB coinciden, pero no las de subidas, ocupación ni tiempos toA.

---

## Tarea 0. Estructura de los CSV y enlace entre paradas

**Cómo:** `scripts/t0_t1.py` (lectura con `pd.read_csv` de cada CSV; filtro por `Direction`). Datos: `DATOS/data/E01_toA/NEW` (15 CSV, uno por parada) y `DATOS/data/E01_toB` (12 CSV).

**0.1 Columnas.** Los 15 CSV de toA comparten un único esquema; los 12 de toB, también (mismo esquema que toA). Son 25 columnas; pandas renombra las repetidas con `.1`:
`TripId, IdExternal, EventDate, EventTime, TimeSlot, Line, Direction, LogicVehicle, Weekday, DayType, Season, FreeDay` (**tabla de salidas desde terminal**: fecha, hora y franja de salida de la expedición) + `TripId.1, Stop, IdExternal.1, EventDate.1, EventTime.1, TimeSlot.1, TemperatureMax, TemperatureMin, RainProbMin, RainProbMax, Board, DropOff, Occupation` (**tabla de llegadas a parada**). Es decir, **el enlace ya está reconstruido en cada CSV** (una fila = una visita a una parada con los datos de salida de su expedición). Cada CSV contiene ambos sentidos; hay que filtrar por `Direction` (2 = toA, 1 = toB), como hace `clean_dataframe`. Las paradas terminales (2646, 5727) aparecen en ambas carpetas.

{S('t0_data')}

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

{S('t1_sizes')}
{extra1}
**1.4 Conclusión.** Registros eliminados / (días × paradas) = **0,92** (toA+toB), es decir un registro eliminado por parada cada **1,09 días**. **No se confirma «un registro cada dos días» (0,5)**; ninguna de las variantes por condición lo da (la más cercana, `Occupation<0` sola, da ≈0,6). Si el cálculo del texto usó otro denominador (p. ej. los 238 días de la ventana, que da 0,93) tampoco coincide.

**Notas 1.5.** Subidas: n = número de días en que la parada tiene algún registro limpio (152–158), porque el pipeline suma por día y franja y añade 0 si ese día no hubo autobús (`final_analysis_board_dropoff.ipynb` celda 3: bucle `for day in unique_days` con `list_boards.append(sum(...))`). Bajadas: una por llegada de autobús; ocupación: una por visita (franja de salida); tiempos de viaje: pares de visitas de la misma expedición en paradas consecutivas con ambas llegadas en la misma franja. Las combinaciones con 0 observaciones en toB (franja 5) son las que no tienen servicio a esa hora.

---

## Tarea 2. Perfil de carga por parada

**Cómo:** `scripts/t2.py`, sobre datos tras `clean_dataframe` + `clean_dataframe_advanced("LA")` (`cleaned(d)` en `common.py`). Franja = `TimeSlot.1` (momento de servicio) para las tres magnitudes; la ocupación es el campo registrado tras la parada.

{S('t2_profile')}

**Figuras:** `figures/fig_load_profile.pdf` (página completa, 17 cm, datos en `fig_load_profile_data.csv`/`tables/t2_peak_stop_profile.csv`) y `figures/fig_hourly_profile.pdf` (1 columna, 8,5 cm, datos en `fig_hourly_profile_data.csv`). Sin título; cada panel lleva una etiqueta corta con el sentido y la hora punta (se puede quitar si el pie de LaTeX lo cubre). Paleta Okabe–Ito, tipografía serif de 8 pt. **Observación:** en el panel de toA la ocupación en la parada terminal 5727 (4,4 pasajeros tras la parada) y en 2646 es poco fiable (Tarea 4.6).

---

## Tarea 3. Dispersión de los conteos

**Cómo:** `scripts/fits.py` y `scripts/t3_t7.py`. Reutiliza `remove_outliers_mad`, `is_normal_simplified`, `test_negative_binomial`, `test_geometric` y `select_by_aic` (cargadas literalmente de `final_analysis_board_dropoff.ipynb` celda 4 y de `fussion_gauss.py`). Conjunto de paradas como en el notebook: bucle principal (sin 2646 ni 5727) más la terminal de origen para subidas (2646 en toA, 5727 en toB) y la terminal de destino para bajadas (5727 en toA, 2646 en toB). Datos: subidas = suma diaria por parada y franja (`TimeSlot.1`), bajadas = valor por llegada, tras MAD. Test de dispersión: (n−1)·s²/x̄ frente a χ²(n−1), bilateral, α = 0,05; s² con ddof=1. Se excluyen las combinaciones con n<2 o media 0.

{S('t3_t7').split('### 7.1')[0]}

**Lectura:** la equidispersión se rechaza casi siempre y siempre por sobredispersión; ninguna combinación infradispersa. Mediana del índice: 3,4 (subidas) y 1,8 (bajadas). Esto contrasta con la selección de la normal en ~62 % de los casos y se explica porque el test de normalidad usado (asimetría/curtosis) es permisivo (Tarea 6.1).

---

## Tarea 4. Balance de subidas y bajadas

**Cómo:** `scripts/t4_t5.py`. Una expedición es «completa» si tiene todas las paradas del sentido. Subconjuntos: S0 todas las visitas de días normales sin limpiar; S1 visitas que pasan la limpieza (expediciones parciales); S2 expediciones completas sin limpiar; **S3 expediciones completas en las que ninguna visita es eliminada por la limpieza del pipeline (`Occupation<80`)**. Ocupación acumulada = suma acumulada de Board − DropOff desde 0 a lo largo del orden de paradas. Diferencia por expedición = subidas − bajadas.

{S('t4_balance')}

**Respuestas:**
- **4.2** Con `Occupation<80` (S3, con terminales): **−4,39 %** total (toA −5,03 %, toB −3,68 %): **confirma el «4,4 % de bajadas de menos»**. Sin limpiar (S0/S2) las sumas están dominadas por valores absurdos de las columnas (millones de pasajeros) y no son interpretables.
- **4.3** Mediana por expedición (S3, con terminales): +3 (toA) y +2 (toB) subidas más que bajadas; 70,5 % (toA) y 64,6 % (toB) de las expediciones tienen más subidas que bajadas.
- **4.4** Ocupación calculada en la última parada (S3): mediana 3 (toA) y 2 (toB), media 3,6 y 2,5, rango −58…75 y −49…93. La ocupación registrada en la última parada tiene mediana 1.
- **4.5** Antes de la limpieza, la ocupación acumulada se vuelve negativa en alguna parada en el **22,2 % (toA)** y **28,3 % (toB)** de las expediciones completas; con la ocupación *registrada*, en el 2,3 % y 5,5 % de todas las expediciones. Tras la limpieza, la acumulada sigue siendo negativa en 21,9 % y 25,9 %: la limpieza elimina valores absurdos pero no la deriva.
- **4.6** **El desequilibrio agregado depende de incluir las terminales**: sin ellas sale **−19,3 % (toA) y +20,5 % (toB)** (S3), de signo opuesto en cada sentido, frente a −5,0 % y −3,7 % con ellas. Las terminales concentran las mayores magnitudes (toA, subconjunto S3 con `Occupation<80`: ver `tables/t4_per_stop_net.csv`), así que no se puede atribuir el −4,4 % a las terminales ni al resto de la ruta por separado con estos datos. En la parada de origen, `Occupation = Board − DropOff` solo en el 26–28 % de las visitas (Tarea 0.3), coherente con el comentario del artículo sobre el cambio de expedición mal registrado.

---

## Tarea 5. Relación entre bajadas y carga

**Cómo:** `scripts/t4_t5.py`. Carga a la llegada = `Occupation` de la parada anterior de la misma expedición (visitas consecutivas, ambas tras la limpieza). Franja = `TimeSlot.1`. Correlaciones con `scipy.stats.pearsonr/spearmanr` por combinación parada×franja con n≥3 y varianza no nula; «significativa positiva» = p<0,05 y r>0 (sin corrección por comparaciones múltiples).

{S('t5_alighting_load')}

**Lectura:** las bajadas están **fuertemente ligadas a la carga**: correlación mediana 0,40 (toA) y 0,53 (toB), positiva y significativa en el 92 % y 95 % de las combinaciones. Esto choca con el supuesto del simulador de que las bajadas se sortean por llegada **independientemente de la carga** (artículo, sección 3.2). La fracción que baja varía mucho por parada (≈2–5 % en las paradas iniciales, ≈24–53 % en las paradas de intercambio, ≈100 % en la terminal final). Nota: en las paradas terminales la fracción puede superar 1 (la carga a la llegada registrada es menor que las bajadas).

---

## Tarea 6. Detalles metodológicos (lectura del código)

Referencias a `.ipynb` con la línea del JSON y la celda. Salvo indicación, las funciones están en `DATOS/src/final_analysis_board_dropoff.ipynb` celda 4.

**6.1 Tests de bondad de ajuste.**
- **Normal:** *no* es chi-cuadrado. `is_normal_simplified` (`DATOS/src/fussion_gauss.py:40-72`) es un test de asimetría y curtosis: z = asimetría/√(6/n) y curtosis exceso/√(24/n); con n<50 se acepta si |z|≤1,96; con 50≤n<300 si |z|≤3,29; con n≥300 se abandonan los z y se acepta si |asimetría|≤2 y |curtosis exceso|+3≤7 (umbrales absolutos, sin nivel de significación). Parámetros: media muestral y desviación típica poblacional (`central_moment(·,2)`, ddof=0) en el test; `select_by_aic` usa media y desviación ddof=1. `test_normal_chi2` (línea 327) está definida pero **no se llama** en ninguna celda.
- **Binomial negativa:** `test_negative_binomial` (línea 279): chi-cuadrado de Pearson, α=0,05, parámetros por **método de momentos** (p = media/varianza, r = media·p/(1−p)); si varianza ≤ media se rechaza directamente. Clases: cada valor entero distinto observado; esperados = n·pmf. Agrupamiento: los valores con esperado <5 se juntan en **una sola clase final** (se añade siempre, aunque esté vacía). Grados de libertad: clases − 1 − 2 (mín. 1). **Fallo detectado:** si todos los esperados son ≥5 la clase final queda con 0/0, el estadístico es NaN y `p_value > alpha` es falso: la candidata se rechaza. Ocurre en {J['nan_nb']} de {J['tot']} combinaciones. Ejemplos impresos y efecto de corregirlo: sección «6.1 bis» más abajo.
- **Geométrica:** `test_geometric` (línea 232): chi-cuadrado, α=0,05, **máxima verosimilitud** (p = 1/(1+media)), clases = valores distintos, esperados n·(1−p)^k·p, agrupamiento de esperados <5 en una clase (solo si existe alguna), gl = clases − 1 − 1. **Fallo detectado:** si tras agrupar quedan ≤2 clases (p. ej. todas con esperado <5, o solo valores 0 y 1) gl ≤ 0 y el p-valor es NaN (se rechaza): {J['nan_g']} de {J['tot']} combinaciones.
- Las clases no incluyen los enteros no observados entre medias, por lo que la distribución esperada no suma n.

**6.2 AIC** (`select_by_aic`, línea 499; `study_abnormal`, línea 422): AIC = −2·log-verosimilitud + 2k con k = 1 (geométrica, línea 543), 2 (binomial negativa, línea 531) y 2 (normal, línea 519). Log-verosimilitud: geométrica `log((1−p)^x·p)` con MLE; binomial negativa `nbinom.logpmf` con **parámetros por momentos** (no MLE); normal `norm.logpdf` (una densidad, no una masa) con σ ddof=1. El AIC de la normal (densidad) y el de las discretas (masa) no son estrictamente comparables. Entre las candidatas no rechazadas gana el AIC mínimo; si las tres se rechazan se evalúan las tres y se elige igualmente el mínimo (`study_abnormal`). Resultado de esa rama: 27+26 combinaciones de subidas y 18+19 de bajadas (Tarea 3.4).

**6.3 Normal → conteo.**
- GAML (`GAMA/src/TEST_MOBILITY/models/mobility_performance.gaml`): `sample_distribution` (línea 133) devuelve `max(0.0, gauss(μ,σ))` (línea 136), es decir **recorta a 0 primero**. Para bajadas, `infer_dropoffs` (línea 160) aplica después `int(floor(...))` (**trunca**; no redondea). Para subidas el valor (tasa horaria) se usa como `float` sin redondear (líneas 853, 857, 865).
- C (`C_REWRITE/src/`): `sample_normal` (`math/distributions/normal.c:29`) devuelve μ+σ·Z **sin recortar**; en bajadas (`engine/simulation.c:55-58`) se recorta a [0, `MAX_OCCUPANCY`=80] y luego `(u16)ret_val` trunca (mismo orden que GAML, con cota superior añadida). Para subidas la tasa sale de `.random(...)` sin recorte en `simulation.c:187-192, 215-220, 261, 292` y entra en `linear_conservative_reconstruction` (`math/math_utils.c:7-57`), que interpola linealmente sin recortar; **en C no hay recorte a 0 de las tasas de subida** (ni en `sample_normal` ni en la reconstrucción), a diferencia del GAML, que sí recorta (`max(0.0, …)`).
- Nota (regla 5): el GAML del repositorio lee `../includes/INPUTS/old_input_data_E01_toA.csv` (línea 181); esos ficheros están en `BASE_DATA/`, no en `GAMA/.../INPUTS/`, donde hay `input_data_E01_*.csv` (solo subidas, sin columna `DataType`) y `alighting_params_*.csv` (beta-binomial). No he podido determinar con cuál se ejecutó el artículo.

**6.4 MAD** (`remove_outliers_mad`, línea 391): umbral **3** (`threshold=3`) y **sí se aplica la constante 1,4826** (`mad_scaled = 1.4826 * mad`, línea 410); se elimina lo que cumple |x − mediana|/(1,4826·MAD) > 3. Si MAD = 0 la función devuelve los datos sin tocarlos: ocurre en 245 de 1.016 combinaciones (24 %), en conteos con muchos valores repetidos. (Para ocupación y tiempos de viaje se usa otro método, ESD generalizado, `estimate_outliers`, `generate_gaussian.py:195`.)

**6.5 Capacidad.** El simulador usa **80** pasajeros: `mobility_performance.gaml:1191` (`int max_passengers <- 80;`, comentario «All buses have the same maximum capacity») y `C_REWRITE/src/agents/bus/bus.h:14` (`#define MAX_OCCUPANCY 80`); es un valor fijado en el código (no hay fuente de datos en el repositorio). Con el corte `Occupation < 80` **la limpieza elimina todas las visitas con ocupación ≥ capacidad**. Visitas eliminadas por `Occupation ≥ 80` (sobre las visitas de días normales que pasan el resto de filtros):

{S('t6_computed')}

De las 832 visitas eliminadas en toA, **151 tienen exactamente 80**; de las 470 de toB, **55** (el resto supera 80). El desglose por franja está en la tabla anterior y en `tables/t6_5_removed_by_occupation_cut.csv` (también con la definición de franja de servicio). La franja 5 y las franjas punta de la mañana en toA (5–7 h) concentran los mayores porcentajes (1,2–1,9 %).

**6.6 Franjas.** Son horarias, de 5 a 23 (19 franjas): `timeslot = [5,…,23]` (`final_analysis_board_dropoff.ipynb` celda 3) y en el simulador `TimeSlot <- 5 + int(total_minutes / 60)` (`mobility_performance.gaml:799`). En los datos `TimeSlot` es la hora de `EventTime` y `TimeSlot.1` la hora de `EventTime.1` (comprobado: 100 % de coincidencia). **Entradas** (subidas, bajadas, tiempos): franja del momento de servicio, `TimeSlot.1` (`final_analysis_board_dropoff.ipynb` líneas 191 y 881; `analysis_time_between_stops.ipynb` líneas 1216-1217 (toA) y 1476-1477 (toB)). **Referencia de validación** (ocupación): franja de salida desde terminal, `TimeSlot` (`generate_gaussian.py:296, 407, 442` y `analisis_ALL_OCCUPATION.ipynb`, función de la línea 45). Ambas definiciones confirmadas.

### 6.1 bis. Casos con p-valor NaN y efecto de corregirlos (`scripts/nan_and_bug.py`)

Las réplicas impresas de los dos tests coinciden con `test_negative_binomial` y `test_geometric` en las 1.016 combinaciones. Corrección aplicada: no crear la clase final vacía (la clase agrupada solo se añade si algún esperado es <5) y exigir al menos 1 grado de libertad; si gl<1 el test no es aplicable y el candidato se mantiene o se descarta (dos políticas).

{S('t6_nan_correction')}

### Celda con `if is_normal or neg_bin or geom:` y valor de `neg_bin` y `geom` en una combinación terminal (`scripts/nan_and_bug.py`)

```
{S('t10_bug_cell')}
```

---

## Tarea 7. Efecto de la eliminación de outliers en las colas

**Cómo:** `scripts/fits.py` y `scripts/t3_t7.py` (`remove_outliers_mad`; percentiles con `np.percentile`, interpolación lineal, sobre los mismos datos antes y después).

{'### 7.1'+S('t3_t7').split('### 7.1')[1]}

**Lectura:** la regla elimina ≈1,5 % de las observaciones (1,3 % en subidas, 1,6 % en bajadas); el p99 baja en mediana un 2,7–10 % según variable y sentido, hasta un 77 % en la combinación más afectada (toA, subidas, parada 82, 16 h: p99 38,35 → 9). Los percentiles 90 y 95 apenas cambian en mediana. Detalle completo por combinación en `tables/t7_tail_per_combination.csv`.

---

## Tarea 8. Visitas a capacidad y censura de la demanda

**Cómo:** `scripts/t8_t9.py`. Capacidad = 80 (Tarea 6.5); umbral del 90 % = 72. Dos estados: **A** antes del corte superior de ocupación (todos los demás filtros del pipeline aplicados); **B** tras `Occupation<80`. En B el porcentaje a capacidad es 0 por construcción; el indicador sólo es medible en A. Franja = `TimeSlot` (salida; referencia de validación); versiones por `TimeSlot.1` se pueden obtener con el mismo script cambiando la columna.

{S('t8_capacity')}

**Lectura:** antes del corte, el **0,49 % (toA) y 0,35 % (toB)** de las visitas están a capacidad (≥80) y el 2,0 % y 1,5 % al ≥90 %. Se concentran en las franjas de 5–8 h de toA (hasta 1,9 % a capacidad en la franja 5) y en 14–18 h de toB (≥72 en el 1,8–3,9 %). En esos momentos pudo haber pasajeros que no subieron y que el APC no registra; el recorte de la limpieza elimina esas visitas del ajuste de la ocupación, por lo que **el indicador de visitas a capacidad del simulador no es contrastable con los datos limpios**.

---

## Tarea 9. Franjas de entrada frente a franjas de referencia

**Cómo:** `scripts/t8_t9.py`. Por visita (tras la limpieza): `TimeSlot` (salida) frente a `TimeSlot.1` (servicio). Figura (1 col.): `figures/fig_slot_mismatch.pdf`, datos `figures/fig_slot_mismatch_data.csv`.

{S('t9_slots')}

**Lectura:** las dos franjas difieren en el **38,2 % (toA) y 40,4 % (toB)** de las visitas; en la primera parada ≈0,3 % y crece a lo largo del recorrido hasta ≈64 % en la última parada de toB (correlación con el orden de parada 0,996 en toA y 0,974 en toB).

---

## Tarea 10. Tabla de no rechazo

**Cómo:** subidas y bajadas: `scripts/fits.py` (+ `t10.py`), mismo procedimiento que el notebook (MAD → tres contrastes → no rechazada si alguna de las tres no se rechaza; `final_analysis_board_dropoff.ipynb` celdas 5 y 8). Ocupación: función `generate_gaussian_per_slot_all_days` cargada literalmente de `analisis_ALL_OCCUPATION.ipynb` (celda 2) y ejecutada por fichero de parada tras `clean_dataframe` (`scripts/t10_heavy.py`). Tiempos de viaje: lógica de `analysis_time_between_stops.ipynb` celda 14 (pares de visitas por `TripId`, diferencia de `EventTime.1`, `is_normal_simplified`, y si falla ESD con hasta 20 outliers y nueva prueba), con `estimate_outliers` de `generate_gaussian.py:195`. Los tiempos de viaje no se usan MAD sino ESD. Test binomial de la proporción frente a 0,95 (`scipy.stats.binomtest`, bilateral) con **intervalo de Wilson al 95 %**. Los N cuentan combinaciones que no son independientes (misma parada o franja), por lo que los p-valores son orientativos.

{S('t10_nonrejection')}
{extra10}
**Lectura:**
- **10.1/10.2** Las ocho cifras coinciden con el artículo y con N = 266/209 (subidas y bajadas toA/toB y tiempos), 285/228 (ocupación).
- **10.3** Frente a 0,95: subidas (ambos sentidos), bajadas hacia La Peseta y ocupación hacia La Peseta quedan **significativamente por debajo** (p<0,05); bajadas hacia Cibeles, ocupación hacia Cibeles y tiempos hacia Cibeles son compatibles con 0,95. Tiempos hacia La Peseta (90,43 %, p=0,006) también por debajo, pero con las 11 combinaciones sin servicio de la franja 5 incluidas en N (sin ellas 95,45 %).
- **Matiz del bug:** las filas «as published» de subidas y bajadas incluyen 19 combinaciones terminales contadas como no rechazadas por el fallo de `if is_normal or neg_bin or geom`. Con el resultado real, las subidas hacia Cibeles son 90,23 % (240/266).
- **10.4** Los rechazos de ocupación se concentran en la franja 23 (33 % de no rechazo; {J['n23']} de {J['n_rej']} rechazos) **y** en las paradas terminales (ver desglose arriba): no es sólo un efecto de la última franja.

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
| Rechazos de ocupación concentrados en la última franja | {100*n23/n_rej:.1f} % de los rechazos en la franja 23; {n_term} de {n_rej} en paradas terminales | **Parcial** | 10.4 |
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
"""
open(f"{ROOT}/analysis_paper/RESULTS.md","w").write(doc+S('rev3'))
print(len(doc))
