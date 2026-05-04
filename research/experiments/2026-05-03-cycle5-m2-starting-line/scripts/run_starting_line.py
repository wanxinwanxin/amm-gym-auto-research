"""
Cycle-5 M2 starting line.

Establishes a reproducible baseline floor + ceiling for the AMM-challenge
scoring rule before M2 optimization begins.

What we run:
1. Fixed-fee sweep on the challenge evaluator: bid=ask in {1,3,5,10,30,100} bps.
   Establishes the floor and shape of `score_challenge` over the trivial
   policy class.
2. Replicate of the inherited best learnable baseline: piecewise-controller
   CEM-best params from `experiments/piecewise_cem_1h_20260422.json`,
   scored on the same seed range so we have an apples-to-apples
   "starting line" the rest of M2 has to beat.

Seeds: range(2000, 2256) — held-out test split (matches the inherited
report's `test_seeds`). 256 seeds keeps wall time ≤ ~5 min.

Outputs:
    research/experiments/2026-05-03-cycle5-m2-starting-line/results/
        fixed_fee_sweep.json
        piecewise_replicate.json
        starting_line.json   # combined summary
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
from arena_policies import PiecewiseControllerParams, PiecewiseControllerStrategy  # noqa: E402

OUTDIR = ROOT / "research/experiments/2026-05-03-cycle5-m2-starting-line/results"
TEST_SEEDS = tuple(range(2000, 2256))

INHERITED_PIECEWISE_PARAMS = {
    "base_fee": 0.0031761646289962934,
    "base_spread": 0.005382800828473529,
    "continuation_large": 0.016965089244693893,
    "continuation_medium": 0.010683567139589125,
    "continuation_small": 0.0007418160153062712,
    "continuation_to_cross_side": 0.6711100624350796,
    "continuation_to_same_side": 0.46227649502613805,
    "large_trade_threshold": 0.017331678478343653,
    "reversal_large": 0.06114156688492659,
    "reversal_medium": 0.023791373551436422,
    "reversal_small": 0.018651454393049955,
    "signal_decay": 0.46913194556337184,
    "small_trade_threshold": 0.004567928620937654,
    "toxicity_decay": 0.5132485563405016,
    "toxicity_to_mid": 0.008964552728672,
    "toxicity_to_side": 0.0438333038385567,
}


def _summarise_batch(batch) -> dict:
    return {
        "score": batch.score,
        "edge_mean_submission": batch.edge_mean_submission,
        "edge_mean_normalizer": batch.edge_mean_normalizer,
        "edge_advantage_mean": batch.edge_advantage_mean,
        "retail_edge_mean_submission": batch.retail_edge_mean_submission,
        "arb_loss_mean_submission": batch.arb_loss_mean_submission,
        "pnl_mean_submission": batch.pnl_mean_submission,
        "pnl_mean_normalizer": batch.pnl_mean_normalizer,
        "n_seeds": len(batch.seeds),
    }


def run_fixed_fee_sweep(fees_bps: tuple[float, ...]) -> list[dict]:
    rows = []
    for bps in fees_bps:
        fee = bps / 1e4
        t0 = time.time()
        batch = run_batch(
            lambda f=fee: FixedFeeStrategy(f, f),
            TEST_SEEDS,
            evaluator_kind="challenge",
        )
        elapsed = time.time() - t0
        row = {"fee_bps": bps, "elapsed_s": elapsed, **_summarise_batch(batch)}
        print(
            f"  fixed_fee bid=ask={bps:>5.1f}bps "
            f"score={row['score']:>8.3f} "
            f"adv={row['edge_advantage_mean']:>+8.3f} "
            f"({elapsed:5.1f}s)",
            flush=True,
        )
        rows.append(row)
    return rows


def run_piecewise_replicate() -> dict:
    params = PiecewiseControllerParams(**INHERITED_PIECEWISE_PARAMS).normalized()
    t0 = time.time()
    batch = run_batch(
        lambda: PiecewiseControllerStrategy(params),
        TEST_SEEDS,
        evaluator_kind="challenge",
    )
    elapsed = time.time() - t0
    summary = _summarise_batch(batch)
    print(
        f"  piecewise(inherited) score={summary['score']:>8.3f} "
        f"adv={summary['edge_advantage_mean']:>+8.3f} ({elapsed:5.1f}s)",
        flush=True,
    )
    return {
        "policy_family": "piecewise",
        "source": "experiments/piecewise_cem_1h_20260422.json::best_validation",
        "params": INHERITED_PIECEWISE_PARAMS,
        "elapsed_s": elapsed,
        **summary,
    }


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f"Test seeds: {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})", flush=True)

    print("\n=== Fixed-fee sweep ===")
    fees_bps = (1.0, 3.0, 5.0, 10.0, 30.0, 100.0)
    fixed_rows = run_fixed_fee_sweep(fees_bps)
    (OUTDIR / "fixed_fee_sweep.json").write_text(
        json.dumps(
            {
                "evaluator_kind": "challenge",
                "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                "rows": fixed_rows,
            },
            indent=2,
        )
    )
    print(f"  -> wrote {OUTDIR / 'fixed_fee_sweep.json'}", flush=True)

    print("\n=== Piecewise replicate (inherited best) ===")
    piecewise_summary = run_piecewise_replicate()
    (OUTDIR / "piecewise_replicate.json").write_text(
        json.dumps(
            {
                "evaluator_kind": "challenge",
                "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                **piecewise_summary,
            },
            indent=2,
        )
    )
    print(f"  -> wrote {OUTDIR / 'piecewise_replicate.json'}", flush=True)

    best_fixed = max(fixed_rows, key=lambda row: row["score"])
    summary = {
        "evaluator_kind": "challenge",
        "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
        "fixed_fee_best": {
            "fee_bps": best_fixed["fee_bps"],
            "score": best_fixed["score"],
        },
        "fixed_fee_30bps": next(row for row in fixed_rows if row["fee_bps"] == 30.0),
        "piecewise_inherited": {
            "score": piecewise_summary["score"],
            "edge_advantage_mean": piecewise_summary["edge_advantage_mean"],
            "source": piecewise_summary["source"],
        },
        "target_score": 540.0,
        "starting_gap_to_target": 540.0 - piecewise_summary["score"],
    }
    (OUTDIR / "starting_line.json").write_text(json.dumps(summary, indent=2))
    print("\n=== Cycle-5 M2 starting line ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
