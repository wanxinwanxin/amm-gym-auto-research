# Cycle 28 — M4 cycle 12: 5-bucket ladder long-CEM with tightened init_std on new dims

**Date**: 2026-05-06.
**Milestone**: M4.
**Predecessor**: cycle 27 (5-bucket ladder long-CEM, init_std_new=0.15) → cluster mean lift_FF +3.093 ± 0.123, n=2, −0.184 below the cycle-26 4-bucket frontier.

## Question

Is the cycle-27 5-bucket underperformance driven by excess exploration variance on the 6 new dimensions (`ultra_tiny_*`, `tiny_*`) at `init_std_frac_new=0.15`? Or is the 5-bucket family intrinsically worse than the 4-bucket on c18-s0 at long-CEM?

## Active hypothesis

> **"Cycle-27's 5-bucket underperformance is driven by excess exploration variance on the 6 new dimensions at init_std_frac_new=0.15. Tightening init_std_new to match the inherited dims' 0.05 fraction will close the 5-bucket vs 4-bucket cluster-mean gap on c18-s0."**

## Decision rule

Cycle-26 4-bucket cluster mean +3.277, ±σ 0.027. For n=2:

| outcome | both seeds | mean lift_FF | interpretation |
|--|--|--|--|
| FRONTIER_LIFTED | both > +3.28 | ≥ +3.28 | tightening lifts cluster onto frontier; cycle 29 confirms with n=3 |
| TIGHTENING_HURT | min < +3.06 | — | std=0.15 was doing useful work; std=0.05 over-restricts new-dim exploration |
| PARTIAL_OR_NO_LIFT | — | < +3.28 | family is binding constraint; cycle 29 tests compute (15g × 24p) independently |

## Method

Identical to cycle-27 driver except `INIT_STD_FRAC_NEW = 0.05` (was 0.15). Same warm-start (direct from c18-s0 piecewise), same CEM mechanics: pop=24, gen=10, elite_frac=0.2, normalizer FixedFee(0.003, 0.003), evaluator real_data, 64 search seeds, 128 val, 256 test, 6-deep rerank-by-val.

Two runs in parallel:
- A. ANCHOR_KEY=cycle18_seed0 RNG_SEED=0
- B. ANCHOR_KEY=cycle18_seed0 RNG_SEED=1

Workers per job=2; 2 jobs × 2 workers = 4 cores saturated.

## Files

- `scripts/run_ladder5_tightstd.py` — driver (cycle-27 driver with `INIT_STD_FRAC_NEW=0.05`).
- `scripts/ladder5_strategy.py` — 5-bucket ladder family (copy of cycle-27).
- `scripts/make_figures.py` — cross-seed summary + 3 figures (3-cluster bar, CEM trajectories overlaid with cycle 27, per-seed lift bars).
- `results/cycle18_seed0_seed{0,1}/{progress.log, history.json, test.json}` — per-seed CEM history + held-out test.
- `results/cross_seed_summary.json` — n>=2 mean/stddev/test scores + decision-rule verdict.
- `figures/m4_c28_anchor_lift_bar.png`, `figures/m4_c28_long_cem_val_curves.png`, `figures/m4_c28_lift_per_seed.png`.
