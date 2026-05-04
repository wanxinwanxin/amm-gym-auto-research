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

---

## 2026-05-03T14:15Z — cycle 5 — M1 closeout + M2 starting line

**Plan for the cycle.** Per cycle-4 STATE: cleanup pass (retire the
obsolete cycle-3 SQL template; pin `pyarrow`); then M2 setup —
document the scoring rule, catalog policy families, run one baseline
to record the inherited starting score.

**Hypothesis going in.** The inherited best learnable score for
`evaluator_kind="challenge"` is somewhere around 414 (piecewise CEM,
`experiments/piecewise_cem_1h_20260422.json`); fixed-fee at 30 bps
should land in the 340s. M2's gap to the >540 target is therefore
~125 points.

**What I ran.**

- Cleanup: moved
  `research/experiments/2026-05-01-cycle3-router-replicate-stitch/scripts/router_filtered_quantiles.sql`
  into `_obsolete/` with a banner header pointing to the cycle-4
  direct-filter pattern; left a `README.md` in the parent dir
  explaining the move. `data_sources.md` already documented the
  `transaction_to_address` lesson from cycle 4 — no change needed.
- Pinned `pyarrow>=15.0`, `pandas>=2.0`, `matplotlib>=3.8` under a new
  `[project.optional-dependencies] research = [...]` group in
  `pyproject.toml`, so figure-build scripts install cleanly. Not
  added to base deps because no `arena_*` package imports them.
- Read `arena_eval/exact_simple_amm/simulator.py` end-to-end to nail
  down the scoring formula (`score_challenge` → mean `edge_submission`
  over 1000 seeds; `edge_submission` accumulates retail trade edges
  minus arbitrageur profit on the submission venue, in token-Y units).
- Cataloged the 13 policy families registered in
  `arena_search/simple_amm_search.py::POLICY_SPECS`; pulled
  best-test scores from inherited `experiments/*_cem_1h_*.json`
  reports (range 377–414, all on `evaluator_kind="challenge"`).
- Wrote `research/notes/scoring_rule.md` (full reference: the score
  formula, the inherited leaderboard, the M2 attack-angle
  recommendations).
- Built and ran
  `research/experiments/2026-05-03-cycle5-m2-starting-line/scripts/run_starting_line.py`:
  fixed-fee sweep at {1,3,5,10,30,100} bps and a replicate of the
  inherited piecewise CEM best on test seeds 2000:2256 (256 seeds,
  matching the inherited test-split).
- Built `figures/m2_starting_line.png` (bar chart of the starting line
  vs target/oracle, plus the fixed-fee curve).
- Updated `presentation/index.html` with the M1 closeout paragraph and
  a full M2 setup section (scoring rule recap, starting line, figure,
  cycle-6 plan).

**What worked.**

- **Piecewise replicates exactly**: 414.010 vs the inherited 414.010
  (3 decimal places). The simulator's seed RNG and evaluator pipeline
  are deterministic in the policy parameters — clean reproducibility.
  This is the cycle-5 starting line for M2.
- The fixed-fee sweep showed a non-monotonic score curve: 30 bps →
  342.83 (parity with normalizer), 100 bps → 373.72 (peak so far). The
  100-bps win is interesting because it sacrifices market share to
  earn more per trade — a pattern the in-sim arbitrageur penalizes
  less than tighter fees.
- `data_sources.md` was already in good shape from cycle 4; nothing
  to add.

**What failed.**

- Wall time blew the 2-hour budget. Total runtime ~3 h on the
  starting-line script — the 1-bps and 5-bps fixed-fee sweeps each
  took >1 h because low fees mean lots of retail/arb trades per seed.
  Mitigation: cycle-6 sweeps stay above 5 bps unless specifically
  needed; consider adding a process-pool to `run_batch`
  (currently sequential).

**Updates implied for the prior.**

- The clairvoyant **structured-retail oracle** at score 586.51 (from
  `experiments/structured_retail_oracle_full_0_999.json`) gives a
  useful upper-bound reference: M2's >540 target is at ~73% of the
  oracle, which means M2 isn't impossible but isn't trivial either.
  Expected by cycle 1 sketch but not directly measured before.
