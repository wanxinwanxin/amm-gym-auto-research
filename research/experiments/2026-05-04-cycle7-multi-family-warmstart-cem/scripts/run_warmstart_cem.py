"""
Cycle-7 M2 — multi-family warm-start CEM driver.

Goal: test the hypothesis that the +18.7 pt warm-start CEM lift seen
on `piecewise` in cycle 6 is family-agnostic, i.e. the inherited
14×22 CEM runs across policy families were all under-converged and
local refinement at the inherited best should yield similar lifts on
`submission_compact` and `submission_basis`.

This script generalises cycle 6's `run_warmstart_cem.py` to take a
`--family` flag selecting one of:

    piecewise         (cycle 6 reproduces this with --rng-seed 0)
    submission_compact
    submission_basis

For each family we use the inherited best-by-validation params from
`experiments/<family>_cem_1h_20260423_rebatch1.json` (or the cycle-5
piecewise pin) as the warm-start anchor, an init_std of 0.10×range,
population 24, generations 12, ProcessPoolExecutor with 3 workers.

Outputs (per family):
  research/experiments/2026-05-04-cycle7-multi-family-warmstart-cem/
      results/warmstart_cem_<family>_history.json
      results/warmstart_cem_<family>_test.json
      results/warmstart_cem_<family>_progress.log
"""

from __future__ import annotations

import argparse
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
from arena_search.simple_amm_search import (  # noqa: E402
    PIECEWISE_CONTROLLER_PARAM_RANGES,
    POLICY_SPECS,
    SUBMISSION_BASIS_PARAM_RANGES,
    SUBMISSION_COMPACT_PARAM_RANGES,
)


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle7-multi-family-warmstart-cem/results"
OUTDIR.mkdir(parents=True, exist_ok=True)


# Inherited piecewise warm-start anchor (best-by-validation from
# `experiments/piecewise_cem_1h_20260422.json`, replicated in cycle 6).
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

# Hand-replicated baselines (cycle-5 measured; cycle-6 confirmed the
# piecewise number). Used as the "starting line" reference in the
# delta computation in the test json.
INHERITED_BASELINE_TEST_SCORE = {
    "piecewise": 414.010,
    "submission_compact": 410.776,
    "submission_basis": 380.262,
}


SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
GENERATIONS = 12
ELITE_FRAC = 0.2
INIT_STD_FRAC = 0.10
MAX_WORKERS = max(1, min(3, (os.cpu_count() or 1) - 1))


def _ranges_for(family: str) -> dict[str, tuple[float, float]]:
    if family == "piecewise":
        return PIECEWISE_CONTROLLER_PARAM_RANGES
    if family == "submission_compact":
        return SUBMISSION_COMPACT_PARAM_RANGES
    if family == "submission_basis":
        return SUBMISSION_BASIS_PARAM_RANGES
    raise ValueError(f"unknown family: {family}")


def _inherited_params(family: str) -> dict[str, float]:
    if family == "piecewise":
        return dict(INHERITED_PIECEWISE_PARAMS)
    rebatch = ROOT / f"experiments/{family}_cem_1h_20260423_rebatch1.json"
    with rebatch.open() as f:
        d = json.load(f)
    return d["best_validation"]["params"]


def _bounds(ranges: dict[str, tuple[float, float]], names: list[str]):
    lows = np.asarray([ranges[n][0] for n in names], dtype=float)
    highs = np.asarray([ranges[n][1] for n in names], dtype=float)
    return lows, highs


def _init_mean_std(family: str, init_std_frac: float):
    ranges = _ranges_for(family)
    names = list(ranges.keys())
    lows, highs = _bounds(ranges, names)
    inh = _inherited_params(family)
    init_mean = np.asarray([inh[n] for n in names], dtype=float)
    init_mean = np.clip(init_mean, lows, highs)
    init_std = init_std_frac * (highs - lows)
    return names, lows, highs, init_mean, init_std


def _evaluate_one_candidate(payload: dict) -> dict:
    """Run a single candidate eval — runs in a worker process."""
    sys.path.insert(0, str(ROOT))
    from arena_eval.exact_simple_amm import (  # noqa: WPS433
        FixedFeeStrategy as _FF,
        run_batch as _rb,
    )
    from arena_search.simple_amm_search import POLICY_SPECS as _SPECS  # noqa: WPS433

    family = payload["family"]
    spec = _SPECS[family]
    params = spec.params_cls(**payload["params"]).normalized()
    seeds = tuple(payload["seeds"])
    normalizer_fee = payload.get("normalizer_fee", 0.003)

    batch = _rb(
        lambda: spec.strategy_cls(params),
        seeds,
        normalizer_strategy_factory=lambda: _FF(normalizer_fee, normalizer_fee),
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


def _evaluate_one_serial(family: str, params_dict: dict, seeds: tuple[int, ...]) -> dict:
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
        "edge_mean_submission": float(batch.edge_mean_submission),
        "edge_mean_normalizer": float(batch.edge_mean_normalizer),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "retail_edge_mean_submission": float(batch.retail_edge_mean_submission),
        "arb_loss_mean_submission": float(batch.arb_loss_mean_submission),
        "n_seeds": len(seeds),
    }


