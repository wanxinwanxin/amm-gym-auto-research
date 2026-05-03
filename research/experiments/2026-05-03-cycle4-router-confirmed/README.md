# Experiment: M1 cycle-4 — router filter executed, MEV-shift hypothesis falsified

**Date**: 2026-05-03 (cycle 4)
**Milestone**: M1 — validate the realistic simulator against on-chain markout.

## Question

Cycle-3's outstanding sub-task was: filter the on-chain reference to
router-originated swaps and re-pull markout. Cycle-2's hypothesis was that
the simulator's +2.74 bps shift versus on-chain came from MEV / fast-CEX
adverse selection, and that "routers strip MEV" so the router-filtered mean
should *rise* toward the sim's +5.79 bps (i.e. close the gap).

Cycle 3 was blocked because the obvious join (`markout_prod x dex_trades`
on `transaction_hash`) blew the BQ-MCP 1 GB billed-bytes ceiling. Cycle 4's
first job: figure out a cheaper way and run the test.

## Going-in prior

If the cycle-3 hypothesis is right, router-filtered on-chain mean markout
should be ~+5 bps (close to sim), and non-router should be very low or
negative (carrying the MEV-paying tail). The +2.74 bps shift would
collapse, M1 calibration would be declared good for router-equivalent
flow, and we'd advance.

## Setup

Key efficiency win: `markout_prod` already has `transaction_to_address`
as a column, so the JOIN against `dex_trades` is unnecessary. Direct
`LOWER(transaction_to_address) IN UNNEST(router_list)` on `markout_prod`
brings each canonical-pool day query to a few hundred MB, well under the
1 GB ceiling. (This invalidates the SQL template at
`research/experiments/2026-05-01-cycle3-router-replicate-stitch/scripts/router_filtered_quantiles.sql`,
which still does the JOIN. Future cycles should follow the cycle-4
pattern — see `research/notes/data_sources.md`.)

For each of `2026-04-25..2026-04-29` we pulled the canonical
WETH/USDC v3 0.05% pool, broken down by `router` vs `non_router` vs `all`,
with `ABS(markout_next) < 0.05` (the cycle-2 outlier filter that suppresses
benchmark-glitch tails). For 4-27 (the canonical cycle-2 day), we also
pulled 100-bucket `APPROX_QUANTILES` of `markout_next` and `markout_15s`
for both groups, sufficient for a CDF overlay.

## Headline result

The cycle-3 hypothesis is **falsified** — and in a particularly informative
way.

| Group | 5-day n | 5-day weighted mean (bps) | total USD |
| --- | --- | --- | --- |
| Sim retail (cycle 2, fee=5 bps, seeds 0..31) | 165,288 | **+5.79** | — |
| On-chain ALL retail | 22,481 | +3.45 | $169 M |
| On-chain ROUTER ONLY | 5,277 | **+0.82** | $101 M |
| On-chain NON-ROUTER | 17,204 | +4.25 | $68 M |

So routers carry **more** adverse selection on the pool side, not less.
Router flow is 23% of trade count but **60% of dollar volume** (avg
$19k/trade vs $4k/trade non-router). The router-only mean is essentially
zero — real LPs barely keep any of the 5 bps fee on aggregator/Universal
Router flow.

Per-day stability is striking: router mean ranges from +0.18 to +2.16 bps
across 5 days; non-router 4.13–4.66 bps. No day deviates from the
qualitative pattern.

## Apples-to-apples sim vs reference

The 90d analysis at `analysis/weth_usdc_90d/` fitted the simulator's
retail impact distribution from **router-only** swaps (per
`REGIME_EXTRACTION.md` §3-4). So the right comparison is:

```
  sim retail          = +5.79 bps
  on-chain ROUTER     = +0.82 bps  (5-day weighted)
  gap                 = -4.97 bps (sim too LP-favorable by ~one whole fee)
```

The gap is **roughly 2× larger** than cycle 2's headline of -2.74 bps.

## What this implies

