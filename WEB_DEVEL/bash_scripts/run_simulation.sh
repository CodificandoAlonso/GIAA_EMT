#!/bin/bash

# ==========================================================================
# Batch execution pipeline. Soporta dos motores:
#
#   gama  -> GAMA headless sobre el proyecto copiado (comportamiento previo,
#            sin cambios).
#   c     -> binario C_REWRITE/simulation.
#
# El motor se lee de 'model' en description.txt, que escribe la pagina de
# configuracion. No se decide en prepare_simulation.sh porque cuando ese
# script corre description.txt aun esta vacio: el usuario elige el motor
# despues, y en ambos casos las entradas que edita son las del proyecto GAMA
# copiado.
#
# Nota sobre el motor en C: todas las rutas de su .env son RELATIVAS
# (data/..., data/outputs/...) y quedan fijadas como macros -D en tiempo de
# compilacion. Una ruta relativa se resuelve contra el directorio de trabajo
# del proceso, de modo que basta con lanzarlo con cd al directorio de la
# simulacion para que lea y escriba dentro de ella. Ni se recompila por
# simulacion ni se toca el codigo C.
#
# Author: Héctor Álvarez Marcos
# ==========================================================================

# ----------------------------- Settings ------------------------------

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_DIR=$(cat ./.last_simulation)
GAMA_SRC="/opt/headless/"
MODEL_NAME="${GAMA_MODEL_NAME:-mobility_performance.gaml}"
BATCH_NAME="batch_1000"
SIM_MODEL_PATH="${BASE_DIR}/TEST_MOBILITY/models/${MODEL_NAME}"

# [MOD] 16 -> 12: debe coincidir con el numero de CPUs del cpuset del
# contenedor (0-11 = los 12 hilos logicos de los 6 P-cores). Con 16 hilos
# contra 12 CPUs habria throttling CFS y varianza no determinista.
GAMA_HPC_CORES=12

C_HPC_CORES=5

# [MOD] Heap: 16384m excedia el limite de 14G del contenedor. La JVM ignora
# el cgroup cuando -Xmx es explicito, asi que el kernel habria matado el
# contenedor a mitad de batch. 11G heap + ~1.5G off-heap + Node ~= 12.7G.
# Este valor DEBE ser identico en ambas soluciones: el tamano de heap
# determina la frecuencia de GC y por tanto el consumo energetico.
JAVA_HEAP="11264m"

# [MOD] SCRIPT_DIR se necesita ya en la Fase 1 (antes estaba en la Fase 6)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# [MOD] Directorio de monitorizacion. Cuelga de BASE_DIR, fuera de
# TEST_MOBILITY/, asi que la Fase 4 no tiene que moverlo.
MONITOR_DIR="${BASE_DIR}/MONITOR"

LOG_FILE="${BASE_DIR}/log_result_${BASE_DIR: -15}.log"

# ----------------------- [NUEVO] Motor de simulacion ----------------------

# Binario y datos de referencia del motor en C (definidos en el Dockerfile).
C_BIN="${EMT_C_BIN:-/app/C_REWRITE/simulation}"
C_DATA_REF="${EMT_C_DATA_REF:-/app/C_REWRITE/data}"

# El muestreador de recursos con --interval 2 daria una o dos muestras sobre
# una ejecucion de segundos: la integral de energia no significaria nada.
MONITOR_INTERVAL_GAMA="${EMT_MONITOR_INTERVAL_GAMA:-2}"
MONITOR_INTERVAL_C="${EMT_MONITOR_INTERVAL_C:-0.1}"

# Analisis: SIM_PLOTS=none omite las ~1000 figuras por celda y deja los JSON
# y los CSV de Bhattacharyya.
export SIM_PLOTS="${SIM_PLOTS:-all}"
export SIM_PLOT_DPI="${SIM_PLOT_DPI:-300}"
export SIM_WORKERS="${SIM_WORKERS:-$C_HPC_CORES}"

# 'model' en description.txt -> motor. Cualquier valor que no sea c_engine
# (incluida su ausencia) cae en GAMA, que es el comportamiento previo.
ENGINE_KEY=$(grep -E '^[[:space:]]*model[[:space:]]' "$BASE_DIR/description.txt" 2>/dev/null \
             | head -1 | awk '{print $2}' | tr -d '"')
