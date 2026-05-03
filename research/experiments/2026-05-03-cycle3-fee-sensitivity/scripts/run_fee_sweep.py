"""Sweep fee_bps and measure retail markout_now / markout_next.

Hypothesis tested
-----------------
The realistic-mode simulator's *retail* markout_now mean should scale
~1:1 with the LP fee, because (a) the empirical retail-impact distribution
is parameterized in basis points relative to the mid (so it doesn't move
when you change the fee), (b) all retail flow is filled at the LP's posted
quote, which is mid + fee, and (c) markout_now ignores any forward price
move.

If `slope(retail_markout_now_mean / fee_bps) ≈ 1`, then the +2.74 bps
gap between sim retail markout (5.80 bps at 5 bps fee) and the on-chain
canonical pool's mean (3.06 bps, also 5 bps fee) cannot be explained by
fee mis-specification, and is consistent with a *missing mechanism*
hypothesis: real LPs lose ~2.7 bps per trade to MEV / fast-CEX adverse
selection that the simulator does not currently model.

If the slope is different (especially <1), then retail-impact tail
heaviness is contributing — interesting on its own, and would point to a
different M1 fix.

Cycle-3 BQ outage substitute. The router-filtered + multi-day BQ pulls
are still the canonical falsification path; this sweep is a lighter
independent diagnostic.

Outputs
-------
- ``results/fee_sweep.json``: per-fee-tier mean/std/percentile for retail
  markout_now and markout_next, across N seeds × M steps.
- ``figures/fee_sweep_retail_markout.png``: retail markout vs fee.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from arena_eval.exact_simple_amm.config import ExactSimpleAMMConfig
from arena_eval.exact_simple_amm.simulator import ExactSimpleAMMSimulator
from arena_eval.exact_simple_amm.strategies import FixedFeeStrategy


def sign_aware_markout(executed_price: float, ref_price: float, amm_buys_x: bool) -> float:
    if executed_price <= 0.0 or ref_price <= 0.0:
        return float("nan")
    if amm_buys_x:
        return math.log(ref_price / executed_price)
    return math.log(executed_price / ref_price)


def run_one_seed(seed: int, fee_bps: float, n_steps: int) -> tuple[list[float], list[float]]:
    """Return (retail markout_now bps list, retail markout_next bps list)."""
    fee = fee_bps * 1e-4
    cfg = ExactSimpleAMMConfig.real_data_from_seed(seed)
    # Override n_steps if requested
    if n_steps != cfg.n_steps:
        cfg = cfg.__class__(**{**cfg.__dict__, "n_steps": n_steps})

    submission = FixedFeeStrategy(bid_fee=fee, ask_fee=fee)
    normalizer = FixedFeeStrategy(bid_fee=fee, ask_fee=fee)
    sim = ExactSimpleAMMSimulator(
        config=cfg,
        submission_strategy=submission,
        normalizer_strategy=normalizer,
        seed=seed,
    )

    pending: list[dict] = []
    out_now: list[float] = []
    out_next: list[float] = []

    while not sim.done:
        step_out = sim.step_once()
        fair_price = float(step_out["fair_price"])

        for row in pending:
            mn = sign_aware_markout(row["executed_price"], fair_price, row["amm_buys_x"])
            if not math.isnan(mn):
                out_next.append(mn * 1e4)
        pending = []

        for ev in step_out["trade_events"]:
            if ev["source"] != "retail":
                continue
            ax, ay = float(ev["amount_x"]), float(ev["amount_y"])
            if ax <= 0.0 or ay <= 0.0:
                continue
            executed_price = ay / ax
            amm_buys_x = (ev["trader_side"] == "sell_x")
            now_mk = sign_aware_markout(executed_price, fair_price, amm_buys_x)
            if not math.isnan(now_mk):
                out_now.append(now_mk * 1e4)
            pending.append({"executed_price": executed_price, "amm_buys_x": amm_buys_x})

    return out_now, out_next


def summarise(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean_bps": float(arr.mean()),
        "std_bps": float(arr.std(ddof=1)),
        "p1_bps": float(np.percentile(arr, 1)),
        "p5_bps": float(np.percentile(arr, 5)),
        "p25_bps": float(np.percentile(arr, 25)),
        "p50_bps": float(np.percentile(arr, 50)),
        "p75_bps": float(np.percentile(arr, 75)),
        "p95_bps": float(np.percentile(arr, 95)),
        "p99_bps": float(np.percentile(arr, 99)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-seeds", type=int, default=8)
    parser.add_argument("--seed-base", type=int, default=200)
    parser.add_argument("--n-steps", type=int, default=5000)
    parser.add_argument("--fees", type=str, default="1,3,5,10",
                        help="Comma-separated fee values in bps")
    parser.add_argument(
        "--out-dir",
        default="research/experiments/2026-05-03-cycle3-fee-sensitivity/results",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fee_bps_list = [float(x) for x in args.fees.split(",")]

    summary: dict = {
        "config": {
            "n_seeds": args.n_seeds,
            "seed_base": args.seed_base,
            "n_steps_per_seed": args.n_steps,
            "step_seconds": 12.0,
            "fees_bps": fee_bps_list,
        },
        "by_fee": [],
    }

    for fee_bps in fee_bps_list:
        all_now: list[float] = []
        all_next: list[float] = []
        for i in range(args.n_seeds):
            seed = args.seed_base + i
            now, nxt = run_one_seed(seed, fee_bps, args.n_steps)
            all_now.extend(now)
            all_next.extend(nxt)
            print(f"  fee={fee_bps:>5.1f}bps seed={seed:>3d}  retail_now={len(now):>5d} retail_next={len(nxt):>5d}")
        rec = {
            "fee_bps": fee_bps,
            "retail_markout_now": summarise(all_now),
            "retail_markout_next": summarise(all_next),
        }
        summary["by_fee"].append(rec)
        print(f"fee={fee_bps:>5.1f}bps  mean_now={rec['retail_markout_now']['mean_bps']:+.3f}bps  "
              f"mean_next={rec['retail_markout_next']['mean_bps']:+.3f}bps")

    # Quick linear fit (fee vs mean_now, mean_next) for the headline slope
    fees_arr = np.array([r["fee_bps"] for r in summary["by_fee"]], dtype=float)
    means_now = np.array([r["retail_markout_now"]["mean_bps"] for r in summary["by_fee"]], dtype=float)
    means_next = np.array([r["retail_markout_next"]["mean_bps"] for r in summary["by_fee"]], dtype=float)
    slope_now, intercept_now = np.polyfit(fees_arr, means_now, 1)
    slope_next, intercept_next = np.polyfit(fees_arr, means_next, 1)
    summary["fits"] = {
        "markout_now": {"slope": float(slope_now), "intercept_bps": float(intercept_now)},
        "markout_next": {"slope": float(slope_next), "intercept_bps": float(intercept_next)},
    }

    out_path = out_dir / "fee_sweep.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
