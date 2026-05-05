#!/usr/bin/env python3
"""Check 13 — long-CEM ladder rerank elites beat the anchor on val.

Encodes the cycle-23/24 "compute threshold" finding: at the long-CEM
budget (10g × 24p), every non-anchor candidate in the rerank pool of a
ladder warm-started from a piecewise anchor beats the anchor on val.
Cycle 22 short-CEM (5g × 12p) returned every-elite-loses-to-anchor
on val on the same c21-s1 anchor; cycle 23 closed that search→val
gap; cycle 24 reproduced the closure on a third c21-s1 seed AND on a
qualitatively different anchor (c21-s2 basin-collapsed).

Pass if every non-anchor candidate val ≥ anchor val + EPS for all
known long-CEM ladder runs in cycles 23 and 24. Falsifying the check
means we have found a long-CEM ladder run where some rerank elite
loses to the anchor on val — which would invalidate the "long-CEM
elites are quality elites" claim and ought to trigger a re-evaluation
of the cycle-23/24 verdict.

Cap: ≤12 active checks. Cycle 24 added this; on next cycle, if any
older check has flipped to a no-op (e.g. its workaround is no longer
needed) it should be retired.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Minimum margin we require non-anchor candidates to beat the anchor by
# on the n=128 val set. Cycle-23 minimum was 0.21; cycle-24 minimum was
# 0.13 (c21-s1 seed 2, gen9 cluster). Use a margin well below the
# observed worst case so a tiny shift in numerics doesn't flip the
# check, but tight enough that a real regression (anchor wins) is
# caught.
EPS = 0.05


RUNS = [
    # (label, path, expected anchor val)
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
        if margin < EPS:
            failures.append(
                f"{label}: worst non-anchor val={worst_val:.4f} ≤ anchor val={anchor_val:.4f} + {EPS} (margin {margin:+.4f})"
            )
        else:
            summaries.append(
                f"{label}: anchor={anchor_val:.4f}, non-anchor min={worst_val:.4f} (margin {margin:+.4f}, n_nonanchor={len(non_anchor)})"
            )

    if failures:
        print("FAIL: long-CEM ladder rerank no longer dominates anchor on val")
        for f in failures:
            print(f"  - {f}")
        for s in summaries:
            print(f"  ok: {s}")
        return 1
    print(
        f"ok: {len(summaries)} long-CEM ladder runs, every non-anchor candidate beats anchor on val by ≥ {EPS}"
    )
    for s in summaries:
        print(f"     {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
