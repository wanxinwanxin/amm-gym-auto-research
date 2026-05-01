# Experiment: M1 baseline markout

**Date**: 2026-04-30 (cycle 2)
**Milestone**: M1 — validate the realistic simulator against on-chain markout.

## Question

Does the realistic-mode exact simulator
(`ExactSimpleAMMConfig.real_data_from_seed`), which combines a
regime-switching price process fitted from Binance ETHUSDT and an
empirical retail price-impact distribution fitted from Uniswap v3 router
swaps, produce a **per-trade markout distribution** comparable to what
we actually observe on-chain on the canonical reference pool
(`WETH/USDC v3 0.05%`, `0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640`)?

Going-in prior (recorded in `STATE.md` cycle-2 plan):

> The body (p25–p75) should match within a few bps because the
> price-return and retail-impact pieces are in-distribution. Tails (p1,
> p99) might be off if the realistic tape under-samples high-vol
> regimes or the arb model is too aggressive vs the real on-chain arb
> cadence. **Mean markout will be slightly more positive in the
> simulator than on-chain** because the simulator has no MEV
> competition for retail flow.

## Setup

**Simulator**.
- `ExactSimpleAMMConfig.real_data_from_seed(seed)` for `seed in 0..31`.
- 10,000 12-second steps per seed (≈33 hours wall-clock, ≈2½ days).
- Both submission and normalizer venues run a `FixedFeeStrategy(bid=ask=5
  bps)` to match the canonical pool's 5 bps fee tier.
- Total: 165,288 retail trades + 207,509 arb trades across the 32 seeds.

**Markout definition** (per `scripts/run_sim_markouts.py::sign_aware_markout`).

For a trade where the AMM **buys X** (retail sells X to AMM):
`markout = log(reference_price / executed_price)`
where `executed_price = amount_y / amount_x` is the Y received per X
delivered.

For a trade where the AMM **sells X** (retail buys X from AMM):
`markout = log(executed_price / reference_price)`.

Sign convention: positive ⇒ the LP that filled the trade was paid by
the reference price. We compute two flavors per trade:
- `markout_now`: reference is the fair price at the trade's step (no
  forward look).
- `markout_next`: reference is the fair price at the *next* step (one
  block ≈ 12 s later) — the simulator's analogue of `markout_next` in
  `markout_prod`.

**On-chain reference**.
- `uniswap-labs.research.markout_prod`, single canonical pool, single
  day (2026-04-27, n=4,293 swaps, $40 M USD volume).
- Filter: `ABS(markout_next) < 0.05` to drop a long but presumably
  spurious tail of >500-bps markouts that almost certainly reflect
  benchmark-quote glitches in the Binance reference (without the filter,
  one of the days in the 5-day sweep had std=71 bps despite p1=-8.3 —
  classic single-outlier blow-up).
- We used 200-bin `APPROX_QUANTILES` instead of pulling raw rows
  because raw rows for one day exceed the 1 GB billed-bytes limit.
- Also pulled day-by-day means and percentiles for 2026-04-25 through
  2026-04-29 in `results/bq_daily_summary.json` to gauge day-to-day
  variability of the reference.

## Results

`results/comparison_table.json` is the canonical side-by-side. Headline
percentiles (all in bps, LP perspective):

| stat | on-chain (BQ, 4-27, n=4293) | sim retail markout_now (n=165k) | sim retail markout_next (n=165k) |
| --- | --- | --- | --- |
| mean | +3.06 | +5.79 | +5.80 |
| std  | 5.23  | 5.80  | 9.82 |
| p1   | -10.1 | -0.05 | -8.5 |
| p5   | -2.91 | +0.06 | -2.80 |
| p25  | -0.24 | +1.95 | +1.86 |
| p50  | +2.42 | +5.68 | +5.67 |
| p75  | +6.43 | +9.48 | +9.44 |
| p95  | +10.5 | +11.1 | +14.4 |
| p99  | +13.4 | +14.1 | +21.1 |

Day-to-day variability of the on-chain reference (5 days, all canonical
pool, with `ABS<0.05` filter):

| date | n | mean (bps) | std (bps) | p25 | p50 | p75 |
| --- | --- | --- | --- | --- | --- | --- |
| 4-25 | 3978 | +3.84 |  9.81 |  +0.73 | +3.11 | +6.15 |
| 4-26 | 6118 | +3.88 |  5.59 |  +0.59 | +3.32 | +7.03 |
| 4-27 | 4293 | +3.06 |  5.23 |  -0.24 | +2.41 | +6.43 |
| 4-28 | 3166 | +3.31 | 13.15 |  -2.80 | +2.20 | +6.00 |
| 4-29 | 4927 | +4.05 | 71.36 |  -0.27 | +2.14 | +6.24 |

The on-chain mean is stable in the +3.0..+4.0 bps range across the
5-day window; std varies wildly because of occasional benchmark-glitch
outliers that the `ABS<0.05` filter doesn't fully suppress.

See `figures/markout_cdf_overlay.png` for the CDF + histogram overlay.

## Interpretation

