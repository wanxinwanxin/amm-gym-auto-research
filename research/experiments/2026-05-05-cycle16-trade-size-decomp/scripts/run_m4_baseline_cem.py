"""
M4 cycle-0 baseline — direct CEM on real_data evaluator.

Question.
  Going into M4 we want to know two things:
    (a) Is the real_data evaluator CEM-friendly? I.e. is the per-batch
        score noisy enough that CEM can't track real gradients, or is it
        well-behaved like the challenge evaluator?
    (b) What does a small-budget direct optimization on real_data
        actually achieve, starting from the c5 anchor (-0.93 lift on
        real_data)? Does it close the gap to c11's +2.10 lift, surpass
        it, or plateau early?

Method.
  Warm-start CEM, init mean = c5 inherited piecewise params, init std
  = 0.10 × (high - low). Population 12, generations 5, elite_frac 0.2,
  search seeds 0..63 (64), val seeds 1000..1127 (128), test seeds
  2000..2255 (256). All evaluations on `evaluator_kind="real_data"`.
  Normalizer FixedFee(0.003, 0.003).

  Workers: ProcessPoolExecutor(max_workers=cpu_count-1). Cycle-6
  measured ~125-130 s/gen at pop=24 dim=16 with 3 workers on the
  challenge eval. real_data is the same compute so we expect ~60-65 s
  at pop=12, total ~5-6 min CEM + val eval per gen.

  This is intentionally a small-budget "is this approach viable"
  experiment, not a full M4 attempt. The goal is to plant a flag for
  M4 cycle 1.
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
from arena_search.simple_amm_search import (  # noqa: E402
    PIECEWISE_CONTROLLER_PARAM_RANGES,
)


OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results/m4_baseline"
)
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = OUTDIR / "progress.log"

# c5 anchor (same as cycle-6 inherited).
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
EVALUATOR_KIND = "real_data"
SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 12
GENERATIONS = 5
ELITE_FRAC = 0.2
INIT_STD_FRAC = 0.10
NORMALIZER_FEE = 0.003
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
    init_mean = np.asarray([INHERITED_PIECEWISE_PARAMS[n] for n in names], dtype=float)
    init_mean = np.clip(init_mean, lows, highs)
    init_std = init_std_frac * (highs - lows)
    return init_mean, init_std


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
        "edge_mean_submission": float(batch.edge_mean_submission),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "retail_edge_advantage_mean": float(batch.retail_edge_advantage_mean),
    }


def _evaluate_one_serial(params: PiecewiseControllerParams, seeds: tuple[int, ...], evaluator_kind: str) -> dict:
    batch = run_batch(
        lambda: PiecewiseControllerStrategy(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        evaluator_kind=evaluator_kind,
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "retail_edge_advantage_mean": float(batch.retail_edge_advantage_mean),
        "n_seeds": len(seeds),
    }


def _log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOGFILE.open("a") as f:
        f.write(line + "\n")


def main() -> None:
    # Truncate previous run's log without unlinking — sandbox blocks unlink
    # (see bin/checks/05_results_dir_unlink_blocked.py).
    LOGFILE.open("w").close()
    rng = np.random.default_rng(RNG_SEED)
    names = _names()
    lows, highs = _bounds()
    mean, std = _initial_mean_std(INIT_STD_FRAC)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    _log(
        f"M4 baseline CEM | piecewise on {EVALUATOR_KIND} | pop={POPULATION} "
        f"gen={GENERATIONS} elite_n={elite_n} init_std_frac={INIT_STD_FRAC} "
        f"workers={MAX_WORKERS}"
    )

    # Measure c5 baseline on val + test up front so we know exactly what we're
    # starting from (sanity / replication of cycle-15 c5 numbers).
    c5_params = PiecewiseControllerParams(**INHERITED_PIECEWISE_PARAMS).normalized()
    t0 = time.time()
    c5_val = _evaluate_one_serial(c5_params, VAL_SEEDS, EVALUATOR_KIND)
    _log(
        f"  c5 val ({EVALUATOR_KIND}, n={len(VAL_SEEDS)}): score={c5_val['score']:7.3f} "
        f"adv={c5_val['edge_advantage_mean']:+7.3f} retail_adv={c5_val['retail_edge_advantage_mean']:+7.3f} "
        f"({time.time()-t0:.1f}s)"
    )

    history: list[dict] = []
    all_elites: list[dict] = []
    t_run = time.time()

    for gen in range(GENERATIONS):
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
                "normalizer_fee": NORMALIZER_FEE,
                "evaluator_kind": EVALUATOR_KIND,
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
        elite_matrix = np.asarray(
            [[r["params"][n] for n in names] for r in elites], dtype=float
        )
        new_mean = elite_matrix.mean(axis=0)
        new_std = np.maximum(elite_matrix.std(axis=0, ddof=0), 1e-4)

        # Validate the best-of-generation candidate on the val seeds.
        best_search_params = PiecewiseControllerParams(**results[0]["params"]).normalized()
        val_t0 = time.time()
        val = _evaluate_one_serial(best_search_params, VAL_SEEDS, EVALUATOR_KIND)
        val_elapsed = time.time() - val_t0

        gen_record = {
            "generation": gen,
            "elite_n": elite_n,
            "best_search_score": results[0]["score"],
            "median_search_score": float(np.median([r["score"] for r in results])),
            "elite_mean_search_score": float(np.mean([r["score"] for r in elites])),
            "fixed_val_score": val["score"],
            "fixed_val_retail_adv": val["retail_edge_advantage_mean"],
            "fixed_val_edge_advantage": val["edge_advantage_mean"],
            "best_search_params": results[0]["params"],
            "mean_after": new_mean.tolist(),
            "std_after": new_std.tolist(),
            "gen_elapsed_s": gen_elapsed,
            "val_elapsed_s": val_elapsed,
        }
        history.append(gen_record)

        _log(
            f"  gen {gen:2d}: best_search={results[0]['score']:6.3f} "
            f"elite_mean={gen_record['elite_mean_search_score']:6.3f} "
            f"median={gen_record['median_search_score']:6.3f} "
            f"val={val['score']:6.3f} adv={val['edge_advantage_mean']:+6.3f} "
            f"retail_adv={val['retail_edge_advantage_mean']:+6.3f} "
            f"({gen_elapsed:5.1f}s + {val_elapsed:4.1f}s)"
        )

        # Persist incrementally.
        (OUTDIR / "history.json").write_text(
            json.dumps(
                {
                    "policy_family": "piecewise",
                    "evaluator_kind": EVALUATOR_KIND,
                    "init_strategy": "c5_warm_start",
                    "init_std_frac": INIT_STD_FRAC,
                    "population_size": POPULATION,
                    "elite_fraction": ELITE_FRAC,
                    "search_seeds": list(SEARCH_SEEDS),
                    "val_seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
                    "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                    "rng_seed": RNG_SEED,
                    "c5_val_score": c5_val["score"],
                    "c5_val_edge_advantage": c5_val["edge_advantage_mean"],
                    "c5_val_retail_advantage": c5_val["retail_edge_advantage_mean"],
                    "history": history,
                },
                indent=2,
            )
        )

        mean = new_mean
        std = new_std

    total_elapsed = time.time() - t_run
    _log(f"CEM complete in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Test eval: rerank top-k by val and take best-by-val on test seeds.
    unique_elites: list[dict] = []
    seen: set[tuple[float, ...]] = set()
    for elite in sorted(all_elites, key=lambda r: r["score"], reverse=True):
        key = tuple(elite["params"][n] for n in names)
        if key in seen:
            continue
        seen.add(key)
        unique_elites.append(elite)
        if len(unique_elites) >= 6:
            break

    rerank: list[dict] = []
    for elite in unique_elites:
        params = PiecewiseControllerParams(**elite["params"]).normalized()
        val = _evaluate_one_serial(params, VAL_SEEDS, EVALUATOR_KIND)
        rerank.append({
            "params": elite["params"],
            "search_score": elite["score"],
            "val_score": val["score"],
            "val_edge_advantage": val["edge_advantage_mean"],
            "val_retail_advantage": val["retail_edge_advantage_mean"],
        })
    rerank.sort(key=lambda r: r["val_score"], reverse=True)

    best = rerank[0]
    best_params = PiecewiseControllerParams(**best["params"]).normalized()
    t_test = time.time()
    test = _evaluate_one_serial(best_params, TEST_SEEDS, EVALUATOR_KIND)
    test_elapsed = time.time() - t_test

    # FixedFee on real_data for lift baseline.
    ff_t0 = time.time()
    ff_test = run_batch(
        lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        TEST_SEEDS,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        evaluator_kind=EVALUATOR_KIND,
    )
    ff_test_score = float(ff_test.score)
    _log(f"  FixedFee test ({EVALUATOR_KIND}): {ff_test_score:.3f} ({time.time()-ff_t0:.1f}s)")

    final = {
        "policy_family": "piecewise",
        "evaluator_kind": EVALUATOR_KIND,
        "init_strategy": "c5_warm_start",
        "init_std_frac": INIT_STD_FRAC,
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "val_retail_advantage": best["val_retail_advantage"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_retail_advantage": test["retail_edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
            "ff_test_score": ff_test_score,
            "lift_FF": test["score"] - ff_test_score,
        },
        "c5_val_score": c5_val["score"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / "test.json").write_text(json.dumps(final, indent=2))
    _log(f"  -> wrote {OUTDIR / 'test.json'}")
    _log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    main()
