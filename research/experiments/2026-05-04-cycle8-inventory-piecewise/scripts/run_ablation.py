"""
Cycle-8 inventory ablation.

The cycle-8 best-by-val params shifted both the inherited 16 piecewise
dims (e.g. signal_decay 0.55 -> 0.67, continuation_to_cross_side 0.90 ->
1.36) AND landed the 3 new inventory params at small but consistent
non-zero magnitudes. The +13.7 pt test lift therefore could be:

  (a) attributable to the inventory dimension itself, OR
  (b) attributable to additional CEM refinement on the 16 piecewise dims
      (which the inventory escape valve happened to enable), OR
  (c) some mix.

This script directly answers the question by re-evaluating the cycle-8
best with the 3 inventory-skew params zeroed out (i.e. running the
PIECEWISE_CONTROLLER strategy on the 16 inherited dims of the cycle-8
best). All other params held identical.

Output: `inventory_ablation.json`.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_policies import (  # noqa: E402
    InventoryAwarePiecewiseParams,
    InventoryAwarePiecewiseStrategy,
    PiecewiseControllerParams,
    PiecewiseControllerStrategy,
)


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle8-inventory-piecewise/results"
TEST_SEEDS = tuple(range(2000, 2256))


def _eval_inv_aware(params_dict: dict, seeds) -> dict:
    p = InventoryAwarePiecewiseParams(**params_dict).normalized()
    batch = run_batch(
        lambda: InventoryAwarePiecewiseStrategy(p),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
    }


def _eval_piecewise(params_dict: dict, seeds) -> dict:
    p = PiecewiseControllerParams(**{
        k: v for k, v in params_dict.items() if k in {f.name for f in PiecewiseControllerParams.__dataclass_fields__.values()}
    }).normalized()
    batch = run_batch(
        lambda: PiecewiseControllerStrategy(p),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
    }


def main() -> None:
    test_json = json.loads((OUTDIR / "inventory_warmstart_cem_test.json").read_text())
    inv_best = test_json["best_by_val"]["params"]

    # 1) Re-eval the inv-aware best as-is (sanity check vs reported test_score).
    print(f"[{time.strftime('%H:%M:%S')}] Re-eval inv-aware best (with non-zero inv params)…")
    t = time.time()
    full = _eval_inv_aware(inv_best, TEST_SEEDS)
    print(f"  -> test={full['score']:.3f} (adv {full['edge_advantage_mean']:+.3f}) ({time.time() - t:.1f}s)")

    # 2) Ablate: zero the 3 inv params, keep 16 piecewise dims, eval with
    #    the inventory_aware_piecewise strategy (so the only difference is
    #    inv-skew=0 vs inv-skew=cycle8-best).
    ablated = dict(inv_best)
    ablated["inventory_skew_to_bid"] = 0.0
    ablated["inventory_skew_to_ask"] = 0.0
    ablated["inventory_skew_dead_zone"] = 0.0

    print(f"[{time.strftime('%H:%M:%S')}] Re-eval inv-aware best with inv params ZEROED…")
    t = time.time()
    ablated_inv_aware = _eval_inv_aware(ablated, TEST_SEEDS)
    print(f"  -> test={ablated_inv_aware['score']:.3f} (adv {ablated_inv_aware['edge_advantage_mean']:+.3f}) ({time.time() - t:.1f}s)")

    # 3) Same 16 dims, but evaluated as PiecewiseControllerStrategy directly
    #    (parity check with #2 — should match within fp noise).
    print(f"[{time.strftime('%H:%M:%S')}] Same 16 dims as PiecewiseControllerStrategy (parity check)…")
    t = time.time()
    pw_eval = _eval_piecewise(ablated, TEST_SEEDS)
    print(f"  -> test={pw_eval['score']:.3f} (adv {pw_eval['edge_advantage_mean']:+.3f}) ({time.time() - t:.1f}s)")

    delta_inv = full["score"] - ablated_inv_aware["score"]
    print()
    print(f"=== Ablation summary (256 test seeds) ===")
    print(f"  Cycle-8 inv-aware best (inv params ON):  {full['score']:.3f}")
    print(f"  Same params with inv params ZEROED:      {ablated_inv_aware['score']:.3f}")
    print(f"  Same 16 dims via PiecewiseStrategy:      {pw_eval['score']:.3f}")
    print()
    print(f"  Δ attributable to the 3 inv-skew params: {delta_inv:+.3f}")
    print(f"  Δ attributable to refined 16 piecewise dims: "
          f"{ablated_inv_aware['score'] - 432.747768827535:+.3f}")
    print(f"  Total Δ vs cycle-6 piecewise best:       "
          f"{full['score'] - 432.747768827535:+.3f}")

    out = {
        "test_n_seeds": len(TEST_SEEDS),
        "cycle8_inv_aware_full": full,
        "cycle8_inv_aware_zeroed": ablated_inv_aware,
        "cycle8_zeroed_as_piecewise_parity_check": pw_eval,
        "cycle6_piecewise_baseline": 432.747768827535,
        "delta_attributable_to_inv_skew": delta_inv,
        "delta_attributable_to_refined_piecewise_dims":
            ablated_inv_aware["score"] - 432.747768827535,
        "total_delta_vs_cycle6_piecewise": full["score"] - 432.747768827535,
        "best_params": inv_best,
        "ablated_params": ablated,
    }
    (OUTDIR / "inventory_ablation.json").write_text(json.dumps(out, indent=2))
    print(f"  -> wrote {OUTDIR / 'inventory_ablation.json'}")


if __name__ == "__main__":
    main()
