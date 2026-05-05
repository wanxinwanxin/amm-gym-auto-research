"""Per-trade-size decomposition of cycle-17 c11_mirror best_by_val params.

Question. Cycle 17's c11+CEM lifted lift_FF +2.10 → +2.77 with retail
kept positive (+0.66). Did it preserve the c11 small-bucket
routing/pricing structure (the key c11 vs c5 difference identified
cycle 16), or did it drift toward an arb-side optimum like c5+CEM did?

Method. Same script as eval_size_decomp_m4_baseline.py, just pulling
params from the c11_mirror test.json instead.
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
SMALL_CUT = 0.003
LARGE_CUT = 0.012

OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle17-m4-c11-mirror/results"
)
ANCHOR_PATH = OUTDIR / "m4_c11_mirror/test.json"


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


def _eval_one_seed(family: str, params_dict: dict, seed: int) -> dict:
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

    buckets = ("small", "medium", "large")
    edge_sub = {b: 0.0 for b in buckets}
    edge_norm = {b: 0.0 for b in buckets}
    cnt_sub = {b: 0 for b in buckets}
    cnt_norm = {b: 0 for b in buckets}

    while not simulator.done:
        step = simulator.step_once()
        fair_price = step["fair_price"]
        for ev in step["trade_events"]:
            if ev["source"] != "retail":
                continue
            ti = ev["trade_info"]
            amount_x = ev["amount_x"]
            amount_y = ev["amount_y"]
            trade_edge = (amount_x * fair_price - amount_y) if ti.is_buy else (amount_y - amount_x * fair_price)
            size_ratio = amount_y / max(ti.reserve_y, 1e-9)
            bkt = _bucket(size_ratio)
            if ev["venue"] == "submission":
                edge_sub[bkt] += trade_edge
                cnt_sub[bkt] += 1
            else:
                edge_norm[bkt] += trade_edge
                cnt_norm[bkt] += 1

    return {
        "edge_sub": edge_sub,
        "edge_norm": edge_norm,
        "cnt_sub": cnt_sub,
        "cnt_norm": cnt_norm,
        "sim_retail_edge_sub": simulator.retail_edge_submission,
        "sim_retail_edge_norm": simulator.retail_edge_normalizer,
    }


def main() -> None:
    rng = np.random.default_rng(0xC17B)
    anchor_doc = json.loads(ANCHOR_PATH.read_text())
    params = anchor_doc["best_by_val"]["params"]
    print(f"Cycle 17 — c11_mirror per-trade-size decomposition; n_seeds={len(VAL_SEEDS)}")
    print(f"  anchor: c11_mirror best_by_val (n_params={len(params)})")

    t0 = time.time()
    per_seed = []
    for i, seed in enumerate(VAL_SEEDS):
        per_seed.append(_eval_one_seed("piecewise", params, seed))
        if (i + 1) % 32 == 0:
            print(f"    seed {i+1}/{len(VAL_SEEDS)} | {time.time() - t0:.1f}s")

    buckets = ("small", "medium", "large")
    per_bucket = {}
    for bkt in buckets:
        adv_per_seed = np.array(
            [r["edge_sub"][bkt] - r["edge_norm"][bkt] for r in per_seed],
            dtype=np.float64,
        )
        cnt_sub_per_seed = np.array([r["cnt_sub"][bkt] for r in per_seed], dtype=np.float64)
        cnt_norm_per_seed = np.array([r["cnt_norm"][bkt] for r in per_seed], dtype=np.float64)
        edge_sub_per_seed = np.array([r["edge_sub"][bkt] for r in per_seed], dtype=np.float64)
        edge_norm_per_seed = np.array([r["edge_norm"][bkt] for r in per_seed], dtype=np.float64)
        adv_lo, adv_hi = _bootstrap_ci(adv_per_seed, 10_000, rng)
        per_bucket[bkt] = {
            "retail_edge_advantage_mean": float(adv_per_seed.mean()),
            "retail_edge_advantage_ci95": [adv_lo, adv_hi],
            "edge_sub_mean": float(edge_sub_per_seed.mean()),
            "edge_norm_mean": float(edge_norm_per_seed.mean()),
            "count_sub_mean": float(cnt_sub_per_seed.mean()),
            "count_norm_mean": float(cnt_norm_per_seed.mean()),
        }

    sim_sub = np.array([r["sim_retail_edge_sub"] for r in per_seed])
    sim_norm = np.array([r["sim_retail_edge_norm"] for r in per_seed])
    overall = float(np.mean(sim_sub - sim_norm))

    out = {
        "label": "c11_mirror",
        "n_seeds": len(VAL_SEEDS),
        "per_bucket": per_bucket,
        "overall_retail_edge_advantage": overall,
        "anchor_params": params,
        "elapsed_s": time.time() - t0,
    }

    print(f"  overall retail_adv={overall:+7.3f}")
    for bkt in buckets:
        r = per_bucket[bkt]
        print(
            f"    {bkt:6s} adv={r['retail_edge_advantage_mean']:+7.3f} "
            f"[{r['retail_edge_advantage_ci95'][0]:+5.2f},{r['retail_edge_advantage_ci95'][1]:+5.2f}] "
            f"| n_sub={r['count_sub_mean']:6.1f} n_norm={r['count_norm_mean']:6.1f} "
            f"| edge_sub={r['edge_sub_mean']:+7.3f} edge_norm={r['edge_norm_mean']:+7.3f}"
        )

    out_path = OUTDIR / "size_decomp_c11_mirror.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"-> wrote {out_path}")


if __name__ == "__main__":
    main()
