"""Run the realistic-mode exact simulator across N seeds and dump per-trade markouts.

Outputs
-------
- ``results/sim_markouts.parquet``: per-trade record with executed price, fair
  prices at trade time and one block later, side, venue, source (retail or arb),
  and derived markouts (now and next-block).
- ``results/sim_summary.json``: percentile / mean / std rollup grouped by
  (venue, source) and overall.

The simulator uses ``ExactSimpleAMMConfig.real_data_from_seed`` (regime-switching
price + empirical-impact retail) with a 5 bps fixed fee on both venues — that
matches the canonical reference pool ``WETH/USDC 0.05%`` we use for the BQ
ground-truth distribution.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from arena_eval.exact_simple_amm.config import ExactSimpleAMMConfig
from arena_eval.exact_simple_amm.simulator import ExactSimpleAMMSimulator
from arena_eval.exact_simple_amm.strategies import FixedFeeStrategy


def sign_aware_markout(executed_price: float, ref_price: float, amm_buys_x: bool) -> float:
    """Return log markout from the LP's perspective.

    LP buys X (retail sells X to AMM): executed_price = Y per X received by retail
    (= Y per X paid by LP). Positive markout means the LP got X cheap relative to
    the reference price, i.e. ``log(ref_price / executed_price)``.

    LP sells X (retail buys X from AMM): executed_price = Y per X paid by retail
    (= Y per X received by LP). Positive markout means the LP got more Y per X than
    the reference, i.e. ``log(executed_price / ref_price)``.
    """
    if executed_price <= 0.0 or ref_price <= 0.0:
        return float("nan")
    if amm_buys_x:
        return math.log(ref_price / executed_price)
    return math.log(executed_price / ref_price)


def run_one_seed(
    seed: int,
    fee_bps: float,
    config: ExactSimpleAMMConfig,
) -> list[dict]:
    """Run one seed and return per-trade rows."""
    fee = fee_bps * 1e-4
    submission = FixedFeeStrategy(bid_fee=fee, ask_fee=fee)
    normalizer = FixedFeeStrategy(bid_fee=fee, ask_fee=fee)
    sim = ExactSimpleAMMSimulator(
        config=config,
        submission_strategy=submission,
        normalizer_strategy=normalizer,
        seed=seed,
    )

    pending_rows: list[dict] = []
    out_rows: list[dict] = []
    fair_price_history: list[float] = []

    while not sim.done:
        step_out = sim.step_once()
        fair_price = float(step_out["fair_price"])
        fair_price_history.append(fair_price)
        timestamp = int(step_out["timestamp"])

        # Resolve the previous-step pending rows now that we know fair_price
        # (which acts as the "next block mid"):
        for row in pending_rows:
            row["fair_price_next"] = fair_price
            row["markout_next_log"] = sign_aware_markout(
                row["executed_price"], fair_price, row["amm_buys_x"]
            )
        out_rows.extend(pending_rows)
        pending_rows = []

        for ev in step_out["trade_events"]:
            amount_x = float(ev["amount_x"])
            amount_y = float(ev["amount_y"])
            if amount_x <= 0.0 or amount_y <= 0.0:
                continue
            executed_price = amount_y / amount_x
            amm_buys_x = (ev["trader_side"] == "sell_x")  # retail sold X to AMM
            row = {
                "seed": seed,
                "timestamp": timestamp,
                "venue": ev["venue"],
                "source": ev["source"],
                "amm_buys_x": amm_buys_x,
                "amount_x": amount_x,
                "amount_y": amount_y,
                "executed_price": executed_price,
                "fair_price": fair_price,
                "markout_now_log": sign_aware_markout(executed_price, fair_price, amm_buys_x),
            }
            pending_rows.append(row)

    # Trades from the last step never get a "next" mid — drop them but keep the
    # markout_now record for completeness (set markout_next_log to NaN).
    for row in pending_rows:
        row["fair_price_next"] = float("nan")
        row["markout_next_log"] = float("nan")
    out_rows.extend(pending_rows)

    return out_rows


def summarise(df: pd.DataFrame, label: str) -> dict:
    pcts = [1, 5, 25, 50, 75, 95, 99]
    out = {"label": label, "n": int(len(df))}
    for col in ["markout_now_log", "markout_next_log"]:
        series = df[col].dropna()
        if len(series) == 0:
            out[col] = {"n": 0}
            continue
        bps = series * 1e4
        out[col] = {
            "n": int(len(series)),
            "mean_bps": float(bps.mean()),
            "std_bps": float(bps.std(ddof=1)),
        }
        for p in pcts:
            out[col][f"p{p}_bps"] = float(np.percentile(bps, p))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-seeds", type=int, default=32)
    parser.add_argument("--seed-base", type=int, default=0)
    parser.add_argument("--fee-bps", type=float, default=5.0,
                        help="LP fee in bps for both bid/ask on both venues. "
                             "Default 5 bps to match the canonical Uniswap v3 "
                             "0.05% pool.")
    parser.add_argument("--out-dir", default="research/experiments/2026-04-30-2240-m1-baseline-markout/results")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for i in range(args.n_seeds):
        seed = args.seed_base + i
        cfg = ExactSimpleAMMConfig.real_data_from_seed(seed)
        rows = run_one_seed(seed, args.fee_bps, cfg)
        print(f"  seed {seed}: {len(rows)} trades")
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    parquet_path = out_dir / "sim_markouts.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"wrote {parquet_path} ({len(df)} rows)")

    summary: dict = {
        "config": {
            "n_seeds": args.n_seeds,
            "seed_base": args.seed_base,
            "fee_bps": args.fee_bps,
            "evaluator_kind": "real_data",
            "n_steps_per_seed": 10_000,
            "step_seconds": 12.0,
        },
        "groups": [],
    }
    summary["groups"].append(summarise(df, "all_trades"))
    summary["groups"].append(
        summarise(df[df["source"] == "retail"], "retail_all_venues")
    )
    summary["groups"].append(
        summarise(df[df["source"] == "arb"], "arb_all_venues")
    )
    for venue in ["submission", "normalizer"]:
        summary["groups"].append(
            summarise(df[(df["source"] == "retail") & (df["venue"] == venue)],
                      f"retail_{venue}")
        )
    summary_path = out_dir / "sim_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
