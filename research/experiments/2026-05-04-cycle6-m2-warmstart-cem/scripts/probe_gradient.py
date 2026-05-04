"""
Cycle-6 side experiment — probe whether gradient ascent on the
differentiable surrogate (`tape_smooth`) can lift the warm-start CEM
result further.

Why: cycle-5's STATE.md flagged `tape_smooth` + Adam as the cycle-6
fallback if CEM stalls. CEM did (sort of) — it converged tightly to
432.7 on test. The cycle-6 prior was that gradient might add another
10-20 pts on top. But an earlier ad-hoc probe (LR=1e-3) made the val
score WORSE after one Adam step (401.93 → 376.16) — gradient norm
was 4815 and the step size was unreasonably large.

This probe is the small, controlled re-test:
- Warm-start at the cycle-6 CEM-best params.
- Try several learning rates (1e-5, 3e-5, 1e-4, 3e-4) for 8 Adam
  steps each.
- Record the smooth train objective and the exact fixed-val score
  per step.

If any LR makes the val score climb above 433, gradient is viable for
cycle 7 and we can do a longer run. If none do, cycle 7 should pivot
(richer policy / inventory shaping / different surrogate calibration).

The probe is small on purpose — 8 Adam steps × 4 LRs × 8 train seeds
≈ 4-5 min of JAX trace+run plus a few minutes of exact eval.
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

# Loaded from warmstart_cem_test.json::best_by_val::params (cycle-6).
CEM_BEST_PARAMS = json.loads((OUTDIR / "warmstart_cem_test.json").read_text())["best_by_val"]["params"]


def main() -> None:
    from arena_search.diff_simple_amm_search import (
        GradientSearchConfig,
        gradient_ascent_search_with_validation,
    )
    from arena_policies import PiecewiseControllerParams

    train_seeds = tuple(range(0, 8))
    val_seeds = tuple(range(1000, 1064))   # 64 val seeds, fast

    learning_rates = (1e-5, 3e-5, 1e-4, 3e-4)
    iterations = 8

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
        print(f"\n--- LR={lr:.0e} ({iterations} Adam iters, {len(train_seeds)} train seeds) ---", flush=True)
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
                "iter": it.iteration,
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
        results.append({"lr": lr, "elapsed_s": elapsed, "per_iter": per_iter})

    # Pull the best fixed_val score per LR; identify the best overall.
    best_per_lr = []
    for r in results:
        scores = [it["fixed_val_score"] for it in r["per_iter"]]
        best_per_lr.append({
            "lr": r["lr"],
            "best_fixed_val_score": max(scores),
            "best_iter": int(scores.index(max(scores))),
            "final_fixed_val_score": scores[-1],
            "delta_vs_init_iter0": scores[-1] - scores[0],
        })

    summary = {
        "init_params": "warm-start from cycle-6 CEM best (val=433.566, test=432.748)",
        "init_val_seeds_subset_score": "see iter=0 of each LR run for the smooth-trained iter-0 result",
        "train_seeds": list(train_seeds),
        "val_seeds": list(val_seeds),
        "results": results,
        "best_per_lr": best_per_lr,
    }
    (OUTDIR / "gradient_probe.json").write_text(json.dumps(summary, indent=2))
    print("\n=== Best-by-LR ===", flush=True)
    for entry in best_per_lr:
        print(json.dumps(entry, indent=2), flush=True)


if __name__ == "__main__":
    main()
