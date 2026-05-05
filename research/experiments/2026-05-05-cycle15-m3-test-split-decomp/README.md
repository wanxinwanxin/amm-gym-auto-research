# M3 cycle 2 — held-out test split + bootstrap CI + retail/arb decomposition

**Date**: 2026-05-05  
**Cycle**: 15

## Question

Cycle 14 produced the first M3 dual-curve plot but every headline
number was a single-seed val estimate (n=128, seeds 1000..1127).
Three things were left unfinished:

1. **Held-out test seeds.** The headline OOD numbers should be on a
   held-out split (2000..2255, n=256) so they aren't being driven by
   the same seeds CEM saw during search.
2. **Bootstrap confidence intervals.** Without per-seed dispersion
   numbers, we cannot tell whether c5/c6's "below FixedFee" finding
   is statistically significant or within batch noise.
3. **PnL decomposition.** The OOD score conflates retail-fee PnL and
   arb-loss PnL. To know *what* early-anchor optimization is breaking
   on real_data, we need to split the score into those components.

This cycle also adds a 9th anchor — **c10-B (rng_seed=1)** — which is
M2's "different rng seed, same recipe" cell. It's the closest thing
we have to a 2nd-chain replicate of the c11 endpoint.

## Method

`scripts/eval_dualcurve_test.py` runs 9 anchors × 4 batches each:
val seeds (1000..1127, n=128) and test seeds (2000..2255, n=256), on
both the `challenge` and `real_data` evaluators. Normalizer is
FixedFee(0.003) in all four. From the per-seed scores in each batch
we report:

- mean (the headline)
- 95% bootstrap CI (10000 resamples on the per-seed mean)
- `retail_edge_advantage_mean` = LP retail fee revenue (sub minus norm)
- `arb_loss_advantage_mean` = -(sub minus norm) of LP arb loss
  (positive = sub bled less than norm)

The decomposition uses fields that already exist on `SimulationResult`
(`retail_edge_submission/normalizer` and `arb_loss_submission/normalizer`),
so no simulator change was needed — just expose them in the eval driver.

## Results

| anchor | n_p | chal_test | chal_test_CI95 | real_test | real_test_CI95 | retail_adv | arb_adv | lift_vs_FF |
|--|--:|--:|:--:|--:|:--:|--:|--:|--:|
| FixedFee(0.003) | – | 342.83 | [336.7, 348.9] | 0.470 | [-0.08, 1.01] | – | – | (norm) |
| c5 baseline | 16 | 414.01 | [405.9, 421.9] | **-0.744** | **[-1.27, -0.23]** | -9.99 | +3.70 | **-1.215** |
| c6 warmstart | 16 | 432.75 | [424.5, 441.1] | **-0.933** | **[-1.47, -0.40]** | -9.04 | +3.01 | **-1.403** |
| c8 inv-aware | 19 | 446.44 | [437.8, 455.0] | -0.283 | [-0.85, +0.27] | -6.38 | +2.36 | -0.754 |
| c9 third-pass | 16 | 448.81 | [439.9, 457.4] | +1.397 | [+0.80, +1.97] | -1.87 | +1.89 | +0.927 |
| c9 EMA-inv | 20 | 456.64 | [448.0, 465.3] | +2.364 | [+1.78, +2.94] | +0.26 | +1.92 | +1.893 |
| c10A noop | 20 | 456.74 | [448.3, 465.5] | +2.554 | [+1.95, +3.13] | +0.91 | +1.85 | +2.084 |
| **c10B s1 (new)** | 16 | 452.96 | [444.3, 461.7] | +1.663 | [+1.09, +2.24] | -1.53 | +2.03 | +1.193 |
| c11 d16_s2 | 16 | 456.80 | [448.0, 465.7] | **+2.574** | **[+1.98, +3.16]** | +1.06 | +1.75 | **+2.104** |
| c13 longrun | 16 | 456.80 | [448.0, 465.5] | +2.574 | [+1.98, +3.15] | +1.06 | +1.75 | +2.104 |

Bold = headline / decision-relevant numbers.

### Key takeaways

1. **The early-anchor inversion is statistically significant on
   test.** c5 (lift -1.21) and c6 (lift -1.40) have 95% bootstrap CIs
   that are **fully below zero** on the held-out test split. The
   "below FixedFee" finding from cycle 14 is not val noise — it
   reproduces with confidence on n=256 unseen seeds.

2. **c11 = c13 *exactly* on test**: real_test 2.574 = 2.574, lift
   2.104 = 2.104. The recipe ceiling we identified on val replicates
   on test, and replicates *on real_data*. This is the third
   independent c11=c13 identity check (val challenge, val real_data,
   test real_data) — the cycle-13 long-run CEM truly produced the
   same parameter vector as the cycle-11 anchor.

3. **PnL decomposition cleanly localizes the failure.** Retail edge
   advantage moves monotonically (modulo rng-seed noise) from -9.99
   (c5) to +1.06 (c11). Arb loss advantage stays in a narrow band of
   +1.75 to +3.70 across the entire trajectory — the policy is *good
   at avoiding adverse selection* throughout. **The breakage of the
   early anchors on real_data is a retail-edge problem, not an
   arb-loss problem.** Specifically, c5 gives back ~10 units of
   retail edge to FixedFee — i.e., the early policy mis-prices retail
   flow on the empirical-impact distribution.

4. **c10B (rng_seed=1) replicates the OOD plateau, lower.** c10B
   real_test = +1.66 (lift +1.19) vs c10A/c11 ≈ +2.6 (lift +2.1). The
   OOD spread across rng seeds (~0.9 lift) is comparable to the
   in-distribution test spread (c11 d16_s2 = 456.80 vs c10B = 452.96
   ≈ 3.84 challenge points). The OOD trajectory is rng-sensitive in
   the *plateau region* but the *shape* (early-harmful → high-leverage
   → plateau) is not.

5. **The high-leverage segment is c8 → c9-EMA on test too** —
   challenge +10.2 → real_test +2.65 (ratio ~0.26). Same ratio cycle
   14 saw on val (~0.275). The two anchors that buy almost all of
   M2's OOD value are the inventory-aware and EMA-inventory
   piecewise variants.

## Caveats

- 9 anchors is still a small set; the rng-seed plateau spread is
  estimated from one extra cell (c10B s1) on top of c10A (s0) and
  c11 (s2). A larger rng-seed sweep at the plateau would pin down
  the variance better but is not the highest-information next step.
- The "early M2 is OOD-harmful" finding is now firmly established
  for the c5 and c6 anchors. We have not retrained from scratch with
  rng_seed=1 from the c5 starting point — that would test whether
  the *trajectory shape* (not just the endpoint) is rng-stable. Not
  done in this cycle.
- The decomposition is at the per-seed-mean level; it does not split
  by trade-size bucket or by signal regime. Doing so could further
  localize whether c5 mis-prices small/medium/large retail or
  specific market regimes — a candidate cycle-16 deliverable.

## Files

- `scripts/eval_dualcurve_test.py` — main eval driver.
- `scripts/make_figure.py` — generates `figures/m3_test_split.png`.
- `results/dualcurve_test.json` — full per-anchor metrics including
  bootstrap CIs and per-seed score arrays.
- `results/dualcurve_test.stdout` — live log of the run.
- `results/run.out` — alias of stdout.
- `figures/m3_test_split.png` — three-panel figure (challenge curve,
  real_data curve with FF reference + below-FF band, decomposition
  bars).
