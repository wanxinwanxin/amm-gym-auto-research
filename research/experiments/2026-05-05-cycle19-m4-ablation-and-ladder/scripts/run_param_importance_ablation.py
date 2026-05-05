"""
M4 cycle-3 — param-importance ablation on c11+CEM long.

Question.
  The cycle-18 long-budget CEM run (10 gen × 24 pop, warm-started from
  c11_d16_s2) lifted real_data lift_FF from c11's anchor +2.10 to +3.01
  (val score 3.885, test 3.476, ff_test 0.470). 16 piecewise params
  moved by varying amounts. Which 2-4 params carry the load? What does
  the optimizer have to encode that c11 already-warm-started piecewise
  was missing?

Method.
  For each of the 16 piecewise params, evaluate the "step-back-to-anchor"
  counterfactual: take the c11+CEM long best-by-val params, reset
  param i to the c11_d16_s2 anchor value, leave the other 15 params at
  the c11+CEM long values. Measure val score (n=128) and decompose
  edge_advantage / retail_edge_advantage.

  Sort by val-score drop relative to c11+CEM long baseline. The
  bottom-K params are the load-bearing ones — they're what the richer
  family must capture.

  Constants (mirror cycle 18):
    - normalizer: FixedFee(0.003, 0.003)
    - evaluator: real_data
    - val seeds: range(1000, 1128)  # n=128
    - parallel: ProcessPoolExecutor(MAX_WORKERS)

Decision wiring.
  - Ablation reveals 1-2 dominant params with > +1.0 score drop each
    → policy-family escalation should focus on richer encoding of those
    specific levers (e.g. continuous spread surface vs. 3-bucket).
  - Ablation reveals diffuse importance (no single param > +0.3 drop)
    → a richer family is unlikely to help; the c11+CEM gain is in
    the joint distribution, not a missing dimension.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_policies import (  # noqa: E402
    PiecewiseControllerParams,
    PiecewiseControllerStrategy,
)


OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle19-m4-ablation-and-ladder/results/ablation"
)
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = OUTDIR / "progress.log"

# c11_d16_s2 anchor (cycle-11 grid CEM, M2 deliverable best-by-val).
C11_PARAMS = {
    "base_fee": 0.0007091416018193545,
    "base_spread": 0.003801937123052311,
    "signal_decay": 0.7648063790901181,
    "toxicity_decay": 0.6015456547795871,
    "small_trade_threshold": 0.003401163958663298,
    "large_trade_threshold": 0.010798304729989912,
    "continuation_small": -1.2385103877482917e-05,
    "continuation_medium": 0.006817365552646046,
    "continuation_large": 0.018880066138232437,
    "reversal_small": 0.009476666430879962,
    "reversal_medium": 0.020351735057164123,
    "reversal_large": 0.07500325588327934,
    "continuation_to_same_side": 0.32864935375355064,
    "continuation_to_cross_side": 1.577209104304979,
    "toxicity_to_mid": 0.012951221801647789,
    "toxicity_to_side": 0.07081310942619837,
}

# c11+CEM long best-by-val (cycle-18 result).
C11_LONG_PARAMS = {
    "base_fee": 0.0002651625453621829,
    "base_spread": 0.004070554016340082,
    "signal_decay": 0.7627950328668307,
    "toxicity_decay": 0.7516377170207057,
    "small_trade_threshold": 0.002848486560218609,
    "large_trade_threshold": 0.008866574986467687,
    "continuation_small": 8.283451496244375e-05,
    "continuation_medium": 0.006929076834258454,
    "continuation_large": 0.017986720175801947,
    "reversal_small": 0.004837147255038543,
    "reversal_medium": 0.012729063516975241,
    "reversal_large": 0.07976951856036607,
    "continuation_to_same_side": -0.19329440684669405,
    "continuation_to_cross_side": 0.9267032329066462,
    "toxicity_to_mid": 0.011186051913361214,
    "toxicity_to_side": 0.07886754688062839,
}

EVALUATOR_KIND = "real_data"
VAL_SEEDS = tuple(range(1000, 1128))  # n=128
NORMALIZER_FEE = 0.003
MAX_WORKERS = max(1, (os.cpu_count() or 1) - 1)


def _log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOGFILE.open("a") as f:
        f.write(line + "\n")


def _evaluate_one_candidate(payload: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa
    from arena_policies import (  # noqa
        PiecewiseControllerParams,
        PiecewiseControllerStrategy,
    )

    params = PiecewiseControllerParams(**payload["params"]).normalized()
    seeds = tuple(payload["seeds"])
    nfee = payload["normalizer_fee"]
    eval_kind = payload["evaluator_kind"]
    batch = run_batch(
        lambda: PiecewiseControllerStrategy(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(nfee, nfee),
        evaluator_kind=eval_kind,
    )
    return {
        "candidate_id": payload["candidate_id"],
        "params": payload["params"],
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "retail_edge_advantage_mean": float(batch.retail_edge_advantage_mean),
    }


def main() -> None:
    LOGFILE.open("w").close()
    _log(
        f"M4 cycle-3 param-importance ablation | piecewise on {EVALUATOR_KIND} | "
        f"val n={len(VAL_SEEDS)} | workers={MAX_WORKERS}"
    )

    names = list(C11_LONG_PARAMS.keys())
    candidates: list[dict] = []
    # Baseline: c11+CEM long itself
    candidates.append(
        {
            "candidate_id": "c11_long_baseline",
            "ablated_param": None,
            "params": dict(C11_LONG_PARAMS),
            "seeds": list(VAL_SEEDS),
            "normalizer_fee": NORMALIZER_FEE,
            "evaluator_kind": EVALUATOR_KIND,
        }
    )
    # Anchor-only baseline (sanity)
    candidates.append(
        {
            "candidate_id": "c11_anchor_baseline",
            "ablated_param": "ALL",
            "params": dict(C11_PARAMS),
            "seeds": list(VAL_SEEDS),
            "normalizer_fee": NORMALIZER_FEE,
            "evaluator_kind": EVALUATOR_KIND,
        }
    )
    # Per-param step-back-to-anchor candidates
    for name in names:
        params = dict(C11_LONG_PARAMS)
        params[name] = C11_PARAMS[name]
        candidates.append(
            {
                "candidate_id": f"ablate_{name}",
                "ablated_param": name,
                "params": params,
                "seeds": list(VAL_SEEDS),
                "normalizer_fee": NORMALIZER_FEE,
                "evaluator_kind": EVALUATOR_KIND,
            }
        )

    _log(f"  total candidates: {len(candidates)}")

    t0 = time.time()
    results: dict[str, dict] = {}
    completed = 0
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_evaluate_one_candidate, c): c["candidate_id"] for c in candidates}
        for fut in as_completed(futures):
            cid = futures[fut]
            try:
                r = fut.result()
            except Exception as e:
                _log(f"  ERROR for {cid}: {e}")
                continue
            results[cid] = r
            completed += 1
            elapsed = time.time() - t0
            _log(
                f"  [{completed}/{len(candidates)}] {cid:42s} score={r['score']:+7.3f} "
                f"adv={r['edge_advantage_mean']:+7.3f} retail_adv={r['retail_edge_advantage_mean']:+7.3f} "
                f"({elapsed:.1f}s)"
            )

    _log(f"  total elapsed: {time.time()-t0:.1f}s")

    # Build ranked output
    base = results.get("c11_long_baseline")
    anchor = results.get("c11_anchor_baseline")
    if base is None:
        _log("  ERROR: baseline missing — bailing")
        return

    rows = []
    for name in names:
        cid = f"ablate_{name}"
        r = results.get(cid)
        if r is None:
            continue
        rows.append(
            {
                "param": name,
                "score": r["score"],
                "score_drop": base["score"] - r["score"],
                "edge_adv": r["edge_advantage_mean"],
                "edge_adv_drop": base["edge_advantage_mean"] - r["edge_advantage_mean"],
                "retail_adv": r["retail_edge_advantage_mean"],
                "retail_adv_drop": base["retail_edge_advantage_mean"]
                - r["retail_edge_advantage_mean"],
                "anchor_value": C11_PARAMS[name],
                "long_value": C11_LONG_PARAMS[name],
                "delta": C11_LONG_PARAMS[name] - C11_PARAMS[name],
            }
        )
    rows.sort(key=lambda r: -r["score_drop"])  # largest drop first

    _log("")
    _log("Ranked param importance (largest score drop = most load-bearing):")
    _log(
        f"  {'rank':<5} {'param':<30} {'score':>7} {'Δscore':>8} {'Δretail':>9} {'Δedge':>8}"
    )
    for i, r in enumerate(rows, 1):
        _log(
            f"  {i:<5} {r['param']:<30} {r['score']:>7.3f} {r['score_drop']:>+8.3f} "
            f"{r['retail_adv_drop']:>+9.3f} {r['edge_adv_drop']:>+8.3f}"
        )

    _log("")
    _log(
        f"baseline score: {base['score']:+7.3f} retail_adv={base['retail_edge_advantage_mean']:+7.3f} "
        f"edge_adv={base['edge_advantage_mean']:+7.3f}"
    )
    if anchor is not None:
        _log(
            f"anchor   score: {anchor['score']:+7.3f} retail_adv={anchor['retail_edge_advantage_mean']:+7.3f} "
            f"edge_adv={anchor['edge_advantage_mean']:+7.3f}"
        )
        _log(
            f"  → full c11_long → c11 reset gives Δscore={base['score']-anchor['score']:+.3f} "
            f"(should equal sum of all 16 ablations only if effects are independent — they're not)"
        )

    out = {
        "policy_family": "piecewise",
        "evaluator_kind": EVALUATOR_KIND,
        "val_n_seeds": len(VAL_SEEDS),
        "baseline": results.get("c11_long_baseline"),
        "anchor_baseline": results.get("c11_anchor_baseline"),
        "ranked": rows,
        "all_results": results,
    }
    with (OUTDIR / "results.json").open("w") as f:
        json.dump(out, f, indent=2)
    _log(f"wrote {OUTDIR / 'results.json'}")


if __name__ == "__main__":
    main()
