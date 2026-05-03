# Data Sources

Every external data source the repo and this research project depend on.
Update this file whenever a new BigQuery table, CSV, or fitted artifact
is adopted.

---

## 1. On-chain markout reference (M1 ground truth)

- **Table**: `uniswap-labs.research.markout_prod`
- **Use**: ground-truth markout distribution for **M1** validation of
  the realistic simulator.
- **Partitioning**: `block_date` (DATE) — required filter; on-demand
  queries hit the 1 GB billed-bytes ceiling for >2 days, so plan to
  scan **one day at a time** and aggregate client-side if a longer
  window is needed.
- **Coverage on 2026-04-28**: 5,854,563 rows; 5 chains
  (`bsc`, `base`, `ethereum`, `arbitrum`, `unichain`); 37 protocols;
  42,908 pools.
- **Schema (key columns)** — full schema dumped to
  `research/notes/markout_prod_schema.txt` if needed:
  - `chain` (string), `project` (string), `protocol` (string)
  - `block_date` (DATE, partition), `block_timestamp`,
    `block_number`, `transaction_hash`, `log_index`, `unique_id`
  - `liquidity_pool_address` (string), `fee` (string, in BPS-like
    scale; `'500'` = 0.05%, `'100'` = 0.01%, `'3000'` = 0.30%)
  - `token_sold_symbol` / `token_bought_symbol` (and `*_address`,
    `*_decimals`, `*_amount`, `*_amount_raw`)
  - `usd_sold_amount`, `usd_bought_amount`, `usd_amount`
  - `transaction_fees_usd`, `swap_count`
  - **Markout columns** (these are what M1 hinges on):
    - `executed_price_with_binance` (FLOAT64) — executed price using
      Binance reference
    - `benchmark` (FLOAT64), `15s_benchmark` (FLOAT64) — Binance mid
      benchmarks at the trade and at +15s
    - `receive_midprice`, `sell_midprice` — Binance top-of-book mid at
      trade time
    - `15s_receive_midprice`, `15s_sell_midprice` — at +15s
    - `markout_next`, `markout_15s` — log-return markout at next block
      / +15s
    - `markout_next_dollar`, `markout_15s_dollar` — dollar-denominated
      markout
    - `*_orderbook_time_diff` — diagnostic on how stale the Binance
      reference quote was relative to the on-chain trade

### Canonical M1 reference pool

WETH/USDC 0.05% on Ethereum: `0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640`.
This is the same pool the simulator's realistic-mode artifacts under
`analysis/weth_usdc_90d/` were fitted from, which keeps the comparison
apples-to-apples.

Snapshot for 2026-04-28 (n=3166 swaps, $34M total USD):

| metric | value |
| --- | --- |
| `markout_next` mean | +3.31 bps |
| `markout_next` std  | 13.15 bps |
| `markout_next` p1   | -73.5 bps |
| `markout_next` p5   | -24.5 bps |
| `markout_next` p25  | -2.8 bps |
| `markout_next` p50  | +2.2 bps |
| `markout_next` p75  | +6.0 bps |
| `markout_next` p95  | +10.1 bps |
| `markout_next` p99  | +14.1 bps |
| `markout_15s` mean  | +3.10 bps |
| `markout_15s` std   | 13.49 bps |

Sign convention (verify in cycle 2): `markout_next` is the log-return
between the next-block reference mid and the executed price, oriented
so positive values mean the LP that filled the trade gets paid by the
next-block fair price. Mean is positive on this pool because LPs charge
a fee and the fee component dominates the systematic adverse-selection
component on the median trade.

### Standard filter for M1

```sql
WHERE block_date = DATE 'YYYY-MM-DD'
  AND chain = 'ethereum'
  AND protocol = 'uniswap_v3'
  AND liquidity_pool_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
```

### Router-filtering markout_prod (resolved cycle 4)

**Pattern of record**: filter directly with
`LOWER(transaction_to_address) IN UNNEST(router_list)` on
`markout_prod`. The column is a built-in on the table (cycle-1 schema
notes missed it; confirmed via `INFORMATION_SCHEMA.COLUMNS` in cycle 4).
**No JOIN** against `dex_trades` is required — and the JOIN form
(template lives at
`research/experiments/2026-05-01-cycle3-router-replicate-stitch/scripts/router_filtered_quantiles.sql`,
**now obsolete**) blew the 1 GB billed-bytes ceiling because it forced
a transaction_hash scan on the full day partition.

Working query (per-day, single canonical pool, ~300 MB billed):

```sql
SELECT COUNT(*), AVG(markout_next)*1e4 AS mean_bps_next, ...
FROM `uniswap-labs.research.markout_prod`
WHERE block_date = DATE 'YYYY-MM-DD'
  AND chain = 'ethereum'
  AND protocol = 'uniswap_v3'
  AND liquidity_pool_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
  AND ABS(markout_next) < 0.05
  AND LOWER(transaction_to_address) IN UNNEST([
    -- 19-router list, see
    -- research/experiments/2026-05-03-cycle4-router-confirmed/results/router_breakdown_2026-04-27.json
    '0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b', ...
  ]);
```

Multi-day pulls: do **one day per query**. The 5-day union exceeded
the ceiling at 3.7 GB billed.

