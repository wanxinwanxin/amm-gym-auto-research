#!/usr/bin/env bash
# Cycle-12 chain driver: latent_full CEM, then fresh-anchor piecewise CEM.
# Runs sequentially in the foreground (caller is expected to backround).

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$HERE/../results"
mkdir -p "$RESULTS"

CHAIN_LOG="$RESULTS/chain.log"
: > "$CHAIN_LOG"   # truncate (sandbox unlink-blocked)

log() {
  echo "[$(date '+%H:%M:%S')] $1" | tee -a "$CHAIN_LOG"
}

ROOT="$(cd "$HERE/../../../.." && pwd)"
cd "$ROOT"

log "=== Cycle 12 chain start ==="
log "ROOT=$ROOT"

log "--- Stage 1/2: latent_full CEM (18-d, init_std=0.25, pop=24, gen=12) ---"
T0=$SECONDS
python3 "$HERE/run_ladder_cem.py" --family latent_full --rng-seed 0 \
  > "$RESULTS/latent_full.stdout" 2>&1
RC1=$?
log "Stage 1 exit code: $RC1, elapsed: $((SECONDS - T0))s"

log "--- Stage 2/2: fresh-anchor piecewise CEM (16-d, init_std=0.30, pop=24, gen=12) ---"
T0=$SECONDS
python3 "$HERE/run_fresh_anchor_piecewise.py" --rng-seed 0 \
  > "$RESULTS/fresh_anchor_piecewise.stdout" 2>&1
RC2=$?
log "Stage 2 exit code: $RC2, elapsed: $((SECONDS - T0))s"

log "=== Cycle 12 chain done (rc1=$RC1, rc2=$RC2) ==="
exit 0