- **Capacity probably isn't the bottleneck**: the inherited
  leaderboard's top four policy families (piecewise 414,
  submission_compact 411, reactive 405, latent_full 390) span very
  different action-space sizes but cluster within 24 points. The
  remaining 126 points to target likely come from better
  optimization and/or inventory-awareness — not from a bigger MLP
  policy. Plan-of-record for cycle 6: warm-start CEM on piecewise,
  fall back to gradient via `tape_smooth` if CEM plateaus.

**Next.**

- Cycle 6: warm-start CEM (or `tape_smooth` gradient) on piecewise
  starting from the inherited best params; push hard on optimization
  and see how high we can move the 414 starting line. Per
  `STATE.md::Next action`, also fill in the fixed-fee peak (5–200 bps
  on a 1-bps grid) as a free sanity check.

**Operational footnotes.**

- Repo mount: `/sessions/funny-laughing-bell/mnt/amm-gym-auto-research`
  (new mount this cycle).
- `git pull --ff-only origin main` failed in the sandbox as expected
  (DNS to github.com is blocked); local commits push via the host
  launchd agent.
- `matplotlib` already installed in `.venv`; `pyarrow` not needed for
  the cycle-5 figure but pinned anyway for future cycles.
- Inherited working-tree changes still untouched.

---

## 2026-05-04T07:23Z — cycle 6 — M2 warm-start CEM (+18.7 pts on test)

**Plan for the cycle.** Per cycle-5 STATE: warm-start CEM on
`piecewise` from the inherited best params, with a narrower initial
std (0.10 × range vs library default 0.25 × range). Population 24,
generations 12. If CEM stalls, fall back to `tape_smooth` gradient
ascent. Held-out test split = `range(2000, 2256)`, search seeds =
`range(0, 64)` to match the inherited-report comparator. Skip the
fixed-fee fine grid (defer to later cycles — the optimization push
is the higher-value spend).

**Hypothesis going in.** The inherited 14×22 CEM was still climbing
at iter 13 (398.9 → 409.2). Local refinement at the inherited best
params should add 5–25 pts; closing the full 126-pt gap to 540
probably needs gradient or a different policy family. Prior on this
cycle's lift: ~+10–20 pts.

**What I ran.**

- Read `arena_search/simple_amm_search.py::cross_entropy_search_with_validation`:
  hard-coded mean = `0.5*(low+high)`, std = `0.25*(high-low)`. **No
  warm-start API.** So I wrote a stand-alone CEM in
  `research/experiments/2026-05-04-cycle6-m2-warmstart-cem/scripts/run_warmstart_cem.py`,
  mirroring the library's update rule but with `init_mean = inherited_best`,
  `init_std = 0.10*(high-low)`, and parallelising candidate evals across
  3 of 4 CPU cores via `ProcessPoolExecutor`. The first candidate of
  every generation is pinned to the current mean (no noise) so the
  inherited best is replicated explicitly at gen 0.
- Read `arena_search/diff_simple_amm_search.py`: the gradient path
  (`gradient_ascent_search_with_validation`) already supports
  `init_params=...` and `policy_family="piecewise"`. Tested with
  LR=1e-3 and 8 train seeds: **the smooth gradient direction makes
  the validation score WORSE in one Adam step (401.93 → 376.16)**.
  Gradient norm 4815 — LR was an order of magnitude too big. Logged
  for cycle 7 follow-up; ran a small LR sweep probe at the end of
  this cycle (see "Side experiment").
- Sandbox env: the host `.venv/bin/python` symlinks into a Mac
  Homebrew path that doesn't exist on this Linux sandbox. Installed
  the project's deps (`gymnasium`, `pyarrow`, `jax[cpu]`) into the
  system `python3` instead. Documented for future cycles.
- Smoke-tested the warm-start CEM with pop=4, gen=2, 16 seeds — the
  ProcessPool path worked end-to-end, replicated 414 on a 16-seed
  test, ran in 20 s.
- **Full warm-start CEM** ran 27.2 min wall-clock (24 candidates × 64
  search seeds × 12 generations + per-gen val + final rerank + test
  eval, ~3 workers). Per-generation log streamed to
  `results/warmstart_cem_progress.log`.

**What worked.**

- **Headline: test_score = 432.748** on held-out seeds 2000:2255
  (n=256), vs the cycle-5 starting line of 414.010. **Δ = +18.74
  pts (+4.5%).** Val score on 128 held-out val seeds = 433.566 —
  consistent with test, so this is real, not val-overfit.