Open follow-up: whether the simulator should be compared to the
ROUTER-only on-chain reference (currently the sim's empirical impact
distribution was fitted from router-only swaps per
`analysis/weth_usdc_90d/`, so router-only is the apples-to-apples
reference). Cycle-4 finding: doing this lifts the gap from -2.74 bps
(vs all-flow) to -4.97 bps (vs router-only).

---

## 2. Realistic-mode price returns (already used in repo)

- **Table**: `uniswap-labs.cex.binance_book_snapshot_5_ETHUSDT`
- **Use**: top-of-book mid price for ETHUSDT; used to fit per-regime
  log-return distributions and the regime transition matrix at
  12-second cadence.
- **Window**: 2023-11-07 through 2025-11-06 (2 years).
- **Source-of-truth pipeline**:
  `analysis/weth_usdc_90d/sql/regime_distributions.sql` and
  `analysis/weth_usdc_90d/sql/regime_transitions.sql`.
- **Fitted artifacts (committed to repo)**:
  - `analysis/weth_usdc_90d/regimes_invcdf.csv` — 501×6, inverse CDF
    of 12-second log-returns per regime, in bps.
  - `analysis/weth_usdc_90d/regimes_transition_matrix.csv` — 5×5
    Markov transition matrix at the 12s step.
  - `analysis/weth_usdc_90d/regimes_summary.csv`,
    `regimes_transitions.csv`.
- **Consumers**:
  - `arena_eval/exact_simple_amm/dynamics.py::RegimeSwitchingReturnProcess`
    (loaded via `ExactSimpleAMMConfig.real_data_from_seed`).
  - `arena_eval/diff_simple_amm/realistic_dynamics.py` (loaded via
    `build_realistic_tape`).
  - **Not yet wired** into `amm_gym/sim/price.py` — see the
    aspirational plan in
    `analysis/weth_usdc_90d/REGIME_EXTRACTION.md` §5.

Documentation: full methodology in
`analysis/weth_usdc_90d/REGIME_EXTRACTION.md` (highly recommended
reading before touching realistic dynamics).

---

## 3. Realistic-mode retail order impact (already used in repo)

- **Table**: `uniswap-allium.ethereum.dex_trades`
- **Use**: extract per-router-swap log price-impact distribution for
  the WETH/USDC 0.05% pool (`0x88e6a0...5640`); used as an empirical
  CDF that the simulator samples per retail order to set order size /
  resulting price impact.
- **Window**: 90 days ending 2025-11-06.
- **Source SQL**:
  - `analysis/weth_usdc_90d/sql/pool_block_returns_router_impact.sql`
  - `analysis/weth_usdc_90d/sql/binance_90d_validation.sql`
  - `analysis/weth_usdc_90d/sql/pool_90d_validation.sql`
- **Fitted artifact**:
  `analysis/weth_usdc_90d/percentiles.csv` — 1001 rows at 0.1%
  steps, columns include `block_return_log` (block-to-block pool log
  returns) and `router_impact_log` (per-router-swap log price impact),
  both in raw log-return and bps.
- **Empirical retail arrival rate**:
  `EMPIRICAL_ROUTER_ARRIVAL_RATE = 186_085 / 645_123` ≈ **0.288 router
  swaps per block** (12s) over the 90-day window, hard-coded in
  `arena_eval/exact_simple_amm/config.py`.
- **Routers identified** (from
  `analysis/weth_usdc_90d/report.md`): Uniswap UR/SwapRouter family,
  1inch v4/v5/v6, 0x Settler/ExchangeProxy, CoW GPv2, Paraswap v5/v6,
  Kyber Aggregation v1/v2, Banana Gun, Maestro, MetaMask Swap.
- **Consumers**:
  - `arena_eval/exact_simple_amm/dynamics.py::EmpiricalImpactRetailTrader`
    via `ExactSimpleAMMConfig.real_data_from_seed`.
  - `arena_eval/diff_simple_amm/realistic_dynamics.py` via
    `build_realistic_tape`.

---

## 4. Other artifacts in the repo

| Path | What it is | When to revisit |
| --- | --- | --- |
| `analysis/weth_usdc_90d/pool_vs_binance.csv` | Side-by-side pool block returns vs Binance 12s returns over 90d. | Sanity-check the assumption that Binance ETHUSDT mid is a fair-price proxy for WETH/USDC. |
| `analysis/weth_usdc_90d/regimes_summary.csv` | Per-regime metadata (volatility bands, count, mean, percentiles). | Recompute regime weights / dwell times. |
| `analysis/weth_usdc_90d/plots/` | Pre-generated figures (CDFs, QQ plot, regime overlays). | Borrow when writing up M1 if the figures still match. |

---

## 5. Tables we have **not** yet adopted

These are mentioned in the autoresearch prompt as being available but
none are referenced in current repo code. Adopt them only when a
specific hypothesis calls for them, and add a row to this file when you
do.

- Cross-chain markout: same table, different `chain` filter.
- Other Uniswap pools at different fee tiers (`fee = '100'`, `'3000'`,
  `'10000'`) for sensitivity sweeps in M4.
- Per-protocol comparison (curve, balancer, etc.) for context if M3
  shows the realistic dynamics are too uniswap-v3-specific.