def _logger(family: str):
    logfile = OUTDIR / f"warmstart_cem_{family}_progress.log"
    # Truncate (rather than unlink) so we don't trip on sandbox filesystem
    # constraints that disallow deletion.
    with logfile.open("w") as _f:
        _f.write("")

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    return _log


def main(family: str, rng_seed: int, generations: int) -> None:
    log = _logger(family)
    rng = np.random.default_rng(rng_seed)
    names, lows, highs, mean, std = _init_mean_std(family, INIT_STD_FRAC)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))
    spec = POLICY_SPECS[family]

    log(
        f"Cycle-7 warm-start CEM | family={family} pop={POPULATION} gen={generations} "
        f"elite_n={elite_n} init_std_frac={INIT_STD_FRAC} workers={MAX_WORKERS} "
        f"rng_seed={rng_seed}"
    )
    log(f"Search seeds: {SEARCH_SEEDS[0]}..{SEARCH_SEEDS[-1]} (n={len(SEARCH_SEEDS)})")
    log(f"Val seeds:    {VAL_SEEDS[0]}..{VAL_SEEDS[-1]} (n={len(VAL_SEEDS)})")
    log(f"Test seeds:   {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})")
    log(f"Anchor params dim={len(names)} (warm-start mean = inherited best-by-val)")

    all_elites: list[dict] = []
    history: list[dict] = []
    t_run = time.time()

    for gen in range(generations):
        candidate_vectors = [mean.copy()]
        for _ in range(POPULATION - 1):
            v = rng.normal(mean, std)
            v = np.clip(v, lows, highs)
            candidate_vectors.append(v)

        payloads = [
            {
                "candidate_id": i,
                "family": family,
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

        elite_matrix = np.asarray(
            [[r["params"][n] for n in names] for r in elites], dtype=float
        )
        new_mean = elite_matrix.mean(axis=0)
        new_std = np.maximum(elite_matrix.std(axis=0, ddof=0), 1e-4)

        # Per-gen val on best-of-search.
        val_t0 = time.time()
        val = _evaluate_one_serial(family, results[0]["params"], VAL_SEEDS)
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

        log(
            f"  gen {gen:2d}: best_search={results[0]['score']:7.3f} "
            f"elite_mean={gen_record['elite_mean_search_score']:7.3f} "
            f"median={gen_record['median_search_score']:7.3f} "
            f"fixed_val={val['score']:7.3f} adv={val['edge_advantage_mean']:+7.3f} "
            f"({gen_elapsed:5.1f}s search + {val_elapsed:4.1f}s val)"
        )

        (OUTDIR / f"warmstart_cem_{family}_history.json").write_text(
            json.dumps(
                {
                    "policy_family": family,
                    "init_strategy": "warm_start_inherited",
                    "init_std_frac": INIT_STD_FRAC,
                    "population_size": POPULATION,
                    "elite_fraction": ELITE_FRAC,
                    "search_seeds": list(SEARCH_SEEDS),
                    "val_seeds": list(VAL_SEEDS),
                    "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                    "rng_seed": rng_seed,
                    "history": history,
                },
                indent=2,
            )
        )

        mean = new_mean
        std = new_std

    total_elapsed = time.time() - t_run
    log(f"CEM complete in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Final test eval: rerank top-8 unique elites on val, take the
    # val-best, score it on held-out test seeds.
    log(
        f"Reranking top-8 unique elites on {len(VAL_SEEDS)} val seeds, "
        f"then scoring val-best on {len(TEST_SEEDS)} test seeds…"
    )

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
        val = _evaluate_one_serial(family, elite["params"], VAL_SEEDS)
        rerank.append({
            "params": elite["params"],
            "search_score": elite["score"],
            "val_score": val["score"],
            "val_edge_advantage": val["edge_advantage_mean"],
        })
    rerank.sort(key=lambda r: r["val_score"], reverse=True)

    best = rerank[0]
    t_test = time.time()
    test = _evaluate_one_serial(family, best["params"], TEST_SEEDS)
    test_elapsed = time.time() - t_test

    starting_line = INHERITED_BASELINE_TEST_SCORE.get(family, float("nan"))
    log(
        f"  Best-by-val | val_score={best['val_score']:.3f} | "
        f"test_score={test['score']:.3f} | adv={test['edge_advantage_mean']:+.3f}  "
        f"({test_elapsed:.1f}s) | starting_line={starting_line:.3f}"
    )
    delta = test["score"] - starting_line if starting_line == starting_line else float("nan")
    log(f"  Δ vs starting line: {delta:+.3f}")

    final = {
        "policy_family": family,
        "init_strategy": "warm_start_inherited",
        "init_std_frac": INIT_STD_FRAC,
        "rng_seed": rng_seed,
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
        },
        "starting_line_test_score": starting_line,
        "delta_vs_starting_line": delta,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / f"warmstart_cem_{family}_test.json").write_text(json.dumps(final, indent=2))
    log(f"  -> wrote {OUTDIR / f'warmstart_cem_{family}_test.json'}")
    log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--family",
        choices=("piecewise", "submission_compact", "submission_basis"),
        required=True,
    )
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--generations", type=int, default=GENERATIONS)
    args = parser.parse_args()
    main(args.family, args.rng_seed, args.generations)
