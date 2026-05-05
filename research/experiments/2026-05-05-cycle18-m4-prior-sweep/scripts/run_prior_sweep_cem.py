"""
M4 cycle-2 — prior sweep: 5g × 12p CEM on real_data warm-started from
{default-piecewise, c6, c8 (16-d projection)}. The c5 and c11 points
are reused from cycles 16/17 for axis continuity.

Question.
  Cycle 17 showed +2.03 lift_FF separation between c5+CEM and c11+CEM
  with identical compute. Was that gap a special property of the c11
  anchor (its retail-positive basin) or a generic basin-dominance
  phenomenon? If we plot final_lift_FF vs starting_lift_FF for several
  anchors, do we see (a) monotone (basin-dominance), (b) starting-line
  irrelevance, or (c) anchor-specific spikes (c11 alone is special)?

Method.
  For each of {default-piecewise, c6_warmstart_best, c8_inv_aware_best}
  run 5-gen × 12-pop CEM with the cycle-17 settings: same seeds
  (search 0-63 / val 1000-1127 / test 2000-2255), same elite_frac
  (0.2), same init_std_frac (0.10), same normalizer FixedFee(0.003,
  0.003), same rng_seed (0), workers = cpu-1.

  c8 is 19-d in its own search; for the 16-d piecewise sweep we drop
  the inventory_skew_* fields. Anchor name prefix records the
  projection.

  For each anchor we record: anchor val_score (start), best-by-val
  params after CEM, test score, FF baseline, lift_FF, and per-bucket
  retail_edge_advantage (small/medium/large) on val.

Output.
  results/prior_sweep/<anchor_id>/{history.json,test.json,progress.log}
  results/prior_sweep_summary.json — one row per anchor.
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


OUTROOT = (
    ROOT
    / "research/experiments/2026-05-05-cycle18-m4-prior-sweep/results/prior_sweep"
)
OUTROOT.mkdir(parents=True, exist_ok=True)


# ----- Anchor params (16-d piecewise family) -----
DEFAULT_PIECEWISE_PARAMS = {
    n: 0.5 * (PIECEWISE_CONTROLLER_PARAM_RANGES[n][0] + PIECEWISE_CONTROLLER_PARAM_RANGES[n][1])
    for n in PIECEWISE_CONTROLLER_PARAM_RANGES
}

# c6 best-by-val (cycle-6 warm-start CEM, M2 score 432.7).
C6_PIECEWISE_PARAMS = {
    "base_fee": 0.002367347771481619,
    "base_spread": 0.004308002150845519,
    "signal_decay": 0.5512724333509836,
    "toxicity_decay": 0.552468164452998,
    "small_trade_threshold": 0.004129871044378966,
    "large_trade_threshold": 0.009904163985697503,
    "continuation_small": -0.00012073758590954386,
    "continuation_medium": 0.012093232860869314,
    "continuation_large": 0.02,
    "reversal_small": 0.016296159249685895,
    "reversal_medium": 0.01927342926722678,
    "reversal_large": 0.07813813355714157,
    "continuation_to_same_side": 0.22765645382739977,
    "continuation_to_cross_side": 0.8964001772946211,
    "toxicity_to_mid": 0.012437665162005649,
    "toxicity_to_side": 0.06301381267531339,
}

# c8 inv-aware best-by-val (cycle-8 inv-piecewise, M2 score 446.4)
# 16-d projection: drop inventory_skew_to_bid/ask/dead_zone.
C8_PIECEWISE_PARAMS_16D = {
    "base_fee": 0.0016550408798529576,
    "base_spread": 0.004243130017056316,
    "signal_decay": 0.6710204554398381,
    "toxicity_decay": 0.5359985273747493,
    "small_trade_threshold": 0.0035434960848610567,
    "large_trade_threshold": 0.010026395287212322,
    "continuation_small": -0.0002902772323995477,
    "continuation_medium": 0.007132694969980573,
    "continuation_large": 0.01823001527951129,
    "reversal_small": 0.01193099991680676,
    "reversal_medium": 0.02189557268220984,
    "reversal_large": 0.07594344828226333,
    "continuation_to_same_side": 0.12260500653949676,
    "continuation_to_cross_side": 1.3580492898846743,
    "toxicity_to_mid": 0.009952017339294478,
    "toxicity_to_side": 0.06882714964266168,
}

ANCHORS = {
    "default": DEFAULT_PIECEWISE_PARAMS,
    "c6_warmstart": C6_PIECEWISE_PARAMS,
    "c8_invaware_16d": C8_PIECEWISE_PARAMS_16D,
}

# Knobs (mirror cycle-17 5g x 12p exactly).
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


def _initial_mean_std(anchor_params: dict, init_std_frac: float) -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows, highs = _bounds()
    init_mean = np.asarray([anchor_params[n] for n in names], dtype=float)
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


def run_one_anchor(anchor_id: str, anchor_params: dict, ff_test_score: float) -> dict:
    outdir = OUTROOT / anchor_id
    outdir.mkdir(parents=True, exist_ok=True)
    logfile = outdir / "progress.log"
    logfile.open("w").close()

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] [{anchor_id}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    rng = np.random.default_rng(RNG_SEED)
    names = _names()
    lows, highs = _bounds()
    mean, std = _initial_mean_std(anchor_params, INIT_STD_FRAC)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    _log(
        f"prior-sweep CEM | piecewise on {EVALUATOR_KIND} | pop={POPULATION} "
        f"gen={GENERATIONS} elite_n={elite_n} workers={MAX_WORKERS}"
    )

    anchor_obj = PiecewiseControllerParams(**anchor_params).normalized()
    t0 = time.time()
    anchor_val = _evaluate_one_serial(anchor_obj, VAL_SEEDS, EVALUATOR_KIND)
    _log(
        f"  anchor val ({EVALUATOR_KIND}, n={len(VAL_SEEDS)}): score={anchor_val['score']:7.3f} "
        f"adv={anchor_val['edge_advantage_mean']:+7.3f} retail_adv={anchor_val['retail_edge_advantage_mean']:+7.3f} "
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

        (outdir / "history.json").write_text(
            json.dumps(
                {
                    "anchor_id": anchor_id,
                    "anchor_params": anchor_params,
                    "policy_family": "piecewise",
                    "evaluator_kind": EVALUATOR_KIND,
                    "init_std_frac": INIT_STD_FRAC,
                    "population_size": POPULATION,
                    "elite_fraction": ELITE_FRAC,
                    "search_seeds": list(SEARCH_SEEDS),
                    "val_seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
                    "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
                    "rng_seed": RNG_SEED,
                    "anchor_val_score": anchor_val["score"],
                    "anchor_val_edge_advantage": anchor_val["edge_advantage_mean"],
                    "anchor_val_retail_advantage": anchor_val["retail_edge_advantage_mean"],
                    "history": history,
                },
                indent=2,
            )
        )

        mean = new_mean
        std = new_std

    total_elapsed = time.time() - t_run
    _log(f"CEM complete in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Rerank: anchor + top-6 unique elites by search score, ranked by val.
    unique_elites: list[dict] = []
    seen: set[tuple[float, ...]] = set()
    anchor_record = {"params": anchor_params, "score": anchor_val["score"]}
    unique_elites.append(anchor_record)
    seen.add(tuple(anchor_params[n] for n in names))
    for elite in sorted(all_elites, key=lambda r: r["score"], reverse=True):
        key = tuple(elite["params"][n] for n in names)
        if key in seen:
            continue
        seen.add(key)
        unique_elites.append(elite)
        if len(unique_elites) >= 7:
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
    test = _evaluate_one_serial(best_params, TEST_SEEDS, EVALUATOR_KIND)

    final = {
        "anchor_id": anchor_id,
        "anchor_params": anchor_params,
        "policy_family": "piecewise",
        "evaluator_kind": EVALUATOR_KIND,
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
        "anchor_val_score": anchor_val["score"],
        "anchor_val_edge_advantage": anchor_val["edge_advantage_mean"],
        "anchor_val_retail_advantage": anchor_val["retail_edge_advantage_mean"],
        "total_elapsed_s": total_elapsed,
    }
    (outdir / "test.json").write_text(json.dumps(final, indent=2))
    _log(f"  best_by_val test_score={test['score']:.3f} lift_FF={test['score']-ff_test_score:+.3f}")
    return final


def main() -> None:
    # FF test baseline (computed once, shared across anchors).
    ff_t0 = time.time()
    ff_test = run_batch(
        lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        TEST_SEEDS,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        evaluator_kind=EVALUATOR_KIND,
    )
    ff_test_score = float(ff_test.score)
    print(f"FF test ({EVALUATOR_KIND}): {ff_test_score:.3f} ({time.time()-ff_t0:.1f}s)", flush=True)

    summary: list[dict] = []
    for anchor_id, params in ANCHORS.items():
        print(f"\n=== anchor: {anchor_id} ===", flush=True)
        final = run_one_anchor(anchor_id, params, ff_test_score)
        summary.append({
            "anchor_id": anchor_id,
            "anchor_val_score": final["anchor_val_score"],
            "anchor_val_retail_advantage": final["anchor_val_retail_advantage"],
            "best_by_val": final["best_by_val"],
        })
        (OUTROOT.parent / "prior_sweep_summary.json").write_text(
            json.dumps({"ff_test_score": ff_test_score, "anchors": summary}, indent=2)
        )

    print("\n=== prior-sweep summary ===", flush=True)
    for row in summary:
        a = row["anchor_id"]
        b = row["best_by_val"]
        print(
            f"  {a:<22} anchor_val={row['anchor_val_score']:+6.3f} "
            f"-> test={b['test_score']:+6.3f} lift_FF={b['lift_FF']:+6.3f} "
            f"retail_adv={b['test_retail_advantage']:+6.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
