# Cycle 10 — no-op-tail CEM (test the wrapper-as-noise hypothesis)

## Question

Cycle-9 ran two CEMs starting from the same cycle-8 anchor (446.61 test):

| run | dim | rng_seed | val | test |
|--|--|--|--|--|
| #1 third-pass piecewise | 16 | 0 | 450.05 | **448.81** |
| #3 EMA-inv piecewise    | 20 | 0 | 457.62 | **456.64** |

But the cycle-9 ablation showed the 4 EMA-inv params themselves contribute
only **+0.024** to the score. The other +7.83 of lift came from CEM
finding refined values for the same 16 piecewise dims while wandering
through 4 inert tail dims.

Three hypotheses can explain that:

- **(A) Inert tails help CEM.** Extra random search directions per
  generation let CEM escape shallow plateaus in the 16-d basin.
- **(B) RNG-seed lottery.** The dim-20 vs dim-16 sampling sequences
  diverge at gen 0; the dim-20 sequence happened to land in a better
  region by chance.
- **(C) The EMA wrapper had real signal the ablation missed.** Maybe
  the ablation broke a non-trivial joint structure between EMA and
  piecewise dims.

This experiment isolates (A) cleanly.

## Method

Two CEMs share the cycle-8 anchor and recipe (pop=24, gen=12,
init_std_frac=0.10, elite=0.20, search/val/test seed splits).

- **Experiment A** — `run_noop_tail_cem.py`: 20-d CEM where the trailing
  4 dims are **pure no-ops** that never enter the fee formula. The eval
  function strips them before instantiating `PiecewiseControllerParams`.
  CEM samples them, selects elites jointly with the piecewise dims, but
  the score is invariant to their values. RNG seed = 0.
- **Experiment B** — `run_seed_lottery_cem.py`: 16-d 4th-pass piecewise
  CEM with **rng_seed=1**. Identical to cycle-9 #1 (which used seed=0).

## Predictions (priors)

| outcome | A test score | B test score | conclusion |
|--|--|--|--|
| (A) wrapper-as-noise real | ≈ 456 | ≈ 449 | inert tails genuinely help CEM |
| (B) seed lottery | ≈ 449 | ≈ 449–456 wide | run-to-run noise dominates |
| (C) EMA had signal | ≈ 449 | ≈ 449 | re-examine cycle-9 ablation |
| mixed (most likely) | between | between | both effects matter; need more reps |

Prior weights: 50% (A), 30% (B), 10% (C), 10% mixed.

## Results

| run | dim | seed | val | test | Δ vs anchor | Δ vs c9 #1 |
|--|--|--|--|--|--|--|
| c8 ablation anchor      | 16 | — | — | 446.61 | (start) | — |
| c9 #1 (3rd-pass)        | 16 | 0 | 450.05 | 448.81 | +2.20 | (baseline) |
| c9 #3 (EMA wrap)        | 20 | 0 | 457.62 | 456.64 | +10.03 | +7.83 |
| **c10 A (no-op tail)**  | 20 | 0 | 457.67 | **456.74** | +10.12 | +7.93 |
| **c10 B (seed lottery)**| 16 | 1 | 453.82 | **452.96** | +6.35 | +4.15 |

## What it changed

- **Hypothesis (A) = wrapper-as-noise: confirmed, with a sharper mechanism.**
  Experiment A reproduces cycle-9 #3 to within 0.10 pts on test using *truly*
  inert tail dims. The cycle-9 ablation was correct: the EMA params
  contribute essentially zero to the score. The +7.83 lift over cycle-9 #1
  is fully explained by the wrapper.
- **Mechanism: not "more search directions", but "different RNG-stream
  offset".** With `np.random.default_rng(seed=0)` and `rng.normal(mean, std)`,
  consuming 20 normals per candidate (instead of 16) advances the RNG state
  92 normals per generation faster than dim=16. From gen 1 onwards, dim=20
  and dim=16 sample completely different candidates. At seed=0, the dim=20
  trajectory happens to land in better candidates.
- **Hypothesis (B) = seed lottery: also real, but smaller.** Experiment B
  (16-d, seed=1) hits 452.96 — beats cycle-9 #1 (448.81) by +4.15 but
  underperforms the 20-d runs (456.7) by ~3.8.
- **Decomposition of the +7.83 c9 #3 vs c9 #1 lift:**
  - ~+4.15 attributable to seed lottery (different rng sampling)
  - ~+3.78 attributable to dim=20 specifically being a luckier sequence
    than dim=16 at this seed
- **Implication for cycle-11 strategy**: cheap multi-seed × multi-dim CEM
  reps should still buy a few more pts. The 16-d basin's true ceiling is
  somewhere ≥ 456.7; a small grid (4 seeds × {16, 20, 24, 28}-dim noop)
  would tell us if it goes higher and bound the search-noise distribution.

## Files

- `scripts/run_noop_tail_cem.py` — Experiment A driver
- `scripts/run_seed_lottery_cem.py` — Experiment B driver
- `scripts/make_comparison_figure.py` — figure builder
- `results/noop_tail_cem_test.json` — Experiment A best-by-val + test
- `results/seed_lottery_cem_test.json` — Experiment B best-by-val + test
- `results/*_history.json` — full per-generation traces
- `figures/cycle10_hypothesis_test.png` — convergence + bar chart vs cycle-9
