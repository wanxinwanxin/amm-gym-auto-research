"""
M4 cycle-1 — per-trade-size decomposition of the cycle-16 M4 baseline.

Question.
  Cycle 16 found that direct CEM on real_data, warm-started from c5,
  lifted edge_advantage from -5.41 → -5.42 (basically unchanged: c5
  test_edge_advantage was -5.0 ish, M4 baseline test_edge_advantage was
  -5.42) BUT *worsened* retail_advantage from c5's -10.14 → -13.10.

  Per-bucket cycle-16 decomp of c5 had small=-9.49, medium=-1.16,
  large=-0.37 (sums to ~-11.0; matches the overall -11.18 reported in
  cycle-15 within batch). The hypothesis going into cycle 17 is that
  the M4 baseline -13.10 is *also* mostly small-bucket (i.e. CEM-from-
  c5 made the routing collapse worse) rather than uniform across
  buckets. If that's true, M4 cycle 1's "policy complexity sweep" must
  account for the small-bucket routing-fix problem.

Method.
  Same as cycle-16 eval_size_decomp.py, but the anchor is the M4
  baseline best-by-val params from
  research/experiments/2026-05-05-cycle16-trade-size-decomp/results/
  m4_baseline/test.json (best_by_val.params).

  Compare per-bucket against c5 (same warm-start) and c11 (M2
  deliverable). The cycle-16 run already wrote those numbers; we
  re-derive only the M4 baseline here and merge into a combined
  table.

Outputs.
  results/size_decomp_m4_baseline.json — same shape as cycle-16's
  size_decomp.json but for the m4_baseline anchor only.
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

# Bucket cuts: match cycle-16 exactly.
SMALL_CUT = 0.003
LARGE_CUT = 0.012

OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle17-m4-c11-mirror/results"
)
OUTDIR.mkdir(parents=True, exist_ok=True)

ANCHOR_PATH = (
    ROOT
    / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results/"
    "m4_baseline/test.json"
)


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
    amt_y_sub = {b: 0.0 for b in buckets}
    amt_y_norm = {b: 0.0 for b in buckets}

    while not simulator.done:
        step = simulator.step_once()
        fair_price = step["fair_price"]
        for ev in step["trade_events"]:
            if ev["source"] != "retail":
                continue
            ti = ev["trade_info"]
            amount_x = ev["amount_x"]
            amount_y = ev["amount_y"]
            if ti.is_buy:
                trade_edge = amount_x * fair_price - amount_y
            else:
                trade_edge = amount_y - amount_x * fair_price

            size_ratio = amount_y / max(ti.reserve_y, 1e-9)
            bkt = _bucket(size_ratio)
            if ev["venue"] == "submission":
                edge_sub[bkt] += trade_edge
                cnt_sub[bkt] += 1
                amt_y_sub[bkt] += amount_y
            else:
                edge_norm[bkt] += trade_edge
                cnt_norm[bkt] += 1
                amt_y_norm[bkt] += amount_y

    return {
        "edge_sub": edge_sub,
        "edge_norm": edge_norm,
        "cnt_sub": cnt_sub,
        "cnt_norm": cnt_norm,
        "amt_y_sub": amt_y_sub,
        "amt_y_norm": amt_y_norm,
        "sim_retail_edge_sub": simulator.retail_edge_submission,
        "sim_retail_edge_norm": simulator.retail_edge_normalizer,
        "rederived_retail_edge_sub": sum(edge_sub.values()),
        "rederived_retail_edge_norm": sum(edge_norm.values()),
    }


def main() -> None:
    rng = np.random.default_rng(0xC17)
    stdout = (OUTDIR / "size_decomp_m4_baseline.stdout").open("w")

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        stdout.write(line + "\n")
        stdout.flush()

    log(f"Cycle 17 — M4 baseline per-trade-size decomposition; evaluator={EVALUATOR_KIND}; n_seeds={len(VAL_SEEDS)}")

    anchor_doc = json.loads(ANCHOR_PATH.read_text())
    params = anchor_doc["best_by_val"]["params"]
    log(f"  anchor: m4_baseline (n_params={len(params)}); "
        f"reported test_retail_advantage={anchor_doc['best_by_val']['test_retail_advantage']:+.3f}")

    t0 = time.time()
    per_seed = []
    for i, seed in enumerate(VAL_SEEDS):
        r = _eval_one_seed("piecewise", params, seed)
        per_seed.append(r)
        if (i + 1) % 32 == 0:
            log(f"    seed {i+1}/{len(VAL_SEEDS)} | {time.time() - t0:.1f}s elapsed")
    elapsed = time.time() - t0

    buckets = ("small", "medium", "large")
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

    # Identity check.
    sim_sub = np.array([r["sim_retail_edge_sub"] for r in per_seed])
    sim_norm = np.array([r["sim_retail_edge_norm"] for r in per_seed])
    red_sub = np.array([r["rederived_retail_edge_sub"] for r in per_seed])
    red_norm = np.array([r["rederived_retail_edge_norm"] for r in per_seed])
    sub_max_err = float(np.max(np.abs(sim_sub - red_sub)))
    norm_max_err = float(np.max(np.abs(sim_norm - red_norm)))

    summary = {
        "label": "m4_baseline",
        "n_seeds": len(VAL_SEEDS),
        "anchor_params": params,
        "anchor_source": str(ANCHOR_PATH.relative_to(ROOT)),
        "per_bucket": per_bucket,
        "identity_check": {
            "max_abs_err_sub": sub_max_err,
            "max_abs_err_norm": norm_max_err,
        },
        "overall_retail_edge_advantage": float(np.mean(sim_sub - sim_norm)),
        "elapsed_s": elapsed,
    }

    log(
        f"  m4_baseline | overall retail_adv="
        f"{summary['overall_retail_edge_advantage']:+7.3f} | "
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

    # Cross-anchor table: pull cycle-16 c5 and c11 numbers and write a
    # combined table. This is the headline artifact for cycle 17.
    cycle16 = json.loads((
        ROOT
        / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results/size_decomp.json"
    ).read_text())
    c16_anchors = {a["label"]: a for a in cycle16["anchors"]}

    combined = {
        "evaluator_kind": EVALUATOR_KIND,
        "n_seeds": len(VAL_SEEDS),
        "seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
        "normalizer_fee": NORMALIZER_FEE,
        "small_cut": SMALL_CUT,
        "large_cut": LARGE_CUT,
        "anchors": [
            c16_anchors["c5_baseline"],
            summary,
            c16_anchors["c11_d16_s2"],
        ],
        "total_elapsed_s": time.time() - t0,
    }

    # m4 - c5 and m4 - c11 per-bucket retail_edge_advantage diffs.
    diffs = {}
    for bkt in buckets:
        m4 = per_bucket[bkt]["retail_edge_advantage_mean"]
        c5 = c16_anchors["c5_baseline"]["per_bucket"][bkt]["retail_edge_advantage_mean"]
        c11 = c16_anchors["c11_d16_s2"]["per_bucket"][bkt]["retail_edge_advantage_mean"]
        diffs[bkt] = {
            "m4_minus_c5": m4 - c5,
            "m4_minus_c11": m4 - c11,
        }
    combined["diffs"] = diffs
    log(f"  per-bucket diffs (m4 - c5, m4 - c11): {diffs}")

    out_path = OUTDIR / "size_decomp_m4_baseline.json"
    out_path.write_text(json.dumps(combined, indent=2))
    log(f"-> wrote {out_path} ({(time.time() - t0) / 60:.1f} min)")
    stdout.close()


if __name__ == "__main__":
    main()