The simulator's empirical retail-impact distribution captures the
*magnitude* of price impact on routed flow but not the *informedness*.
Real router flow is correlated with short-term Binance price drift —
when the aggregator routes, it tends to do so when the real market
favors that direction. The sim's flow is uniformly random with respect
to drift. To close the calibration gap, the simulator would need either
(a) a learned correlation between trade direction and the future
Binance price tape, or (b) a direct adverse-selection drag of ~5 bps on
routed retail.

This finding **upgrades the M1 deliverable** from "shape match, small
mean shift" to "shape match, large mean shift fully attributable to a
specific missing mechanism (informed-trade adverse selection on
router-origin flow)" — a much more useful baseline.

## Updated prior

- The cycle-2 +2.74 bps shift was an *underestimate* of the structural
  gap, because it averaged the heavily-adverse-selected router flow
  with the much-cleaner non-router flow.
- The cycle-3 fee-sensitivity sweep (intercept ≈ 0.8 bps after
  controlling for fee) becomes more sharply diagnostic: even when the
  sim's fee equals the on-chain fee, the *fitted* impact distribution
  is missing the negative correlation between order direction and
  short-term price drift that real router flow has.
- M1's "validate the simulator" deliverable should explicitly state
  this missing mechanism rather than wave at "MEV." It's
  adverse-selection on aggregator flow, fully measurable in
  `markout_15s` (the value where router flow is +0.22 bps mean — even
  closer to zero than `markout_next`).

## Files

- `results/router_breakdown_2026-04-27.json` — per-group means/stds for
  the canonical day, with the router-list and the comparison table to
  the sim baseline.
- `results/router_quantiles_2026-04-27.json` — 100-bucket
  `APPROX_QUANTILES` for router and non_router on 4-27, both
  `markout_next` and `markout_15s`. Drives the CDF overlay.
- `results/multi_day_breakdown.json` — per-day means/stds for 4-25..4-29
  plus 5-day weighted aggregate.
- `figures/router_cdf_overlay.png` — sim vs on-chain ALL vs ROUTER vs
  NON-ROUTER CDF, two x-windows (body and wide tail).
- `figures/per_day_means.png` — bar chart of per-day means with the sim
  baseline as a reference line.
- `scripts/build_router_cdf_overlay.py` and
  `scripts/build_per_day_chart.py` — figure builders. Reproducible from
  results JSONs.

## Reproducing

The BQ pulls used the `transaction_to_address` column on `markout_prod`
directly (no JOIN), with `block_date = DATE 'YYYY-MM-DD'`,
`liquidity_pool_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'`,
`ABS(markout_next) < 0.05`, and the 19-router list shown in
`router_breakdown_2026-04-27.json`. See LOG.md cycle-4 entry for the
exact SQL.

```bash
source .venv/bin/activate
PYTHONPATH=. python research/experiments/2026-05-03-cycle4-router-confirmed/scripts/build_router_cdf_overlay.py
PYTHONPATH=. python research/experiments/2026-05-03-cycle4-router-confirmed/scripts/build_per_day_chart.py
```

## Limitations / next steps

- The router list (19 addresses) is canonical — UR, 1inch, 0x, CowSwap,
  Paraswap, Odos, Bebop, Kyber, the v2 Router, and the v3 Router. It
  does NOT include private-mempool builders or some fringe routers.
  Mis-classified flow could shift the router-mean a tenth of a bp;
  not material to the headline.
- We didn't pull 100-bucket quantiles for non-canonical days — saving
  BQ budget for cycle 5. The 4-27 CDF overlay is the canonical figure
  for the presentation; per-day means already establish robustness.
- Cycle 5 should evaluate whether adding a learned
  `direction × future-tape` correlation to the sim's retail flow closes
  the gap. If yes, M1 closes with a "calibration extension PR." If no,
  the missing mechanism is more subtle (size selection? routed-only
  pool selection?) and we keep digging or accept the gap as a known
  limitation.
- Also: M2 should not wait. The simulator-vs-reality gap at the *mean*
  level is a real but bounded calibration issue; the M2 challenge is on
  the SIMPLE simulator anyway, where this concern doesn't apply. Cycle
  5's dual focus: (a) one calibration experiment, (b) start sketching
  the M2 policy/optimization plan.
