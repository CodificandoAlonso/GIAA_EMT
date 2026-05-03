#!/bin/bash

# ==========================================================================
#Pre-Simulation script for  GAMA headless batch execution
#This code will create the directories and save to a enviroment variable the timestamp from the directory
# generated, in order for the next script(the one which will run the batch) to know where to find the project dir.
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
GAMA_SRC="/opt/gama-platform/headless/"
MODEL_NAME="modelpassengersfinal_with_passenger_agents.gaml"
BATCH_NAME="batch_1000"
SIM_MODEL_PATH="${BASE_DIR}/TEST_MOBILITY/models/${MODEL_NAME}"

HPC_CORES=16


LOG_FILE="${BASE_DIR}/log_result_${BASE_DIR: -15}.log"

# ----------------------------- FUNCIONES ----------------------------------

format_time() {
    local total_seconds=$1
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


cleanup_on_exit() {
    echo ""
    log_warning "Execution interrupted by user"
    log_warning "TRYING TO TERMINATE GAMA PROCESS... ${GAMA_PID}"
    kill -9 $GAMA_PID 2>/dev/null
    rm -rf ./.workspace*
    log_info "Cleanup done after interruption"
    exit 1
}
trap cleanup_on_exit SIGINT SIGTERM

# ========================== BEGIN ===========================

PIPELINE_START=$(date +%s)

log_info "=========================================="
log_info "  GAMA BATCH EXECUTION PIPELINE"
log_info "=========================================="
log_info "Batch experiment: $BATCH_NAME"
log_info "HPC cores: $HPC_CORES"
log_info "Source project: $GAMA_PROJECT"
log_info "Simulation directory: $BASE_DIR"


# ------------------- FASE 1: EJECUCIÓN BATCH GAMA ------------------------

BATCH_START=$(date +%s)

log_info "--- Phase 1: Batch Execution ---"
log_info "Starting GAMA headless batch execution against copied project..."

# Extract total simulations from batch name (batch_1000 → 1000)
TOTAL_SIMS="${BATCH_NAME##*_}"

# Results land inside the copied project
RESULTS_DIR="$BASE_DIR/TEST_MOBILITY/logs/RESULTS"

#debug flags disable to enable boost performance
export JAVA_TOOL_OPTIONS="-Denable_debug=false -Denable_logging=false -XX:+UseG1GC"

#-m 16gb of available RAM heap and HPC_CORES "threads" which parallelyzes the simulations
"${GAMA_SRC}gama-headless.sh" -m 16384m -hpc $HPC_CORES -batch $BATCH_NAME "$SIM_MODEL_PATH" \
>> "$LOG_FILE" 2>&1 &

GAMA_PID=$!

echo ""

# Progress bar loop
while kill -0 $GAMA_PID 2>/dev/null; do
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

wait $GAMA_PID
GAMA_EXIT_CODE=$?

BATCH_END=$(date +%s)
BATCH_TIME=$((BATCH_END - BATCH_START))

if [ $GAMA_EXIT_CODE -eq 0 ]; then
    log_success "Batch execution completed in $(format_time $BATCH_TIME)"
else
    log_error "Batch execution FAILED with exit code $GAMA_EXIT_CODE after $(format_time $BATCH_TIME)"
fi

# ------------------- FASE 4: EXTRACCIÓN Y LIMPIEZA -----------------------

POST_CLEANUP_START=$(date +%s)

log_info "--- Phase 4: Extract & Cleanup ---"
log_info "Extracting results, events, and inputs..."

# Move results and events out of the copied project
mv "$BASE_DIR/TEST_MOBILITY/logs/RESULTS" "$BASE_DIR/RESULTS"
mv "$BASE_DIR/TEST_MOBILITY/logs/EVENTS"  "$BASE_DIR/EVENTS"
mv "$BASE_DIR/TEST_MOBILITY/logs/PASSENGERS" "$BASE_DIR/PASSENGERS"
mkdir -p "$BASE_DIR/PLOTS"
mkdir -p "$BASE_DIR/PLOTS/to_A"
mkdir -p "$BASE_DIR/PLOTS/to_A/stops"
mkdir -p "$BASE_DIR/PLOTS/to_A/times"
mkdir -p "$BASE_DIR/PLOTS/to_B"
mkdir -p "$BASE_DIR/PLOTS/to_B/stops"
mkdir -p "$BASE_DIR/PLOTS/to_B/times"
mkdir -p "$BASE_DIR/PLOTS/general"
mkdir -p "$BASE_DIR/PLOTS/buses"

# Keep the inputs that drove this simulation
mv "$BASE_DIR/TEST_MOBILITY/includes"     "$BASE_DIR/includes"


log_info "Removing copied GAMA project files..."
rm -rf "$BASE_DIR/TEST_MOBILITY"

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

# ------------------- FASE 6: DATA EXTRACTION & ANALYSIS -------------------

EXTRACTION_START=$(date +%s)

log_info "--- Phase 6: Data Extraction & Analysis ---"

# data_extractor.py uses os.getcwd() to resolve .last_simulation and all
# relative paths, so it must be invoked from the bash_scripts directory
# where it lives (same directory as this shell script).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Dependency check ---
REQUIRED_PACKAGES=("pandas" "numpy" "matplotlib" "scipy")
MISSING_PACKAGES=()
PLOT_COUNT=0
JSON_COUNT=0

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import ${pkg}" 2>/dev/null; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    log_warning "Missing Python packages: ${MISSING_PACKAGES[*]}"
    log_info "Installing missing dependencies..."
    pip3 install --break-system-packages "${MISSING_PACKAGES[@]}" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log_error "Failed to install Python dependencies. Aborting data extraction."
        PYTHON_EXIT_CODE=1
        EXTRACTION_END=$(date +%s)
        EXTRACTION_TIME=$((EXTRACTION_END - EXTRACTION_START))
    fi
else
    log_info "All Python dependencies satisfied"
fi

if [ "${PYTHON_EXIT_CODE:-0}" -eq 0 ]; then
    log_info "Running data_extractor.py (${TOTAL_SIMS} simulations, plots + JSON output)..."

    python3 "${SCRIPT_DIR}/data_extractor.py" >> "$LOG_FILE" 2>&1
    PYTHON_EXIT_CODE=$?

    EXTRACTION_END=$(date +%s)
    EXTRACTION_TIME=$((EXTRACTION_END - EXTRACTION_START))
fi

if [ $PYTHON_EXIT_CODE -eq 0 ]; then
    PLOT_COUNT=$(find "$BASE_DIR/PLOTS" -name "*.png" 2>/dev/null | wc -l)
    JSON_COUNT=$(find "$BASE_DIR/PLOTS" -name "*.json" 2>/dev/null | wc -l)
    log_success "Data extraction completed in $(format_time $EXTRACTION_TIME)"
    log_info "Generated $PLOT_COUNT plots and $JSON_COUNT JSON files"
else
    log_error "Data extraction FAILED with exit code $PYTHON_EXIT_CODE after $(format_time $EXTRACTION_TIME)"
    log_error "Check $LOG_FILE for Python traceback"
fi

# ------------------- FINAL STRUCTURE LOG ----------------------------------

log_info "Final simulation directory structure:"
log_info "  $BASE_DIR/"
log_info "  ├── RESULTS/          (simulation output CSVs)"
log_info "  ├── EVENTS/           (event logs)"
log_info "  ├── PASSENGERS/       (passenger wait-time logs)"
log_info "  ├── PLOTS/"
log_info "  │   ├── to_A/         (occupation & time distribution plots)"
log_info "  │   ├── to_B/         (occupation & time distribution plots)"
log_info "  │   ├── general/      (aggregate occupation plots)"
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
printf "%-35s %s\n" "1. Pre-cleanup:" "$(format_time $CLEANUP_TIME)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "2. Project snapshot:" "$(format_time $SNAPSHOT_TIME)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "3. Batch execution:" "$(format_time $BATCH_TIME)" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Exit code:" "$GAMA_EXIT_CODE" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Result files:" "$RESULT_FILES" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Total size:" "$TOTAL_SIZE" | tee -a "$LOG_FILE"
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

log_success "=== Pipeline finished ==="