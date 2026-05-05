# 2026-05-05 cycle 21 — M4: multi-seed long-CEM on c11+CEM long

**Question.** Cycle-18's long-CEM (10g × 24p, piecewise, warm c11) on
real_data hit lift_FF +3.006 *at a single rng seed*. Is that +3.0 a
**budget ceiling** (would lift further with more seeds / more compute)
or a **population ceiling** (the typical seed lands near +3.0)? With 3
seeds of the identical recipe, what is the cross-seed mean and
dispersion?

**Decision rule** (combined with cycle-18 seed=0 result of +3.006):

- mean lift_FF > +3.20 → +3.0 was a budget/anchor-search-noise ceiling
- mean lift_FF in [+3.00, +3.20] → +3.0 is a population ceiling
- mean lift_FF < +3.00 → cycle-18's single-seed +3.006 was on the
  high end; the ceiling is even tighter than thought

## Method

Identical to cycle-18's `run_long_cem_from_c11.py`, parameterized by
`RNG_SEED` env var:

- Family: piecewise controller (16 params, normalized to 19-d
  controller vector)
- Warm-start: c11_d16_s2 best-by-val params (cycle-11 grid CEM, M2
  deliverable)
- Init mean = c11 params clipped to bounds; init std = 0.10 ×
  (high − low)
- Population = 24, generations = 10, elite_frac = 0.20 (elite_n = 4)
- Search seeds = range(0, 64); val seeds = range(1000, 1128);
  test seeds = range(2000, 2256)
- Normalizer = FixedFee(0.003, 0.003)
- Evaluator = real_data
- Two new seeds run: rng_seed=1, rng_seed=2 (cycle-18 already
  contributes seed=0)
- Workers per process: 2 (down from cycle-18's 3) so both seeds
  could share the 4-core sandbox in parallel; total CPU saturation
  was equivalent

Final pick: rerank pool = {c11 anchor} ∪ {top 6 unique elites by
search_score across all gens}, ranked by val_score. Test on
n=256 held-out seeds.

## Results

| seed | source pick | val_score | test_score | lift_FF | retail_adv | edge_adv |
|--:|--|--:|--:|--:|--:|--:|
| 0 (cycle 18) | gen 8 elite | 3.822 | 3.476 | **+3.006** | +3.215 | +4.925 |
| 1 (cycle 21) | gen 8 elite | 3.651 | 3.370 | **+2.900** | +3.820 | +5.189 |
| 2 (cycle 21) | gen 2 elite | 3.215 | 2.746 | **+2.275** | -3.024 | +1.267 |
| **mean ± σ (n=3)** | — | 3.563 | 3.197 | **+2.727 ± 0.322** | +1.337 ± 3.16 | +3.794 ± 1.83 |

(σ is population stddev, ddof=0.)

**Verdict: `ceiling_even_tighter`.** Cross-seed mean **+2.727** is
**below** the +3.00–+3.20 decision band. Cycle-18's single-seed
+3.006 was a +0.86σ (about top-quartile) draw above the multi-seed
mean.

## What it changes

1. **The "+3.0 lift_FF on real_data" headline that's been cited
   since cycle 18 was a single-seed positive draw, not a population
   metric.** The right number, at this CEM budget on this family
   with this warm-start, is +2.73 ± 0.32 (n=3). The +3.0 is roughly
   the 75th percentile of the seed distribution, not the median.
2. **Seed dispersion is much larger than previously thought.** At
   pop=24 × gen=10 the test lift_FF stddev across rng_seeds is
   **0.32** — about 2.5× larger than the ladder-CEM stddev seen at
   pop=12 × gen=5 in cycle 20 (±0.13). This is counter-intuitive
   (more compute usually narrows variance) and suggests the long
   trajectory occasionally locks into bad basins (seed=2 here
   collapsed at gen 6 with retail_adv -18 and never recovered).
3. **Cycle-19/20 ladder vs piecewise comparisons used cycle-18-seed-0
   as the ladder anchor — a high-end single draw of the *piecewise*
   distribution.** At face value the ladder mean +3.111 lifts only
   +0.10 over that anchor. Compared to the piecewise multi-seed
   mean +2.727, the ladder mean is +0.38 above — but this is
   confounded: the ladder is being warm-started from a high-end
   piecewise draw, not from the typical piecewise outcome. A clean
   apples-to-apples ladder-vs-piecewise comparison needs ladder
   runs warm-started from each piecewise seed, not just seed=0.
4. **All single-seed M4 comparisons in cycles 16-19 are subject to
   ±0.32 stddev on lift_FF.** Many of the apparent effects in those
   cycles (warm-start choice, compute extension, family escalation)
   are within this noise band and need re-checking with ≥3 seeds
   before being treated as effects.

## Operational notes

- Wall-clock: parallel launch at 20:28, both done by ~21:18.
  Each run = ~46 min wall (CEM 42 min + rerank 5 min + FF test
  ~75 s).
- CPU: workers=2 per run × 2 runs = 4 workers on 4 cores. Memory
  stayed under 50% headroom throughout.
- Per-gen wall: ~218 s (vs cycle-18's 150 s with workers=3).
  About 1.45× slower per gen but 2× the throughput.
- Outputs (per seed):
  - `results/seed{1,2}/history.json` — per-gen elite stats + means
  - `results/seed{1,2}/test.json` — best-by-val rerank, n=256 test
  - `results/seed{1,2}/progress.log` — wall-clock-stamped trace
- Cross-seed analysis:
  - `results/cross_seed_summary.json`
  - `figures/m4_c21_long_cem_val_curves.png`
  - `figures/m4_c21_long_cem_seed_dispersion.png`

## Cycle-22 plan-of-record

Two competing follow-ups; pick one based on cycle-22 budget:

1. **Apples-to-apples ladder-vs-piecewise.** Run ladder family CEM
   warm-started from cycle-21 seed=1 and seed=2 long-CEM bests
   (currently the ladder thread only has runs from cycle-18 seed-0).
   Decide whether ladder's +0.10 lift over its specific anchor is
   real cross-seed.
2. **Pivot to a structurally different family.** Smooth-head MLP
   replacing the bucketed continuation/reversal terms, with ≥3
   seeds from the start. The +2.7 ceiling motivates this stronger
   than the +3.0 ceiling did.

The second is more informative if the M4 hypothesis is "richer
families lift the ceiling"; the first is more informative if the
question is "did the ladder claim hold up." Both should be run
multi-seeded.
