-- =========================================================================
-- *** OBSOLETE — retained for historical reference only ***
--
-- Retired in cycle 5 (2026-05-03). The dex_trades JOIN below was unnecessary
-- all along: `markout_prod` already exposes `transaction_to_address` as a
-- top-level column (confirmed via INFORMATION_SCHEMA in cycle 4). Worse, in
-- practice the JOIN form blew the 1 GB billed-bytes ceiling because the
-- transaction_hash IN-subquery forced a full-day partition scan on
-- markout_prod (~1.06 GB billed even after block_number windowing).
--
-- USE INSTEAD the direct-filter pattern documented in
-- `research/notes/data_sources.md` §1 ("Router-filtering markout_prod"):
--
--   WHERE LOWER(transaction_to_address) IN UNNEST(router_list)
--
-- which bills ~300 MB/day on the canonical pool. The router list itself
-- is canonical at:
--   research/experiments/2026-05-03-cycle4-router-confirmed/results/
--     router_breakdown_2026-04-27.json
-- =========================================================================
--
-- Original cycle-3 header (kept verbatim below for context):
--
-- Router-filtered markout pull from markout_prod, joined to dex_trades router-tx-set
-- via tx_hash (no log_index because markout_prod stores log_index but dex_trades log_index
-- is row-per-swap-leg, which agrees only sometimes — we use tx-hash-only filter, which is
-- correct for "did a router originate the tx?" rather than "is this swap leg routed".
-- Run one day at a time. Set @block_date and @min_blk/@max_blk per day; bytes-billed is
-- ~0.3 GB per day, well under the 1 GB ceiling.

-- Per-day script template:
WITH router_tx AS (
  SELECT TRANSACTION_HASH AS tx_hash
  FROM `uniswap-allium.ethereum.dex_trades`
  WHERE DATE(BLOCK_TIMESTAMP) = DATE 'YYYY-MM-DD'
    AND BLOCK_NUMBER BETWEEN MIN_BLK AND MAX_BLK
    AND LIQUIDITY_POOL_ADDRESS = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
    AND LOWER(TRANSACTION_TO_ADDRESS) IN UNNEST([
      '0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b','0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad',
      '0x66a9893cc07d91d95644aedd05d03f95e1dba8af','0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45',
      '0xe592427a0aece92de3edee1f18e0157c05861564','0x7a250d5630b4cf539739df2c5dacb4c659f2488d',
      '0x1111111254fb6c44bac0bed2854e76f90643097d','0x1111111254eeb25477b68fb85ed929f73a960582',
      '0x111111125421ca6dc452d289314280a0f8842a65','0xdef1c0ded9bec7f1a1670819833240f027b25eff',
      '0x0000000000001ff3684f28c67538d4d072c22734','0x9008d19f58aabd9ed0d60971565aa8510560ab41',
      '0xdef171fe48cf0115b1d80b88dc8eab59176fee57','0x6a000f20005980200259b80c5102003040001068',
      '0x6131b5fae19ea4f9d964eac0408e4408b66337b5','0x617dee16b86534a5d792a4d7a62fb491b544111e',
      '0xbdb3ba9ffe392549e1f8658dd2630c141fdf47b6','0x51c72848c68a965f66fa7a88855f9f7784502a7f',
      '0x881d40237659c251811cec9c364ef91dc08d300c'
    ])
)
SELECT COUNT(*) AS n,
       AVG(markout_next) * 1e4 AS mean_bps_next,
       STDDEV(markout_next) * 1e4 AS std_bps_next,
       AVG(markout_15s) * 1e4 AS mean_bps_15s,
       STDDEV(markout_15s) * 1e4 AS std_bps_15s,
       SUM(usd_amount) AS total_usd,
       APPROX_QUANTILES(markout_next, 200) AS q_next,
       APPROX_QUANTILES(markout_15s, 200) AS q_15s
FROM `uniswap-labs.research.markout_prod`
WHERE block_date = DATE 'YYYY-MM-DD'
  AND chain = 'ethereum'
  AND protocol = 'uniswap_v3'
  AND liquidity_pool_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
  AND ABS(markout_next) < 0.05
  AND transaction_hash IN (SELECT tx_hash FROM router_tx);

-- Per-day block ranges used (look these up via:
--   SELECT MIN(block_number), MAX(block_number)
--   FROM `uniswap-labs.research.markout_prod`
--   WHERE block_date = DATE 'YYYY-MM-DD' AND ... pool filters)
-- 2026-04-25: 24952936..24960116 (look up if used)
-- 2026-04-26: 24960127..24967639
-- 2026-04-27: 24967647..24974824
-- 2026-04-28: 24974832..24982009
-- 2026-04-29: 24982017..24989199
