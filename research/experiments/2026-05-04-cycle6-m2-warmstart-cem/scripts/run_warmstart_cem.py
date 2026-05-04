"""
Cycle-6 M2 — warm-start CEM on the piecewise policy.

Cycle 5 measured the M2 starting line at score = 414.010 (piecewise CEM
best, inherited from `experiments/piecewise_cem_1h_20260422.json`,
replicated on test seeds 2000:2256). The M2 target is >540 — a 126-point
gap.

Hypothesis (from cycle-5 STATE.md): the inherited 14-gen × 22-pop CEM
has not converged. Warm-starting CEM at the inherited best params with
a *narrow* initial std should let us do local refinement that the
random-init CEM can't reach in 14 generations.

What we run
-----------
1. **Warm-start CEM**: piecewise policy, mean = inherited best params,
   initial std = `init_std_frac * (high - low)` per dimension. We use
   `init_std_frac = 0.10` (smaller than the default 0.25 used in the
   library `cross_entropy_search`). Population = 24 (vs inherited 22),
   generations = 12, elite_fraction = 0.2 (matching inherited).
2. **Search seeds**: range(0, 64) — same as inherited search seeds.
3. **Per-iteration validation**: 128 fixed seeds (range(1000, 1128)),
   matching half the inherited validation set (saves time).
4. **Final test eval**: range(2000, 2256) — held-out, matching the
   inherited test split, so cycle-6 numbers are directly comparable to
   the cycle-5 starting line and the inherited 414.010.
5. **Parallelism**: candidate evaluations within a generation are run
   across a `ProcessPoolExecutor` of `max_workers` workers (defaults to
   `os.cpu_count()`). Each worker independently evaluates one
   candidate's run_batch over the search seeds.

Outputs
-------
research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/
    warmstart_cem_history.json   # per-generation best/elites
    warmstart_cem_test.json      # held-out test score for the final
                                 # best-validation params, plus the
                                 # rerank ladder of top-k.
    warmstart_cem_progress.log   # streaming per-gen log
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_policies import PiecewiseControllerParams, PiecewiseControllerStrategy  # noqa: E402
from arena_search.simple_amm_search import (  # noqa: E402
    PIECEWISE_CONTROLLER_PARAM_RANGES,
)


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results"
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = OUTDIR / "warmstart_cem_progress.log"

INHERITED_PIECEWISE_PARAMS = {
    "base_fee": 0.0031761646289962934,
    "base_spread": 0.005382800828473529,
    "continuation_large": 0.016965089244693893,
    "continuation_medium": 0.010683567139589125,
    "continuation_small": 0.0007418160153062712,
    "continuation_to_cross_side": 0.6711100624350796,
    "continuation_to_same_side": 0.46227649502613805,
    "large_trade_threshold": 0.017331678478343653,
    "reversal_large": 0.06114156688492659,
    "reversal_medium": 0.023791373551436422,
    "reversal_small": 0.018651454393049955,
    "signal_decay": 0.46913194556337184,
    "small_trade_threshold": 0.004567928620937654,
    "toxicity_decay": 0.5132485563405016,
    "toxicity_to_mid": 0.008964552728672,
    "toxicity_to_side": 0.0438333038385567,
}

# Knobs.
SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
GENERATIONS = 12
ELITE_FRAC = 0.2
INIT_STD_FRAC = 0.10
RNG_SEED = 0
MAX_WORKERS = max(1, (os.cpu_count() or 1) - 1)


def _names() -> list[str]:
    return list(PIECEWISE_CONTROLLER_PARAM_RANGES.keys())


def _bounds() -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows = np.asarray([PIECEWISE_CONTROLLER_PARAM_RANGES[n][0] for n in names], dtype=float)
    highs = np.asarray([PIECEWISE_CONTROLLER_PARAM_RANGES[n][1] for n in names], dtype=float)
    return lows, highs


def _initial_mean_std(init_std_frac: float) -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows, highs = _bounds()
    init_mean = np.asarray(
        [INHERITED_PIECEWISE_PARAMS[n] for n in names], dtype=float
    )
    init_mean = np.clip(init_mean, lows, highs)
    init_std = init_std_frac * (highs - lows)
    return init_mean, init_std


def _params_from_vector(vector: np.ndarray) -> PiecewiseControllerParams:
    names = _names()
    return PiecewiseControllerParams(**dict(zip(names, vector.tolist(), strict=True))).normalized()


def _vector_from_params(params: PiecewiseControllerParams) -> np.ndarray:
    names = _names()
    d = params.to_dict()
    return np.asarray([d[n] for n in names], dtype=float)


def _evaluate_one_candidate(payload: dict) -> dict:
    """Run a single candidate eval — runs in a worker process."""
    sys.path.insert(0, str(ROOT))
    from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: WPS433
    from arena_policies import PiecewiseControllerParams, PiecewiseControllerStrategy  # noqa: WPS433

    params = PiecewiseControllerParams(**payload["params"]).normalized()
    seeds = tuple(payload["seeds"])
    normalizer_fee = payload.get("normalizer_fee", 0.003)

    batch = run_batch(
        lambda: PiecewiseControllerStrategy(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(normalizer_fee, normalizer_fee),
        evaluator_kind="challenge",
    )
    return {
        "candidate_id": payload["candidate_id"],
        "params": payload["params"],
        "score": float(batch.score),
        "edge_mean_submission": float(batch.edge_mean_submission),
        "edge_mean_normalizer": float(batch.edge_mean_normalizer),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "retail_edge_mean_submission": float(batch.retail_edge_mean_submission),
        "arb_loss_mean_submission": float(batch.arb_loss_mean_submission),
    }


def _evaluate_one_serial(params: PiecewiseControllerParams, seeds: tuple[int, ...]) -> dict:
    batch = run_batch(
        lambda: PiecewiseControllerStrategy(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return {
        "score": float(batch.score),
        "edge_mean_submission": float(batch.edge_mean_submission),
        "edge_mean_normalizer": float(batch.edge_mean_normalizer),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "retail_edge_mean_submission": float(batch.retail_edge_mean_submission),
        "arb_loss_mean_submission": float(batch.arb_loss_mean_submission),
        "n_seeds": len(seeds),
    }


def _log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOGFILE.open("a") as f:
        f.write(line + "\n")


def main() -> None:
    LOGFILE.unlink(missing_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    names = _names()
    lows, highs = _bounds()
    mean, std = _initial_mean_std(INIT_STD_FRAC)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    _log(
        f"Cycle-6 warm-start CEM | piecewise | pop={POPULATION} gen={GENERATIONS} "
        f"elite_n={elite_n} init_std_frac={INIT_STD_FRAC} workers={MAX_WORKERS}"
    )
    _log(f"Search seeds: {SEARCH_SEEDS[0]}..{SEARCH_SEEDS[-1]} (n={len(SEARCH_SEEDS)})")
    _log(f"Val seeds:    {VAL_SEEDS[0]}..{VAL_SEEDS[-1]} (n={len(VAL_SEEDS)})")
    _log(f"Test seeds:   {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})")
    _log(
        f"Init mean (inherited best) — score on val seeds will be measured "
        f"in generation 0 alongside the warm-start population."
    )

    # Track all unique elites across generations for final reranking.
    all_elites: list[dict] = []

    # The first candidate of generation 0 is the inherited best itself, so
    # we can confirm replication and have a stable anchor.
    history: list[dict] = []

    t_run = time.time()

    for gen in range(GENERATIONS):
        # Sample population: first member is the current mean (the inherited
        # warm-start anchor in gen 0; the elite mean thereafter).
        candidate_vectors = [mean.copy()]
        for _ in range(POPULATION - 1):
            v = rng.normal(mean, std)
            v = np.clip(v, lows, highs)
            candidate_vectors.append(v)

        payloads = [
            {
                "candidate_id": i,
                "params": dict(zip(names, vec.tolist(), strict=True)),
                "seeds": list(SEARCH_SEEDS),
                "normalizer_fee": 0.003,
            }
            for i, vec in enumerate(candidate_vectors)
        ]

        gen_t0 = time.time()
        results: list[dict] = []
        if MAX_WORKERS > 1:
            with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
                for fut in as_completed(pool.submit(_evaluate_one_candidate, p) for p in payloads):
                    results.append(fut.result())
        else:
            for p in payloads:
                results.append(_evaluate_one_candidate(p))
        results.sort(key=lambda r: r["score"], reverse=True)
        gen_elapsed = time.time() - gen_t0

        elites = results[:elite_n]
        all_elites.extend(elites)

        # Update CEM moments from elites.
        elite_matrix = np.asarray(
            [[r["params"][n] for n in names] for r in elites], dtype=float
        )
        new_mean = elite_matrix.mean(axis=0)
        new_std = np.maximum(elite_matrix.std(axis=0, ddof=0), 1e-4)

        # Validate the best-of-generation candidate on the fixed val seeds.
        best_search_params = PiecewiseControllerParams(**results[0]["params"]).normalized()
        val_t0 = time.time()
        val = _evaluate_one_serial(best_search_params, VAL_SEEDS)
        val_elapsed = time.time() - val_t0

        gen_record = {
            "generation": gen,
            "elite_n": elite_n,
            "best_search_score": results[0]["score"],
            "median_search_score": float(np.median([r["score"] for r in results])),
            "elite_mean_search_score": float(np.mean([r["score"] for r in elites])),
            "fixed_val_score": val["score"],
            "fixed_val_edge_advantage": val["edge_advantage_mean"],
            "best_search_params": results[0]["params"],
            "mean_after": new_mean.tolist(),
            "std_after": new_std.tolist(),
            "gen_elapsed_s": gen_elapsed,
            "val_elapsed_s": val_elapsed,
        }
        history.append(gen_record)

        _log(
            f"  gen {gen:2d}: best_search={results[0]['score']:7.3f} "
            f"elite_mean={gen_record['elite_mean_search_score']:7.3f} "
            f"median={gen_record['median_search_score']:7.3f} "
            f"fixed_val={val['score']:7.3f} adv={val['edge_advantage_mean']:+7.3f} "
            f"({gen_elapsed:5.1f}s search + {val_elapsed:4.1f}s val)"
        )

        # Persist incrementally so a crash mid-run still leaves usable data.
        (OUTDIR / "warmstart_cem_history.json").write_text(
            json.dumps(
                {
                    "policy_family": "piecewise",
                    "init_strategy": "warm_start_inherited",
                    "init_std_frac": INIT_STD_FRAC,
                    "population_size": POPULATION,
                    "elite_fraction": ELITE_FRAC,
                    "search_seeds": list(SEARCH_SEEDS),
                    "val_seeds": list(VAL_SEEDS),
                    "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                    "rng_seed": RNG_SEED,
                    "history": history,
                },
                indent=2,
            )
        )

        mean = new_mean
        std = new_std

    total_elapsed = time.time() - t_run
    _log(f"CEM complete in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Final test eval: rerank top-k by fixed_val score, then take the best
    # by val and report its test score. Also report the test score of the
    # final-generation best-search candidate for diagnostics.
    _log(f"Reranking top elites on val seeds (already done per-gen) and "
         f"computing test score on {len(TEST_SEEDS)} seeds…")

    # Build the rerank ladder: take all unique elites across generations,
    # rerank them on the fixed val seeds (uses only top-k to keep cost
    # manageable; we already have val scores per generation but not for all
    # elites).
    unique_elites: list[dict] = []
    seen: set[tuple[float, ...]] = set()
    for elite in sorted(all_elites, key=lambda r: r["score"], reverse=True):
        key = tuple(elite["params"][n] for n in names)
        if key in seen:
            continue
        seen.add(key)
        unique_elites.append(elite)
        if len(unique_elites) >= 8:
            break

    rerank: list[dict] = []
    for elite in unique_elites:
        params = PiecewiseControllerParams(**elite["params"]).normalized()
        val = _evaluate_one_serial(params, VAL_SEEDS)
        rerank.append({
            "params": elite["params"],
            "search_score": elite["score"],
            "val_score": val["score"],
            "val_edge_advantage": val["edge_advantage_mean"],
        })
    rerank.sort(key=lambda r: r["val_score"], reverse=True)

    # Pick the val-best candidate and score it on held-out test seeds.
    best = rerank[0]
    best_params = PiecewiseControllerParams(**best["params"]).normalized()
    t_test = time.time()
    test = _evaluate_one_serial(best_params, TEST_SEEDS)
    test_elapsed = time.time() - t_test

    _log(
        f"  Best-by-val | val_score={best['val_score']:.3f} | "
        f"test_score={test['score']:.3f} | adv={test['edge_advantage_mean']:+.3f}  "
        f"({test_elapsed:.1f}s)"
    )

    final = {
        "policy_family": "piecewise",
        "init_strategy": "warm_start_inherited",
        "init_std_frac": INIT_STD_FRAC,
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
        },
        "starting_line_test_score": 414.010,
        "delta_vs_starting_line": test["score"] - 414.010,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / "warmstart_cem_test.json").write_text(json.dumps(final, indent=2))
    _log(f"  -> wrote {OUTDIR / 'warmstart_cem_test.json'}")
    _log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    main()
