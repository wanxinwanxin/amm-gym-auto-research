"""
Cycle-9 #1 — Third-pass warm-start CEM on bare piecewise.

Anchor = cycle-8 ablation best (16 piecewise dims; the inv-skew tail of
cycle-8's `inventory_aware_piecewise` best was zeroed and parity-matched
the same 446.6 score as the inventory-aware run on test seeds).

Hypothesis. Cycle 6 (gen ~12) lifted bare piecewise from 414 to 432.7;
cycle 8's "inventory-aware" CEM (which the ablation showed was really a
second pass of warm-start CEM on bare piecewise) lifted it from 432.7 to
446.6. Prior: ~50/50 a third pass adds another +3-7 pts before the basin
is truly converged.

Same recipe as cycles 6-8: pop=24, gen=12, init_std_frac=0.10,
elite_frac=0.20, search seeds 0..63, val 1000..1127, test 2000..2255.

Outputs:
  research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/
      third_pass_cem_history.json
      third_pass_cem_test.json
      third_pass_cem_progress.log
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
)


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results"
OUTDIR.mkdir(parents=True, exist_ok=True)

FAMILY = "piecewise"

# Cycle-8 ablation file holds the cycle-8 best; the `ablated_params`
# entry has inv-skew zeroed, leaving exactly the 16 piecewise params at
# the cycle-8 best. test_n=256 score = 446.6131784961775.
CYCLE8_ABLATION_JSON = (
    ROOT
    / "research/experiments/2026-05-04-cycle8-inventory-piecewise/results/inventory_ablation.json"
)
INHERITED_BASELINE_TEST_SCORE = 446.6131784961775

SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
GENERATIONS = 12
ELITE_FRAC = 0.2
INIT_STD_FRAC = 0.10
MAX_WORKERS = max(1, min(3, (os.cpu_count() or 1) - 1))


def _bounds(ranges, names):
    lows = np.asarray([ranges[n][0] for n in names], dtype=float)
    highs = np.asarray([ranges[n][1] for n in names], dtype=float)
    return lows, highs


def _inherited_anchor() -> dict[str, float]:
    """Cycle-8 best with inv-skew tail dropped — i.e. bare piecewise best."""
    with CYCLE8_ABLATION_JSON.open() as f:
        d = json.load(f)
    full = dict(d["ablated_params"])
    return {k: v for k, v in full.items() if not k.startswith("inventory_skew_")}


def _evaluate_one_candidate(payload: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from arena_eval.exact_simple_amm import (  # noqa: WPS433
        FixedFeeStrategy as _FF,
        run_batch as _rb,
    )
    from arena_search.simple_amm_search import POLICY_SPECS as _SPECS  # noqa: WPS433

    spec = _SPECS[payload["family"]]
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
        "edge_advantage_mean": float(batch.edge_advantage_mean),
    }


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


def _logger():
    logfile = OUTDIR / "third_pass_cem_progress.log"
    with logfile.open("w") as _f:
        _f.write("")

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    return _log


def main(rng_seed: int, generations: int) -> None:
    log = _logger()
    rng = np.random.default_rng(rng_seed)
    ranges = PIECEWISE_CONTROLLER_PARAM_RANGES
    names = list(ranges.keys())
    lows, highs = _bounds(ranges, names)
    inh = _inherited_anchor()
    init_mean = np.asarray([inh[n] for n in names], dtype=float)
    init_mean = np.clip(init_mean, lows, highs)
    init_std = INIT_STD_FRAC * (highs - lows)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    log(
        f"Cycle-9 third-pass piecewise warm-start CEM | dim={len(names)} "
        f"pop={POPULATION} gen={generations} elite_n={elite_n} "
        f"init_std_frac={INIT_STD_FRAC} workers={MAX_WORKERS} rng_seed={rng_seed}"
    )
    log(f"Anchor: {dict(zip(names, init_mean.tolist()))}")
    log(f"Search seeds: {SEARCH_SEEDS[0]}..{SEARCH_SEEDS[-1]} (n={len(SEARCH_SEEDS)})")
    log(f"Val seeds:    {VAL_SEEDS[0]}..{VAL_SEEDS[-1]} (n={len(VAL_SEEDS)})")
    log(f"Test seeds:   {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})")

    anchor_check = _evaluate_one_serial(FAMILY, dict(zip(names, init_mean.tolist())), SEARCH_SEEDS)
    log(f"Anchor search-seed score: {anchor_check['score']:.3f} (cycle-8 ablation == bare piecewise best)")

    all_elites: list[dict] = []
    history: list[dict] = []
    mean = init_mean.copy()
    std = init_std.copy()
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
                "family": FAMILY,
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

        val_t0 = time.time()
        val = _evaluate_one_serial(FAMILY, results[0]["params"], VAL_SEEDS)
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
            f"  gen {gen:2d}: best={results[0]['score']:7.3f} "
            f"elite_mean={gen_record['elite_mean_search_score']:7.3f} "
            f"val={val['score']:7.3f} ({gen_elapsed:5.1f}s+{val_elapsed:4.1f}s)"
        )

        (OUTDIR / "third_pass_cem_history.json").write_text(
            json.dumps(
                {
                    "policy_family": FAMILY,
                    "init_strategy": "warm_start_from_cycle8_ablation",
                    "init_std_frac": INIT_STD_FRAC,
                    "population_size": POPULATION,
                    "elite_fraction": ELITE_FRAC,
                    "search_seeds": list(SEARCH_SEEDS),
                    "val_seeds": list(VAL_SEEDS),
                    "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                    "rng_seed": rng_seed,
                    "anchor_search_score": anchor_check["score"],
                    "anchor_params": dict(zip(names, init_mean.tolist())),
                    "history": history,
                },
                indent=2,
            )
        )

        mean = new_mean
        std = new_std

    total_elapsed = time.time() - t_run
    log(f"CEM complete in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    log("Reranking top-8 unique elites on val seeds, then scoring val-best on test…")
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
        val = _evaluate_one_serial(FAMILY, elite["params"], VAL_SEEDS)
        rerank.append({
            "params": elite["params"],
            "search_score": elite["score"],
            "val_score": val["score"],
            "val_edge_advantage": val["edge_advantage_mean"],
        })
    rerank.sort(key=lambda r: r["val_score"], reverse=True)

    best = rerank[0]
    t_test = time.time()
    test = _evaluate_one_serial(FAMILY, best["params"], TEST_SEEDS)
    test_elapsed = time.time() - t_test

    delta = test["score"] - INHERITED_BASELINE_TEST_SCORE
    log(
        f"  Best-by-val | val={best['val_score']:.3f} | test={test['score']:.3f} | "
        f"adv={test['edge_advantage_mean']:+.3f}  ({test_elapsed:.1f}s) | "
        f"cycle8_starting_line={INHERITED_BASELINE_TEST_SCORE:.3f}"
    )
    log(f"  Δ vs cycle-8 ablation best: {delta:+.3f}")

    final = {
        "policy_family": FAMILY,
        "init_strategy": "warm_start_from_cycle8_ablation",
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
        "starting_line_test_score": INHERITED_BASELINE_TEST_SCORE,
        "delta_vs_starting_line": delta,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (OUTDIR / "third_pass_cem_test.json").write_text(json.dumps(final, indent=2))
    log(f"  -> wrote {OUTDIR / 'third_pass_cem_test.json'}")
    log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--generations", type=int, default=GENERATIONS)
    args = parser.parse_args()
    main(args.rng_seed, args.generations)
