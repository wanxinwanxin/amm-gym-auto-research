"""
Cycle-8 M2 — init_std sensitivity sweep on `submission_compact`.

Cycle-7 ran warm-start CEM at init_std_frac=0.10 from the inherited
`submission_compact` best (test 410.78) and lifted to 416.08 (+5.3 pts).
Population kept drifting upward at gen 11 but val plateaued by gen 8 —
suggests either the basin is flat or noise floor was hit. Cycle-8
hypothesis: was 0.10 the wrong width? Sweep init_std_frac ∈
{0.05, 0.20, 0.30} and report the per-init-std lift to either
(a) confirm the cycle-7 prescription should be re-spec'd to "warm-start
AND match init_std to inherited basin width" (if 0.20 or 0.30 lifts to
~430+) or (b) close the question by showing 0.10 was already close to
optimal for this family.

Each sub-run: 6 generations (cycle-7 saw val plateau by gen 8, so 6 is
enough to see whether the basin is wider or narrower than 0.10×range).
Same pop=24, same elite_frac, same train/val/test seed split as cycle 7.

Outputs (per init_std_frac):
  research/experiments/2026-05-04-cycle8-init-std-sweep/results/
      init_std_<frac>_history.json
      init_std_<frac>_test.json
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
    POLICY_SPECS,
    SUBMISSION_COMPACT_PARAM_RANGES,
)


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle8-init-std-sweep/results"
OUTDIR.mkdir(parents=True, exist_ok=True)

FAMILY = "submission_compact"
INHERITED_BASELINE_TEST_SCORE = 410.776  # cycle-5 measurement, cycle-7 confirmed

SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
GENERATIONS = 6
ELITE_FRAC = 0.2
MAX_WORKERS = max(1, min(3, (os.cpu_count() or 1) - 1))


def _bounds(ranges, names):
    lows = np.asarray([ranges[n][0] for n in names], dtype=float)
    highs = np.asarray([ranges[n][1] for n in names], dtype=float)
    return lows, highs


def _inherited_anchor() -> dict[str, float]:
    rebatch = ROOT / f"experiments/{FAMILY}_cem_1h_20260423_rebatch1.json"
    with rebatch.open() as f:
        d = json.load(f)
    return d["best_validation"]["params"]


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


def _logger(tag: str):
    logfile = OUTDIR / f"init_std_{tag}_progress.log"
    with logfile.open("w") as _f:
        _f.write("")

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    return _log


def run_one_init_std(init_std_frac: float, rng_seed: int, generations: int) -> dict:
    tag = f"{init_std_frac:.2f}".replace(".", "p")
    log = _logger(tag)
    rng = np.random.default_rng(rng_seed)
    ranges = SUBMISSION_COMPACT_PARAM_RANGES
    names = list(ranges.keys())
    lows, highs = _bounds(ranges, names)
    inh = _inherited_anchor()
    init_mean = np.asarray([inh[n] for n in names], dtype=float)
    init_mean = np.clip(init_mean, lows, highs)
    init_std = init_std_frac * (highs - lows)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    log(
        f"Cycle-8 init_std sweep | family={FAMILY} init_std_frac={init_std_frac} "
        f"pop={POPULATION} gen={generations} elite_n={elite_n} "
        f"workers={MAX_WORKERS} rng_seed={rng_seed}"
    )

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

        history.append({
            "generation": gen,
            "best_search_score": results[0]["score"],
            "elite_mean_search_score": float(np.mean([r["score"] for r in elites])),
            "fixed_val_score": val["score"],
            "best_search_params": results[0]["params"],
            "mean_after": new_mean.tolist(),
            "std_after": new_std.tolist(),
            "gen_elapsed_s": gen_elapsed,
            "val_elapsed_s": val_elapsed,
        })

        log(
            f"  init_std_frac={init_std_frac:.2f} gen {gen:2d}: "
            f"best={results[0]['score']:7.3f} "
            f"elite_mean={float(np.mean([r['score'] for r in elites])):7.3f} "
            f"val={val['score']:7.3f} "
            f"({gen_elapsed:5.1f}s+{val_elapsed:4.1f}s)"
        )

        (OUTDIR / f"init_std_{tag}_history.json").write_text(
            json.dumps({
                "policy_family": FAMILY,
                "init_std_frac": init_std_frac,
                "rng_seed": rng_seed,
                "history": history,
            }, indent=2)
        )

        mean = new_mean
        std = new_std

    total_elapsed = time.time() - t_run
    log(f"  init_std={init_std_frac:.2f} CEM done in {total_elapsed:.1f}s")

    # Pick top-4 unique elites, rerank on val, score val-best on test.
    unique_elites: list[dict] = []
    seen: set[tuple[float, ...]] = set()
    for elite in sorted(all_elites, key=lambda r: r["score"], reverse=True):
        key = tuple(elite["params"][n] for n in names)
        if key in seen:
            continue
        seen.add(key)
        unique_elites.append(elite)
        if len(unique_elites) >= 4:
            break

    rerank: list[dict] = []
    for elite in unique_elites:
        val = _evaluate_one_serial(FAMILY, elite["params"], VAL_SEEDS)
        rerank.append({
            "params": elite["params"],
            "search_score": elite["score"],
            "val_score": val["score"],
        })
    rerank.sort(key=lambda r: r["val_score"], reverse=True)
    best = rerank[0]
    test = _evaluate_one_serial(FAMILY, best["params"], TEST_SEEDS)
    delta = test["score"] - INHERITED_BASELINE_TEST_SCORE

    log(
        f"  init_std={init_std_frac:.2f}: best_val={best['val_score']:.3f} "
        f"-> test={test['score']:.3f} (Δ vs starting line {delta:+.3f})"
    )

    final = {
        "family": FAMILY,
        "init_std_frac": init_std_frac,
        "rng_seed": rng_seed,
        "rerank": rerank,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "test_score": test["score"],
            "test_n_seeds": len(TEST_SEEDS),
        },
        "starting_line_test_score": INHERITED_BASELINE_TEST_SCORE,
        "delta_vs_starting_line": delta,
        "total_elapsed_s": total_elapsed,
    }
    (OUTDIR / f"init_std_{tag}_test.json").write_text(json.dumps(final, indent=2))
    return final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init-std-fracs",
        type=float,
        nargs="+",
        default=[0.05, 0.20, 0.30],
    )
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--generations", type=int, default=GENERATIONS)
    args = parser.parse_args()

    summary: list[dict] = []
    for init_std in args.init_std_fracs:
        result = run_one_init_std(init_std, args.rng_seed, args.generations)
        summary.append({
            "init_std_frac": init_std,
            "test_score": result["best_by_val"]["test_score"],
            "delta_vs_starting_line": result["delta_vs_starting_line"],
            "total_elapsed_s": result["total_elapsed_s"],
        })
    (OUTDIR / "sweep_summary.json").write_text(json.dumps(summary, indent=2))
    print("=== sweep summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
