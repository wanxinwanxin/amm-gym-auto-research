"""
Cycle-14: complete the cycle-13 long-run rerank step.

The cycle-13 long-run CEM (gen=24) finished all 24 generations
(history.json has 24 records) but the post-CEM rerank/test step
got killed before result.json was written. This script reuses
the per-gen elites recorded in history.json (best_search_params
of each gen + the explicit elite stats in the matching scripts;
since history.json only records best_search_params per gen, we
take the union of gen-best params as the rerank pool — this is
slightly less rich than the original "top-8 across all gens" but
still valid because per-gen best is by definition an elite, and
the elite cluster narrows fast).

Output:
  results/longrun_d16_s0_g24/result.json
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

EVAL_FAMILY = "piecewise"
PIECEWISE_DIM = 16
CHAMPION_TEST_SCORE = 456.8032181567959
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))

OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/longrun_d16_s0_g24"
)


def _evaluate(family: str, params_dict: dict, seeds) -> dict:
    spec = POLICY_SPECS[family]
    pw_only = {k: v for k, v in params_dict.items() if not k.startswith("noop_")}
    params = spec.params_cls(**pw_only).normalized()
    batch = run_batch(
        lambda: spec.strategy_cls(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
    }


def main() -> None:
    hist_path = OUTDIR / "history.json"
    with hist_path.open() as f:
        hist = json.load(f)

    # Build a candidate pool from per-gen bests; dedupe by rounded params.
    names = list(hist["history"][0]["best_search_params"].keys())
    pool: list[dict] = []
    seen: set[tuple[float, ...]] = set()
    # gens sorted by their best_search_score, descending.
    gens_sorted = sorted(
        hist["history"], key=lambda g: g["best_search_score"], reverse=True
    )
    for g in gens_sorted:
        params = g["best_search_params"]
        key = tuple(round(params[n], 12) for n in names)
        if key in seen:
            continue
        seen.add(key)
        pool.append(
            {
                "generation": g["generation"],
                "search_score": g["best_search_score"],
                "params": params,
            }
        )
        if len(pool) >= 8:
            break

    print(
        f"[{time.strftime('%H:%M:%S')}] reranking {len(pool)} unique gen-best elites on "
        f"{len(VAL_SEEDS)} val seeds…",
        flush=True,
    )
    rerank: list[dict] = []
    for entry in pool:
        t0 = time.time()
        v = _evaluate(EVAL_FAMILY, entry["params"], VAL_SEEDS)
        elapsed = time.time() - t0
        print(
            f"  gen {entry['generation']:2d} | search={entry['search_score']:.3f} "
            f"| val={v['score']:.3f} | adv={v['edge_advantage_mean']:+.3f} ({elapsed:.1f}s)",
            flush=True,
        )
        rerank.append(
            {
                "params": entry["params"],
                "search_score": entry["search_score"],
                "val_score": v["score"],
                "val_edge_advantage": v["edge_advantage_mean"],
                "from_generation": entry["generation"],
            }
        )

    rerank.sort(key=lambda r: r["val_score"], reverse=True)
    best = rerank[0]

    print(
        f"[{time.strftime('%H:%M:%S')}] best-by-val from gen {best['from_generation']} "
        f"(val={best['val_score']:.3f}); scoring on {len(TEST_SEEDS)} test seeds…",
        flush=True,
    )
    t0 = time.time()
    test = _evaluate(EVAL_FAMILY, best["params"], TEST_SEEDS)
    elapsed = time.time() - t0
    delta = test["score"] - CHAMPION_TEST_SCORE
    print(
        f"  test={test['score']:.3f} | adv={test['edge_advantage_mean']:+.3f} "
        f"({elapsed:.1f}s) | Δ champion={delta:+.3f}",
        flush=True,
    )

    final = {
        "policy_family": EVAL_FAMILY,
        "cell_label": "longrun_d16_s0_g24",
        "core_dim": PIECEWISE_DIM,
        "init_strategy": "warm_start_cycle11_d16_s2",
        "init_std_frac": 0.10,
        "rng_seed": 0,
        "generations": 24,
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
            "from_generation": best["from_generation"],
        },
        "champion_test_score": CHAMPION_TEST_SCORE,
        "delta_vs_champion": delta,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "rerank_pool": "per-gen-best (24 gens, 8 unique kept) — the "
        "in-driver rerank step never completed, so this is a fallback "
        "pool that's strictly weaker than the all-gens-elite pool the "
        "driver would have used.",
    }
    (OUTDIR / "result.json").write_text(json.dumps(final, indent=2))
    print(f"  -> wrote {OUTDIR / 'result.json'}", flush=True)


if __name__ == "__main__":
    main()
