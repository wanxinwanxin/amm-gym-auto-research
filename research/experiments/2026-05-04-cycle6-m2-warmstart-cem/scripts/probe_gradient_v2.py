"""
Smaller gradient probe (cycle 6 — v2).

The first probe (`probe_gradient.py`) ran out of memory or got killed
silently — used 8 train seeds × 8 iters × 4 LRs (~256 Adam-step
gradients to compute, each with full backward through 256-step tape
across 8 tapes). This v2 runs a tighter sweep:

- 4 train seeds, 5 Adam iters per LR.
- 3 LRs: 1e-5, 1e-4, 1e-3.
- 32 val seeds for fast iteration-level eval.

Goal is unchanged: identify whether *any* learning rate, when starting
from the cycle-6 CEM-best point, makes the exact validation score go
UP rather than DOWN. If yes → cycle 7 runs a longer Adam pass with
that LR. If no → defer gradient until the smooth surrogate is
recalibrated.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTDIR = ROOT / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results"
OUTDIR.mkdir(parents=True, exist_ok=True)

CEM_BEST_PARAMS = json.loads((OUTDIR / "warmstart_cem_test.json").read_text())["best_by_val"]["params"]


def main() -> None:
    from arena_search.diff_simple_amm_search import (
        GradientSearchConfig,
        gradient_ascent_search_with_validation,
    )
    from arena_policies import PiecewiseControllerParams

    train_seeds = tuple(range(0, 4))
    val_seeds = tuple(range(1000, 1032))   # 32 seeds, ~6 sec
    learning_rates = (1e-5, 1e-4, 1e-3)
    iterations = 5

    init_params = PiecewiseControllerParams(**CEM_BEST_PARAMS)

    results = []
    for lr in learning_rates:
        cfg = GradientSearchConfig(
            train_seeds=train_seeds,
            validation_seeds=val_seeds,
            test_seeds=(),
            evaluator_kind="challenge",
            normalizer_fee=0.003,
            train_n_steps=256,
            exact_eval_n_steps=10_000,
            policy_family="piecewise",
        )
        print(f"\n--- LR={lr:.0e}  ({iterations} iters, {len(train_seeds)} train seeds, {len(val_seeds)} val seeds) ---", flush=True)
        t0 = time.time()
        out = gradient_ascent_search_with_validation(
            cfg,
            iterations=iterations,
            learning_rate=lr,
            gradient_clip=None,
            init_params=init_params,
            fresh_validation_interval=0,
            fresh_validation_seed_count=0,
            rerank_top_k=2,
            seed=0,
        )
        elapsed = time.time() - t0
        per_iter = []
        for it in out.history:
            per_iter.append({
                "iter": int(it.iteration),
                "train_obj": float(it.train_objective),
                "grad_norm": float(it.gradient_norm),
                "fixed_val_score": float(it.fixed_validation.score),
                "fixed_val_adv": float(it.fixed_validation.edge_advantage_mean),
            })
            print(
                f"  iter {it.iteration:2d}: train={it.train_objective:+10.3f} "
                f"|g|={it.gradient_norm:8.2f} val={it.fixed_validation.score:7.3f}",
                flush=True,
            )
        scores = [it["fixed_val_score"] for it in per_iter]
        results.append({
            "lr": lr,
            "elapsed_s": elapsed,
            "per_iter": per_iter,
            "best_fixed_val_score": max(scores),
            "best_iter": int(scores.index(max(scores))),
            "final_fixed_val_score": scores[-1],
            "delta_vs_iter0": scores[-1] - scores[0],
        })

    init_anchor_score = results[0]["per_iter"][0]["fixed_val_score"]
    summary = {
        "init_params": "warm-start from cycle-6 CEM best (val=433.566 on 128 seeds, test=432.748 on 256)",
        "anchor_val_score_32seeds_iter0": init_anchor_score,
        "train_seeds": list(train_seeds),
        "val_seeds": list(val_seeds),
        "results": results,
        "best_per_lr": [
            {
                "lr": r["lr"],
                "best_fixed_val_score": r["best_fixed_val_score"],
                "best_iter": r["best_iter"],
                "final_fixed_val_score": r["final_fixed_val_score"],
                "delta_vs_iter0": r["delta_vs_iter0"],
            }
            for r in results
        ],
    }
    (OUTDIR / "gradient_probe.json").write_text(json.dumps(summary, indent=2))
    print("\n=== Best-by-LR ===", flush=True)
    for entry in summary["best_per_lr"]:
        print(json.dumps(entry, indent=2), flush=True)


if __name__ == "__main__":
    main()