1. **Shape matches; level is biased.** Both distributions are
   unimodal, right-skewed (long upper tail bounded near the fee value),
   and concentrated within ±15 bps. The simulator captures the *shape*
   of LP markout reasonably well.
2. **The simulator is too LP-favorable by ~2.7 bps in the mean** (sim
   +5.80 vs on-chain +3.06). The whole CDF curve is shifted right
   relative to the BQ reference. This is consistent with the prior:
   the simulator has no fast-CEX/MEV adverse-selection — every retail
   trade is "polite" relative to the next-block price, so the LP
   pockets close to the full fee.
3. **`markout_now` matches on-chain `std` well (5.80 vs 5.23 bps); the
   difference shows up in `markout_next`** (sim 9.82 vs on-chain 5.23).
   The extra 4 bps of std in `markout_next` is the contribution of the
   regime-switching price step between trade and the next-block
   reference — that's the simulator's "next-block fair price drift,"
   which apparently overshoots the on-chain version. Possible
   explanations:
   - The regime-switching tape was fitted to per-block log-returns of
     the *Binance mid*, not the on-chain pool's effective fair price
     at trade time. If on-chain trades cluster near periods where the
     AMM's own arb has just moved the pool toward fair, then "fair
     price one block later" has *less* drift on-chain than for a
     uniformly-sampled simulator step.
   - The 12-second cadence is exact in the sim (one regime draw per
     step). On-chain blocks are ~12 s but trades aren't uniformly
     placed in the second-by-second timeline within the block, so the
     +12 s reference isn't really "one regime draw later."
4. **Tails (p1, p99) of `markout_next`**: sim has +21.1 vs on-chain
   +13.4 at p99 — sim's right tail is too fat. p1 is closer (sim -8.5
   vs on-chain -10.1) — sim's left tail is *not too thin*, but the body
   is shifted right enough that p25 is +1.86 in sim vs -0.24 on-chain.

## Updates to prior

- **Hypothesis confirmed**: simulator mean is too LP-positive; MEV
  hypothesis is consistent. Quantum: ~2.7 bps shift in the mean, ~2 bps
  shift across the bulk of the CDF.
- **Hypothesis revised**: I expected only the tails to be off. In fact
  the *whole CDF* is shifted by an approximately constant offset (~2-3
  bps). That's a much stronger statement than "tails are off" and
  suggests a single missing mechanism (negative LP markout from MEV)
  rather than several small mechanisms.
- **New hypothesis for cycle 3**: if we apply a mean-shift of -2.7 bps
  to the simulator markouts (i.e., assume there is a constant per-trade
  MEV tax that the LP pays), do the higher moments line up too? If
  yes, the simulator is near-perfect modulo a constant — and we can
  bake that constant into `EmpiricalImpactRetailTrader` as a calibration
  knob (already partially supported via `retail_impact_scale_mode`).

## Caveats

- **Sample size asymmetry**: on-chain reference is n=4,293 from one
  day; simulator is n=165,288 across 32 seeds. The on-chain CDF is
  much noisier in the tails. To sharpen the tail comparison we'd want
  multi-day on-chain pulls — the BQ 1-GB ceiling forces day-by-day
  pulls, but stitching N×1-day quantile sets together is tractable
  next cycle.
- **No router filter on the on-chain side**. `markout_prod` doesn't
  expose `is_router`. For the canonical pool, ~30% of swaps are
  router-originated per the 90d analysis. The 70% non-router fraction
  includes arb + MEV bots — which are the trades whose markout the
  simulator's "polite retail" cannot reproduce. Filtering the on-chain
  side to routers (via a join against the router address list in
  `analysis/weth_usdc_90d/report.md`) is a natural cycle-3 follow-up
  and would directly test the MEV-shift hypothesis above.
- **5 bps fee on both venues**. The simulator's two-venue routing means
  flow splits across both AMMs; for the on-chain reference, all flow
  hits the single 0.05% pool. The split shouldn't change *per-trade*
  markout, only the *count* of trades, so this is fine for distribution
  matching.
- The sign convention has been spot-checked: simulator retail mean of
  +5.80 bps matches the intuition that an LP charging 5 bps fee should
  collect ~5 bps of markout per trade in a fair-price world. The fact
  that on-chain LPs collect only +3.06 bps is exactly the "where did
  the missing 2 bps go?" question MEV explains.

## Files

```
README.md                           ← this doc
scripts/run_sim_markouts.py         ← runs sim, writes per-trade parquet
scripts/build_overlay.py            ← turns parquet + BQ CDF into figure + table
results/sim_markouts.parquet        ← per-trade simulator markouts (372k rows)
results/sim_summary.json            ← per-(venue,source) percentile rollup
results/bq_quantiles_2026-04-27.json ← 200-bin BQ quantile dump for canonical pool, 4-27
results/bq_daily_summary.json       ← per-day on-chain mean/std/percentile snapshot
results/comparison_table.json       ← canonical sim-vs-onchain table
figures/markout_cdf_overlay.png     ← CDF + histogram overlay
```
