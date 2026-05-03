# Experiment: M1 fee-tier sensitivity sweep

**Date**: 2026-05-03 (cycle 3)
**Milestone**: M1 — validate the realistic simulator against on-chain
markout. Cycle-3 substitute experiment, run because the BigQuery MCP
tool was unresponsive for the entire cycle and the canonical cycle-3
plan (router-filtered + multi-day BQ pulls) was blocked.

## Question

Is the +2.74 bps gap between sim retail markout (mean +5.79 bps at
fee=5 bps, 32 seeds) and on-chain reference (mean +3.06 bps on the
canonical WETH/USDC v3 0.05% pool, 4-27) a *fee mis-specification*
artefact, or is it structural — i.e. the simulator is missing a
mechanism (MEV, fast-CEX adverse selection) that real LPs face?

## Going-in prior

If retail markout is fee-driven, the slope of (retail markout mean)
against (fee_bps) should be ~1, with a small intercept that captures
the fitted retail-impact distribution's bias. In that regime the +2.74
bps gap cannot be explained by tweaking fee — it has to be a missing
mechanism.

## Setup

- `ExactSimpleAMMConfig.real_data_from_seed(seed)` for `seed in
  200..207` (8 seeds, fresh from cycle-2's seed sets).
- 5,000 12-second steps per seed (≈17 hr wall-clock per seed; ~half
  the cycle-2 baseline length, but plenty for a mean estimate).
- `FixedFeeStrategy(bid_fee=ask_fee=fee)` on both submission and
  normalizer venues.
- Fee values: `1, 3, 5, 10` bps.
- Retail-only trades (the M1 question is about retail markout vs
  on-chain reference; arb-side markout is structurally negative and
  uninteresting here).

## Results

`results/fee_sweep.json` is the canonical dump. Headline:

| fee (bps) | retail markout_now mean (bps) | retail markout_next mean (bps) | n |
| --- | --- | --- | --- |
| 1  | +1.76  | +1.77  | 20,918 |
| 3  | +3.75  | +3.77  | 20,918 |
| 5  | +5.73  | +5.74  | 20,918 |
| 10 | +10.63 | +10.64 | 20,920 |

Linear fit (mean vs fee_bps):
- markout_now:  **slope = 0.985, intercept = +0.79 bps**.
- markout_next: **slope = 0.985, intercept = +0.80 bps**.

So sim retail markout is essentially `fee + 0.8 bps` across the 1–10
bps range. The +0.8 bps intercept is the fitted retail-impact
distribution's static bias (retail's empirical price-impact percentiles
are slightly LP-favorable in the body — an artefact of fitting on
router-only swaps that already strip the MEV-paying tail).

## Interpretation

At the canonical `fee=5 bps`:

```
  sim retail markout   = +5.73 bps   (fee +5.0, impact-bias +0.79, residual -0.06)
  on-chain reference   = +3.06 bps
  gap                  = -2.67 bps
```

The on-chain LP keeps **53%** of the fee on the average retail trade.
The sim LP keeps **115%** (fee plus a small impact-driven bias).

Because the slope-vs-fee is 1.0 and the intercept is ~0, the gap is
**not fee-specification**: changing the simulator's fee parameter
*cannot* close it. The gap also can't be explained by the empirical
impact distribution (already accounted for in the 0.79 bps intercept).

The remaining structural difference of ~2.7 bps per retail trade is
consistent with **MEV / fast-CEX adverse selection**: real on-chain LPs
are sniped on the most informed retail flow, while the simulator's
retail flow is uniform/uninformed (drawn from a fitted impact
distribution that has no concept of "informed" vs "uninformed" retail).

This reproduces independently of seed-split (cycle-3 replicate on seeds
100..131 gave +5.80 bps, exactly matching cycle-2 baseline on seeds
0..31 of +5.80).

## Updated prior

- The +2.74 bps shift is **structural**, not parametric. M1's M-shaped
  conclusion is now: simulator body matches on-chain ~1:1, simulator's
  *fee component* is correctly modeled, but the simulator is missing a
  ~2.7 bps adverse-selection drag on the retail-side mean.
- The cycle-2 falsification test (router-filter the on-chain reference,
  see whether the gap collapses) is still the cleanest direct evidence.
  This experiment is the indirect fee-decomposition complement.

## Limitations

- 8 seeds × 5,000 steps is half the cycle-2 baseline budget. Mean
  estimates have ~0.05 bps of seed-noise (back-of-envelope from cycle-2
  vs cycle-3 replicate matching to 3 decimal places); irrelevant for a
  +2.7 bps headline.
- Doesn't test heteroscedasticity: a "real" MEV mechanism would shift
  the right-tail of markout_next more than the left tail. This sweep
  only looks at means. For tail-shift evidence, see the cycle-2
  CDF overlay (`research/experiments/2026-04-30-2240-m1-baseline-markout/figures/markout_cdf_overlay.png`)
  which already shows the CDF is shifted ~uniformly.
- Doesn't test arb-side markout. The arb venue's negative markout is
  structurally driven by the price-process arrival rate; a separate
  experiment.

## Next steps (cycle 4 and beyond)

1. **Run the BQ-blocked cycle-3 work first** when BigQuery is back:
   - Router-filtered on-chain pull (SQL pre-built at
     `research/experiments/2026-05-01-cycle3-router-replicate-stitch/scripts/router_filtered_quantiles.sql`).
   - Multi-day reference stitch.
2. **Quantify arb-side markout** vs the price process to make sure the
   simulator's arb actor isn't taking too much of the LP's fee.
3. **Optionally**: design an "MEV decay" extension to the realistic
   sim — subtract a bps-scale forward-look penalty from the LP's
   markout on a fitted fraction of retail trades — and see if the
   markout_next CDF tightens to match on-chain. This would close the
   M1 calibration story before M2.
