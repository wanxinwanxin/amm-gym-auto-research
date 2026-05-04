"""
Cycle-9 EMA-inventory ablation. Same pattern as cycle 8: take the EMA-
inventory CEM best, zero the 4 inventory params (decay → 0, skew bid
→ 0, skew ask → 0, dead_zone → 0), re-evaluate on the 256 test seeds.

If Δ ≈ 0: the EMA dimension is dead, just like instantaneous; the +10
pt lift is from additional CEM exploration of the 16 piecewise dims.

If Δ < 0: zeroing the EMA dim hurts the score — the inventory dimension
is alive after all.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

OUTDIR = ROOT / "research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results"
TEST_JSON = OUTDIR / "ema_inventory_cem_test.json"
TEST_SEEDS = tuple(range(2000, 2256))


def _evaluate(family: str, params_dict: dict, seeds) -> dict:
    spec = POLICY_SPECS[family]
    params = spec.params_cls(**params_dict).normalized()
    batch = run_batch(
        lambda: spec.strategy_cls(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
    }


def main() -> None:
    with TEST_JSON.open() as f:
        d = json.load(f)
    full_params = dict(d["best_by_val"]["params"])
    full_score = d["best_by_val"]["test_score"]
    full_edge = d["best_by_val"]["test_edge_advantage"]

    ablated = dict(full_params)
    for k in ("inventory_ema_decay", "inventory_skew_to_bid",
              "inventory_skew_to_ask", "inventory_skew_dead_zone"):
        ablated[k] = 0.0

    # As another sanity check: the ablated 20-d EMA family should match
    # bare piecewise (16 dims) on the same 16-dim subset.
    piecewise_params = {k: v for k, v in ablated.items()
                         if not k.startswith("inventory_")}

    cycle8_baseline = 446.6131784961775

    print(f"Re-evaluating cycle-9 EMA best on {len(TEST_SEEDS)} test seeds…")
    t0 = time.time()

    full_check = _evaluate("ema_inventory_piecewise", full_params, TEST_SEEDS)
    print(f"  full EMA-aware  : score={full_check['score']:.4f} edge_adv={full_check['edge_advantage_mean']:+.3f} ({time.time()-t0:.1f}s)")

    t0 = time.time()
    abl_check = _evaluate("ema_inventory_piecewise", ablated, TEST_SEEDS)
    print(f"  EMA-zeroed (4d) : score={abl_check['score']:.4f} edge_adv={abl_check['edge_advantage_mean']:+.3f} ({time.time()-t0:.1f}s)")

    t0 = time.time()
    pw_check = _evaluate("piecewise", piecewise_params, TEST_SEEDS)
    print(f"  piecewise (16d) : score={pw_check['score']:.4f} edge_adv={pw_check['edge_advantage_mean']:+.3f} ({time.time()-t0:.1f}s)")

    delta_full_vs_zeroed = full_check["score"] - abl_check["score"]
    delta_zeroed_vs_cycle8 = abl_check["score"] - cycle8_baseline
    delta_full_vs_cycle8 = full_check["score"] - cycle8_baseline

    print()
    print(f"  Δ (full vs zeroed)  = {delta_full_vs_zeroed:+.3f}  ← attributable to EMA-inventory dim")
    print(f"  Δ (zeroed vs c8)    = {delta_zeroed_vs_cycle8:+.3f}  ← attributable to refined piecewise dims (CEM exploration)")
    print(f"  Δ (full vs c8)      = {delta_full_vs_cycle8:+.3f}  ← total lift")

    out = {
        "test_n_seeds": len(TEST_SEEDS),
        "cycle9_ema_full": full_check,
        "cycle9_ema_zeroed": abl_check,
        "cycle9_zeroed_as_piecewise": pw_check,
        "cycle8_piecewise_baseline": cycle8_baseline,
        "delta_attributable_to_ema": delta_full_vs_zeroed,
        "delta_attributable_to_refined_piecewise_dims": delta_zeroed_vs_cycle8,
        "total_delta_vs_cycle8": delta_full_vs_cycle8,
        "best_params": full_params,
        "ablated_params": ablated,
    }
    (OUTDIR / "ema_inventory_ablation.json").write_text(json.dumps(out, indent=2))
    print(f"  -> wrote {OUTDIR / 'ema_inventory_ablation.json'}")


if __name__ == "__main__":
    main()
