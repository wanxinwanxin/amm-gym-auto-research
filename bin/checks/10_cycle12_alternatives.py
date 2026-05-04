#!/usr/bin/env python3
"""
Methodological fact (cycle 12): two cold-start alternatives to the
warm-start piecewise CEM under the matched (pop=24, gen=12) recipe
both land below the warm-start cluster's ~457 ceiling on the held-out
test seeds:

  - Cycle-12 stage 1 (latent_full ladder, 18-d, defaults+wide init):
      test ≈ 388.6 (adv ≈ −124).  Hypothesis (a) "capacity is the
      bottleneck" was strongly falsified: the richer family with
      explicit EMAs over six market features lands ~68 pts below
      warm-start piecewise.
  - Cycle-12 stage 2 (piecewise, 16-d, defaults + init_std=0.30):
      test ≈ 418.6 (adv ≈ −36).  Fresh-anchor wide-init couldn't
      catch warm-start in 12 gens — the 38-pt gap suggests warm-start
      is doing genuine refinement, not just consuming compute.

This check re-evaluates each cycle-12 best-by-val on a 32-seed test
slice and asserts they reproduce within ±15 pts of their full-test
reference.  A flip in either direction means scoring or simulator
semantics changed; that would invalidate the cycle-12 falsification
and the cycle-13 ceiling argument.

Cheap: 32 seeds × 2 candidates ≈ 15-25s on the sandbox.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

CYCLE12_DIR = ROOT / "research/experiments/2026-05-04-cycle12-latent-ladder-cem/results"

CASES = [
    {
        "label": "fresh-anchor piecewise (cycle-12 stage 2)",
        "result_json": CYCLE12_DIR / "fresh_anchor_piecewise_test.json",
        "family": "piecewise",
        "expected_full_test": 418.65,
        "tolerance": 15.0,
    },
    {
        "label": "latent_full ladder (cycle-12 stage 1)",
        "result_json": CYCLE12_DIR / "latent_full_test.json",
        "family": "latent_full",
        "expected_full_test": 388.57,
        "tolerance": 15.0,
    },
]

# Constraint that ties the cycle-13 ceiling argument together:
# both cycle-12 alternatives must land below the warm-start cluster's
# d16_s2 champion (456.80) on this 32-seed test slice. If either
# closes the gap, hypothesis (c) "saturation is a recipe ceiling"
# loses its strongest piece of evidence.
CHAMPION_TEST_SCORE_FULL = 456.80
CHAMPION_HEADROOM_PTS = 5.0  # 32-seed noise band; alternatives must be below
# (champion - headroom) to count as "decisively below" the warm-start cluster.

SEEDS = tuple(range(2000, 2032))  # 32-seed subset of the 256 test seeds

def evaluate(family: str, params: dict) -> tuple[float, float]:
    spec = POLICY_SPECS[family]
    fitted = spec.params_cls(**params).normalized()
    batch = run_batch(
        lambda: spec.strategy_cls(fitted),
        SEEDS,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return float(batch.score), float(batch.edge_advantage_mean)


for case in CASES:
    if not case["result_json"].exists():
        print(f"FAIL: cycle-12 result missing: {case['result_json']}")
        sys.exit(1)
    data = json.loads(case["result_json"].read_text())
    params = data["best_by_val"]["params"]
    score, adv = evaluate(case["family"], params)
    expected = case["expected_full_test"]
    tol = case["tolerance"]
    if abs(score - expected) > tol:
        print(
            f"FAIL: {case['label']} on 32 seeds = {score:.3f} "
            f"(expected ≈{expected:.1f}±{tol:.0f})"
        )
        sys.exit(1)
    if score >= CHAMPION_TEST_SCORE_FULL - CHAMPION_HEADROOM_PTS:
        print(
            f"FAIL: {case['label']} 32-seed score = {score:.3f} now "
            f"within {CHAMPION_HEADROOM_PTS:.0f} pts of champion "
            f"({CHAMPION_TEST_SCORE_FULL:.1f}); cycle-12 falsification flipped"
        )
        sys.exit(1)
    print(
        f"  {case['label']:50s}  score={score:7.3f} adv={adv:+7.2f} "
        f"(expected ≈{expected:.1f}, tol ±{tol:.0f}, champion {CHAMPION_TEST_SCORE_FULL:.1f})"
    )

print(
    f"ok: cycle-12 alternatives reproduce within tolerance and "
    f"both remain decisively below the warm-start cluster"
)
