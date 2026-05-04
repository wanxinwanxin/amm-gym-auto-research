"""
Cycle-12 M2 — capacity escalation: ladder-family CEM.

Hypothesis (from cycle-11 STATE.md):

  The 16-d piecewise basin under the cycle-8 anchor + (pop=24, gen=12)
  recipe ceilings out near 457 on held-out test. We've now run 7 cells
  and the spread is roughly 449-457. Going-in question for cycle 12:

  *Can a richer policy family — the ladder family with state EMAs
  (flow / opportunity / fair-price / toxicity / competition /
  inventory) — break that ceiling?*

The ladder family lives in arena_policies/latent_ladder.py. Its rungs
are progressively richer:
    LatentFlowStrategy            8 params
    LatentFairStrategy           11 params  (+fair-price tracking)
    LatentToxicityStrategy       14 params  (+toxicity decay)
    LatentCompetitionStrategy    16 params  (+competitor-fee tracking)
    LatentFullStrategy           18 params  (+inventory)

Cycle 12 runs CEM from-default on `latent_full` — the richest rung.
Rationale: if even the full 18-d ladder can't beat the 456.80
piecewise ceiling under the same pop/gen recipe, the ladder family is
not the bottleneck (and we should pivot to fresh-anchor / longer-run
CEM, or different reward shaping, in cycle 13). If it beats, we ablate
which sub-feature drives the lift.

Parameter spaces don't overlap between piecewise and latent_full, so
"warm-start from d16_s2 best" can't be literal. Instead we start CEM
at the LatentFullParams default mean with init_std = 0.25 × range
(wider than the 0.10 used for piecewise warm-starts, because we're
starting from hand-chosen defaults rather than a refined anchor —
need broader exploration). The bar to beat is held-out test = 456.80.

Recipe:
    - population: 24
    - generations: 12
    - elite_fraction: 0.2 (elite_n = 4)
    - init_std: 0.25 × (high − low) per dimension
    - rng_seed: 0
    - search seeds: range(0, 64)
    - per-gen val seeds: range(1000, 1128)
    - held-out test seeds: range(2000, 2256)
    - 3 workers (3 of 4 cores)
    - normalizer: FixedFee(0.003, 0.003), evaluator: "challenge"
    - rerank: top-8 unique elites on val, take val-best, score on test

Outputs:
    research/experiments/2026-05-04-cycle12-latent-ladder-cem/results/
        latent_full_progress.log     # streaming per-gen log
        latent_full_history.json     # per-gen best/elite/val
        latent_full_test.json        # final val/test/rerank
"""

from __future__ import annotations

import argparse
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
from arena_search.simple_amm_search import (  # noqa: E402
    LATENT_COMPETITION_PARAM_RANGES,
    LATENT_FAIR_PARAM_RANGES,
    LATENT_FLOW_PARAM_RANGES,
    LATENT_FULL_PARAM_RANGES,
    LATENT_TOXICITY_PARAM_RANGES,
    POLICY_SPECS,
)


HERE = Path(__file__).resolve().parent
OUTDIR = HERE.parent / "results"
OUTDIR.mkdir(parents=True, exist_ok=True)


# Bar to beat: the cycle-11 d16_s2 piecewise held-out test score.
PIECEWISE_BAR_TEST_SCORE = 456.803  # cycle 11 d16_s2 best_by_val
PIECEWISE_PRIOR_TEST_SCORE = 414.010  # cycle 5 starting line

LADDER_RANGES = {
    "latent_flow": LATENT_FLOW_PARAM_RANGES,
    "latent_fair": LATENT_FAIR_PARAM_RANGES,
    "latent_toxicity": LATENT_TOXICITY_PARAM_RANGES,
    "latent_competition": LATENT_COMPETITION_PARAM_RANGES,
    "latent_full": LATENT_FULL_PARAM_RANGES,
}


SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
GENERATIONS = 12
ELITE_FRAC = 0.2
INIT_STD_FRAC = 0.25  # wider — we start from defaults, not a refined anchor
MAX_WORKERS = max(1, min(3, (os.cpu_count() or 1) - 1))


