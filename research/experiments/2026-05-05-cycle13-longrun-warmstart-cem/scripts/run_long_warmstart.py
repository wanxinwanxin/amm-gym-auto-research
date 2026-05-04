"""
Cycle-13 long-run warm-start CEM — gen=24 from cycle-11 d16_s2 anchor.

Cycle 12 closed with three live hypotheses about why warm-start CEM
saturated near 457 in cycles 9-11:
    (a) capacity is the bottleneck — falsified (latent_full @ 388.6).
    (b) the cycle-8 anchor is in a sub-optimal basin — not resolved
        (fresh-anchor piecewise was still climbing at gen 11).
    (c) the saturation is a recipe ceiling under (pop=24, gen=12)
        — most consistent with the data.

This driver tests (c) directly: doubling the CEM budget (gen=24 vs 12)
on the *same* warm-start anchor (cycle-11 d16_s2 best, the current M2
champion at test = 456.80) under the *same* recipe (pop=24,
init_std_frac=0.10, elite_frac=0.20).

Decision rule, decided BEFORE running:
    test ≥ 460       → recipe ceiling falsified; warm-start refinement
                       still has room. Continue cycle 14 along this
                       axis (gen=36 or larger pop).
    457 ≤ test < 460 → marginal lift, ambiguous; one more replicate
                       (different rng seed) needed to call it.
    test  < 457      → recipe ceiling confirmed at this anchor.
                       Pivot to M3 with d16_s2 (456.80) as the M2
                       deliverable (~85% of way to 540).

Anchor: cycle-11 d16_s2 best_by_val params (test_score 456.80).
Recipe parity: pop=24, generations=24, init_std_frac=0.10,
elite_frac=0.20. Same val/test seed split (1000..1127 / 2000..2255)
as every prior M2 cycle, so the result is on the same scoreboard.

Wall-clock estimate: cycle-11 d16_s2 ran 12 gens in 30.2 min CEM +
4.8 min rerank = 35 min. Doubling gens predicts ~60 min CEM + ~5 min
rerank = ~65 min total. Fits one cycle.

Usage:
    python run_long_warmstart.py --rng-seed 0 --generations 24
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

EVAL_FAMILY = "piecewise"
PIECEWISE_DIM = 16

CYCLE11_D16_S2_RESULT = (
    ROOT
    / "research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2/result.json"
)

# The current M2 champion's test score (the value we're trying to beat).
CHAMPION_TEST_SCORE = 456.8032181567959

SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
DEFAULT_GENERATIONS = 24
ELITE_FRAC = 0.2
INIT_STD_FRAC = 0.10
MAX_WORKERS = max(1, min(3, (os.cpu_count() or 1) - 1))


def _piecewise_bounds():
    ranges = PIECEWISE_CONTROLLER_PARAM_RANGES
    names = list(ranges.keys())
    lows = np.asarray([ranges[n][0] for n in names], dtype=float)
    highs = np.asarray([ranges[n][1] for n in names], dtype=float)
    return names, lows, highs


def _load_anchor() -> dict[str, float]:
    """Cycle-11 d16_s2 best_by_val.params — the current M2 champion."""
    with CYCLE11_D16_S2_RESULT.open() as f:
        d = json.load(f)
    params = d["best_by_val"]["params"]
    # piecewise core only (no noop tail — d16 had tail_dim=0 anyway)
    return {k: v for k, v in params.items() if not k.startswith("noop_")}


def _evaluate_one_candidate(payload: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from arena_eval.exact_simple_amm import (  # noqa: WPS433
        FixedFeeStrategy as _FF,
        run_batch as _rb,
    )
    from arena_search.simple_amm_search import POLICY_SPECS as _SPECS  # noqa: WPS433

    spec = _SPECS[payload["family"]]
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


def _logger(outdir: Path):
    logfile = outdir / "progress.log"
    with logfile.open("w") as _f:
        _f.write("")

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    return _log


def main(rng_seed: int, generations: int) -> None:
    cell_label = f"longrun_d16_s{rng_seed}_g{generations}"
    outdir = (
        ROOT
        / f"research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/{cell_label}"
    )
    outdir.mkdir(parents=True, exist_ok=True)

    log = _logger(outdir)
    rng = np.random.default_rng(rng_seed)

    pw_names, pw_lows, pw_highs = _piecewise_bounds()
    names = list(pw_names)
    lows = pw_lows.copy()
    highs = pw_highs.copy()

    anchor = _load_anchor()
    init_mean = np.asarray([anchor[n] for n in pw_names], dtype=float)
    init_mean = np.clip(init_mean, pw_lows, pw_highs)
    init_std = INIT_STD_FRAC * (highs - lows)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    log(
        f"Cycle-13 long-run warm-start CEM | {cell_label} | "
        f"core_dim={len(pw_names)} pop={POPULATION} gen={generations} elite_n={elite_n} "
        f"init_std_frac={INIT_STD_FRAC} workers={MAX_WORKERS} rng_seed={rng_seed}"
    )
    log(f"Anchor: cycle-11 d16_s2 best_by_val (champion test={CHAMPION_TEST_SCORE:.3f})")
    log(f"Anchor params: {dict(zip(pw_names, init_mean.tolist()))}")
    log(f"Search seeds: {SEARCH_SEEDS[0]}..{SEARCH_SEEDS[-1]} (n={len(SEARCH_SEEDS)})")
    log(f"Val seeds:    {VAL_SEEDS[0]}..{VAL_SEEDS[-1]} (n={len(VAL_SEEDS)})")
    log(f"Test seeds:   {TEST_SEEDS[0]}..{TEST_SEEDS[-1]} (n={len(TEST_SEEDS)})")

    anchor_check = _evaluate_one_serial(
        EVAL_FAMILY, dict(zip(names, init_mean.tolist())), SEARCH_SEEDS
    )
    log(f"Anchor search-seed score: {anchor_check['score']:.3f} (parity check)")

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
            f"val={val['score']:7.3f} "
            f"({gen_elapsed:5.1f}s+{val_elapsed:4.1f}s)"
        )

        (outdir / "history.json").write_text(
            json.dumps(
                {
                    "policy_family": EVAL_FAMILY,
                    "cell_label": cell_label,
                    "core_dim": PIECEWISE_DIM,
                    "init_strategy": "warm_start_cycle11_d16_s2",
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
        rerank.append(
            {
                "params": elite["params"],
                "search_score": elite["score"],
                "val_score": val["score"],
                "val_edge_advantage": val["edge_advantage_mean"],
            }
        )
    rerank.sort(key=lambda r: r["val_score"], reverse=True)

    best = rerank[0]
    t_test = time.time()
    test = _evaluate_one_serial(EVAL_FAMILY, best["params"], TEST_SEEDS)
    test_elapsed = time.time() - t_test

    delta = test["score"] - CHAMPION_TEST_SCORE
    log(
        f"  Best-by-val | val={best['val_score']:.3f} | test={test['score']:.3f} | "
        f"adv={test['edge_advantage_mean']:+.3f}  ({test_elapsed:.1f}s) | "
        f"champion={CHAMPION_TEST_SCORE:.3f}"
    )
    log(f"  Δ vs cycle-11 d16_s2 champion: {delta:+.3f}")

    final = {
        "policy_family": EVAL_FAMILY,
        "cell_label": cell_label,
        "core_dim": PIECEWISE_DIM,
        "init_strategy": "warm_start_cycle11_d16_s2",
        "init_std_frac": INIT_STD_FRAC,
        "rng_seed": rng_seed,
        "generations": generations,
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
        },
        "champion_test_score": CHAMPION_TEST_SCORE,
        "delta_vs_champion": delta,
        "target_score": 540.0,
        "remaining_gap": 540.0 - test["score"],
        "total_elapsed_s": total_elapsed,
        "test_elapsed_s": test_elapsed,
    }
    (outdir / "result.json").write_text(json.dumps(final, indent=2))
    log(f"  -> wrote {outdir / 'result.json'}")
    log(json.dumps(final["best_by_val"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--generations", type=int, default=DEFAULT_GENERATIONS)
    args = parser.parse_args()
    main(args.rng_seed, args.generations)
