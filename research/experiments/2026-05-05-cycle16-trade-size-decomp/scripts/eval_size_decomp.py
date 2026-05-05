"""
M3 cycle-3 — per-trade-size decomposition of retail edge for c5 vs c11.

Question.
  Cycle 15 localized the early-anchor (c5) OOD failure mode to retail-flow
  pricing: retail_edge_advantage swung -9.99 (c5) → +1.06 (c11), while
  arb_loss_advantage stayed in a narrow +1.7 to +3.7 band across the
  whole anchor trajectory. The active hypothesis going into cycle 16 is:
  *the early-anchor harm is concentrated in specific trade-size buckets*.
  If true, M4 has a concrete inductive-bias target. If false (uniform
  across buckets), the real_data evaluator is the bottleneck and we go
  straight to direct M4 optimization on real_data.

Method.
  We bucket retail trades by the same `size_ratio = amount_y /
  reserve_y_post` that the piecewise controller itself uses (file:
  arena_policies/piecewise_controller.py:90), with cuts at the c5
  default thresholds 0.003 (small/medium) and 0.012 (medium/large).

  The simulator's `step_once()` already exposes every trade event
  (including arb), pre/post state, and trade_info. We loop step_once
  externally so we can accumulate per-bucket retail edge for
  submission and normalizer venues without modifying the simulator
  itself.

  trade_edge formula (retail trade):
    if amm_buys_x (i.e. amm gets x, gives y → trader sold x):
        edge = amount_x * fair_price - amount_y
    else (amm sells x, gets y → trader bought x):
        edge = amount_y - amount_x * fair_price
  This matches arena_eval/exact_simple_amm/simulator.py:738.

Anchors evaluated.
  c5 baseline (piecewise default — closest thing to "starting line")
  c11 d16_s2 (M2 best — closest thing to "M2 deliverable")
  Both on real_data evaluator, n=128 seeds (val split, faster than the
  cycle-15 256-seed test split — since cycle 15 already CI-locked the
  aggregate retail/arb numbers, this cycle just needs the bucket
  decomposition to be directionally clear).

Outputs.
  results/size_decomp.json:
    per-anchor x per-bucket: count_sub, count_norm, edge_sub, edge_norm,
    retail_edge_advantage, mean_amount_y_sub
  figures/retail_edge_by_bucket.png:
    grouped bar chart, c5 vs c11, by bucket
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy  # noqa: E402
from arena_eval.exact_simple_amm.config import ExactSimpleAMMConfig  # noqa: E402
from arena_eval.exact_simple_amm.simulator import ExactSimpleAMMSimulator  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

VAL_SEEDS = tuple(range(1000, 1128))
NORMALIZER_FEE = 0.003
EVALUATOR_KIND = "real_data"

# Bucket cuts on size_ratio = amount_y / reserve_y_post. Match c5 defaults.
SMALL_CUT = 0.003
LARGE_CUT = 0.012

OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results"
)
OUTDIR.mkdir(parents=True, exist_ok=True)

ANCHORS = [
    {
        "label": "c5_baseline",
        "family": "piecewise",
        "path": "research/experiments/2026-05-03-cycle5-m2-starting-line/results/piecewise_replicate.json",
        "params_key": "params",
    },
    {
        "label": "c11_d16_s2",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2/result.json",
        "params_key": ("best_by_val", "params"),
    },
]


def _get(d: dict, key):
    if isinstance(key, tuple):
        for k in key:
            d = d[k]
        return d
    return d[key]


def _strip_noop(params: dict) -> dict:
    return {k: v for k, v in params.items() if not k.startswith("noop_")}


def _bucket(size_ratio: float) -> str:
    if size_ratio < SMALL_CUT:
        return "small"
    if size_ratio < LARGE_CUT:
        return "medium"
    return "large"


def _bootstrap_ci(values: np.ndarray, n_bs: int, rng: np.random.Generator) -> tuple[float, float]:
    n = values.shape[0]
    if n == 0:
        return (0.0, 0.0)
    idx = rng.integers(0, n, size=(n_bs, n))
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _eval_one_seed(
    family: str,
    params_dict: dict,
    seed: int,
) -> dict:
    """Run one episode and return per-bucket retail edge totals (sub-norm)."""
    spec = POLICY_SPECS[family]
    cleaned = _strip_noop(params_dict)
    params = spec.params_cls(**cleaned).normalized()
    submission_strategy = spec.strategy_cls(params)
    normalizer_strategy = FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE)

    config = ExactSimpleAMMConfig.for_evaluator(seed, EVALUATOR_KIND)
    simulator = ExactSimpleAMMSimulator(
        config=config,
        submission_strategy=submission_strategy,
        normalizer_strategy=normalizer_strategy,
        seed=seed,
    )

    # Per-bucket × per-venue accumulators.
    buckets = ("small", "medium", "large")
    edge_sub = {b: 0.0 for b in buckets}
    edge_norm = {b: 0.0 for b in buckets}
    cnt_sub = {b: 0 for b in buckets}
    cnt_norm = {b: 0 for b in buckets}
    amt_y_sub = {b: 0.0 for b in buckets}
    amt_y_norm = {b: 0.0 for b in buckets}

    while not simulator.done:
        step = simulator.step_once()
        fair_price = step["fair_price"]
        for ev in step["trade_events"]:
            if ev["source"] != "retail":
                continue
            ti = ev["trade_info"]  # post-trade
            amount_x = ev["amount_x"]
            amount_y = ev["amount_y"]
            # trade_edge: same convention as simulator.py:738
            if ti.is_buy:
                # amm_buys_x is False (trader bought x → amm sold x).
                # The simulator treats trader_side="buy_x" as amm_buys_x=False.
                # is_buy on TradeInfo means "amm bought x" (see execute_buy_x).
                # So is_buy=True → amm_buys_x=True → trader sold x.
                trade_edge = amount_x * fair_price - amount_y
            else:
                trade_edge = amount_y - amount_x * fair_price

            size_ratio = amount_y / max(ti.reserve_y, 1e-9)
            bkt = _bucket(size_ratio)
            if ev["venue"] == "submission":
                edge_sub[bkt] += trade_edge
                cnt_sub[bkt] += 1
                amt_y_sub[bkt] += amount_y
            else:  # normalizer
                edge_norm[bkt] += trade_edge
                cnt_norm[bkt] += 1
                amt_y_norm[bkt] += amount_y

    # Sanity: also track simulator's overall retail edge totals to verify
    # we re-derived them correctly.
    sim_retail_edge_sub = simulator.retail_edge_submission
    sim_retail_edge_norm = simulator.retail_edge_normalizer
    re_sub = sum(edge_sub.values())
    re_norm = sum(edge_norm.values())

    return {
        "edge_sub": edge_sub,
        "edge_norm": edge_norm,
        "cnt_sub": cnt_sub,
        "cnt_norm": cnt_norm,
        "amt_y_sub": amt_y_sub,
        "amt_y_norm": amt_y_norm,
        "sim_retail_edge_sub": sim_retail_edge_sub,
        "sim_retail_edge_norm": sim_retail_edge_norm,
        "rederived_retail_edge_sub": re_sub,
        "rederived_retail_edge_norm": re_norm,
    }


def main() -> None:
    rng = np.random.default_rng(0xC16)
    stdout = (OUTDIR / "size_decomp.stdout").open("w")

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        stdout.write(line + "\n")
        stdout.flush()

    log(f"Cycle 16 — per-trade-size decomposition; evaluator={EVALUATOR_KIND}; n_seeds={len(VAL_SEEDS)}")

    results = []
    t_start = time.time()
    for anchor in ANCHORS:
        path = ROOT / anchor["path"]
        d = json.loads(path.read_text())
        params = _get(d, anchor["params_key"])

        log(f"  evaluating anchor {anchor['label']} (n_params={len(params)})…")
        t0 = time.time()
        per_seed = []
        for i, seed in enumerate(VAL_SEEDS):
            r = _eval_one_seed(anchor["family"], params, seed)
            per_seed.append(r)
            if (i + 1) % 32 == 0:
                log(f"    seed {i+1}/{len(VAL_SEEDS)} | {time.time() - t0:.1f}s elapsed")
        elapsed = time.time() - t0

        # Aggregate per-bucket arrays for advantage stats.
        buckets = ("small", "medium", "large")
        anchor_summary = {"label": anchor["label"], "n_seeds": len(VAL_SEEDS)}
        per_bucket = {}
        for bkt in buckets:
            adv_per_seed = np.array(
                [r["edge_sub"][bkt] - r["edge_norm"][bkt] for r in per_seed],
                dtype=np.float64,
            )
            cnt_sub_per_seed = np.array(
                [r["cnt_sub"][bkt] for r in per_seed], dtype=np.float64
            )
            cnt_norm_per_seed = np.array(
                [r["cnt_norm"][bkt] for r in per_seed], dtype=np.float64
            )
            amt_y_sub_per_seed = np.array(
                [r["amt_y_sub"][bkt] for r in per_seed], dtype=np.float64
            )
            amt_y_norm_per_seed = np.array(
                [r["amt_y_norm"][bkt] for r in per_seed], dtype=np.float64
            )
            edge_sub_per_seed = np.array(
                [r["edge_sub"][bkt] for r in per_seed], dtype=np.float64
            )
            edge_norm_per_seed = np.array(
                [r["edge_norm"][bkt] for r in per_seed], dtype=np.float64
            )
            adv_lo, adv_hi = _bootstrap_ci(adv_per_seed, 10_000, rng)
            per_bucket[bkt] = {
                "retail_edge_advantage_mean": float(adv_per_seed.mean()),
                "retail_edge_advantage_ci95": [adv_lo, adv_hi],
                "edge_sub_mean": float(edge_sub_per_seed.mean()),
                "edge_norm_mean": float(edge_norm_per_seed.mean()),
                "count_sub_mean": float(cnt_sub_per_seed.mean()),
                "count_norm_mean": float(cnt_norm_per_seed.mean()),
                "amt_y_sub_mean": float(amt_y_sub_per_seed.mean()),
                "amt_y_norm_mean": float(amt_y_norm_per_seed.mean()),
            }
        # Overall sanity: rederived = simulator-aggregate
        sim_sub = np.array([r["sim_retail_edge_sub"] for r in per_seed])
        sim_norm = np.array([r["sim_retail_edge_norm"] for r in per_seed])
        red_sub = np.array([r["rederived_retail_edge_sub"] for r in per_seed])
        red_norm = np.array([r["rederived_retail_edge_norm"] for r in per_seed])
        sub_max_err = float(np.max(np.abs(sim_sub - red_sub)))
        norm_max_err = float(np.max(np.abs(sim_norm - red_norm)))
        anchor_summary["per_bucket"] = per_bucket
        anchor_summary["identity_check"] = {
            "max_abs_err_sub": sub_max_err,
            "max_abs_err_norm": norm_max_err,
        }
        anchor_summary["overall_retail_edge_advantage"] = float(
            np.mean(sim_sub - sim_norm)
        )
        anchor_summary["elapsed_s"] = elapsed
        results.append(anchor_summary)

        # Log compact summary.
        log(
            f"  {anchor['label']:14s} | overall retail_adv="
            f"{anchor_summary['overall_retail_edge_advantage']:+7.3f} | "
            f"sub_id_err={sub_max_err:.2e} norm_id_err={norm_max_err:.2e} | "
            f"{elapsed:.1f}s"
        )
        for bkt in buckets:
            r = per_bucket[bkt]
            log(
                f"    {bkt:6s} adv={r['retail_edge_advantage_mean']:+7.3f} "
                f"[{r['retail_edge_advantage_ci95'][0]:+6.2f},{r['retail_edge_advantage_ci95'][1]:+6.2f}] "
                f"| n_sub={r['count_sub_mean']:6.1f} n_norm={r['count_norm_mean']:6.1f} "
                f"| edge_sub={r['edge_sub_mean']:+7.3f} edge_norm={r['edge_norm_mean']:+7.3f}"
            )

    # Cross-anchor diff: c5 minus c11 per bucket.
    if len(results) == 2:
        c5 = results[0]["per_bucket"]
        c11 = results[1]["per_bucket"]
        diffs = {}
        for bkt in ("small", "medium", "large"):
            diffs[bkt] = c5[bkt]["retail_edge_advantage_mean"] - c11[bkt]["retail_edge_advantage_mean"]
        log(f"  c5 minus c11 retail_edge_advantage by bucket: {diffs}")
    else:
        diffs = {}

    out = {
        "evaluator_kind": EVALUATOR_KIND,
        "n_seeds": len(VAL_SEEDS),
        "seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
        "normalizer_fee": NORMALIZER_FEE,
        "small_cut": SMALL_CUT,
        "large_cut": LARGE_CUT,
        "anchors": results,
        "diffs_c5_minus_c11": diffs,
        "total_elapsed_s": time.time() - t_start,
    }
    out_path = OUTDIR / "size_decomp.json"
    out_path.write_text(json.dumps(out, indent=2))
    log(f"-> wrote {out_path} ({(time.time() - t_start) / 60:.1f} min)")
    stdout.close()


if __name__ == "__main__":
    main()
