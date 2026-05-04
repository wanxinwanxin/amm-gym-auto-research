#!/usr/bin/env bash
# Cycle-11 grid driver: run 3 cells sequentially.
#
# Cells (3 sequential CEM runs, ~30 min each, ~90 min total):
#   1. (16-d, seed=2): third 16-d seed for noise floor
#   2. (24-d-noop, seed=0): higher tail dim at base seed
#   3. (24-d-noop, seed=1): same higher dim at different seed
#
# This script is meant to run via `nohup bash run_grid.sh &`.
set -uo pipefail

cd "$(dirname "$0")/.." # land in cycle-11-grid-cem/
EXP_DIR="$(pwd)"
ROOT="$(git -C "$EXP_DIR" rev-parse --show-toplevel)"
SCRIPTS_DIR="$EXP_DIR/scripts"
LOG_DIR="$EXP_DIR/results"
mkdir -p "$LOG_DIR"

CELLS=(
  "16 2"
  "24 0"
  "24 1"
)

t_global=$(date +%s)
{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycle-11 grid driver starting; cells=${#CELLS[@]}"
} | tee "$LOG_DIR/grid_driver.log"

for cell in "${CELLS[@]}"; do
  read -r DIM SEED <<<"$cell"
  CELL_LABEL="d${DIM}_s${SEED}"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] === cell ${CELL_LABEL} ===" | tee -a "$LOG_DIR/grid_driver.log"
  t_cell=$(date +%s)
  (
    cd "$ROOT"
    python3 "$SCRIPTS_DIR/run_grid_cell.py" --dim-total "$DIM" --rng-seed "$SEED"
  ) >>"$LOG_DIR/cell_${CELL_LABEL}.stdout" 2>&1
  rc=$?
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] cell ${CELL_LABEL} exit=${rc} elapsed=$(($(date +%s) - t_cell))s" \
    | tee -a "$LOG_DIR/grid_driver.log"
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycle-11 grid driver done; total elapsed=$(($(date +%s) - t_global))s" \
  | tee -a "$LOG_DIR/grid_driver.log"
