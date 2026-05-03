# Cycle Log

Append-only chronological record of autoresearch cycles.

---

## 2026-04-30T20:38Z — cycle 1 — bootstrap

**Plan for the cycle.** Repo had no `research/` directory. Per the
prompt's first-cycle bootstrap section: scaffold the directory tree,
skim the codebase and write up the lay of the land in `README.md`,
inspect the schema of `uniswap-labs.research.markout_prod` and run a
validation query, catalog every BigQuery table the repo already
references, and sketch the M1 plan in `STATE.md`.

**What I ran.**

- `git status` / `git log --oneline -20` — confirmed clean main with
  several uncommitted working changes (cycle 1 leaves these alone).
- Read `README.md`, `project_description.md`, `docs/project_plan.md`,
  `docs/simple_amm_math_primer.md` (top), and
  `analysis/weth_usdc_90d/REGIME_EXTRACTION.md` for the data-source
  paper trail.
- Listed and skimmed `amm_gym/sim/`, `arena_eval/exact_simple_amm/`,
  `arena_eval/diff_simple_amm/`, `arena_policies/`, `arena_search/`,
  `training/`. Total ~12k LOC across these packages.
- BigQuery: schema dump via `INFORMATION_SCHEMA.COLUMNS` on
  `markout_prod` (65 columns, partitioned by `block_date`); top
  chain/protocol breakdown for 2026-04-28 (5 chains, 37 protocols, 4.3M
  pools, 5.85M rows); pool list for ethereum + uniswap_v3 + WETH/USDC
  for the same day; canonical-pool percentile snapshot (n=3166,
  $34M USD, mean markout_next ~3.3 bps, std ~13 bps).

**What worked.**

- Schema and one-day distribution probes finished comfortably under the
  1-GB-billed limit.
- Found the canonical reference pool
  `0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640` (WETH/USDC 0.05%) — same
  pool the realistic-mode artifacts in `analysis/weth_usdc_90d/` were
  fitted from. That keeps the M1 comparison apples-to-apples.

**What failed.**

- One BigQuery query asked for a 7-day window on `markout_prod` and
  exceeded the 1-GB billed-bytes ceiling (3.6 GB needed). Workaround:
  stick to one-day scans for now; if we need a bigger sample for tail
  estimation, batch one day at a time and union client-side.

**Updates implied for the prior.**

- The realistic-mode artifacts under `analysis/weth_usdc_90d/` are
  **not** drop-in plumbed into `amm_gym/`. They are wired into
  `arena_eval/exact_simple_amm/` (the faithful evaluator) via
  `ExactSimpleAMMConfig.real_data_from_seed` and into
  `arena_eval/diff_simple_amm/realistic_dynamics.py` via
  `build_realistic_tape`. The instructions in
  `REGIME_EXTRACTION.md` §5 about replacing
  `amm_gym/sim/price.py::GBMPriceProcess` are aspirational, not done.
- This means M1 "validate the realistic simulator" should run the
  **exact** simulator with `evaluator_kind='real_data'`, not the
  `amm_gym/` env. Updated the cycle 2 plan in `STATE.md`
  accordingly.

**Next.**

- Cycle 2: per `STATE.md`, run the realistic simulator end-to-end with
  fixed-fee strategies on both venues, dump every router-retail trade
  with markout, and overlay against the BQ percentile snapshot.

**Operational footnotes.**

- Encountered a stale `.git/index.lock` (host filesystem refused
  `unlink` due to FUSE-mount permissions; `mv` worked, so the recovery
  pattern is `mv .git/index.lock .git/index.lock.bak` before retrying).
