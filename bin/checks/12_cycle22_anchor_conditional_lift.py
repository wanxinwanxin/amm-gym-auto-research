#!/usr/bin/env python3
"""
Cycle 22: encode the cross-anchor null-lift finding as a check.

Cycle 19 reported a +0.245 ladder-over-piecewise test lift_FF
warm-started from cycle-18-seed-0. Cycle 21 then revealed that
cycle-18-seed-0 was the +75th-percentile draw of the piecewise
long-CEM seed distribution. Cycle 22 ran the apples-to-apples
cross-anchor control on cycle-21-seed-1 piecewise (median of the
distribution) and found ladder lift = +0.000 on two rng seeds, plus
a stretch run on cycle-21-seed-2 piecewise that also returned
+0.000.

This check re-reads cycle-22's results and asserts:

  1. Each cycle-22 ladder run's `best_by_val.source` is "anchor"
     (i.e. the rerank winner was the warm-start, not a CEM elite).
  2. Each cycle-22 ladder test_score is bit-equal (to within
     |Δ| < 1e-6) to the cycle-21 piecewise test_score for the
     same anchor seed. This is the identity-warm-start propagation:
     when CEM cannot beat the anchor on val, the rerank picks the
     anchor and the ladder's test reduces to the parent piecewise's
     test.

If reality changes (e.g. simulator semantics shift, ladder gets a
different default warm-start, seed mapping changes), the bit-equal
test will fail — at which point the cross-anchor null-lift reading
needs revisiting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = (
    ROOT
    / "research/experiments/2026-05-05-cycle22-m4-ladder-anchor-control/results"
)
PARENT = (
    ROOT
    / "research/experiments/2026-05-05-cycle21-m4-longcem-multiseed/results"
)

LADDER_RUNS = {
    "cycle21_seed1_seed0": "seed1",  # ladder run -> piecewise parent
    "cycle21_seed1_seed1": "seed1",
    "cycle21_seed2_seed0": "seed2",
}


def load(path: Path) -> dict:
    if not path.exists():
        print(f"missing: {path}")
        sys.exit(2)
    return json.loads(path.read_text())


for ladder_run, parent_seed in LADDER_RUNS.items():
    ladder = load(EXP / ladder_run / "test.json")
    parent = load(PARENT / parent_seed / "test.json")

    bv = ladder["best_by_val"]
    if bv.get("source") != "anchor":
        print(
            f"FAIL {ladder_run}: best_by_val.source = "
            f"{bv.get('source')!r}, expected 'anchor' (cross-anchor "
            "null-lift assumption broken)"
        )
        sys.exit(1)

    ladder_test = float(bv["test_score"])
    parent_test = float(parent["best_by_val"]["test_score"])
    delta = abs(ladder_test - parent_test)
    if delta > 1e-6:
        print(
            f"FAIL {ladder_run}: ladder test_score {ladder_test:.6f} "
            f"≠ parent piecewise test_score {parent_test:.6f} "
            f"(|Δ|={delta:.6e}); identity warm-start no longer propagates"
        )
        sys.exit(1)

print(
    "ok: 3/3 cycle-22 ladder runs rerank-pick anchor; "
    "ladder test ≡ piecewise test on the same anchor seed; "
    "cross-anchor null-lift result holds"
)
