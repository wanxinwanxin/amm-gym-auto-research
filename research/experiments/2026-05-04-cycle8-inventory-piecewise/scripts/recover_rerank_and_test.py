"""Recover the final test eval after the cycle-8 inventory CEM driver was
killed mid-rerank.

The driver wrote `inventory_warmstart_cem_history.json` through gen 11
(complete) but did not get to write `inventory_warmstart_cem_test.json`
because the python process was reaped between cycles. This recovery
script:

1. Loads `history.json`, recovers the per-gen top-1 candidates' params
   (those are the gen-best params on the search seeds — a good
   approximation of the elites the driver would have re-ranked).
2. De-dupes and keeps the top-8 by search score.
3. Re-evaluates each on the val seeds, picks val-best.
4. Scores val-best on the held-out test seeds.
5. Writes `inventory_warmstart_cem_test.json` in the same shape as
   cycle-7's test json so downstream figure code Just Works.
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
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle8-inventory-piecewise/results"
HISTORY = OUTDIR / "inventory_warmstart_cem_history.json"
FAMILY = "inventory_aware_piecewise"

# These match the cycle-8 driver constants (search/val/test seed split).
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
INHERITED_BASELINE_TEST_SCORE = 432.747768827535


def _evaluate_one_serial(family: str, params_dict: dict, seeds) -> dict:
    spec = POLICY_SPECS[family]
    params = spec.params_cls(**params_dict).normalized()
    batch = run_batch(
        lambda: spec.strategy_cls(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "n_seeds": len(seeds),
    }


def main() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Loading history…")
    h = json.loads(HISTORY.read_text())
    history = h["history"]
    rng_seed = h.get("rng_seed", 0)
    init_std_frac = h.get("init_std_frac", 0.10)

    # Each gen has best_search_params + best_search_score. Take those as
    # candidate elites. (We don't have the full elite_n=4 list per gen, but
    # the per-gen top-1 across 12 gens gives 12 candidates which after
    # dedup is enough for top-8.)
    candidates: list[dict] = []
    for g in history:
        candidates.append({
            "score": float(g["best_search_score"]),
            "params": dict(g["best_search_params"]),
            "generation": int(g["generation"]),
        })
    candidates.sort(key=lambda c: c["score"], reverse=True)

    names = list(candidates[0]["params"].keys())
    seen: set[tuple[float, ...]] = set()
    unique: list[dict] = []
    for c in candidates:
        key = tuple(c["params"][n] for n in names)
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
        if len(unique) >= 8:
            break

    print(f"[{time.strftime('%H:%M:%S')}] Reranking top-{len(unique)} on {len(VAL_SEEDS)} val seeds…")
    rerank: list[dict] = []
    t_rr = time.time()
    for c in unique:
        val = _evaluate_one_serial(FAMILY, c["params"], VAL_SEEDS)
        rerank.append({
            "params": c["params"],
            "search_score": c["score"],
            "search_score_gen": c["generation"],
            "val_score": val["score"],
            "val_edge_advantage": val["edge_advantage_mean"],
        })
        print(
            f"  gen {c['generation']:2d}: search={c['score']:7.3f} -> "
            f"val={val['score']:7.3f}"
        )
    rerank.sort(key=lambda r: r["val_score"], reverse=True)
    print(f"  rerank done in {time.time() - t_rr:.1f}s")

    best = rerank[0]
    print(f"[{time.strftime('%H:%M:%S')}] Scoring val-best on {len(TEST_SEEDS)} test seeds…")
    t_t = time.time()
    test = _evaluate_one_serial(FAMILY, best["params"], TEST_SEEDS)
    test_elapsed = time.time() - t_t
    delta = test["score"] - INHERITED_BASELINE_TEST_SCORE

    print(
        f"  Best-by-val | val={best['val_score']:.3f} | test={test['score']:.3f} | "
        f"adv={test['edge_advantage_mean']:+.3f} ({test_elapsed:.1f}s)"
    )
    print(f"  Δ vs cycle-6 piecewise best: {delta:+.3f}")

    final = {
        "policy_family": FAMILY,
        "init_strategy": "warm_start_piecewise_plus_zero_inv",
        "init_std_frac": init_std_frac,
        "rng_seed": rng_seed,
        "rerank_source": "recovered_from_history_top1_per_gen",
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
        },
        "starting_line_test_score": INHERITED_BASELINE_TEST_SCORE,
        "delta_vs_starting_line": delta,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / "inventory_warmstart_cem_test.json").write_text(json.dumps(final, indent=2))
    print(f"  -> wrote {OUTDIR / 'inventory_warmstart_cem_test.json'}")


if __name__ == "__main__":
    main()
