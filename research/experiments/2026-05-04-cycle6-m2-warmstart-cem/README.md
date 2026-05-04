# Cycle 6 — M2 warm-start CEM on piecewise

**Date**: 2026-05-04
**Milestone**: M2 — optimize against the simple-AMM challenge.
**Starting line** (cycle 5): `score = 414.010` (piecewise CEM-best from
`experiments/piecewise_cem_1h_20260422.json`, replicated on test seeds
`range(2000, 2256)`).
**Target**: `score > 540`.
**Gap to close this cycle**: 126 points.

## Hypothesis

The inherited piecewise CEM ran for **14 generations × 22 population**
from a *random* initial mean (the dead-center of every parameter range)
and still showed monotone search-score improvement at the final
generation (398.91 → 409.21 across iters 0..13). That curve hadn't
plateaued. Two things should help:

1. **Warm-starting** the CEM mean at the inherited best params shifts
   the search distribution onto the high-quality manifold immediately,
   so generations 0..n are local refinement rather than slow re-discovery.
2. **Narrower initial std** (`init_std_frac = 0.10`, vs the library
   default of `0.25`) tightens the local search radius so we exploit
   rather than re-explore. The library's `cross_entropy_search` shrinks
   `std` automatically across generations — but only after the first
   generation has thrown 22 broad random shots.

The cycle-6 prior is therefore: **a 24×12 warm-start CEM should beat
the 22×14 random-init CEM by 5–25 points, but probably not enough to
clear 540 on its own.** That last 100-point gap most likely needs
either gradient ascent on `tape_smooth` from the warm-start CEM result
(cycle 7) or a switch to a richer policy / inventory shaping (cycle 8+).

## Configuration

| knob | value | source / why |
| --- | --- | --- |
| policy_family | `piecewise` | top of inherited leaderboard (414) |
| init_mean | `INHERITED_PIECEWISE_PARAMS` | `experiments/piecewise_cem_1h_20260422.json::best_test::params` |
| init_std_frac | 0.10 | tighter than library default 0.25 — exploit over explore |
| population | 24 | matches inherited 22, slightly more for diversity |
| generations | 12 | matches inherited 14, slightly fewer; budget-aware |
| elite_fraction | 0.20 | matches inherited |
| search_seeds | `range(0, 64)` | matches inherited search_seeds |
| val_seeds | `range(1000, 1128)` | half of inherited 1000:1256 to halve val cost |
| test_seeds | `range(2000, 2256)` | matches inherited test_seeds |
| normalizer | `FixedFeeStrategy(0.003, 0.003)` | matches inherited / scoring_rule.md |
| evaluator_kind | `"challenge"` | as required by M2 target |
| parallelism | `ProcessPoolExecutor(max_workers=3)` | leaves 1 of 4 cores free |
| RNG seed | 0 | reproducibility |

The first candidate of every generation is set to the current `mean`
deterministically (no noise) — so generation 0 always evaluates the
inherited best params, anchoring replication.

## Outputs

```
results/
  warmstart_cem_history.json   # per-generation best/elite/median + new
                               # mean+std + fixed-val score
  warmstart_cem_test.json      # rerank ladder of top-8 elites (by val
                               # score) + held-out test score for the
                               # best-by-val candidate
  warmstart_cem_progress.log   # streaming per-gen log (timestamps)
  run.stdout.log               # captured stdout/err of the run
```

`figures/m2_warmstart_cem.png` is built by
`scripts/build_figure.py` from the JSON outputs.

## Reproduction

```sh
source .venv/bin/activate   # or use system python3 with deps installed
python3 research/experiments/2026-05-04-cycle6-m2-warmstart-cem/scripts/run_warmstart_cem.py
python3 research/experiments/2026-05-04-cycle6-m2-warmstart-cem/scripts/build_figure.py
```

## How to interpret the result

* **Headline number**: `warmstart_cem_test.json::best_by_val::test_score`,
  evaluated on `range(2000, 2256)` — directly comparable to the cycle-5
  starting line (414.010).
* **Delta vs starting line**: same JSON, `delta_vs_starting_line`.
* **Generalization check**: compare `best_by_val::val_score` to
  `best_by_val::test_score`; a large gap suggests overfitting to val
  seeds (unlikely with 128 val × 256 test, but worth eyeballing).
* **Search-curve diagnostic**: `warmstart_cem_history.json::history[]`
  has per-generation `best_search_score`, `elite_mean_search_score`,
  `fixed_val_score`. Plot all three vs generation to see whether CEM
  is still improving at gen 12 (→ run more) or has plateaued (→ switch
  to gradient / different policy).

## Caveats / known sources of error

* **Search-seed re-use**: cycle-5's piecewise replicate showed the
  inherited best scored 414.010 on test seeds 2000:2256 but the search
  uses seeds 0:64. Different seed slices have different noise — use
  the held-out test score, not the search score, when reporting.
* **CEM stochasticity**: with `RNG_SEED=0` this run is deterministic,
  but a different seed could land in a different local optimum. M3/M4
  would call for multiple-seed reruns; for cycle 6 we report a single
  seed run and note the constraint.
* **CEM is local**: warm-start trades "explore" for "exploit". If the
  inherited best happens to be in a shallow basin and a much better
  basin lives elsewhere in piecewise-param-space, this cycle won't
  find it. Mitigation in future cycles: keep the inherited 22×14 CEM
  result on hand as the "broad-scan" reference and also try
  multi-restart warm-start with a few perturbed seed means.
