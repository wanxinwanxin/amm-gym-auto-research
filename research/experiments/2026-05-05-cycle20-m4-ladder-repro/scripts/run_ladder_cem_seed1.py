"""
M4 cycle-20 — Reproducibility check for cycle-19 ladder CEM (seed=1).

Question.
  Cycle-19 ran the 4-bucket ladder family with rng_seed=0 (single seed)
  and reported test lift_FF +3.251 — in the cycle-18 [+3.20, +3.50]
  "marginal" band. Is that signal seed-stable, or did cycle-19 get a
  lucky pick?

  Decision rule on lift_FF (test n=256, real_data):
    [+3.15, +3.35]  -> reproducible; cycle-19's headline holds.
    < +3.15 (e.g. closer to c11+CEM long's +3.01) -> cycle-19 was
                      lucky; family-escalation case is weaker.
    > +3.35  -> ladder is even better than cycle-19's estimate;
                use this seed's params as new anchor.

Method.
  Identical CEM mechanics, identical search/val/test seed splits to
  cycle-19 (range(0,64) / range(1000,1128) / range(2000,2256)). The
  only knob changed is rng_seed: 0 -> 1.
  - normalizer: FixedFee(0.003, 0.003)
  - evaluator: real_data
  - dim=19, pop=12, gen=5, elite_frac=0.2
  - init_std_frac: 0.05 inherited / 0.15 new dims
  - rerank: anchor + top 6 unique elites by search score, picked best
    by val score
  - same FF baseline on the same test seeds for lift_FF.

  Sharing the search/val/test seed splits means any score drift between
  cycle-19 and cycle-20 is attributable to the CEM rng stream, not to
  evaluator data drift.
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
SCRIPT_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from ladder_strategy import (  # noqa: E402
    LADDER_PARAM_RANGES,
    LadderControllerParams,
    LadderControllerStrategy,
)


OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle20-m4-ladder-repro/results/ladder_cem_seed1"
)
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = OUTDIR / "progress.log"

# c11+CEM long best-by-val (cycle-18 result) -- identical to cycle-19.
C11_LONG_PIECEWISE = {
    "base_fee": 0.0002651625453621829,
    "base_spread": 0.004070554016340082,
    "signal_decay": 0.7627950328668307,
    "toxicity_decay": 0.7516377170207057,
    "small_trade_threshold": 0.002848486560218609,
    "large_trade_threshold": 0.008866574986467687,
    "continuation_small": 8.283451496244375e-05,
    "continuation_medium": 0.006929076834258454,
    "continuation_large": 0.017986720175801947,
    "reversal_small": 0.004837147255038543,
    "reversal_medium": 0.012729063516975241,
    "reversal_large": 0.07976951856036607,
    "continuation_to_same_side": -0.19329440684669405,
    "continuation_to_cross_side": 0.9267032329066462,
    "toxicity_to_mid": 0.011186051913361214,
    "toxicity_to_side": 0.07886754688062839,
}


def _build_warmstart_ladder() -> dict[str, float]:
    p = C11_LONG_PIECEWISE
    return {
        "base_fee": p["base_fee"],
        "base_spread": p["base_spread"],
        "signal_decay": p["signal_decay"],
        "toxicity_decay": p["toxicity_decay"],
        "tiny_trade_threshold": p["small_trade_threshold"] * 0.5,
        "small_trade_threshold": p["small_trade_threshold"],
        "large_trade_threshold": p["large_trade_threshold"],
        "continuation_tiny": p["continuation_small"],
        "continuation_small": p["continuation_small"],
        "continuation_medium": p["continuation_medium"],
        "continuation_large": p["continuation_large"],
        "reversal_tiny": p["reversal_small"],
        "reversal_small": p["reversal_small"],
        "reversal_medium": p["reversal_medium"],
        "reversal_large": p["reversal_large"],
        "continuation_to_same_side": p["continuation_to_same_side"],
        "continuation_to_cross_side": p["continuation_to_cross_side"],
        "toxicity_to_mid": p["toxicity_to_mid"],
        "toxicity_to_side": p["toxicity_to_side"],
    }


NEW_DIMS = {"tiny_trade_threshold", "continuation_tiny", "reversal_tiny"}
INIT_STD_FRAC_INHERITED = 0.05
INIT_STD_FRAC_NEW = 0.15

EVALUATOR_KIND = "real_data"
SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 12
GENERATIONS = 5
ELITE_FRAC = 0.2
NORMALIZER_FEE = 0.003
RNG_SEED = 1   # <-- the only knob changed from cycle-19
MAX_WORKERS = max(1, (os.cpu_count() or 1) - 1)
RERANK_TOP_K = 6


def _names() -> list[str]:
    return list(LADDER_PARAM_RANGES.keys())


def _bounds() -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows = np.asarray([LADDER_PARAM_RANGES[n][0] for n in names], dtype=float)
    highs = np.asarray([LADDER_PARAM_RANGES[n][1] for n in names], dtype=float)
    return lows, highs


def _initial_mean_std() -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows, highs = _bounds()
    warm = _build_warmstart_ladder()
    init_mean = np.asarray([warm[n] for n in names], dtype=float)
    init_mean = np.clip(init_mean, lows, highs)
    init_std = np.empty_like(init_mean)
    for i, n in enumerate(names):
        frac = INIT_STD_FRAC_NEW if n in NEW_DIMS else INIT_STD_FRAC_INHERITED
        init_std[i] = frac * (highs[i] - lows[i])
    return init_mean, init_std


def _evaluate_one_candidate(payload: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(SCRIPT_DIR))
    from ladder_strategy import LadderControllerParams, LadderControllerStrategy  # noqa
    from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa

    params = LadderControllerParams(**payload["params"]).normalized()
    seeds = tuple(payload["seeds"])
    nfee = payload["normalizer_fee"]
    eval_kind = payload["evaluator_kind"]
    batch = run_batch(
        lambda: LadderControllerStrategy(params),
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


def _evaluate_one_serial(params: LadderControllerParams, seeds: tuple[int, ...], evaluator_kind: str) -> dict:
    batch = run_batch(
        lambda: LadderControllerStrategy(params),
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


def _evaluate_ff(seeds: tuple[int, ...], evaluator_kind: str) -> dict:
    batch = run_batch(
        lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
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


def _vec_to_param_dict(vec: np.ndarray) -> dict[str, float]:
    return {n: float(v) for n, v in zip(_names(), vec)}


def main() -> None:
    LOGFILE.open("w").close()
    rng = np.random.default_rng(RNG_SEED)
    names = _names()
    lows, highs = _bounds()
    mean, std = _initial_mean_std()
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    _log(
        f"M4 cycle-20 ladder-family CEM repro | dim={len(names)} | "
        f"pop={POPULATION} gen={GENERATIONS} elite_n={elite_n} "
        f"init_std_inh={INIT_STD_FRAC_INHERITED} init_std_new={INIT_STD_FRAC_NEW} "
        f"workers={MAX_WORKERS} RNG_SEED={RNG_SEED}"
    )

    # Anchor (extended c11_long). MUST match cycle-19 anchor val numbers
    # exactly (deterministic, same warm-start params, same VAL_SEEDS).
    anchor_params = LadderControllerParams(**_vec_to_param_dict(mean)).normalized()
    t0 = time.time()
    anchor_val = _evaluate_one_serial(anchor_params, VAL_SEEDS, EVALUATOR_KIND)
    _log(
        f"  anchor_ladder val ({EVALUATOR_KIND}, n={len(VAL_SEEDS)}): "
        f"score={anchor_val['score']:+7.3f} "
        f"adv={anchor_val['edge_advantage_mean']:+7.3f} "
        f"retail_adv={anchor_val['retail_edge_advantage_mean']:+7.3f} "
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
                "candidate_id": f"gen{gen}_c{i}",
                "params": _vec_to_param_dict(v),
                "seeds": list(SEARCH_SEEDS),
                "normalizer_fee": NORMALIZER_FEE,
                "evaluator_kind": EVALUATOR_KIND,
            }
            for i, v in enumerate(candidate_vectors)
        ]

        gen_t0 = time.time()
        results: list[dict] = []
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(_evaluate_one_candidate, p) for p in payloads]
            for fut in as_completed(futures):
                results.append(fut.result())

        results.sort(key=lambda r: int(r["candidate_id"].split("_c")[1]))
        scores = np.asarray([r["score"] for r in results], dtype=float)
        elite_idx = np.argsort(-scores)[:elite_n]
        elite_vectors = np.stack([candidate_vectors[i] for i in elite_idx])
        elite_scores = scores[elite_idx]

        new_mean = elite_vectors.mean(axis=0)
        new_std = elite_vectors.std(axis=0)
        std_floor = 0.5 * std
        new_std = np.maximum(new_std, std_floor * 0.25)

        gen_record = {
            "gen": gen,
            "best_score": float(scores.max()),
            "elite_mean_score": float(elite_scores.mean()),
            "mean_score": float(scores.mean()),
            "best_params": _vec_to_param_dict(candidate_vectors[int(np.argmax(scores))]),
            "elapsed_s": float(time.time() - gen_t0),
        }
        history.append(gen_record)
        for ei in elite_idx:
            all_elites.append({"gen": gen, **results[int(ei)]})

        _log(
            f"  gen {gen}: best={scores.max():+7.3f} elite_mean={elite_scores.mean():+7.3f} "
            f"all_mean={scores.mean():+7.3f} ({gen_record['elapsed_s']:.1f}s)"
        )

        with (OUTDIR / "history.json").open("w") as f:
            json.dump(history, f, indent=2)

        mean = new_mean
        std = new_std

    _log(f"  CEM done in {time.time()-t_run:.1f}s")

    seen_keys: set[tuple[float, ...]] = set()
    rerank_pool: list[dict] = []
    anchor_dict = _vec_to_param_dict(_initial_mean_std()[0])
    rerank_pool.append(
        {
            "params": anchor_dict,
            "search_score": float("nan"),
            "source": "anchor",
        }
    )
    seen_keys.add(tuple(round(v, 9) for v in anchor_dict.values()))
    all_elites_sorted = sorted(all_elites, key=lambda x: -x["score"])
    for el in all_elites_sorted:
        key = tuple(round(v, 9) for v in el["params"].values())
        if key in seen_keys:
            continue
        rerank_pool.append(
            {
                "params": el["params"],
                "search_score": el["score"],
                "source": f"gen{el['gen']}",
            }
        )
        seen_keys.add(key)
        if len(rerank_pool) >= RERANK_TOP_K + 1:
            break

    _log(f"  rerank pool: {len(rerank_pool)} candidates (anchor + top {len(rerank_pool)-1} unique elites)")

    rerank_results: list[dict] = []
    for i, c in enumerate(rerank_pool):
        params = LadderControllerParams(**c["params"]).normalized()
        t = time.time()
        v = _evaluate_one_serial(params, VAL_SEEDS, EVALUATOR_KIND)
        rerank_results.append(
            {
                "params": c["params"],
                "search_score": c["search_score"],
                "val_score": v["score"],
                "val_edge_advantage": v["edge_advantage_mean"],
                "val_retail_advantage": v["retail_edge_advantage_mean"],
                "source": c["source"],
            }
        )
        _log(
            f"    rerank {i} ({c['source']:>10s}): val={v['score']:+7.3f} "
            f"adv={v['edge_advantage_mean']:+7.3f} retail_adv={v['retail_edge_advantage_mean']:+7.3f} "
            f"({time.time()-t:.1f}s)"
        )

    rerank_results.sort(key=lambda r: -r["val_score"])
    best = rerank_results[0]

    t_test_start = time.time()
    best_params = LadderControllerParams(**best["params"]).normalized()
    test = _evaluate_one_serial(best_params, TEST_SEEDS, EVALUATOR_KIND)
    ff_test = _evaluate_ff(TEST_SEEDS, EVALUATOR_KIND)
    lift_FF = test["score"] - ff_test["score"]
    _log(
        f"  TEST best (n={len(TEST_SEEDS)}): score={test['score']:+7.3f} "
        f"adv={test['edge_advantage_mean']:+7.3f} "
        f"retail_adv={test['retail_edge_advantage_mean']:+7.3f}"
    )
    _log(f"  FF test score: {ff_test['score']:+7.3f}")
    _log(f"  lift_FF (test): {lift_FF:+.3f}")

    # Decision-rule annotation
    if lift_FF > 3.35:
        verdict = "REPRO_BETTER"
    elif lift_FF >= 3.15:
        verdict = "REPRO_OK"
    else:
        verdict = "REPRO_FAIL"
    _log(f"  verdict ({lift_FF:+.3f} vs cycle-19 +3.251): {verdict}")

    out = {
        "rng_seed": RNG_SEED,
        "policy_family": "ladder_4bucket",
        "evaluator_kind": EVALUATOR_KIND,
        "init_strategy": "c11_long_warm_start_split_small",
        "population_size": POPULATION,
        "generations": GENERATIONS,
        "init_std_frac_inherited": INIT_STD_FRAC_INHERITED,
        "init_std_frac_new": INIT_STD_FRAC_NEW,
        "anchor_val_score": anchor_val["score"],
        "anchor_val_edge_advantage": anchor_val["edge_advantage_mean"],
        "anchor_val_retail_advantage": anchor_val["retail_edge_advantage_mean"],
        "history": history,
        "rerank": rerank_results,
        "best_by_val": {
            "params": best["params"],
            "val_score": best["val_score"],
            "val_edge_advantage": best["val_edge_advantage"],
            "val_retail_advantage": best["val_retail_advantage"],
            "source": best["source"],
            "test_score": test["score"],
            "test_edge_advantage": test["edge_advantage_mean"],
            "test_retail_advantage": test["retail_edge_advantage_mean"],
            "test_n_seeds": len(TEST_SEEDS),
            "ff_test_score": ff_test["score"],
            "lift_FF": lift_FF,
            "verdict": verdict,
        },
        "total_elapsed_s": float(time.time() - t0),
        "test_elapsed_s": float(time.time() - t_test_start),
    }
    with (OUTDIR / "test.json").open("w") as f:
        json.dump(out, f, indent=2)
    _log(f"wrote {OUTDIR / 'test.json'}")


if __name__ == "__main__":
    main()
