# Cycle 20 — M4 cycle 4: ladder-CEM seed reproducibility check

## Question

Cycle-19 ran the 4-bucket ladder family CEM with `rng_seed=0` (single
seed) and reported test `lift_FF +3.251` — sitting in cycle-18's
[+3.20, +3.50] "marginal" decision band. Was that signal seed-stable,
or did cycle-19 catch a lucky pick?

The cycle-19 STATE plan-of-record specified a strict decision rule:

| seed-1 lift_FF | verdict |
| --- | --- |
| [+3.15, +3.35] | reproducible — cycle-19 headline holds |
| < +3.15 | cycle-19 was lucky; revisit family-escalation case |
| > +3.35 | ladder is even better than estimated |

## Method

Identical CEM mechanics, identical search/val/test seed splits to
cycle-19. Only `rng_seed` changed: 0 → 1, then 0 → 2 once seed-1 came in
under the band.

- Family: `LadderControllerStrategy` (4 size buckets, 19 dims)
- Warm-start: `c11+CEM long` params, with the new "tiny" bucket
  initialized to match the small bucket (identity warm-start; gen-0
  candidate-0 reproduces c11+CEM long behaviour exactly)
- CEM: 5 generations × 12 population, elite 20%, init_std_frac
  0.05 inherited / 0.15 new dims
- Evaluator: `real_data`
- Search seeds: `range(0, 64)` (n=64); val seeds: `range(1000, 1128)`
  (n=128); test seeds: `range(2000, 2256)` (n=256)
- FF baseline: `FixedFeeStrategy(0.003, 0.003)` on the same TEST seeds
- 7-candidate val-rerank pool (anchor + top 6 unique elites by
  search score)

Sharing the search/val/test seed splits across seeds means any score
drift is attributable to the CEM rng stream alone, not to evaluator
data drift.

## Result

### Three-seed ladder dispersion (held-out test n=256, real_data)

| rng_seed | source pick | test_score | lift_FF | retail_adv | edge_adv |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0 (cycle-19) | gen 4 elite | 3.721 | **+3.251** | +3.113 | +5.163 |
| 1 (cycle-20) | gen 4 elite | 3.546 | **+3.076** | +3.834 | +5.431 |
| 2 (cycle-20) | anchor (CEM never beat warm-start) | 3.476 | **+3.006** | +3.215 | +4.925 |

**Cross-seed ladder summary:**
- mean test lift_FF: **+3.111**
- sample stddev (n=3): **±0.126**
- range: [+3.006, +3.251] (Δ = 0.245)
- piecewise c11+CEM long anchor: +3.006 (single seed)
- ladder lift over c11_long: **+0.105** mean (within seed noise)

### Verdict per cycle-19 decision rule

- seed=1 lift_FF +3.076 < +3.15 → **REPRO_FAIL**
- seed=2 lift_FF +3.006 = c11+CEM long anchor (CEM elites never beat
  the warm-start on val) → **NULL** (no family payoff in this seed)

Cycle-19's "+3.251" was a positive tail of a distribution centered near
the c11+CEM long anchor, not a reproducible step-change. The "+0.25
incremental gain" headline reported in cycle 19 is, with three seeds,
revised to **+0.10 ± 0.13** lift_FF — a signal indistinguishable from
zero at this budget.

### Why each seed picked what it picked

- **seed=0**: gen 4 produced a candidate with val 4.030 (vs anchor
  3.885); rerank picked the gen-4 candidate; on test it scored 3.721.
- **seed=1**: gen 4 produced a candidate with val 3.930 (vs anchor
  3.885); rerank picked the gen-4 candidate; on test it scored 3.546
  (val→test drop of -0.384, larger than seed=0's -0.309).
- **seed=2**: search-side trajectory degraded — best candidates each
  gen scored *below* the anchor's search-side baseline (gen 0..4 best:
  2.901, 2.704, 2.645, 2.682, 2.721, none of which beat the anchor's
  ~2.9 on search seeds). All elite candidates also lost to the
  anchor on val (best non-anchor val: 3.716, vs anchor 3.885). Rerank
  correctly selected the anchor; test = c11+CEM long test exactly.

The seed-2 outcome is particularly informative: at this CEM budget
(5 gen × 12 pop), the optimizer is **not reliably finding any candidate
that survives the search→val→test pipeline above the warm-start**. One
in three seeds returns the anchor unchanged.

## What it changed

- **Cycle-19 verdict revised.** Cycle 19 declared the ladder family
  added +0.245 lift_FF on top of c11+CEM long. With n=3 seeds, the
  family payoff is +0.105 ± 0.126 — within seed noise. Cycle 19's
  "marginal band" verdict was correct; the *magnitude* of the gain
  it reported was a single-seed positive draw.
- **The +3.0 ceiling holds.** Cycle 18's "saturating near +3.0"
  prior, which cycle 19 partially falsified, is **re-confirmed** at
  this CEM budget: across families (piecewise c11+CEM long,
  ladder-4-bucket), across rng seeds, the mean test lift_FF on
  real_data is in [+3.0, +3.1].
- **The next experiment must control seed noise.** Any family-
  escalation experiment going forward needs ≥3 seeds *before*
  declaring a new headline. The cost is real — each ladder seed run
  is ~13 min wall-clock — but the reproducibility cost of skipping
  it (cycle 19) is bigger.
- **Single-seed CEM at this budget is high-variance.** This is
  itself a methodological finding: pop=12 × gen=5 search-CEM has
  enough rng-stream variance that the gen-4 best-on-val candidate's
  test score has stddev ~0.13 across rng_seeds — comparable to the
  family-escalation effect we're trying to measure.
- **The retail vs arb split varies wildly across seeds.** Seed=0
  (retail +3.11 / edge +5.16) vs seed=1 (retail +3.83 / edge +5.43)
  differ by +0.7 retail and +0.27 edge — *the same family at the
  same budget finds basins with very different retail/arb tradeoffs.*
  Cycle-19's "family escalation pays on the arb side, compute extension
  pays on the retail side" generalisation was overfit to a
  single-seed comparison. The relationship is not stable.

## Files

- `scripts/ladder_strategy.py` — copy of cycle-19's ladder controller
  (unchanged); kept local to keep the cycle's edits scoped.
- `scripts/run_ladder_cem_seed1.py` — seed=1 driver.
- `scripts/run_ladder_cem_seed2.py` — seed=2 driver.
- `scripts/make_figures.py` — figure builder + cross-seed summary.
- `results/ladder_cem_seed1/{history.json, test.json, progress.log}`
- `results/ladder_cem_seed2/{history.json, test.json, progress.log}`
- `results/summary.json` — cross-seed table, mean/std/min/max.
- `figures/m4_c20_seed_dispersion.png` — bar chart of lift_FF across
  3 seeds vs c11+CEM long anchor + cycle-19 reproducibility band.
- `figures/m4_c20_val_curves.png` — search-score trajectories for
  the three seeds.
