"""
M4 cycle 29 — 5-bucket ladder long-CEM with TIGHTENED init_std on
new dims (init_std_frac_new=0.05) at HIGHER CEM compute (15g × 24p
vs cycle 28's 10g × 24p).

Question.
  Cycle 28 ran 5-bucket ladder long-CEM on c18-s0 at 10g × 24p with
  tightened init_std_new=0.05. Result: cluster mean lift_FF
  +3.253 ± 0.009 (n=2), 13× tighter than cycle 27 but still
  −0.024 below the cycle-26 4-bucket cluster mean +3.277 ± 0.027
  (within ~0.9σ of the 4-bucket cluster). Two interpretations
  remained open: (a) the 4-bucket is a genuine family ceiling on
  c18-s0 at 10g×24p; (b) the 5-bucket-tight family would catch up
  at higher CEM compute (the family is more capable but requires
  more compute to express).

  The cycle-28 elite-mean trajectory was still slowly rising at
  gen 9 (gen 7→8→9 deltas: +0.010, +0.008 on seed 0; pattern
  similar on seed 1). Compute-limited, not converged.

  Active hypothesis going into cycle 29:

    "At init_std_new=0.05, the 5-bucket family is variance-matched
     to the 4-bucket family on c18-s0 long-CEM. The remaining
     −0.024 cluster-mean gap is compute-bounded: at 15g×24p budget
     (1.5× compute), the 5-bucket-tight cluster will close the gap
     or exceed the 4-bucket cluster on c18-s0."

  Decision rule. Cycle-26 4-bucket cluster mean +3.277, ±σ 0.027.
  For n=2 at 15g×24p:
    * Both seeds > +3.20 AND cluster mean lift_FF > +3.28 → 15g×24p
      compute lifts the 5-bucket cluster onto/past the 4-bucket
      frontier; cycle 30 confirms with n=3 and the M4 frontier
      moves to the 5-bucket family.
    * At least one seed < +3.20 → 4-bucket is the c18-s0 ceiling
      at long-CEM; the M4 headline locks at +3.277 ± 0.027.
    * Both seeds in [+3.20, +3.28], cluster mean in (+3.253, +3.28)
      → modest compute gain, family ceiling still an open question.
      Stretch with n=3 in cycle 30.

Method.
  Identical to cycle-28 driver except GENERATIONS=15 (was 10).
  Same warm-start, same CEM mechanics: pop=24, elite_frac=0.2,
  init_std_frac_new=0.05, init_std_frac_inh=0.05, normalizer
  FixedFee(0.003, 0.003), evaluator real_data, 64 search seeds,
  128 val, 256 test, 6-deep rerank-by-val.

  Two runs in parallel:
    A. ANCHOR_KEY=cycle18_seed0 RNG_SEED=0
    B. ANCHOR_KEY=cycle18_seed0 RNG_SEED=1

  Note: distinct from cycle-28 RNG seeds because the search trajectory
  diverges after gen 9 anyway (and the seed=0/1 results in cycle 28
  are reused as a 10-gen prefix sanity check, but the cycle-29 run
  draws an independent search trajectory).

  Workers per job=2; 2 jobs * 2 workers = 4 cores.

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
from ladder5_strategy import (  # noqa: E402
    LADDER5_PARAM_RANGES,
    Ladder5ControllerParams,
    Ladder5ControllerStrategy,
)


# Piecewise anchor — identical to cycle-26 driver, repeated here for
# completeness and self-containment.
ANCHORS_PIECEWISE: dict[str, dict[str, float]] = {
    "cycle18_seed0": {
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
    },
}

ANCHOR_NOMINAL_LIFT_FF: dict[str, float] = {
    "cycle18_seed0": 3.005713888877396,
}


def _build_warmstart_ladder5(piecewise: dict[str, float]) -> dict[str, float]:
    """Warm-start a 5-bucket ladder from a 16-d piecewise anchor.

    Identity-equivalent: ultra_tiny and tiny inherit piecewise's
    small-bucket continuation/reversal; thresholds split the original
    small bucket into ultra_tiny [0, 0.25*small) + tiny [0.25*small,
    0.5*small) + small [0.5*small, small_thresh).
    """
    p = piecewise
    return {
        "base_fee": p["base_fee"],
        "base_spread": p["base_spread"],
        "signal_decay": p["signal_decay"],
        "toxicity_decay": p["toxicity_decay"],
        "ultra_tiny_trade_threshold": p["small_trade_threshold"] * 0.25,
        "tiny_trade_threshold": p["small_trade_threshold"] * 0.5,
        "small_trade_threshold": p["small_trade_threshold"],
        "large_trade_threshold": p["large_trade_threshold"],
        "continuation_ultra_tiny": p["continuation_small"],
        "continuation_tiny": p["continuation_small"],
        "continuation_small": p["continuation_small"],
        "continuation_medium": p["continuation_medium"],
        "continuation_large": p["continuation_large"],
        "reversal_ultra_tiny": p["reversal_small"],
        "reversal_tiny": p["reversal_small"],
        "reversal_small": p["reversal_small"],
        "reversal_medium": p["reversal_medium"],
        "reversal_large": p["reversal_large"],
        "continuation_to_same_side": p["continuation_to_same_side"],
        "continuation_to_cross_side": p["continuation_to_cross_side"],
        "toxicity_to_mid": p["toxicity_to_mid"],
        "toxicity_to_side": p["toxicity_to_side"],
    }


# Inherited dims = the same dims that exist in piecewise (16 of them).
# New dims = ultra_tiny_threshold + continuation_ultra_tiny +
# reversal_ultra_tiny + tiny_threshold + continuation_tiny + reversal_tiny.
# (Note: the 4-bucket ladder treats tiny_* as new vs piecewise; for
# direct 5-bucket-from-piecewise warm-start, tiny_* are also new.)
NEW_DIMS = {
    "ultra_tiny_trade_threshold",
    "continuation_ultra_tiny",
    "reversal_ultra_tiny",
    "tiny_trade_threshold",
    "continuation_tiny",
    "reversal_tiny",
}
INIT_STD_FRAC_INHERITED = 0.05
# Cycle 28 contrast: tighten new-dim init_std to match inherited
# (cycle-27 used 0.15 → cluster mean lift_FF +3.093 ± 0.123).
INIT_STD_FRAC_NEW = 0.05

EVALUATOR_KIND = "real_data"
SEARCH_SEEDS = tuple(range(0, 64))
VAL_SEEDS = tuple(range(1000, 1128))
TEST_SEEDS = tuple(range(2000, 2256))
POPULATION = 24
GENERATIONS = 15
ELITE_FRAC = 0.2
NORMALIZER_FEE = 0.003
RERANK_TOP_K = 6


def _names() -> list[str]:
    return list(LADDER5_PARAM_RANGES.keys())


def _bounds() -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows = np.asarray([LADDER5_PARAM_RANGES[n][0] for n in names], dtype=float)
    highs = np.asarray([LADDER5_PARAM_RANGES[n][1] for n in names], dtype=float)
    return lows, highs


def _initial_mean_std(piecewise_anchor: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    names = _names()
    lows, highs = _bounds()
    warm = _build_warmstart_ladder5(piecewise_anchor)
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
    from ladder5_strategy import Ladder5ControllerParams, Ladder5ControllerStrategy  # noqa
    from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa

    params = Ladder5ControllerParams(**payload["params"]).normalized()
    seeds = tuple(payload["seeds"])
    nfee = payload["normalizer_fee"]
    eval_kind = payload["evaluator_kind"]
    batch = run_batch(
        lambda: Ladder5ControllerStrategy(params),
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
    params: Ladder5ControllerParams, seeds: tuple[int, ...], evaluator_kind: str
) -> dict:
    batch = run_batch(
        lambda: Ladder5ControllerStrategy(params),
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
    anchor_key = os.environ.get("ANCHOR_KEY", "cycle18_seed0")
    rng_seed = int(os.environ.get("RNG_SEED", "0"))
    max_workers = int(os.environ.get("MAX_WORKERS", str(max(1, (os.cpu_count() or 1) - 1))))

    if anchor_key not in ANCHORS_PIECEWISE:
        raise ValueError(f"unknown ANCHOR_KEY={anchor_key}; valid: {list(ANCHORS_PIECEWISE)}")
    piecewise_anchor = ANCHORS_PIECEWISE[anchor_key]

    outdir = (
        ROOT
        / f"research/experiments/2026-05-07-cycle29-m4-5bucket-15gx24p/results/{anchor_key}_seed{rng_seed}"
    )
    outdir.mkdir(parents=True, exist_ok=True)
    logfile = outdir / "progress.log"
    # Truncate via open("w") (cycle-26 sandbox quirk: cannot unlink).
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
        f"M4 cycle-29 5-bucket-ladder TIGHTSTD LONG-CEM 15g x 24p | anchor={anchor_key} rng_seed={rng_seed} "
        f"| dim={len(names)} pop={POPULATION} gen={GENERATIONS} elite_n={elite_n} "
        f"init_std_frac_new={INIT_STD_FRAC_NEW} init_std_frac_inh={INIT_STD_FRAC_INHERITED} "
        f"workers={max_workers}"
    )
    _log(f"  anchor lift_FF nominal: {ANCHOR_NOMINAL_LIFT_FF.get(anchor_key, float('nan')):+.3f}")

    anchor_params = Ladder5ControllerParams(**_vec_to_param_dict(mean)).normalized()
    t0 = time.time()
    anchor_val = _evaluate_one_serial(anchor_params, VAL_SEEDS, EVALUATOR_KIND)
    _log(
        f"  anchor_5bucket val ({EVALUATOR_KIND}, n={len(VAL_SEEDS)}): "
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

    # Build rerank pool: anchor + top-K unique elites by search score.
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
        params = Ladder5ControllerParams(**c["params"]).normalized()
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
    best_params = Ladder5ControllerParams(**best["params"]).normalized()
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
        "policy_family": "ladder_5bucket",
        "evaluator_kind": EVALUATOR_KIND,
        "init_strategy": f"warm_start_from_{anchor_key}_piecewise_direct",
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
