# Experiment: M1 cycle-3 router-filter + replicate + multi-day stitch

**Date**: 2026-05-01 — 2026-05-03 (cycle 3)
**Milestone**: M1 — validate the realistic simulator against on-chain
markout. Cycle-3's three sub-tasks per `STATE.md` (cycle-2 close):

1. Router-filtered on-chain pull (falsification of the +2.74 bps
   MEV-shift hypothesis).
2. Replicate the cycle-2 baseline on a fresh seed split (sanity).
3. Stitch a 5–7 day on-chain reference for tighter percentile
   estimation.

## Status (2026-05-03 close)

| Sub-task | Status | Notes |
| --- | --- | --- |
| **(2) Replicate** | ✅ done | seeds 100..131 → retail markout_next mean = **+5.796 bps** vs cycle-2 baseline (seeds 0..31) +5.795 bps. Reproduces to 3 dp. |
| **(1) Router-filter** | ⏸ blocked on BQ | SQL is pre-built at `scripts/router_filtered_quantiles.sql`. Carry to cycle 4. |
| **(3) Multi-day stitch** | ⏸ blocked on BQ | Carry to cycle 4. |

The cycle-3 BigQuery MCP tool was unresponsive throughout the cycle
(repeated timeouts on even `SELECT 1`). To make cycle-3 productive we
ran a **fee-tier sensitivity sweep** in a separate experiment dir
(`research/experiments/2026-05-03-cycle3-fee-sensitivity/`). That sweep
provides indirect evidence the +2.74 bps gap is structural (not
fee-misspecification), because slope(retail markout vs fee) ≈ 1.0 with
a near-zero intercept.

## Replication detail

`results/seed100_replicate/sim_summary.json` is the raw output from
re-running the cycle-2 baseline on seeds 100..131:

| group | n | mean_now (bps) | mean_next (bps) | std_now | std_next |
| --- | --- | --- | --- | --- | --- |
| retail (seeds 100..131) | 166,610 | +5.780 | +5.796 | 5.62 | 8.71 |
| retail (seeds 0..31, cycle 2) | 165,288 | +5.795 | +5.795 | 5.80 | 9.82 |

Mean differences: ~0.01–0.02 bps. The +2.74 bps shift relative to
on-chain (+3.06 bps) is clearly not a 32-seed-noise artefact.

Note: the std on `markout_next` differs slightly across the two seed
splits (8.71 vs 9.82), driven by the right tail of the regime tape;
this is a higher-order effect that the multi-day BQ stitch would let
us evaluate against on-chain tail-shape, but isn't material for the
mean-shift conclusion.

## Files

- `scripts/router_filtered_quantiles.sql` — pre-built BQ template for
  the router-filtered pull. Per-day block ranges already noted at the
  bottom. To use: substitute `YYYY-MM-DD` and `MIN_BLK..MAX_BLK`,
  optionally trim the router list if any day exceeds the 1 GB billed
  ceiling.
- `results/seed100_replicate/sim_markouts.parquet` — per-trade dump
  for the replicate (~14 MB; 367k rows).
- `results/seed100_replicate/sim_summary.json` — group-by-source/venue
  rollup.

## Reproducing

```bash
source .venv/bin/activate
PYTHONPATH=. python research/experiments/2026-04-30-2240-m1-baseline-markout/scripts/run_sim_markouts.py \
  --n-seeds 32 --seed-base 100 \
  --out-dir research/experiments/2026-05-01-cycle3-router-replicate-stitch/results/seed100_replicate
```