def _bounds(ranges: dict[str, tuple[float, float]], names: list[str]):
    lows = np.asarray([ranges[n][0] for n in names], dtype=float)
    highs = np.asarray([ranges[n][1] for n in names], dtype=float)
    return lows, highs


def _default_params_dict(family: str) -> dict[str, float]:
    """Use the dataclass's hand-chosen defaults as the CEM start."""
    spec = POLICY_SPECS[family]
    default = spec.params_cls()  # all-defaults instance
    return default.normalized().to_dict()


def _init_mean_std(family: str, init_std_frac: float):
    ranges = LADDER_RANGES[family]
    names = list(ranges.keys())
    lows, highs = _bounds(ranges, names)
    defaults = _default_params_dict(family)
    init_mean = np.asarray([defaults[n] for n in names], dtype=float)
    init_mean = np.clip(init_mean, lows, highs)
    init_std = init_std_frac * (highs - lows)
    return names, lows, highs, init_mean, init_std


def _evaluate_one_candidate(payload: dict) -> dict:
    """Worker process: score one candidate on the search seeds."""
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
    logfile = OUTDIR / f"{family}_progress.log"
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
        f"Cycle-12 ladder CEM | family={family} pop={POPULATION} gen={generations} "
        f"elite_n={elite_n} init_std_frac={INIT_STD_FRAC} workers={MAX_WORKERS} "
        f"rng_seed={rng_seed}"
    )
    log(f"Search seeds: {SEARCH_SEEDS[0]}..{SEARCH_SEEDS[-1]} (n={len(SEARCH_SEEDS)})")
    log(f"Val seeds:    {VAL_SEEDS[0]}..{VAL_SEEDS[-1]} (n={len(VAL_SEEDS)})")
    log(f"Test seeds:   {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})")
    log(f"Anchor: defaults (param dim = {len(names)}); std = {INIT_STD_FRAC} × range")
    log(f"Bar to beat: piecewise d16_s2 cycle-11 = {PIECEWISE_BAR_TEST_SCORE:.3f}")

    # Confirm the default mean's score on val seeds first as a sanity check.
    sanity_t0 = time.time()
    sanity = _evaluate_one_serial(family, dict(zip(names, mean.tolist(), strict=True)), VAL_SEEDS)
    log(
        f"Sanity (default mean on val): score={sanity['score']:.3f} "
        f"adv={sanity['edge_advantage_mean']:+.3f} ({time.time()-sanity_t0:.1f}s)"
    )

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

        (OUTDIR / f"{family}_history.json").write_text(
            json.dumps(
                {
                    "policy_family": family,
                    "init_strategy": "defaults_wide_init_std",
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

    # Final test eval: rerank top-8 unique elites on val, take val-best,
    # score on held-out test seeds.
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

    delta_vs_piecewise = test["score"] - PIECEWISE_BAR_TEST_SCORE
    log(
        f"  Best-by-val | val_score={best['val_score']:.3f} | "
        f"test_score={test['score']:.3f} | adv={test['edge_advantage_mean']:+.3f}  "
        f"({test_elapsed:.1f}s) | piecewise bar={PIECEWISE_BAR_TEST_SCORE:.3f} "
        f"| Δ_vs_piecewise={delta_vs_piecewise:+.3f}"
    )

    final = {
        "policy_family": family,
        "init_strategy": "defaults_wide_init_std",
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
        "piecewise_bar_test_score": PIECEWISE_BAR_TEST_SCORE,
        "piecewise_prior_test_score": PIECEWISE_PRIOR_TEST_SCORE,
        "delta_vs_piecewise_bar": delta_vs_piecewise,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / f"{family}_test.json").write_text(json.dumps(final, indent=2))
    log(f"  -> wrote {OUTDIR / f'{family}_test.json'}")
    log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--family",
        choices=tuple(LADDER_RANGES.keys()),
        required=True,
    )
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--generations", type=int, default=GENERATIONS)
    args = parser.parse_args()
    main(args.family, args.rng_seed, args.generations)
