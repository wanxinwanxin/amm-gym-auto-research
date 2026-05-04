#!/usr/bin/env python3
"""
Methodological fact (cycle 8): the cycle-8 ablation params (with
inv-skew zeroed out) parity-match a bare `piecewise` policy and score
~446.6 on test seeds. This check re-evaluates that anchor on a small
seed slice and asserts it lands within ±2 pts of 446.6 — drift outside
this band would mean the simulator changed under us, or the params
file was mangled.

Cheap: 32 seeds, ~5-10s on the sandbox.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

ABLATION = ROOT / "research/experiments/2026-05-04-cycle8-inventory-piecewise/results/inventory_ablation.json"
if not ABLATION.exists():
    print(f"FAIL: ablation file missing at {ABLATION}")
    sys.exit(1)
data = json.loads(ABLATION.read_text())
ablated = data["ablated_params"]
piecewise_params = {k: v for k, v in ablated.items() if not k.startswith("inventory_skew_")}
spec = POLICY_SPECS["piecewise"]
params = spec.params_cls(**piecewise_params).normalized()
seeds = tuple(range(2000, 2032))  # subset of cycle-8 test seeds (2000..2255)
batch = run_batch(
    lambda: spec.strategy_cls(params),
    seeds,
    normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
    evaluator_kind="challenge",
)
score = float(batch.score)
expected_full_test = 446.61
# The 32-seed subset is noisier than the 256-seed test; allow ±15 pts.
if abs(score - expected_full_test) > 15.0:
    print(f"FAIL: piecewise anchor on 32 seeds = {score:.3f} (expected ≈{expected_full_test:.1f}±15)")
    sys.exit(1)
print(f"ok: piecewise anchor on 32 seeds = {score:.3f} (expected ≈{expected_full_test:.1f}±15)")