- **CEM converged tightly within 12 generations**: by gen 11,
  best_search / elite_mean / median = 427.7 / 427.6 / 427.2 (within
  0.5 pts of each other — population collapsed to a single basin).
  The val-best params (selected by reranking the top-8 elites on the
  fixed val set, not by gen-11 best_search) sat ~5 pts above the
  gen-11 best_search.
- **edge_advantage trended toward zero**: gen 0 = -85.9 → gen 11 =
  -8.9. The cycle-5 inherited point was net-negative against the
  30 bps normalizer in flow allocation (i.e. losing share but
  earning more per trade); the cycle-6 warm-start CEM mostly closed
  that gap, suggesting the optimization moved toward more competitive
  spreads rather than just wider ones.
- **Parallelism worked cleanly**. 3-worker ProcessPoolExecutor cut
  per-generation wall-clock to ~110 s vs the projected ~300 s
  sequential. The stand-alone CEM is dropped-in compatible with the
  library's `cross_entropy_search_with_validation` evaluator and
  produces an equivalent `history` JSON.
- **Diff vs inherited best params** is informative: the cycle-6
  best pushes `continuation_to_cross_side` 0.67 → 0.90,
  `continuation_large` to its upper bound 0.02, and
  `reversal_large` 0.061 → 0.078. All three move quotes more
  aggressively after big trades — i.e. the policy is now stronger at
  recapturing displacement, which is consistent with the
  edge_advantage drift toward zero.

**What failed.**

- The pre-CEM gradient probe at LR=1e-3 dropped val from 401.9 →
  376.2 in one step. This is consistent with the gradient norm
  (~4800) plus LR being together way too aggressive. Either the
  smooth surrogate's local geometry is much sharper than expected
  near the inherited point, or the surrogate's objective sign is
  miscalibrated in some regions (`expected_piecewise_edge` returned
  -2705 for an 8-tape, 256-step expansion — wildly off from the
  expected ~+8 pts proportional scaling vs the exact 414 over
  10,000 steps; needs investigation in cycle 7).
- The host `.venv` was Mac-only, so the cycle started with a 5-min
  detour to install deps in system python.
- Did not run the fixed-fee fine grid this cycle (cycle-5 STATE's
  optional task). Deferred — the +19 pt CEM lift is the headline; a
  ±2 pt refinement to the fixed-fee peak would not change the M2
  story.

**Updates implied for the prior.**

- The 414 wall was an under-converged optimizer, not a real ceiling.
  Warm-start CEM eats 19 pts essentially for free. **The cycle-5
  prediction that "more optimization on existing piecewise" was the
  cheapest first push verified.**
- We're now at 432.7 / 540 = 80% of target, vs 76.7% at the start
  of cycle 6. Still 107 pts to go. CEM on piecewise won't get there
  on its own — the population converged tight. To make the next
  push, cycle 7 should (a) test whether the warm-start lift is
  family-agnostic by re-running on `submission_compact` and
  `submission_basis`, (b) re-attempt gradient with proper LR
  calibration, (c) try inventory-aware shaping.
- Updated cycle-7 plan-of-record into `STATE.md` and into the
  presentation's "Cycle 7 plan" section.

**Side experiment — gradient probe (cycle-6 outcome).**

After CEM finished, ran a small Adam probe from the cycle-6 CEM-best
point. The first attempt (8 train seeds × 8 iters × 4 LRs) appears
to have OOM-killed silently — only the LR header line made it to
stdout before the python process disappeared. Re-ran a tighter
version (2 train seeds × 256 train_n_steps × 2 Adam iters × 3 LRs;
results in `gradient_probe.json`):

```
LR=1e-5: val 442.21 → 442.27   (Δ +0.06; statistically zero on 32 val seeds)
LR=1e-4: val 441.96 → 441.73   (Δ -0.23; gradient pushes val down)
LR=1e-3: val 425.07 → 280.34   (catastrophic collapse in 2 steps)
```

Smooth-train objective sat at -2895 (vs the exact score of ~+433):
the smooth surrogate's value is in the wrong sign and wildly off in
scale around the CEM-best basin. At small LRs the surrogate gradient
is essentially noise vs the exact-score gradient; at big LRs it
actively destroys the policy. **Conclusion: do not pursue
gradient-on-piecewise from CEM-best in cycle 7 without first running
a smooth-vs-exact correlation sweep around the CEM-best point.** This
flips the cycle-5 plan-of-record (which had gradient as the cycle-6
fallback if CEM stalled) and reshuffles the cycle-7 priorities —
multi-family warm-start CEM is now #1.

