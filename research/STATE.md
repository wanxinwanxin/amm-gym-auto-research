# State — current cycle

**Last updated**: 2026-04-30 (cycle 1, bootstrap)

## Active milestone

**M1 — Validate realistic simulator against on-chain markout.**

## Current sub-task

Cycle 1 finished: scaffolding created, BigQuery `markout_prod` schema
inspected, validation query run, data sources cataloged.

## Next action (cycle 2)

Run the realistic simulator end-to-end and produce its markout
distribution, then compare against the WETH/USDC 0.05% pool reference
distribution we pulled into `research/notes/data_sources.md`.

Concretely:

1. Create
   `research/experiments/2026-04-30-1800-m1-baseline-markout/` with a
   driver script that
   - instantiates `ExactSimpleAMMConfig.real_data_from_seed(seed)` for a
     handful of seeds (start with 8 seeds, scale later);
   - runs `arena_eval.exact_simple_amm.simulator.run_seed` with a
     fixed-fee 30 bps strategy on both venues so the markout we measure
     reflects pure dynamics, not policy effects;
   - logs every router-routed retail trade with `(venue, amount_y,
     pre_state[mid], post_state[mid], fair_price, markout)` so we can
     reconstruct a markout distribution comparable to the BQ table's
     `markout_next` column.
2. Compute simulator markout per trade. The simulator's exact
   counterpart of `markout_next` is the log-ratio between the
   *post-trade* fair price one block later and the executed price.
   Use the per-trade `trade_info` from the simulator and reconstruct
   the next-step `fair_price`.
3. Side-by-side percentile table and overlay CDF plot:
   simulated retail markout vs `markout_prod` filtered to
   `chain='ethereum' AND protocol='uniswap_v3' AND
   liquidity_pool_address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'`
   over the same calendar window we documented (need to pick a fixed
   1-day or 7-day reference window; the 1-day query budget is small).
4. Write up findings in
   `research/experiments/<id>/README.md` and a first M1 section in
   `research/presentation/index.html`.

## Hypothesis going into cycle 2

The realistic simulator was built to match the *price-return*
distribution from Binance and the *retail-impact* distribution from
on-chain router swaps separately. Markout combines them with the AMM
fee structure and the arb actor. **Prior**: the body of the markout
distribution (p25–p75) should match within a few bps because both
pieces are in-distribution; the tails (p1, p99) might be off if the
realistic tape under-samples high-vol regimes or if the arb model is
too aggressive vs the real on-chain arb cadence. We expect **mean
markout to be slightly more positive in the simulator than on-chain**
because the simulator has no MEV competition for retail flow.

## Blockers for user

None.

## Operational notes

- Repo path on this machine: `/sessions/happy-fervent-wright/mnt/amm-gym-auto-research`.
  (The prompt nominally says `/sessions/upbeat-practical-gauss/...`; the
  actual mount is what `pwd` shows. Always confirm with `pwd` and
  `git remote -v`.)
- The repo had **uncommitted working changes** when cycle 1 started
  (modifications across `arena_eval/`, `arena_policies/`,
  `arena_search/`, `scripts/`, `tests/`, plus several untracked files
  including `oracle.py`, `retail_recapture.py`, calibration scripts).
  Cycle 1 left those untouched and **only added files under
  `research/`** to its commit. Future cycles should follow the same
  rule unless they explicitly own a refactor.
- `.venv/` exists and should be activated for any pytest or simulator
  runs.
- BigQuery on-demand bytes-billed limit per query is **1 GB**. Multi-day
  spans on `markout_prod` are larger than that. Stick to single-day
  scans for M1 unless we batch carefully.
