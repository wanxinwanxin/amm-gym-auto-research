"""
Cycle-10 Experiment A — 20-d no-op-tail piecewise warm-start CEM.

Hypothesis test: cycle-9 #3 (EMA-inv wrapper) lifted M2 446.6 → 456.64 vs
cycle-9 #1 (bare 16-d 4th-pass) which lifted to only 448.81. The cycle-9
ablation showed the EMA-inv params themselves contributed only +0.024 to
the score. So the +7.83 lift must come from one of:

  (A) inert tail dims help CEM by adding random search directions that
      escape shallow plateaus in the 16-d basin
  (B) rng_seed lottery (different sampling sequence at dim=20 vs dim=16)
  (C) the EMA-inv wrapper had real signal that the ablation missed

This experiment tests (A) cleanly. The CEM samples a 20-d vector but
*only* the first 16 dims enter the fee formula. The trailing 4 dims are
pure noise — they cannot affect the score, even in principle.

Anchor: cycle-8 ablated piecewise (16 dims) extended with 4 zeros. Same
recipe as cycle-9 EMA: pop=24, gen=12, init_std_frac=0.10, elite=0.20.
RNG seed=0 (matches cycle-9 #3 for direct comparison).

If A score ≈ 456.6: hypothesis (A) confirmed; "wrapper-as-noise" is real.
If A score ≈ 449:   hypothesis (C) becomes more likely (EMA had signal).
If A score is between: weak/intermediate evidence; rerun with seed=1.

Companion: run_seed_lottery_cem.py tests hypothesis (B).
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


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results"
OUTDIR.mkdir(parents=True, exist_ok=True)

# We keep `family` = "piecewise" for evaluation; the tail dims are
# discarded before instantiating the params class.
EVAL_FAMILY = "piecewise"

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

# Number of inert tail dimensions added beyond the 16 piecewise dims.
NUM_NOOP_TAIL = 4

# Bounds for the noop tail dims. Each is a unit-interval normal that
# CEM samples freely; the value is never read by the simulator.
NOOP_LOWS = np.full(NUM_NOOP_TAIL, -1.0)
NOOP_HIGHS = np.full(NUM_NOOP_TAIL, 1.0)
NOOP_INIT_MEAN = np.zeros(NUM_NOOP_TAIL)


def _piecewise_bounds():
    ranges = PIECEWISE_CONTROLLER_PARAM_RANGES
    names = list(ranges.keys())
    lows = np.asarray([ranges[n][0] for n in names], dtype=float)
    highs = np.asarray([ranges[n][1] for n in names], dtype=float)
    return names, lows, highs


def _inherited_anchor() -> dict[str, float]:
    """Cycle-8 best, piecewise core only (16 dims)."""
    with CYCLE8_ABLATION_JSON.open() as f:
        d = json.load(f)
    return {k: v for k, v in d["ablated_params"].items() if not k.startswith("inventory_")}


def _evaluate_one_candidate(payload: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from arena_eval.exact_simple_amm import (  # noqa: WPS433
        FixedFeeStrategy as _FF,
        run_batch as _rb,
    )
    from arena_search.simple_amm_search import POLICY_SPECS as _SPECS  # noqa: WPS433

    spec = _SPECS[payload["family"]]
    # Drop the trailing noop dims from the params dict before
    # instantiating; the eval params class doesn't even know about them.
    params_dict = {k: v for k, v in payload["params"].items() if not k.startswith("noop_")}
    params = spec.params_cls(**params_dict).normalized()
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
        "n_seeds": len(seeds),
    }


def _logger():
    logfile = OUTDIR / "noop_tail_cem_progress.log"
    with logfile.open("w") as _f:
        _f.write("")

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    return _log


def main(rng_seed: int, generations: int, num_noop_tail: int) -> None:
    log = _logger()
    rng = np.random.default_rng(rng_seed)

    pw_names, pw_lows, pw_highs = _piecewise_bounds()
    noop_names = [f"noop_{i}" for i in range(num_noop_tail)]
    names = pw_names + noop_names
    noop_lows = np.full(num_noop_tail, -1.0)
    noop_highs = np.full(num_noop_tail, 1.0)
    noop_init_mean = np.zeros(num_noop_tail)
    lows = np.concatenate([pw_lows, noop_lows])
    highs = np.concatenate([pw_highs, noop_highs])

    inh = _inherited_anchor()
    pw_init = np.asarray([inh[n] for n in pw_names], dtype=float)
    pw_init = np.clip(pw_init, pw_lows, pw_highs)
    init_mean = np.concatenate([pw_init, noop_init_mean])
    init_std = INIT_STD_FRAC * (highs - lows)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    log(
        f"Cycle-10A no-op-tail piecewise warm-start CEM | "
        f"core_dim={len(pw_names)} tail_dim={num_noop_tail} total_dim={len(names)} "
        f"pop={POPULATION} gen={generations} elite_n={elite_n} "
        f"init_std_frac={INIT_STD_FRAC} workers={MAX_WORKERS} rng_seed={rng_seed}"
    )
    log(f"Anchor (piecewise core only): {dict(zip(pw_names, pw_init.tolist()))}")
    log(f"Anchor (noop tail): {dict(zip(noop_names, noop_init_mean.tolist()))} (these are inert)")
    log(f"Search seeds: {SEARCH_SEEDS[0]}..{SEARCH_SEEDS[-1]} (n={len(SEARCH_SEEDS)})")
    log(f"Val seeds:    {VAL_SEEDS[0]}..{VAL_SEEDS[-1]} (n={len(VAL_SEEDS)})")
    log(f"Test seeds:   {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})")

    anchor_check = _evaluate_one_serial(EVAL_FAMILY, dict(zip(names, init_mean.tolist())), SEARCH_SEEDS)
    log(f"Anchor search-seed score: {anchor_check['score']:.3f} (parity check: should equal cycle-8 anchor)")

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
                "family": EVAL_FAMILY,
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
        val = _evaluate_one_serial(EVAL_FAMILY, results[0]["params"], VAL_SEEDS)
        val_elapsed = time.time() - val_t0

        # noop tail diagnostic — what is CEM actually doing in those dims?
        noop_means = new_mean[len(pw_names):].tolist()
        noop_stds = new_std[len(pw_names):].tolist()

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
            "noop_means": noop_means,
            "noop_stds": noop_stds,
            "gen_elapsed_s": gen_elapsed,
            "val_elapsed_s": val_elapsed,
        }
        history.append(gen_record)

        log(
            f"  gen {gen:2d}: best={results[0]['score']:7.3f} "
            f"elite_mean={gen_record['elite_mean_search_score']:7.3f} "
            f"val={val['score']:7.3f} | "
            f"noop_mean=[{','.join(f'{x:+.3f}' for x in noop_means)}] "
            f"noop_std=[{','.join(f'{x:.3f}' for x in noop_stds)}] "
            f"({gen_elapsed:5.1f}s+{val_elapsed:4.1f}s)"
        )

        (OUTDIR / "noop_tail_cem_history.json").write_text(
            json.dumps(
                {
                    "policy_family": EVAL_FAMILY,
                    "wrapper": f"noop_tail_n{num_noop_tail}",
                    "init_strategy": "warm_start_cycle8_ablation_plus_zero_noop_tail",
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
        # de-dup on the 16 piecewise dims only since the noop dims don't matter for score
        key = tuple(round(elite["params"][n], 12) for n in pw_names)
        if key in seen:
            continue
        seen.add(key)
        unique_elites.append(elite)
        if len(unique_elites) >= 8:
            break

    rerank: list[dict] = []
    for elite in unique_elites:
        val = _evaluate_one_serial(EVAL_FAMILY, elite["params"], VAL_SEEDS)
        rerank.append({
            "params": elite["params"],
            "search_score": elite["score"],
            "val_score": val["score"],
            "val_edge_advantage": val["edge_advantage_mean"],
        })
    rerank.sort(key=lambda r: r["val_score"], reverse=True)

    best = rerank[0]
    t_test = time.time()
    test = _evaluate_one_serial(EVAL_FAMILY, best["params"], TEST_SEEDS)
    test_elapsed = time.time() - t_test

    delta = test["score"] - INHERITED_BASELINE_TEST_SCORE
    log(
        f"  Best-by-val | val={best['val_score']:.3f} | test={test['score']:.3f} | "
        f"adv={test['edge_advantage_mean']:+.3f}  ({test_elapsed:.1f}s) | "
        f"cycle8_starting_line={INHERITED_BASELINE_TEST_SCORE:.3f}"
    )
    log(f"  Δ vs cycle-8 ablation best: {delta:+.3f}")

    final = {
        "policy_family": EVAL_FAMILY,
        "wrapper": f"noop_tail_n{num_noop_tail}",
        "init_strategy": "warm_start_cycle8_ablation_plus_zero_noop_tail",
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
    (OUTDIR / "noop_tail_cem_test.json").write_text(json.dumps(final, indent=2))
    log(f"  -> wrote {OUTDIR / 'noop_tail_cem_test.json'}")
    log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--generations", type=int, default=GENERATIONS)
    parser.add_argument("--num-noop-tail", type=int, default=NUM_NOOP_TAIL)
    args = parser.parse_args()
    main(args.rng_seed, args.generations, args.num_noop_tail)
