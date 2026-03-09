#!/bin/bash

# ==========================================================================
# Pipeline de ejecución batch de simulaciones GAMA para el modelo de
# movilidad de la ruta 401. Este script gestiona la limpieza de logs
# anteriores, la ejecución del batch en modo headless, y la limpieza
# de los workspaces temporales generados por GAMA.
# Autor: hectoralv22
# ==========================================================================

# ----------------------------- CONFIGURACIÓN ------------------------------

GAMA_SRC="/opt/gama-platform/headless/"
MODEL_PATH="GAMA/src/TEST_MOBILITY/models/mobility_performance.gaml"
BATCH_NAME="batch_1000"
HPC_CORES=10

# ----------------------------- DIRECTORIOS --------------------------------


TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BASE_DIR="./WEB_DEVEL/data/logs/SIMULATION_${TIMESTAMP}"
mkdir -p "./WEB_DEVEL/data/logs"
mkdir -p "$BASE_DIR/RESULTS"
mkdir -p "$BASE_DIR/EVENTS"

LOG_FILE="${BASE_DIR}/log_result_${TIMESTAMP}.log"

# Symlink so GAMA's relative '../logs/RESULTS' and '../logs/EVENTS' land in the timestamped dir
GAMA_LOGS_DIR="./GAMA/src/TEST_MOBILITY/logs"
rm -rf "$GAMA_LOGS_DIR/RESULTS"
rm -rf "$GAMA_LOGS_DIR/EVENTS"
ln -s "$(realpath "$BASE_DIR/RESULTS")" "$GAMA_LOGS_DIR/RESULTS"
ln -s "$(realpath "$BASE_DIR/EVENTS")" "$GAMA_LOGS_DIR/EVENTS"

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
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $1" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [WARNING] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" | tee -a "$LOG_FILE"
}

cleanup_on_exit() {
    echo ""
    log_warning "Execution interrupted by user"
    kill $GAMA_PID 2>/dev/null
    rm -rf ./.workspace*
    log_info "Cleanup done after interruption"
    exit 1
}
trap cleanup_on_exit SIGINT SIGTERM

# ========================== INICIO DEL PIPELINE ===========================

PIPELINE_START=$(date +%s)

log_info "=========================================="
log_info "  GAMA BATCH EXECUTION PIPELINE"
log_info "=========================================="
log_info "Batch experiment: $BATCH_NAME"
log_info "HPC cores: $HPC_CORES"
log_info "Model: $MODEL_PATH"
log_info "Output directory: $BASE_DIR"

# ---------------------- FASE 1: LIMPIEZA PREVIA ---------------------------

CLEANUP_START=$(date +%s)

log_info "--- Phase 1: Cleanup ---"
log_info "Cleaning up previous GAMA workspace directories..."

rm -rf ./.workspace*

CLEANUP_END=$(date +%s)
CLEANUP_TIME=$((CLEANUP_END - CLEANUP_START))

log_success "Cleanup completed in $(format_time $CLEANUP_TIME)"

# ------------------- FASE 2: EJECUCIÓN BATCH GAMA ------------------------

BATCH_START=$(date +%s)

log_info "--- Phase 2: Batch Execution ---"
log_info "Starting GAMA headless batch execution..."

# Extract total simulations from batch name (batch_1000 → 1000)
TOTAL_SIMS="${BATCH_NAME##*_}"

"${GAMA_SRC}gama-headless.sh" -hpc $HPC_CORES -batch $BATCH_NAME "$MODEL_PATH" >> "$LOG_FILE" 2>&1 &
GAMA_PID=$!

echo ""

# Progress bar loop
while kill -0 $GAMA_PID 2>/dev/null; do
    COMPLETED=$(find "$BASE_DIR/RESULTS" -name "*.csv" 2>/dev/null | wc -l)
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
COMPLETED=$(find "$BASE_DIR/RESULTS" -name "*.csv" 2>/dev/null | wc -l)
ELAPSED=$(($(date +%s) - BATCH_START))

BAR=""
for ((i=0; i<30; i++)); do BAR="${BAR}#"; done

printf "\r  [%s] 100%% (%d/%d) %s | Done!                \n" \
    "$BAR" \
    "$COMPLETED" "$TOTAL_SIMS" \
    "$(format_time $ELAPSED)"

wait $GAMA_PID
GAMA_EXIT_CODE=$?

BATCH_END=$(date +%s)
BATCH_TIME=$((BATCH_END - BATCH_START))

if [ $GAMA_EXIT_CODE -eq 0 ]; then
    log_success "Batch execution completed in $(format_time $BATCH_TIME)"
else
    log_error "Batch execution FAILED with exit code $GAMA_EXIT_CODE after $(format_time $BATCH_TIME)"
fi

# ------------------- FASE 3: LIMPIEZA POST-EJECUCIÓN ---------------------

POST_CLEANUP_START=$(date +%s)

log_info "--- Phase 3: Post-execution Cleanup ---"
log_info "Removing GAMA workspace directories..."

rm -rf ./.workspace*

POST_CLEANUP_END=$(date +%s)
POST_CLEANUP_TIME=$((POST_CLEANUP_END - POST_CLEANUP_START))

log_success "Post-cleanup completed in $(format_time $POST_CLEANUP_TIME)"

# ------------------- FASE 4: VALIDACIÓN DE RESULTADOS --------------------

log_info "--- Phase 4: Results Validation ---"

RESULT_FILES=$(find "$BASE_DIR/RESULTS" -name "*.csv" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BASE_DIR/RESULTS" 2>/dev/null | cut -f1)

log_info "Result CSV files generated: $RESULT_FILES"
log_info "Total results size: $TOTAL_SIZE"

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
printf "%-35s %s\n" "2. Batch execution:" "$(format_time $BATCH_TIME)" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Exit code:" "$GAMA_EXIT_CODE" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Result files:" "$RESULT_FILES" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "   - Total size:" "$TOTAL_SIZE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "3. Post-cleanup:" "$(format_time $POST_CLEANUP_TIME)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "------------------------------------------" | tee -a "$LOG_FILE"
printf "%-35s %s\n" "TOTAL PIPELINE TIME:" "$(format_time $TOTAL_TIME)" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

log_success "=== Pipeline finished ==="
