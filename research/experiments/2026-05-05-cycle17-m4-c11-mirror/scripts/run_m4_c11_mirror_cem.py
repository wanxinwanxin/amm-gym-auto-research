"""
M4 cycle-1 — mirror experiment: direct CEM on real_data warm-started
from c11_d16_s2 instead of c5.

Question.
  Cycle 16 ran a 5-gen × 12-pop CEM directly on the real_data evaluator,
  warm-started from c5, and lifted from −1.214 → +0.739 lift_FF on test.
  c11_d16_s2 (the M2 deliverable) measures +2.10 lift_FF on the same
  test seeds (cycle-15). We don't know whether c11+CEM saturates near
  +2.10 (piecewise-family real_data ceiling) or lifts past it (the
  warm-start prior is what dominates and the policy class still has
  room).

  Decision rule:
    - if c11+CEM > +2.20 lift_FF → "warm-start prior dominates"
    - if c11+CEM ∈ [+2.00, +2.20] → c11 is a piecewise-family real_data
      ceiling; M4 needs richer family or retail-aware loss.
    - if c11+CEM < +2.00 → CEM on real_data is regressing c11; the
      real_data evaluator is actively misleading the optimizer.

Method.
  Identical to cycle-16 m4_baseline EXCEPT init mean = c11_d16_s2 best-
  by-val params (16-d piecewise, no noop tail). Same population (12),
  same generations (5), same elite_frac (0.2), same init_std_frac
  (0.10), same search/val/test seed splits, same normalizer FixedFee
  (0.003, 0.003), same rng_seed (0), same workers (cpu-1).
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
    / "research/experiments/2026-05-05-cycle17-m4-c11-mirror/results/m4_c11_mirror"
)
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = OUTDIR / "progress.log"

# c11_d16_s2 anchor (cycle-11 grid CEM, M2 deliverable best-by-val).
C11_PIECEWISE_PARAMS = {
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

# Knobs (mirror cycle-16 exactly).
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
    init_mean = np.asarray([C11_PIECEWISE_PARAMS[n] for n in names], dtype=float)
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
        f"M4 c11 mirror CEM | piecewise on {EVALUATOR_KIND} | pop={POPULATION} "
        f"gen={GENERATIONS} elite_n={elite_n} init_std_frac={INIT_STD_FRAC} "
        f"workers={MAX_WORKERS}"
    )

    # Measure c11 baseline on val + test up front so we know exactly where
    # we start from.
    c11_params = PiecewiseControllerParams(**C11_PIECEWISE_PARAMS).normalized()
    t0 = time.time()
    c11_val = _evaluate_one_serial(c11_params, VAL_SEEDS, EVALUATOR_KIND)
    _log(
        f"  c11 val ({EVALUATOR_KIND}, n={len(VAL_SEEDS)}): score={c11_val['score']:7.3f} "
        f"adv={c11_val['edge_advantage_mean']:+7.3f} retail_adv={c11_val['retail_edge_advantage_mean']:+7.3f} "
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
                    "init_strategy": "c11_d16_s2_warm_start",
                    "init_std_frac": INIT_STD_FRAC,
                    "population_size": POPULATION,
                    "elite_fraction": ELITE_FRAC,
                    "search_seeds": list(SEARCH_SEEDS),
                    "val_seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
                    "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                    "rng_seed": RNG_SEED,
                    "c11_val_score": c11_val["score"],
                    "c11_val_edge_advantage": c11_val["edge_advantage_mean"],
                    "c11_val_retail_advantage": c11_val["retail_edge_advantage_mean"],
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
    # ALSO include the c11 anchor itself in the rerank pool — if no
    # candidate beats c11 on val, best-by-val is trivially c11 (no
    # regression).
    unique_elites: list[dict] = []
    seen: set[tuple[float, ...]] = set()
    # Inject c11 anchor as the first candidate.
    anchor_record = {
        "params": C11_PIECEWISE_PARAMS,
        "score": c11_val["score"],  # placeholder; real search_score not relevant
    }
    unique_elites.append(anchor_record)
    seen.add(tuple(C11_PIECEWISE_PARAMS[n] for n in names))
    for elite in sorted(all_elites, key=lambda r: r["score"], reverse=True):
        key = tuple(elite["params"][n] for n in names)
        if key in seen:
            continue
        seen.add(key)
        unique_elites.append(elite)
        if len(unique_elites) >= 7:  # 1 anchor + 6 elites
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
        "init_strategy": "c11_d16_s2_warm_start",
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
        "c11_val_score": c11_val["score"],
        "c11_val_edge_advantage": c11_val["edge_advantage_mean"],
        "c11_val_retail_advantage": c11_val["retail_edge_advantage_mean"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / "test.json").write_text(json.dumps(final, indent=2))
    _log(f"  -> wrote {OUTDIR / 'test.json'}")
    _log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    main()