if [ "$ENGINE_KEY" = "c_engine" ]; then
    ENGINE="c"
    ANALYSIS_SCRIPT="${SCRIPT_DIR}/new_c_eval.py"
    HPC_CORES=$C_HPC_CORES
else
    ENGINE="gama"
    ANALYSIS_SCRIPT="${SCRIPT_DIR}/data_extractor.py"
    HPC_CORES=$GAMA_HPC_CORES
fi

# 'seed' en description.txt -> MASTER_SEED (lo lee el binario en C, que aborta
# si no esta definido). La pagina de configuracion siempre la escribe; si falta
# o no es un entero de 64 bits se genera una y se anota en description.txt para
# que la ejecucion sea reproducible.
MASTER_SEED=$(grep -E '^[[:space:]]*seed[[:space:]]' "$BASE_DIR/description.txt" 2>/dev/null \
              | head -1 | awk '{print $2}' | tr -d '"')
# Cota 2^64-1 comparada como texto: la aritmetica de bash es de 64 bits con signo.
if ! [[ "$MASTER_SEED" =~ ^[0-9]{1,20}$ ]] \
   || { [ ${#MASTER_SEED} -eq 20 ] && [[ "$MASTER_SEED" > "18446744073709551615" ]]; }; then
    MASTER_SEED=$(od -An -N8 -tu8 /dev/urandom | tr -d ' ')
    sed -i '/^[[:space:]]*seed[[:space:]]/d' "$BASE_DIR/description.txt" 2>/dev/null
    echo "seed $MASTER_SEED" >> "$BASE_DIR/description.txt"
    SEED_GENERATED="yes"
fi
export MASTER_SEED

# ----------------------------- FUNCIONES ----------------------------------

format_time() {
    local total_seconds=${1:-0}
    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))

    if [ $hours -gt 0 ]; then
        echo "${hours}h ${minutes}m ${seconds}s"
    elif [ $minutes -gt 0 ]; then
        echo "${minutes}m ${seconds}s"
    else
        echo "${seconds}s"
    fi
}

log_info() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Marcadores de estado que lee el servidor (server.js, simStatus):
#   .error -> la ejecucion ha fallado. Una linea por fallo con el formato
#             "fecha|FASE|codigo|mensaje"; la primera es la causa que se
#             muestra en la interfaz.
#   .done  -> simulacion y analisis terminados sin ningun error: las graficas
#             y los JSON estan completos.
ERROR_FILE="${BASE_DIR}/.error"
DONE_FILE="${BASE_DIR}/.done"

# record_error FASE CODIGO MENSAJE
record_error() {
    log_error "$3"
    printf '%s|%s|%s|%s\n' "$(date +'%Y-%m-%d %H:%M:%S')" "$1" "$2" "${3//|//}" >> "$ERROR_FILE"
}

has_error() {
    [ -s "$ERROR_FILE" ]
}

cleanup_on_exit() {
    echo ""
    log_warning "Execution interrupted by user"
    record_error "INTERRUPTED" 130 "Ejecucion interrumpida por una senal (SIGINT/SIGTERM)"
    # [MOD] SIGTERM (no -9) al monitor: necesita capturarlo para volcar el
    # summary. Con -9 se pierde la ejecucion interrumpida entera.
    if [ -n "${MONITOR_PID:-}" ]; then
        log_warning "TERMINATING MONITOR PROCESS... ${MONITOR_PID}"
        kill -TERM $MONITOR_PID 2>/dev/null
        wait $MONITOR_PID 2>/dev/null
    fi
    log_warning "TRYING TO TERMINATE SIMULATION PROCESS... ${SIM_PID:-}"
    kill -9 ${SIM_PID:-} 2>/dev/null
    rm -rf ./.workspace*
    log_info "Cleanup done after interruption"
    exit 1
}
trap cleanup_on_exit SIGINT SIGTERM

# ========================== BEGIN ===========================

PIPELINE_START=$(date +%s)

# Un relanzamiento parte de cero: se descartan los marcadores de la ejecucion anterior.
rm -f "$ERROR_FILE" "$DONE_FILE"

log_info "=========================================="
log_info "  SIMULATION EXECUTION PIPELINE"
log_info "=========================================="
log_info "Engine: $ENGINE (model key: ${ENGINE_KEY:-<unset>})"

log_info "HPC cores: $HPC_CORES"
if [ -n "${SEED_GENERATED:-}" ]; then
    log_warning "No valid seed in description.txt, generated one"
fi
log_info "MASTER_SEED: $MASTER_SEED"


log_info "Simulation directory: $BASE_DIR"

# ------------------- FASE 1: EJECUCIÓN ----------------------------------

BATCH_START=$(date +%s)

log_info "--- Phase 1: Simulation ---"

# [MOD] El directorio del monitor debe existir antes de exportar
# JAVA_TOOL_OPTIONS, porque el log de GC escribe dentro.
mkdir -p "$MONITOR_DIR"

if [ "$ENGINE" = "gama" ]; then

    log_info "Batch experiment: $BATCH_NAME"
    log_info "JVM heap: $JAVA_HEAP"
    log_info "Starting GAMA headless batch execution against copied project..."

    # Extract total simulations from batch name (batch_1000 → 1000)
    TOTAL_SIMS="${BATCH_NAME##*_}"

    # Results land inside the copied project
    RESULTS_DIR="$BASE_DIR/TEST_MOBILITY/logs/RESULTS"

    # [MOD] -Xlog:gc* anadido. El pico de heap real del log de GC es exacto;
    # memory.peak del cgroup mide RSS del arbol completo. Son complementarios:
    # a 2s de muestreo se pierden picos transitorios de GC.
    #debug flags disable to enable boost performance
    export JAVA_TOOL_OPTIONS="-Denable_debug=false -Denable_logging=false -XX:+UseG1GC -Xlog:gc*:file=${MONITOR_DIR}/gc.log:time,uptime,level:filecount=1,filesize=100m"

    #-m heap and HPC_CORES "threads" which parallelyzes the simulations
    "${GAMA_SRC}gama-headless.sh" -m $JAVA_HEAP -hpc $HPC_CORES -batch $BATCH_NAME "$SIM_MODEL_PATH" \
    >> "$LOG_FILE" 2>&1 &

    SIM_PID=$!

    # [MOD] Muestreador de recursos del contenedor (cgroup v2). Lee el cgroup,
    # no $SIM_PID, porque gama-headless.sh es un wrapper y el trabajo real
    # esta en el proceso java hijo. --watch-pid solo sirve de red de seguridad.
    python3 "${SCRIPT_DIR}/monitor_resources.py" \
        --outdir "$MONITOR_DIR" \
        --results-dir "$RESULTS_DIR" \
        --watch-pid "$SIM_PID" \
        --cores "$HPC_CORES" \
        --interval "$MONITOR_INTERVAL_GAMA" \
        --label "${MODEL_NAME%.gaml}" >> "$LOG_FILE" 2>&1 &
    MONITOR_PID=$!
    log_info "Resource monitor started (PID $MONITOR_PID) -> $MONITOR_DIR"

    echo ""

    # Progress bar loop
    while kill -0 $SIM_PID 2>/dev/null; do
        COMPLETED=$(find "$RESULTS_DIR" -name "*.csv" 2>/dev/null | wc -l)
        PERCENT=$((COMPLETED * 100 / TOTAL_SIMS))
        FILLED=$((PERCENT * 30 / 100))
        ELAPSED=$(($(date +%s) - BATCH_START))

        if [ $COMPLETED -gt 0 ]; then
            ETA=$(( (ELAPSED * TOTAL_SIMS / COMPLETED) - ELAPSED ))
            ETA_STR="ETA: $(format_time $ETA)"
        else
            ETA_STR="ETA: calculating..."
        fi

        BAR=""
        for ((i=0; i<FILLED; i++)); do BAR="${BAR}#"; done
        for ((i=FILLED; i<30; i++)); do BAR="${BAR}-"; done

        printf "\r  [%s] %3d%% (%d/%d) %s | %s " \
            "$BAR" \
            "$PERCENT" "$COMPLETED" "$TOTAL_SIMS" \
            "$(format_time $ELAPSED)" "$ETA_STR"

        sleep 2
    done

    # Final progress bar update
    COMPLETED=$(find "$RESULTS_DIR" -name "*.csv" 2>/dev/null | wc -l)
    ELAPSED=$(($(date +%s) - BATCH_START))

    BAR=""
    for ((i=0; i<30; i++)); do BAR="${BAR}#"; done

    printf "\r  [%s] 100%% (%d/%d) %s | Done!                \n" \
        "$BAR" \
        "$COMPLETED" "$TOTAL_SIMS" \
        "$(format_time $ELAPSED)"

    echo ""

    wait $SIM_PID
    SIM_EXIT_CODE=$?

else
    # ------------------------- Motor en C ------------------------------
    #
    # Las entradas se montan en $BASE_DIR/data/ con los nombres exactos que
    # el binario tiene compilados, y las salidas apareceran en
    # $BASE_DIR/data/outputs/. Se copian desde el proyecto GAMA copiado,
    # que es lo que edita la pagina de configuracion: asi ambos motores
    # parten literalmente del mismo fichero de entrada.

    log_info "Binary: $C_BIN"

    if [ ! -x "$C_BIN" ]; then
        log_error "Rebuild the image (make release) or set EMT_C_BIN"
        record_error "SETUP" 1 "C engine binary not found or not executable: $C_BIN"
        exit 1
    fi

    C_INPUTS="$BASE_DIR/C_REWRITE/data"
    if [ ! -d "$C_INPUTS" ]; then
        record_error "SETUP" 1 "Inputs not found at $C_INPUTS. Was the simulation prepared?"
        exit 1
    fi

    mkdir -p "$BASE_DIR/data/outputs"

    for f in input_data_E01_toA.csv input_data_E01_toB.csv \
             input_times_stops_toA.csv input_times_stops_toB.csv \
             alighting_params_toA.csv alighting_params_toB.csv \
             final_input.json; do
        if [ ! -f "$C_INPUTS/$f" ]; then
            record_error "SETUP" 1 "Missing input file: $C_INPUTS/$f"
            exit 1
        fi
        cp "$C_INPUTS/$f" "$BASE_DIR/data/$f"
    done


    # input_stops.txt no lo gestiona la interfaz: es fijo por linea y se
    # toma de la copia de referencia que va dentro de la imagen.
    if [ ! -f "$C_DATA_REF/input_stops.txt" ]; then
        record_error "SETUP" 1 "Missing reference file: $C_DATA_REF/input_stops.txt"
        exit 1
    fi
    cp "$C_DATA_REF/input_stops.txt" "$BASE_DIR/data/input_stops.txt"

    log_info "Inputs staged at $BASE_DIR/data"

    RESULTS_DIR="$BASE_DIR/data/outputs"

    # cd al directorio de la simulacion: es lo que hace que las rutas
    # relativas compiladas en el binario apunten aqui dentro.
    ( cd "$BASE_DIR" && exec "$C_BIN" ) >> "$LOG_FILE" 2>&1 &
    SIM_PID=$!

    python3 "${SCRIPT_DIR}/monitor_resources.py" \
        --outdir "$MONITOR_DIR" \
        --results-dir "$RESULTS_DIR" \
        --watch-pid "$SIM_PID" \
        --cores "$HPC_CORES" \
        --interval "$MONITOR_INTERVAL_C" \
        --label "c_engine" >> "$LOG_FILE" 2>&1 &
    MONITOR_PID=$!
    log_info "Resource monitor started (PID $MONITOR_PID) -> $MONITOR_DIR"

    echo ""
    while kill -0 $SIM_PID 2>/dev/null; do
        printf "\r  running... %s " "$(format_time $(($(date +%s) - BATCH_START)))"
        sleep 1
    done
    printf "\r  done in %s                    \n" \
        "$(format_time $(($(date +%s) - BATCH_START)))"
    echo ""

    wait $SIM_PID
    SIM_EXIT_CODE=$?
fi

# [MOD] Cerrar el monitor DESPUES de que la simulacion termine, con SIGTERM
# para que vuelque monitor_summary.json antes de salir.
log_info "Stopping resource monitor..."
kill -TERM "$MONITOR_PID" 2>/dev/null
wait "$MONITOR_PID" 2>/dev/null
MONITOR_PID=""

BATCH_END=$(date +%s)
BATCH_TIME=$((BATCH_END - BATCH_START))

if [ $SIM_EXIT_CODE -eq 0 ]; then
    log_success "Simulation completed in $(format_time $BATCH_TIME)"
else
    record_error "SIMULATION" "$SIM_EXIT_CODE" \
        "Simulation ($ENGINE) FAILED with exit code $SIM_EXIT_CODE after $(format_time $BATCH_TIME)"
fi

# ------------------- FASE 4: EXTRACCIÓN Y LIMPIEZA -----------------------

POST_CLEANUP_START=$(date +%s)

log_info "--- Phase 4: Extract & Cleanup ---"
log_info "Extracting results, events, and inputs..."

if [ "$ENGINE" = "gama" ]; then
    # Move results and events out of the copied project
    mv "$BASE_DIR/TEST_MOBILITY/logs/RESULTS" "$BASE_DIR/RESULTS"
    mv "$BASE_DIR/TEST_MOBILITY/logs/EVENTS"  "$BASE_DIR/EVENTS"
    mv "$BASE_DIR/TEST_MOBILITY/logs/PASSENGERS" "$BASE_DIR/PASSENGERS"
else
    # El motor en C emite un unico fichero por magnitud. Se colocan con los
    # nombres que espera new_c_eval.py.
    mkdir -p "$BASE_DIR/RESULTS" "$BASE_DIR/EVENTS" "$BASE_DIR/PASSENGERS"
    [ -f "$BASE_DIR/data/outputs/results.csv" ] \
        && mv "$BASE_DIR/data/outputs/results.csv"    "$BASE_DIR/RESULTS/results.csv"
    [ -f "$BASE_DIR/data/outputs/passengers.csv" ] \
        && mv "$BASE_DIR/data/outputs/passengers.csv" "$BASE_DIR/PASSENGERS/passengers.csv"
    [ -f "$BASE_DIR/data/outputs/anomalies.csv" ] \
        && mv "$BASE_DIR/data/outputs/anomalies.csv"  "$BASE_DIR/EVENTS/anomalies.csv"
fi

mkdir -p "$BASE_DIR/PLOTS"
mkdir -p "$BASE_DIR/PLOTS/to_A"
mkdir -p "$BASE_DIR/PLOTS/to_A/stops"
mkdir -p "$BASE_DIR/PLOTS/to_A/times"
mkdir -p "$BASE_DIR/PLOTS/to_B"
mkdir -p "$BASE_DIR/PLOTS/to_B/stops"
mkdir -p "$BASE_DIR/PLOTS/to_B/times"
mkdir -p "$BASE_DIR/PLOTS/general"
mkdir -p "$BASE_DIR/PLOTS/buses"

# [MOD] Subdirectorio para las figuras de monitorizacion
mkdir -p "$BASE_DIR/PLOTS/monitoring"

if [ "$ENGINE" = "gama" ]; then
# Keep the inputs that drove this simulation
mv "$BASE_DIR/TEST_MOBILITY/includes"     "$BASE_DIR/includes"
else
mv "$BASE_DIR/C_REWRITE/data" "$BASE_DIR/includes"
fi


log_info "Removing copied GAMA project files..."
rm -rf "$BASE_DIR/TEST_MOBILITY"

log_info "Removing copied C proyect files..."
rm -rf "$BASE_DIR/C_REWRITE"

if [ "$ENGINE" = "c" ]; then
    # Los CSV ya se han movido; data/ solo contiene copias de las entradas,
    # que quedan conservadas en includes/.
    log_info "Removing C engine staging directory..."
    rm -rf "$BASE_DIR/data"
fi

log_info "Removing GAMA workspace directories..."
rm -rf ./.workspace*

POST_CLEANUP_END=$(date +%s)
POST_CLEANUP_TIME=$((POST_CLEANUP_END - POST_CLEANUP_START))

log_success "Extract & cleanup completed in $(format_time $POST_CLEANUP_TIME)"

# ------------------- FASE 5: VALIDACIÓN DE RESULTADOS --------------------

log_info "--- Phase 5: Results Validation ---"

RESULT_FILES=$(find "$BASE_DIR/RESULTS" -name "*.csv" 2>/dev/null | wc -l)
EVENT_FILES=$(find "$BASE_DIR/EVENTS" -name "*.csv" 2>/dev/null | wc -l)
PASSENGER_FILES=$(find "$BASE_DIR/PASSENGERS" -name "*.csv" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BASE_DIR/RESULTS" 2>/dev/null | cut -f1)

log_info "Result CSV files generated: $RESULT_FILES"
log_info "Event CSV files generated: $EVENT_FILES"
log_info "Passenger CSV files generated: $PASSENGER_FILES"
log_info "Total results size: $TOTAL_SIZE"

if [ "$ENGINE" = "c" ]; then
    # Un fichero por magnitud, con cabecera. anomalies.csv puede faltar de
    # forma legitima: una ejecucion sin retrasos no genera eventos.
    # Ademas de existir, la cabecera debe empezar como la que escribe el
    # binario: el analisis no falla con ficheros corruptos, genera graficas vacias.
    for spec in "RESULTS/results.csv:simulation_id,bus_code,travels_completed,stop_num,direction" \
                "PASSENGERS/passengers.csv:simulation_id,bus_code,travels_completed,stop_num"; do
        f="${spec%%:*}"
        header="${spec#*:}"
        if [ ! -s "$BASE_DIR/$f" ]; then
            record_error "OUTPUTS" 1 "Missing or empty required output: $f"
            SIM_EXIT_CODE=1
        elif [[ "$(head -1 "$BASE_DIR/$f")" != "$header"* ]]; then
            record_error "OUTPUTS" 1 "Unexpected header in $f: $(head -1 "$BASE_DIR/$f" | cut -c1-80)"
            SIM_EXIT_CODE=1
        elif [ "$(wc -l < "$BASE_DIR/$f")" -lt 2 ]; then
            record_error "OUTPUTS" 1 "No data rows in $f"
            SIM_EXIT_CODE=1
        else
            log_info "$f: $(( $(wc -l < "$BASE_DIR/$f") - 1 )) rows"
        fi
    done
    if [ ! -s "$BASE_DIR/EVENTS/anomalies.csv" ]; then
        log_warning "EVENTS/anomalies.csv absent or empty (no delay events recorded)"
    fi
elif [ "$RESULT_FILES" -eq 0 ]; then
    record_error "OUTPUTS" 1 "GAMA produced no result CSV files in RESULTS/"
fi

# [MOD] Validacion de la monitorizacion: si el summary no existe, el
# batch no es utilizable para la comparacion energetica.
if [ -f "$MONITOR_DIR/monitor_summary.json" ]; then
    MONITOR_OK="yes"
    log_success "Resource monitor summary present"
else
    MONITOR_OK="NO"
    log_error "monitor_summary.json MISSING - this batch cannot be used for the energy comparison"
fi

# ------------------- FASE 6: DATA EXTRACTION & ANALYSIS -------------------

EXTRACTION_START=$(date +%s)

log_info "--- Phase 6: Data Extraction & Analysis ---"

# El script de analisis resuelve .last_simulation y todas las rutas
# relativas con os.getcwd(), asi que debe invocarse desde este directorio.
# [MOD] SCRIPT_DIR ya definido en el bloque de settings.

# --- Dependency check ---
REQUIRED_PACKAGES=("pandas" "numpy" "matplotlib" "scipy")
MISSING_PACKAGES=()
PLOT_COUNT=0
JSON_COUNT=0

# Sin resultados no hay nada que analizar: el analisis solo anadiria un
# segundo error que taparia la causa real.
if has_error; then
    log_warning "Skipping data extraction: the pipeline already failed (see $ERROR_FILE)"
    PYTHON_EXIT_CODE=1
    EXTRACTION_TIME=0
    SKIP_ANALYSIS="yes"
fi

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    [ -n "${SKIP_ANALYSIS:-}" ] && break
    if ! python3 -c "import ${pkg}" 2>/dev/null; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    log_warning "Missing Python packages: ${MISSING_PACKAGES[*]}"
    log_info "Installing missing dependencies..."
    pip3 install --break-system-packages "${MISSING_PACKAGES[@]}" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        record_error "DEPENDENCIES" 1 "Failed to install Python dependencies: ${MISSING_PACKAGES[*]}"
        PYTHON_EXIT_CODE=1
        EXTRACTION_END=$(date +%s)
        EXTRACTION_TIME=$((EXTRACTION_END - EXTRACTION_START))
    fi
else
    log_info "All Python dependencies satisfied"
fi

if [ -z "${SKIP_ANALYSIS:-}" ] && [ "${PYTHON_EXIT_CODE:-0}" -eq 0 ]; then
    log_info "Running $(basename "$ANALYSIS_SCRIPT") (plots=$SIM_PLOTS dpi=$SIM_PLOT_DPI workers=$SIM_WORKERS)..."

    python3 "$ANALYSIS_SCRIPT" >> "$LOG_FILE" 2>&1
    PYTHON_EXIT_CODE=$?

    EXTRACTION_END=$(date +%s)
    EXTRACTION_TIME=$((EXTRACTION_END - EXTRACTION_START))
fi

if [ $PYTHON_EXIT_CODE -eq 0 ] && ! has_error; then
    PLOT_COUNT=$(find "$BASE_DIR/PLOTS" -name "*.png" 2>/dev/null | wc -l)
    JSON_COUNT=$(find "$BASE_DIR/PLOTS" -name "*.json" 2>/dev/null | wc -l)
    log_success "Data extraction completed in $(format_time $EXTRACTION_TIME)"
    log_info "Generated $PLOT_COUNT plots and $JSON_COUNT JSON files"
    # Marca de finalizacion: se escribe al final del analisis, cuando ya
    # existen todas las figuras y JSON. El servidor la usa como "Graficas listas".
    touch "$DONE_FILE"
elif [ -z "${SKIP_ANALYSIS:-}" ]; then
    log_error "Check $LOG_FILE for Python traceback"
    record_error "ANALYSIS" "$PYTHON_EXIT_CODE" \
        "$(basename "$ANALYSIS_SCRIPT") FAILED with exit code $PYTHON_EXIT_CODE after $(format_time $EXTRACTION_TIME)"
fi

# ------------------- FINAL STRUCTURE LOG ----------------------------------

log_info "Final simulation directory structure:"
log_info "  $BASE_DIR/"
log_info "  ├── RESULTS/          (simulation output CSVs)"
log_info "  ├── EVENTS/           (event logs)"
log_info "  ├── PASSENGERS/       (passenger wait-time logs)"
log_info "  ├── MONITOR/          (resource timeseries, summary, GC log)"
log_info "  ├── PLOTS/"
log_info "  │   ├── to_A/         (occupation & time distribution plots)"
log_info "  │   ├── to_B/         (occupation & time distribution plots)"
log_info "  │   ├── general/      (aggregate occupation plots)"
log_info "  │   ├── monitoring/   (CPU, memory, power & progress plots)"
log_info "  │   ├── buses/        (per-bus per-trip plots + general_info.json)"
log_info "  │   └── json_output_general_info.json"
log_info "  ├── includes/         (frozen simulation parameters)"
log_info "  └── log_result_*.log  (pipeline log)"

# ========================= RESUMEN DE EJECUCIÓN ==========================

PIPELINE_END=$(date +%s)
TOTAL_TIME=$((PIPELINE_END - PIPELINE_START))

echo ""
echo "==========================================" | tee -a "$LOG_FILE"
echo "     EXECUTION SUMMARY" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "0. Engine:" "$ENGINE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
# [MOD] CLEANUP_TIME y SNAPSHOT_TIME vienen de prepare_simulation.sh, que es
# OTRO proceso: sus variables no se heredan. Antes se imprimia "0s" en
# silencio (falso positivo). Ahora se marca como no disponible.
printf "%-35s %s\n" "1. Pre-cleanup:" "${CLEANUP_TIME:+$(format_time $CLEANUP_TIME)}${CLEANUP_TIME:-n/a (prepare_simulation.sh)}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "2. Project snapshot:" "${SNAPSHOT_TIME:+$(format_time $SNAPSHOT_TIME)}${SNAPSHOT_TIME:-n/a (prepare_simulation.sh)}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "3. Simulation:" "$(format_time $BATCH_TIME)" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Exit code:" "$SIM_EXIT_CODE" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Result files:" "$RESULT_FILES" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Total size:" "$TOTAL_SIZE" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - HPC cores:" "$HPC_CORES" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Master seed:" "$MASTER_SEED" | tee -a "$LOG_FILE"
if [ "$ENGINE" = "gama" ]; then
printf "%-35s %s\n" "   - JVM heap:" "$JAVA_HEAP" | tee -a "$LOG_FILE"
fi
printf "%-35s %s\n" "   - Monitor summary:" "$MONITOR_OK" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "4. Extract & cleanup:" "$(format_time $POST_CLEANUP_TIME)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "5. Data extraction & analysis:" "$(format_time $EXTRACTION_TIME)" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Exit code:" "$PYTHON_EXIT_CODE" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Plots generated:" "$PLOT_COUNT" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - JSON files generated:" "$JSON_COUNT" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "------------------------------------------" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "TOTAL PIPELINE TIME:" "$(format_time $TOTAL_TIME)" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Simulation: $BASE_DIR" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if has_error; then
    log_error "=== Pipeline finished with errors: $(head -1 "$ERROR_FILE" | cut -d'|' -f2-) ==="
    exit 1
fi

log_success "=== Pipeline finished ==="