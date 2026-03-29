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




GAMA_SRC="/opt/gama-platform/headless/"
GAMA_PROJECT="../../GAMA/src/TEST_MOBILITY"
MODEL_NAME="mobility_performance.gaml"
BATCH_NAME="batch_1000"
HPC_CORES=16

# ----------------------------- Directories --------------------------------

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BASE_DIR="../data/logs/SIMULATION_${TIMESTAMP}"

mkdir -p "../data/logs"
mkdir -p "$BASE_DIR"
touch "$BASE_DIR/description.txt"

LOG_FILE="${BASE_DIR}/log_result_${TIMESTAMP}.log"

# ----------------------------- Functions ----------------------------------

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
    kill $GAMA_PID 2>/dev/null
    rm -rf ./.workspace*
    log_info "Cleanup done after interruption"
    exit 1
}
trap cleanup_on_exit SIGINT SIGTERM

# ========================== BEGIN ===========================

PIPELINE_START=$(date +%s)

log_info "=========================================="
log_info "  GAMA BATCH SIMULATION PREPARATION"
log_info "=========================================="
log_info "Batch experiment: $BATCH_NAME"
log_info "HPC cores: $HPC_CORES"
log_info "Source project: $GAMA_PROJECT"
log_info "Simulation directory: $BASE_DIR"

# ---------------------- PHASE 1. CLEANUP ---------------------------

CLEANUP_START=$(date +%s)

log_info "--- Phase 1: Pre-cleanup ---"

# Remove old symlinks from original project (leftover from previous runs)
log_info "Removing previous symlinks from original project..."
rm -rf "$GAMA_PROJECT/logs/RESULTS"
rm -rf "$GAMA_PROJECT/logs/EVENTS"
rm -rf "$GAMA_PROJECT/logs/PASSENGERS"

# Remove GAMA workspace directories
log_info "Removing previous GAMA workspace directories..."
rm -rf ./.workspace*

CLEANUP_END=$(date +%s)
CLEANUP_TIME=$((CLEANUP_END - CLEANUP_START))

log_success "Pre-cleanup completed in $(format_time $CLEANUP_TIME)"

# ------------------- FASE 2: PROJECT SNAPSHOT -----------------------------

SNAPSHOT_START=$(date +%s)

log_info "--- Phase 2: Project Snapshot ---"
log_info "Copying full GAMA project to simulation directory..."

# Copy the entire GAMA project into the simulation directory
cp -r "$GAMA_PROJECT" "$BASE_DIR/TEST_MOBILITY"

# Create output directories inside the copied project
mkdir -p "$BASE_DIR/TEST_MOBILITY/logs/RESULTS"
mkdir -p "$BASE_DIR/TEST_MOBILITY/logs/EVENTS"
mkdir -p "$BASE_DIR/TEST_MOBILITY/logs/PASSENGERS"
# Model path now points to the copied project
SIM_MODEL_PATH="$BASE_DIR/TEST_MOBILITY/models/$MODEL_NAME"

SNAPSHOT_END=$(date +%s)
SNAPSHOT_TIME=$((SNAPSHOT_END - SNAPSHOT_START))

log_success "Project snapshot created in $(format_time $SNAPSHOT_TIME)"
log_info "Copied model path: $SIM_MODEL_PATH"
log_info "Inputs can be modified at: $BASE_DIR/TEST_MOBILITY/includes/"


echo "$BASE_DIR" > ./.last_simulation