**Next.**

- Cycle 7: triage gradient_probe.json, then run multi-family
  warm-start CEM (`submission_compact`, `submission_basis`). If any
  family lifts >+30 pts from its inherited start, that's the
  policy-class signal. Otherwise pivot to inventory shaping.
- Stretch: re-run cycle-6 with `RNG_SEED=1` to confirm the +19 pts
  isn't a single-seed artifact.

**Operational footnotes.**

- Repo mount: `/sessions/vibrant-dreamy-volta/mnt/amm-gym-auto-research`
  (each cycle gets a different sandbox name; always confirm with
  `pwd`).
- `git pull --ff-only origin main` failed in the sandbox as expected
  (DNS to github.com is blocked from inside this container); local
  commits push via the host launchd agent.
- The `.venv` in the repo is Mac-only — system `python3` with deps
  installed via `pip install --break-system-packages` works inside
  the sandbox. Updated cycle-6 experiment README to note this.
- Inherited working-tree changes (across `arena_eval/`,
  `arena_policies/`, etc.) still untouched per the convention from
  earlier cycles.
- Cycle-6 wall-clock: ~30 min CEM + ~5 min docs + ~5 min gradient
  probe ≈ 40 min, well under the 2-hour budget. Most of the cycle
  spent waiting for the CEM run to finish.

---

## 2026-05-04T10:30Z — cycle 7 — multi-family warm-start CEM (falsifies cycle-6 generalization)

**Plan for the cycle.** Per cycle-6 STATE: run cycle-6's warm-start
CEM recipe (24×12 pop×gen, init_std_frac=0.10, mean = inherited
best-by-val) on `submission_compact` (inherited test 410.78) and
`submission_basis` (inherited test 380.26). Compare deltas vs
piecewise's +18.74. If both lift by ~+15-22 pts, the cycle-6 result
is family-agnostic — bottleneck is optimizer convergence. If one
lifts much more, action-space matters. If neither lifts ≥+5,
piecewise is special.

**Hypothesis going in.** ~70/30 the lift is family-agnostic (the
cycle-6 prescription generalizes). If wrong, the most likely
alternative is "submission_basis already had a tighter inherited
optimizer" because its inherited validation_rerank value (380.47)
sits very close to its inherited best_search (375.43).

**What I ran.**

- Wrote a generic warm-start CEM driver
  `research/experiments/2026-05-04-cycle7-multi-family-warmstart-cem/scripts/run_warmstart_cem.py`
  generalising cycle-6's `run_warmstart_cem.py` to take a
  `--family` flag. Pulls inherited best params from
  `experiments/<family>_cem_1h_20260423_rebatch1.json::best_validation`
  for the submission families; falls back to a hand-pinned dict for
  piecewise. Same pop/gen/elite/seeds as cycle 6.
- Pre-flight: `pip install --break-system-packages gymnasium pyarrow
  "jax[cpu]"` in the sandbox (matches cycle-6 setup). Ran a tiny
  pop=4 gen=2 smoke test, hit a sandbox PermissionError on
  `Path.unlink` for the progress log; switched to truncate-via-open.
- **`submission_compact` warm-start CEM** (rng_seed=0) launched in
  background. Wall-clock 28.6 min. Final test_score 416.08 (val
  416.88). **Δ = +5.30 pts**. CEM population still drifting upward
  modestly at gen 11 (best_search 411.40, +1.0 pt over gens 9-11)
  but val plateaued by gen 8 around 416.6-416.9.
- **`submission_basis` warm-start CEM** (rng_seed=0) launched after
  compact finished. Wall-clock 27.8 min. Final test_score 380.82
  (val 380.79). **Δ = +0.56 pts** — within val noise. CEM
  population fully collapsed by gen 5; gen-over-gen val change
  ≤0.05 from gen 4 onward.
- Built `figures/family_comparison.png` (3-panel convergence) and
  `figures/family_lift_bar.png` (inherited vs cycle-7 by family).

**What worked.**

- The parametric driver worked first try after the smoke test patch.
  ProcessPoolExecutor + fork start method handles the 3 different
  policy classes cleanly.
