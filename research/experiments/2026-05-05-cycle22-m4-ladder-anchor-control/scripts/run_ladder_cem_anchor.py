"""
M4 cycle 22 — apples-to-apples ladder CEM warm-started from a specific
piecewise anchor (cycle-21 seed=1 or seed=2) and rng_seed.

Question.
  Cycle-19 reported a ladder-vs-piecewise lift of +0.10 lift_FF on test,
  warm-started from cycle-18-seed-0 (which cycle 21 revealed was the
  +75th-percentile draw of the piecewise long-CEM distribution, not the
  median). Was the cycle-19 ladder lift a real cross-anchor family
  effect, or an anchor-quality artefact?

  Cycle 22 controls for anchor sampling by re-running the ladder CEM
  warm-started from each of the cycle-21 piecewise seeds, instead of
  the lucky cycle-18 seed=0 anchor. Decision rule is documented in
  cycle-22 STATE.md.

Method.
  Identical CEM mechanics to cycle 19 (5g x 12p, 19d, init_std_inh=0.05,
  init_std_new=0.15, elite_frac=0.2, normalizer FixedFee(0.003,0.003),
  evaluator real_data, 64 search seeds, 128 val, 256 test). The only
  difference is the warm-start piecewise dict and the CEM rng_seed.

Configuration (env vars):
  ANCHOR_KEY = "cycle21_seed1" | "cycle21_seed2"
  RNG_SEED   = int (default 0)
  MAX_WORKERS = int (default cpu_count - 1)

Output:
  results/{anchor_key}_seed{rng_seed}/{progress.log, history.json,
                                       test.json}
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


# Cycle-21 piecewise best-by-val params (val/test/lift):
#   seed=1: val 3.651 / test 3.370 / lift_FF +2.900 / retail_adv +3.820
#   seed=2: val 3.215 / test 2.746 / lift_FF +2.275 / retail_adv -3.024
# These come straight from the test.json best_by_val.params block.

ANCHORS_PIECEWISE: dict[str, dict[str, float]] = {
    "cycle21_seed1": {
        "base_fee": 0.0006208445535922105,
        "base_spread": 0.003436627602351996,
        "signal_decay": 0.7302888149404205,
        "toxicity_decay": 0.6311676747057064,
        "small_trade_threshold": 0.003407485039155859,
        "large_trade_threshold": 0.011984514969267026,
        "continuation_small": 6.11147060609066e-05,
        "continuation_medium": 0.007922324781625346,
        "continuation_large": 0.015605042844432974,
        "reversal_small": 0.005839846883903697,
        "reversal_medium": 0.024867266602991257,
        "reversal_large": 0.07530855148753474,
        "continuation_to_same_side": 0.20987707889979262,
        "continuation_to_cross_side": 1.5904088789069952,
        "toxicity_to_mid": 0.007631817874876309,
        "toxicity_to_side": 0.06877448555402835,
    },
    # Cycle-21 seed=2 best-by-val (gen-2 elite, post basin-collapse)
    # placeholder — fill at runtime from results/seed2/test.json
    "cycle21_seed2": None,
}

ANCHOR_NOMINAL_LIFT_FF: dict[str, float] = {
    "cycle21_seed1": 2.899545354389765,
    "cycle21_seed2": 2.275403095096121,
}


def load_seed2_params() -> dict[str, float]:
    p = (
        ROOT
        / "research/experiments/2026-05-05-cycle21-m4-longcem-multiseed/results/seed2/test.json"
    )
    d = json.load(p.open())
    return d["best_by_val"]["params"]


def _build_warmstart_ladder(piecewise: dict[str, float]) -> dict[str, float]:
    p = piecewise
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


# Match cycle-19 settings exactly.
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
RERANK_TOP_K = 6


def _names() -> list[str]:
    return list(LADDER_PARAM_RANGES.keys())


def _bounds() -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows = np.asarray([LADDER_PARAM_RANGES[n][0] for n in names], dtype=float)
    highs = np.asarray([LADDER_PARAM_RANGES[n][1] for n in names], dtype=float)
    return lows, highs


def _initial_mean_std(piecewise_anchor: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows, highs = _bounds()
    warm = _build_warmstart_ladder(piecewise_anchor)
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


def _evaluate_one_serial(
    params: LadderControllerParams, seeds: tuple[int, ...], evaluator_kind: str
) -> dict:
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


def _vec_to_param_dict(vec: np.ndarray) -> dict[str, float]:
    return {n: float(v) for n, v in zip(_names(), vec)}


def main() -> None:
    anchor_key = os.environ.get("ANCHOR_KEY", "cycle21_seed1")
    rng_seed = int(os.environ.get("RNG_SEED", "0"))
    max_workers = int(os.environ.get("MAX_WORKERS", str(max(1, (os.cpu_count() or 1) - 1))))

    if anchor_key not in ANCHORS_PIECEWISE:
        raise ValueError(f"unknown ANCHOR_KEY={anchor_key}; valid: {list(ANCHORS_PIECEWISE)}")
    if anchor_key == "cycle21_seed2":
        ANCHORS_PIECEWISE["cycle21_seed2"] = load_seed2_params()
    piecewise_anchor = ANCHORS_PIECEWISE[anchor_key]

    outdir = (
        ROOT
        / f"research/experiments/2026-05-05-cycle22-m4-ladder-anchor-control/results/{anchor_key}_seed{rng_seed}"
    )
    outdir.mkdir(parents=True, exist_ok=True)
    logfile = outdir / "progress.log"
    logfile.open("w").close()

    def _log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with logfile.open("a") as f:
            f.write(line + "\n")

    rng = np.random.default_rng(rng_seed)
    names = _names()
    lows, highs = _bounds()
    mean, std = _initial_mean_std(piecewise_anchor)
    elite_n = max(1, int(POPULATION * ELITE_FRAC))

    _log(
        f"M4 cycle-22 ladder CEM | anchor={anchor_key} rng_seed={rng_seed} "
        f"| dim={len(names)} pop={POPULATION} gen={GENERATIONS} elite_n={elite_n} "
        f"workers={max_workers}"
    )
    _log(f"  anchor lift_FF nominal: {ANCHOR_NOMINAL_LIFT_FF.get(anchor_key, float('nan')):+.3f}")

    # Anchor (extended ladder of the piecewise anchor) — must score
    # very close to the piecewise anchor (identity warm-start).
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
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
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

        with (outdir / "history.json").open("w") as f:
            json.dump(history, f, indent=2)

        mean = new_mean
        std = new_std

    _log(f"  CEM done in {time.time()-t_run:.1f}s")

    seen_keys: set[tuple[float, ...]] = set()
    rerank_pool: list[dict] = []
    anchor_dict = _vec_to_param_dict(_initial_mean_std(piecewise_anchor)[0])
    rerank_pool.append({"params": anchor_dict, "search_score": float("nan"), "source": "anchor"})
    seen_keys.add(tuple(round(v, 9) for v in anchor_dict.values()))
    all_elites_sorted = sorted(all_elites, key=lambda x: -x["score"])
    for el in all_elites_sorted:
        key = tuple(round(v, 9) for v in el["params"].values())
        if key in seen_keys:
            continue
        rerank_pool.append(
            {"params": el["params"], "search_score": el["score"], "source": f"gen{el['gen']}"}
        )
        seen_keys.add(key)
        if len(rerank_pool) >= RERANK_TOP_K + 1:
            break

    _log(f"  rerank pool: {len(rerank_pool)} candidates")

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

    out = {
        "policy_family": "ladder_4bucket",
        "evaluator_kind": EVALUATOR_KIND,
        "init_strategy": f"warm_start_from_{anchor_key}_piecewise",
        "anchor_key": anchor_key,
        "rng_seed": rng_seed,
        "anchor_nominal_lift_FF": ANCHOR_NOMINAL_LIFT_FF.get(anchor_key),
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
        },
        "total_elapsed_s": float(time.time() - t0),
        "test_elapsed_s": float(time.time() - t_test_start),
    }
    with (outdir / "test.json").open("w") as f:
        json.dump(out, f, indent=2)
    _log(f"wrote {outdir / 'test.json'}")


if __name__ == "__main__":
    main()
