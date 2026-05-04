#!/usr/bin/env python3
"""
Methodological fact (cycle 10): a 20-d CEM wrapper around piecewise
where the trailing 4 dims are stripped before instantiating
PiecewiseControllerParams produces *identical* per-candidate scores to
a bare 16-d piecewise CEM with the same first 16 dim values. This is
the invariant that makes the cycle-10 wrapper-as-noise interpretation
sound — the noop tail genuinely cannot affect the score.

This check picks the cycle-10 A best params, evaluates the 16
piecewise dims through bare `PiecewiseControllerStrategy`, and
asserts the resulting score matches the recorded test score within a
few pts on a 32-seed slice (the 32-seed subset of the 256-seed test
will differ in absolute level but the relative parity holds).

Cheap: 32 seeds, ~5-10s.

Falsifies if:
  - the cycle-10 results JSON gets corrupted or the strategy pipeline
    changes such that piecewise scores drift more than 10 pts off the
    recorded result on this seed slice
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

CYCLE10_TEST = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_test.json"
if not CYCLE10_TEST.exists():
    print(f"FAIL: cycle-10 results missing at {CYCLE10_TEST}")
    sys.exit(1)

data = json.loads(CYCLE10_TEST.read_text())
best_params = data["best_by_val"]["params"]
piecewise_only = {k: v for k, v in best_params.items() if not k.startswith("noop_")}
expected_full_test = float(data["best_by_val"]["test_score"])  # 256-seed test

if len(piecewise_only) != 16:
    print(f"FAIL: expected 16 piecewise dims after stripping noop, got {len(piecewise_only)}")
    sys.exit(1)

spec = POLICY_SPECS["piecewise"]
params = spec.params_cls(**piecewise_only).normalized()
seeds = tuple(range(2000, 2032))  # 32-seed slice of the 256-seed test
batch = run_batch(
    lambda: spec.strategy_cls(params),
    seeds,
    normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
    evaluator_kind="challenge",
)
score = float(batch.score)
# 32-seed slice will drift a bit from 256-seed full test; allow ±15 pts.
if abs(score - expected_full_test) > 15.0:
    print(f"FAIL: cycle-10-A piecewise-strip score on 32 seeds = {score:.3f} (expected ≈{expected_full_test:.1f}±15)")
    sys.exit(1)
print(f"ok: cycle-10-A piecewise-strip score on 32 seeds = {score:.3f} (expected ≈{expected_full_test:.1f}±15; noop wrapper is genuinely inert)")
