# State — current cycle

**Last updated**: 2026-05-01 (cycle 2)

## Active milestone

**M1 — Validate realistic simulator against on-chain markout.**
First baseline comparison landed; refining and broadening it next
cycle.

## Current sub-task

Cycle 2 finished:
- Built `research/experiments/2026-04-30-2240-m1-baseline-markout/`
  with a 32-seed realistic-mode sim + per-trade markout dump
  (`results/sim_markouts.parquet`, 372k rows).
- Pulled BQ ground truth as a 200-bin quantile dump for the canonical
  WETH/USDC v3 0.05% pool on 2026-04-27, plus per-day summaries for
  4-25 through 4-29.
- Built `figures/markout_cdf_overlay.png` and a side-by-side
  `comparison_table.json`.
- Updated `presentation/index.html` with the M1 section,
  headline, table, figure, and the next-cycle plan.

**Headline finding**: the realistic simulator's per-trade markout
distribution is ~the same shape as on-chain, but **shifted right by
+2.74 bps in the mean**. Whole-CDF shift, not just tails — strongly
suggests one missing mechanism (MEV / fast-CEX adverse selection)
rather than a diffuse mismatch.

## Next action (cycle 3)

The MEV-shift hypothesis is the highest-information experiment to run
next. Three sub-tasks, in order:

1. **Filter the on-chain reference to router-originated swaps** and
   re-pull the CDF.
   - Router list lives in `analysis/weth_usdc_90d/report.md` (or
     equivalent — confirm by re-reading the file).
   - The 90d analysis already filtered to routers for impact fitting
     and got n=186,085 of 593,310 swaps (~31.4%). For a single day,
     n probably drops from ~4.3k to ~1.4k — still enough for percentile
     estimation but with noisier tails.
   - Markout_prod doesn't expose router flag directly; we'll need
     either (a) a `transaction_to_address IN (router_list)` filter or
     (b) a join against another BQ table that has the router flag.
   - **If the +2.74 bps shift collapses to <1 bps under router filter:
     hypothesis confirmed, simulator is well-calibrated for
     router-equivalent retail flow, and the M1 deliverable is solid.**
   - If the shift remains: the gap is something else (sim's empirical
     impact percentiles are themselves biased? sim's arb actor is too
     gentle? regime tape underestimates between-trade vol?). Will need
     another diagnostic.
2. **Replicate on a second seed split** (seeds 100..131, fresh) to
   confirm the +2.74 bps shift reproduces. Tiny experiment, ~30 s of
   runtime; do it before publishing M1 as "done."
3. **Stitch a 5-7 day on-chain reference** by 1-day pulls + client-side
   union of quantile sets, so the tail comparison has decent
   statistical power. Quantile-of-quantiles is approximate; preferred
   approach is to pull the per-day mean/var into the union and recompute
   percentiles via interpolation across the per-day inverse-CDFs.

If M1 closes cleanly in cycle 3, **start M2 in cycle 4** by sketching
the policy family + optimization strategy. The codebase already has
`arena_search/simple_amm_search.py` (search infra) and several policy
families under `arena_policies/` — first pass is probably "verify the
existing baselines' challenge scores, then escalate from
`piecewise_controller.py` toward more expressive families."

## Hypothesis going into cycle 3

If the +2.74 bps shift is MEV/sniping, then:
- Filtering on-chain to routers should shrink the shift toward zero.
- The shift should be robust across seeds (≤±0.3 bps across two seed
  splits of 32 seeds each).
- The right-tail overshoot in `markout_next` (sim p99 = +21.1 vs
  on-chain +13.4) should narrow when we remove the regime-tape's
  one-block-of-extra-variance — easy diagnostic: compare
  `markout_now` (no forward look) to a reconstructed "intra-block
  Binance benchmark" markout from BQ. The
  `15s_*` midprice columns in `markout_prod` are exactly this.

## Blockers for user

None. Push topology: sandbox can't push directly; host launchd agent
ships `origin/main` every 15 min. Just commit and move on.

## Operational notes

- Repo path on this machine: `/sessions/bold-eloquent-babbage/mnt/amm-gym-auto-research`
  (changed from cycle 1's `happy-fervent-wright` mount; always
  confirm with `pwd` and `git remote -v`).
- `pyarrow` was installed into `.venv` this cycle (needed for parquet
  writes). Pin it in `requirements.txt` if any of the `arena_*`
  packages start importing it directly.
- Cycle 2 left the inherited working-tree changes
  (`arena_eval/`, `arena_policies/`, `arena_search/`, `scripts/`,
  `tests/`, plus untracked `oracle.py`, `retail_recapture.py`,
  calibration scripts) **untouched**, as cycle 1 did. Future cycles
  should keep doing this unless they explicitly own a refactor.
- BigQuery on-demand bytes-billed limit per query is **1 GB**.
  Multi-day spans on `markout_prod` are larger than that. Stick to
  single-day scans for per-trade pulls; for summary stats a
  multi-day filter may also exceed when the pool sees high volume,
  so prefer day-by-day with `GROUP BY block_date`.
- BQ output >100KB exceeds the MCP tool's response token budget but
  is auto-saved to a Claude tool-results file under
  `/sessions/.../tool-results/`. We can `cp` it into the experiment
  dir without re-running the query. Used this trick for the
  200-quantile pull this cycle.
- Scripts that import the repo packages need `PYTHONPATH=.` (or to be
  run from a setup.py-installed environment); the experiment scripts
  in this cycle relied on `PYTHONPATH=.` from the repo root.
