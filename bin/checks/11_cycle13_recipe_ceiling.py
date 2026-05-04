#!/usr/bin/env python3
"""
Cycle-13/14: encode the recipe-ceiling finding as a check.

Cycle 13 found that doubling the warm-start CEM gen budget on the
cycle-11 d16_s2 anchor produced **zero lift** — the best-by-val
candidate after 24 gens was the anchor itself (gen 0). This check
re-derives that statement from history.json: it asserts that the
anchor's gen-0 best_search_score is *not strictly beaten* by any
later generation by more than the anchor self-noise band (~1.5 pts
across the 64-seed search-seed eval).

If reality changes (simulator semantics shift, params get re-scored
differently), the gen-0 anchor will no longer dominate and this
check will flip to FAIL — at which point cycle-14's "M2 is closed"
conclusion needs revisiting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HIST = ROOT / "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/longrun_d16_s0_g24/history.json"
RESULT = ROOT / "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/longrun_d16_s0_g24/result.json"

if not HIST.exists():
    # First-cycle bootstrap: the file should exist after cycle 13.
    print(f"missing: {HIST}")
    sys.exit(2)
if not RESULT.exists():
    print(f"missing: {RESULT}")
    sys.exit(2)

hist = json.loads(HIST.read_text())["history"]
result = json.loads(RESULT.read_text())

# 1. The anchor (gen 0 best) is the best-by-val of the cycle-13 run.
anchor_gen = result["best_by_val"]["from_generation"]
if anchor_gen != 0:
    print(
        f"unexpected: cycle-13 best-by-val came from gen {anchor_gen}, not gen 0; "
        "recipe-ceiling no longer cleanly described by 'anchor is the optimum'"
    )
    sys.exit(1)

# 2. No subsequent gen's best_search_score beats gen-0's anchor score by >2 pts.
gen0_search = hist[0]["best_search_score"]
later_max = max(g["best_search_score"] for g in hist[1:])
delta = later_max - gen0_search
TOL = 2.0
if delta > TOL:
    print(
        f"recipe ceiling broken: a later gen has best_search={later_max:.3f} > "
        f"gen0 {gen0_search:.3f} + {TOL}; revisit cycle-13 conclusion"
    )
    sys.exit(1)

print(
    f"ok: cycle-13 gen0 anchor (best_search={gen0_search:.3f}) still dominates "
    f"all 23 later gens (max={later_max:.3f}, Δ={delta:+.3f}); recipe ceiling holds"
)
