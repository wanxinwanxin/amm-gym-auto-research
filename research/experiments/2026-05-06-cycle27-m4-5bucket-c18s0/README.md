# Cycle 27 — M4 cycle 11 — 5-bucket ladder long-CEM on c18-s0

## Question

Cycle 26 confirmed the c18-s0 piecewise anchor + 4-bucket ladder
long-CEM is the M4 frontier on `real_data`: n=3 mean test
+3.747, lift_FF +3.277 ± 0.027, lift over piecewise +0.271 ± 0.027.
The c18-s0 cluster is anomalously tight (σ ±0.027 vs c21-s1 ±0.066),
which gives cheap statistical power for follow-on tests.

The active cycle-27 hypothesis: **a structurally richer policy
family at long-CEM on c18-s0 multi-seed can move the M4 frontier
above +3.277 lift_FF cross-seed mean.**

## Method

Implementing the cycle-27 plan-of-record candidate (a): a 5-bucket
ladder strategy that splits the cycle-26 4-bucket's `tiny` bucket
into `ultra_tiny + tiny`. 22 dims (vs 4-bucket's 19; vs piecewise's
16). Identity warm-start directly from the c18-s0 piecewise anchor
(same convention as cycle-26's 4-bucket), so cycle-27 lift over
piecewise is apples-to-apples comparable with cycle 26 on the
same anchor.

(Author note on labelling. The cycle-26 plan-of-record called this
candidate a "6-bucket ladder (one extra small-bucket)", but the
description "split the tiny bucket from cycle-26's 4-bucket into
tiny+ultra-tiny" implies one bucket addition: 4 → 5. We follow
the description, treating the labelling as a typo. See LOG cycle 27.)

Identical CEM mechanics to cycle 23/24/25/26 (init_std_inh=0.05,
init_std_new=0.15, elite_frac=0.2, normalizer FixedFee(0.003,0.003),
evaluator `real_data`, 64 search seeds, 128 val, 256 held-out test,
RERANK_TOP_K=6 plus the anchor) and identical long-CEM budget
(POPULATION=24, GENERATIONS=10).

Two parallel runs:
- A. ANCHOR_KEY=cycle18_seed0 RNG_SEED=0
- B. ANCHOR_KEY=cycle18_seed0 RNG_SEED=1

`workers=2` per job, 2 jobs × 2 workers = 4 cores saturated.

## Decision rules (n=2 cycle-27)

The cycle-26 c18-s0 cluster: mean lift_FF +3.277, σ ±0.027.
Frontier threshold: +3.31 (= cluster mean + 1σ). For n=2:

- **Both seeds individually > +3.31 → richer family lifts**;
  cycle 28 confirms with seed=2 (n=3).
- **At least one seed < +3.28 → richer family does NOT
  consistently help on c18-s0**; lock M4 headline at the
  4-bucket cluster mean +3.277 ± 0.027.
- **Both in [+3.28, +3.31] → borderline**; cycle 28 should run
  a 3rd seed to disambiguate.

## Files

- `scripts/ladder5_strategy.py` — 5-bucket ladder strategy class
  (22 dims, identity warm-start from piecewise verified bit-equal
  on n=8 real_data seeds).
- `scripts/run_ladder5_longcem.py` — long-CEM driver, mirrors
  cycle-26 driver `run_ladder_longcem.py`.
- `scripts/make_figures.py` — cross-seed summary + 3 figures
  (lift cluster comparison, CEM trajectories, per-seed lift).
- `results/cycle18_seed0_seed{0,1}/{progress.log, history.json,
  test.json}` — per-seed CEM history + held-out test eval.
- `results/cross_seed_summary.json` — aggregated n=2 results.
- `figures/m4_c27_anchor_lift_curve.png`,
  `figures/m4_c27_long_cem_val_curves.png`,
  `figures/m4_c27_lift_summary.png` — cycle-27 figures.
