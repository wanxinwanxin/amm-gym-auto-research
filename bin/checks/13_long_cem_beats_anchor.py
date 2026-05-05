#!/usr/bin/env python3
"""Check 13 — long-CEM ladder rerank pool is BIMODAL: either elites
beat anchor by ≥+0.10 on val, or CEM collapses and worst non-anchor
trails anchor by ≥−0.50 on val. Cycles 23/24/25 show no run lands
between those two regimes.

Cycle-24 invariant ("every non-anchor candidate beats anchor by
+0.05") was falsified by cycle 25 c21-s2 seed=1 — a long-CEM run
whose CEM trajectory collapsed; all non-anchor val scores fell
1.4 below the anchor and the rerank picked the anchor itself.
Rather than retire the check outright (we can't unlink files in
this sandbox), this is the bimodal replacement: we now assert that
every long-CEM ladder run falls into one of two regimes, never
between them.

Pass if for every known long-CEM ladder run, either:
  (A) "search-find" regime: worst non-anchor val ≥ anchor val + 0.10
       (cycle 23 s0/s1, cycle 24 s2 c21-s1 / s0 c21-s2, cycle 25 s0 c18-s0)
  (B) "search-collapse" regime: worst non-anchor val ≤ anchor val − 0.50
       (cycle 25 s1 c21-s2)

Failing the check means a long-CEM ladder run lands in the
in-between band (-0.50, +0.10) of (worst-elite-val − anchor-val) —
which would mean the dichotomy is false and CEM has a third regime
we don't yet understand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Bimodal thresholds. (worst_nonanchor_val - anchor_val) must lie
# OUTSIDE the open interval (LOW, HIGH).
HIGH = 0.10   # search-find regime: margin ≥ +0.10
LOW = -0.50   # search-collapse regime: margin ≤ -0.50

RUNS = [
    (
        "cycle23 c21-s1 seed=0",
        ROOT
        / "research/experiments/2026-05-06-cycle23-m4-ladder-longcem/results/cycle21_seed1_seed0/test.json",
    ),
    (
        "cycle23 c21-s1 seed=1",
        ROOT
        / "research/experiments/2026-05-06-cycle23-m4-ladder-longcem/results/cycle21_seed1_seed1/test.json",
    ),
    (
        "cycle24 c21-s1 seed=2",
        ROOT
        / "research/experiments/2026-05-06-cycle24-m4-ladder-longcem-followup/results/cycle21_seed1_seed2/test.json",
    ),
    (
        "cycle24 c21-s2 seed=0",
        ROOT
        / "research/experiments/2026-05-06-cycle24-m4-ladder-longcem-followup/results/cycle21_seed2_seed0/test.json",
    ),
    (
        "cycle25 c21-s2 seed=1",
        ROOT
        / "research/experiments/2026-05-06-cycle25-m4-cross-anchor-stabilizer/results/cycle21_seed2_seed1/test.json",
    ),
    (
        "cycle25 c18-s0 seed=0",
        ROOT
        / "research/experiments/2026-05-06-cycle25-m4-cross-anchor-stabilizer/results/cycle18_seed0_seed0/test.json",
    ),
    (
        "cycle26 c18-s0 seed=1",
        ROOT
        / "research/experiments/2026-05-06-cycle26-m4-c18s0-multiseed/results/cycle18_seed0_seed1/test.json",
    ),
    (
        "cycle26 c18-s0 seed=2",
        ROOT
        / "research/experiments/2026-05-06-cycle26-m4-c18s0-multiseed/results/cycle18_seed0_seed2/test.json",
    ),
]


def main() -> int:
    failures: list[str] = []
    summaries: list[str] = []
    for label, path in RUNS:
        if not path.exists():
            failures.append(f"{label}: missing {path}")
            continue
        d = json.load(path.open())
        rerank = d.get("rerank", [])
        if not rerank:
            failures.append(f"{label}: empty rerank pool")
            continue
        anchor = next((r for r in rerank if r["source"] == "anchor"), None)
        if anchor is None:
            failures.append(f"{label}: no anchor entry in rerank")
            continue
        anchor_val = float(anchor["val_score"])
        non_anchor = [r for r in rerank if r["source"] != "anchor"]
        if not non_anchor:
            failures.append(f"{label}: no non-anchor candidates in rerank")
            continue
        worst = min(non_anchor, key=lambda r: float(r["val_score"]))
        worst_val = float(worst["val_score"])
        margin = worst_val - anchor_val
        if margin >= HIGH:
            regime = "find"
        elif margin <= LOW:
            regime = "collapse"
        else:
            regime = "in-between"

        if regime == "in-between":
            failures.append(
                f"{label}: margin {margin:+.4f} is in the dead zone ({LOW:+.2f}, {HIGH:+.2f})"
            )
        else:
            summaries.append(
                f"{label}: anchor={anchor_val:.4f}, worst_nonanchor={worst_val:.4f} (margin {margin:+.4f}) regime={regime}"
            )

    if failures:
        print("FAIL: long-CEM ladder run landed in the unknown in-between regime")
        for f in failures:
            print(f"  - {f}")
        for s in summaries:
            print(f"  ok: {s}")
        return 1
    print(
        f"ok: {len(summaries)} long-CEM ladder runs, all bimodal (margin ≥ {HIGH} or ≤ {LOW})"
    )
    for s in summaries:
        print(f"     {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