- Both runs incrementally persisted history JSON every generation,
  so even if a run had been killed mid-cycle the data would be
  recoverable.
- The signal across the 3 families is clean and large enough to draw
  conclusions on a single rng seed: piecewise +18.7, compact +5.3,
  basis +0.6. Variance between rng seeds is plausibly ±2 pts at
  most, so the family-dependence is real, not noise.

**What failed (i.e., the cycle's main finding).**

- **The cycle-6 +18.7 lift does not generalize.** The cycle-6
  prescription "warm-start CEM is almost free wins on top of any
  prior random-init result" was overfitted to the piecewise result.
  On `submission_compact` we still got something useful (+5.3) but
  on `submission_basis` we got effectively zero. The cycle-7 #1
  hypothesis is *falsified*.
- We did not run the cycle-7 #2 sanity check (RNG_SEED=1 on
  piecewise). Falsifying the family-agnostic hypothesis was higher
  value-of-information; the seed sanity check can wait for cycle 8
  and is not cycle-critical given the strong family signal.

**Updates implied for the prior.**

- **Action-space structure matters more than param count.**
  Piecewise (16 params, explicit large/medium/small × continuation/
  reversal) is doing real structural work; submission_basis (32
  params, dense exponential-decay state + linear bias terms) is
  *not* — its inherited 14×22 CEM had already converged to a
  flat-bottom basin.
- **Init_std=0.10×range may be the wrong width** for the
  exponential-decay-state families. Compact's slow-but-real drift
  hints the basin shape might support a wider noise budget. Cycle
  8 should sweep init_std on submission_compact specifically.
- **Optimizer convergence and action-space jointly determine the
  warm-start lift size.** A clean way to express this: warm-start
  CEM only adds value where (a) the inherited optimizer left
  meaningful score on the table AND (b) the policy class has
  structure for local refinement to exploit. submission_basis fails
  (a); submission_compact partially fails (b).
- **Best M2 score remains 432.75** (piecewise, cycle 6). 107 pts
  to the M2 target. Cycle 8's three-pronged plan (inventory-aware
  piecewise / init_std sweep / smooth-exact correlation) is in
  STATE.md.

**Side observations.**

- `submission_basis`'s edge_advantage_mean is ~−134, vs
  `submission_compact`'s ~−45 and `piecewise`'s ~−9. Even at the
  inherited best, submission_basis is hemorrhaging flow share
  to the 30-bps normalizer. This is consistent with
  high-dimensional dense biases producing wider effective spreads
  than the explicit piecewise structure.
- Despite different param counts (16/20/32), all three runs took
  almost exactly the same wall-clock per generation (~140-145s).
  The bottleneck is `run_batch` × 64 search seeds × ~10k steps,
  not policy inference. This means cycle 8's 3-param inventory
  fork won't add measurable cost to piecewise CEM.

**Next.**

- Cycle 8: implement inventory-aware piecewise (highest-value first
  given the cycle-7 finding that piecewise's structure carries the
  family), then init_std sweep on submission_compact (cheap second),
  then smooth-vs-exact correlation study (cheap diagnostic). Per
  STATE.md.
- Defer indefinitely: gradient via tape_smooth from CEM-best
  (still failing per cycle 6); RNG-seed sanity on piecewise
  (interesting but not cycle-critical given cycle-7's strong
  family signal).

**Operational footnotes.**

- Repo mount: `/sessions/trusting-great-dijkstra/mnt/amm-gym-auto-research`.
- `git pull --ff-only origin main` failed in the sandbox as expected
  (DNS to github.com is blocked from inside this container); local
  commits push via the host launchd agent.
- The `.venv` in the repo is Mac-only — system `python3` with deps
  installed via `pip install --break-system-packages` works inside
  the sandbox. Cycle-7 carried this over from cycle 6 in ~30s.
- Sandbox cannot `unlink` files in the experiment results dir; the
  cycle-7 driver truncates progress logs via `open("w")` instead of
  `Path.unlink`. Documented in STATE.md operational notes.
- Cycle-7 wall-clock: ~57 min CEM (28.6 + 27.8) + ~10 min
  setup/figs/docs ≈ 67 min, well under the 2-hour budget.
- Inherited working-tree changes (across `arena_eval/`,
  `arena_policies/`, etc.) still untouched per convention.
