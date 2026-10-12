#!/bin/bash

# ==========================================================================
#Pre-Simulation script for  GAMA headless batch execution
#This code will create the directories and save to a enviroment variable the timestamp from the directory
# generated, in order for the next script(the one which will run the batch) to know where to find the project dir.
#
# Author: Héctor Álvarez Marcos
# ==========================================================================

# Usage: prepare_simulation.sh [SIMULATION_YYYYMMDD_HHMMSS]
#   With an id (what the web server does) the simulation directory is created
#   under that name and nothing else is written, so several simulations can be
#   prepared and run at the same time. Without it a timestamped id is generated
#   and saved to .last_simulation, for manual use from the command line.

# All relative paths below are relative to this script's directory.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

# ----------------------------- Settings ------------------------------

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#DATA DIR
DATA_DIR="../../BASE_DATA/*"

#GAMA
GAMA_SRC="/opt/gama-platform/headless/"
GAMA_PROJECT="../../GAMA/src/TEST_MOBILITY"
MODEL_NAME="mobility_performance.gaml"
BATCH_NAME="batch_1000"
GAMA_HPC_CORES=8

#C
C_PROJECT="../../C_REWRITE"
C_HPC_CORES=5

# ----------------------------- Directories --------------------------------

if [ -n "${1:-}" ]; then
    SIM_ID="$1"
    if ! [[ "$SIM_ID" =~ ^SIMULATION_[0-9]{8}_[0-9]{6}$ ]]; then
        echo "Invalid simulation id: $SIM_ID" >&2
        exit 2
    fi
else
    SIM_ID="SIMULATION_$(date +%Y%m%d_%H%M%S)"
fi
TIMESTAMP="${SIM_ID#SIMULATION_}"
BASE_DIR="../data/logs/${SIM_ID}"

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
log_info "HPC cores: GAMA=$GAMA_HPC_CORES C=$C_HPC_CORES"
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

# GAMA workspaces are no longer created here: each run keeps its own under
# <simulation>/.work (see run_simulation.sh), so there is nothing shared to clean.

CLEANUP_END=$(date +%s)
CLEANUP_TIME=$((CLEANUP_END - CLEANUP_START))

log_success "Pre-cleanup completed in $(format_time $CLEANUP_TIME)"

# ------------------- FASE 2: PROJECT SNAPSHOT -----------------------------

SNAPSHOT_START=$(date +%s)

log_info "--- Phase 2: Project Snapshot ---"
log_info "Copying full GAMA project to simulation directory..."

# Copy the entire GAMA project into the simulation directory
cp -r "$GAMA_PROJECT" "$BASE_DIR/TEST_MOBILITY"

#WE ARE GONNA REMOVE THE DATA FROM TEST_MOBILITY
rm "$BASE_DIR/TEST_MOBILITY/includes/INPUTS/"*

log_info "--- Phase 2.2: Copying C DIR Inside the sim directory ---"

cp -r "$C_PROJECT" "$BASE_DIR/C_REWRITE"

#WE ARE GONNA REMOVE THE DATA FROM C_REWRITE
rm -rf "$BASE_DIR/C_REWRITE/data/"*

#NOW, FOR BOTH FILES

for f in $DATA_DIR; do
    filename="$f"
    log_info "copying $filename to C's and GAMA's data folders"
    cp -r $filename "$BASE_DIR/C_REWRITE/data/"
    cp -r $filename "$BASE_DIR/TEST_MOBILITY/includes/INPUTS/"
done

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

if [ -z "${1:-}" ]; then
    echo "$BASE_DIR" > ./.last_simulation
fi
echo "$SIM_ID"