- Author identity was unset in the sandbox; used per-commit env vars
  (`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`,
  `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`) rather than touching
  `git config` (the prompt's guardrail forbids modifying it).
- `git push origin main` failed: no SSH key in sandbox + DNS to
  `github.com` is blocked. Documented as a user blocker in
  `STATE.md`. Local commit `d6482f4` sits on `main`.

---

## 2026-04-30T21:10Z — cycle 1.5 — host-side ops fixes (out-of-band)

Not a research cycle — between cycle 1 and cycle 2 the user ran a
host-side agent that resolved both blockers cycle 1 surfaced.

- The cycle 1 commits (`d6482f4`, `01afdb6`) were pushed to `origin/main`
  from the host.
- A launchd agent (`~/Library/LaunchAgents/com.xinwan.amm-gym-push.plist`)
  now runs every 15 min on the host and pushes `origin main`. The
  sandbox no longer needs to push.
- Stale `.git/*.lock*` files and orphaned `.git/objects/**/tmp_obj_*`
  cleaned; `git gc --prune=now` ran clean on the host.
- `scripts/git_unstick.sh` (host-authored) wired into
  `AUTORESEARCH_PROMPT.md` step 1 so every future cycle starts with
  the stale-lock sweep.
- Local git identity set to `amm-gym-autoresearch /
  autoresearch@amm-gym.local`; future commits no longer need env-var
  injection.
- The investigation of the FUSE-mount config that denies `unlink` was
  skipped — the mount is internal to the Cowork sandbox container and
  not visible from the host. The preflight script is the equilibrium.

Host-side ops commit: `b96f489`. Updated `STATE.md` to clear the user
blocker and document the new push topology.

---

## 2026-05-01T00:45Z — cycle 2 — M1 baseline markout

**Plan for the cycle.** Per cycle-1's STATE.md: build
`research/experiments/2026-04-30-2240-m1-baseline-markout/`, run the
realistic exact simulator with a fixed-fee strategy on multiple seeds,
dump every retail trade with markout_now and markout_next, pull a
200-bin quantile reference from `markout_prod` for the canonical pool,
and overlay a CDF + percentile table. Update presentation with the M1
section.

Hypothesis going in (recorded in cycle-1 STATE): body matches within a
few bps; tails might be off; mean should be biased LP-positive because
sim has no MEV competition.

**What I ran.**

- Smoke-tested one seed of `ExactSimpleAMMConfig.real_data_from_seed(0)`
  with `FixedFeeStrategy(bid=ask=5e-4)` — 0.3 s for 10k steps,
  generates ~12k trades / seed (~5k retail). Cheap.
- Built `scripts/run_sim_markouts.py`: 32 seeds × 10k steps, dumps
  per-trade parquet (372k rows, 165k of which are retail).
- Built `scripts/build_overlay.py`: turns parquet + BQ quantile JSON
  into `comparison_table.json` and `figures/markout_cdf_overlay.png`.
- BQ pulls: per-day stats for canonical pool 4-25..4-29 (5 days), and
  one 200-bin `APPROX_QUANTILES` dump for 4-27 (small enough under the
  1 GB ceiling with `ABS(markout_next) < 0.05` filter to suppress
  benchmark glitches).
- Wrote experiment README (`research/experiments/2026-04-30-2240-m1-baseline-markout/README.md`).
- Updated `presentation/index.html` with the M1 section, headline
  insight, side-by-side table, CDF figure, and cycle-3 plan.

**What worked.**

- Sim-vs-chain shape match is striking: both unimodal, right-skewed,
  comparable interquartile widths. The simulator's price + retail
  fitting is in good shape.
- Mean shift is **+2.74 bps** (sim retail markout_next +5.80 vs
  on-chain +3.06 on 4-27); standard-deviation match for `markout_now`
  is essentially perfect (5.80 vs 5.23 bps).
- BQ tool-result file workaround for >100KB outputs (cp from
  `/sessions/.../tool-results/` into the experiment dir) — works
  smoothly, no need to re-query.

**What failed.**

- 7-day union of `markout_prod` exceeded the 1 GB billed-bytes ceiling
  (3.5 GB needed). Workaround: 1-day-at-a-time pulls + client-side
  merge, deferred to cycle 3.
- A raw per-row pull of one day (with `ABS<0.05` filter, n=4,293)
  exceeded the MCP tool's token budget — but the auto-saved
  tool-results file is fine to `cp` over.

**Updates implied for the prior.**

- I expected only the *tails* to be biased. Reality: the *whole CDF*
  is shifted by an approximately constant ~2-3 bps between p25 and p75.
  That's a stronger and more useful claim — it points to one missing
  mechanism, not many small ones. Updated cycle-3 hypothesis is "this
  is MEV / fast-CEX adverse selection," which has a clean falsification
  test: filter on-chain to router-originated swaps (which strip the
  MEV contribution) and see whether the shift collapses.

**Next.**

- Cycle 3: per `STATE.md`,
  (a) re-pull on-chain reference filtered to router swaps,
  (b) sanity-check by running 32 fresh seeds and confirming the +2.74
      bps shift reproduces,
  (c) stitch a 5-7 day reference for tighter tail comparison.
- If M1 closes cleanly in cycle 3, M2 begins in cycle 4.

**Operational footnotes.**

- Repo mount this cycle is `/sessions/bold-eloquent-babbage/mnt/amm-gym-auto-research`
  (cycle 1 was on `happy-fervent-wright`); confirmed with `pwd` and
  `git remote -v`. Always confirm.
- `git pull --ff-only origin main` fails inside the sandbox because
  github.com DNS is blocked; that's expected per the cycle-1 ops fix
  — the launchd agent on the host pushes outgoing commits.
- Installed `pyarrow` into `.venv` (needed for parquet writes); not
  added to repo `requirements.txt` because no `arena_*` package
  imports it.
- Inherited working-tree changes left untouched, as in cycle 1.

---

## 2026-05-03T11:00Z — cycle 4 — router-filter executed, MEV-shift hypothesis falsified

**Plan for the cycle.** Per cycle-3's STATE: probe BigQuery; if it's back
up, run the router-filtered on-chain pull (cycle-3 carry-over) and
multi-day stitch. If router-filtered mean is ~+5 bps the cycle-3
"routers strip MEV" hypothesis is confirmed and M1 closes; if not,
update prior and rethink.

**Hypothesis going in.** Cycle-3 expectation: filtering on-chain to
router-originated swaps should strip the MEV-paying tail and shift the
mean from +3.06 bps up toward sim's +5.79 bps. Falsification would be
either (a) router-filtered mean stays low, or (b) it goes even lower.

**What I ran.**

- Probed BQ with `SELECT 1` — responsive this cycle.
- Tried the cycle-3 SQL template (JOIN markout_prod × dex_trades on
  transaction_hash). Failed: 1.06 GB billed-bytes vs 1 GB ceiling. Even
  with quarter-day block_number windows, still over (clustering on
  block_number doesn't prune partition reads in this case, because the
  IN-subquery forces a transaction_hash scan).
- Inspected markout_prod's column list via INFORMATION_SCHEMA. **Key
  finding**: `transaction_to_address` is already a column on
  markout_prod. The JOIN against dex_trades was unnecessary all along.
- Direct router filter: `LOWER(transaction_to_address) IN
  UNNEST(router_list)` on markout_prod. ~300 MB billed per day, fits
  comfortably.
- Pulled the canonical-day (4-27) breakdown (router/non-router/all
  means + std + total_usd) and 100-bucket APPROX_QUANTILES for both
  groups.
- Pulled per-day breakdowns for 4-25..4-29 (5 days, sequentially because
  the 5-day union exceeded the 1 GB ceiling at 3.7 GB).
- Built `figures/router_cdf_overlay.png` (CDF: sim, ALL, ROUTER,
  NON-ROUTER) and `figures/per_day_means.png` (per-day bar chart with
  sim baseline as reference line).
- Wrote experiment README at
  `research/experiments/2026-05-03-cycle4-router-confirmed/README.md`.
- Updated `presentation/index.html` with the cycle-4 section, including
  the falsification result, the implication for M1, and the cycle-5
  carry-overs.

**What worked.**

- The `transaction_to_address` discovery was the unlock; will save
  every future router-filter query from JOIN gymnastics. Documented in
  the experiment README as a reusable pattern; cycle 5 should put it
  in `research/notes/data_sources.md`.
- All 5 days pulled and processed in under ~15 minutes of BQ time.
- CDF figure cleanly shows the 4-way separation; per-day chart
  establishes day-to-day robustness.

**What failed.**

- 5-day union query (3.7 GB) blew the ceiling. Mitigation: 1-day
  pulls + client-side merge.
- The cycle-3 SQL template is now obsolete. Keep it for historical
  reference but stop using it.

**Updates implied for the prior.**

- The cycle-3 hypothesis is **falsified**. Routers carry MORE adverse
  selection on the pool side, not less. Router 5-day weighted mean =
  +0.82 bps; non-router = +4.25 bps; all = +3.45 bps; sim = +5.79.
  Gap to apples-to-apples (router) reference is ~5 bps, not ~2.7 bps.
- The mechanism is now sharper: the simulator's empirical retail-impact
  distribution captures impact-magnitude on routed flow but not
  informedness (correlation between trade direction and short-term
  Binance drift).
- M1 deliverable is restated: "shape matches; level over-credits LP by
  ~5 bps on apples-to-apples (router-only) reference; cause is the
  fitted impact distribution being directionally uniform when reality
  is direction-correlated." Cleaner, more useful conclusion.
- The cycle-2 +2.74 bps headline averaged the heavily-adverse-selected
  router flow with cleaner non-router flow — it underestimated the
  structural gap by ~2x.

**Next.**

- Cycle 5: cleanup (retire cycle-3 SQL template; update data_sources
  notes). Then start M2 setup — read `arena_search/simple_amm_search.py`
  and `arena_policies/`, find the AMM challenge scoring rule, run one
  baseline.
- Cycle 5+ side-track (optional): prototype the simulator's retail
  informedness extension. If it closes the router-mean gap, ship as
  M1 calibration PR; otherwise document the residual.

**Operational footnotes.**

- Repo mount this cycle: `/sessions/clever-ecstatic-tesla/mnt/amm-gym-auto-research`
  (cycle 1: `happy-fervent-wright`; cycle 2: `bold-eloquent-babbage`;
  cycle 3: `bold-eloquent-babbage`). Always confirm with `pwd`.
- `git pull --ff-only origin main` failed inside sandbox as expected
  (DNS to github.com is blocked); host launchd agent handles outbound.
- `pyarrow` re-installed into `.venv`. Install doesn't persist across
  mounts. Cycle-5 cleanup item: pin in `requirements.txt`.
- Inherited working-tree changes left untouched, as in earlier cycles.
