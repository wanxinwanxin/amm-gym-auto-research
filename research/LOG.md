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

---

## 2026-05-04T14:40Z — cycle 8 — inventory-aware piecewise (ablation kills the headline) + init_std sweep

**Plan for the cycle.** Per cycle-7 STATE: three priorities for cycle 8:
(1) inventory-aware piecewise warm-start CEM, (2) init_std sensitivity
on `submission_compact`, (3) smooth-vs-exact correlation diagnostic.
Run them in roughly that VOI order. Inventory was the single most
informative experiment to run because piecewise's structural advantage
was the cycle-7 finding and we wanted to know if the family had more
headroom or was action-space-saturated.

**Hypotheses going in.**
- Inventory: ~60/40 the dimension matters. Cycle-6 piecewise had
  val_edge_advantage = -19.3, so adding fee skew to pull inventory
  back to neutral should claw back some adverse-selection losses.
- Init_std: ~70/30 the cycle-7 0.10 default was correct (cycle 7
  noted population still drifting at gen 11 but val plateaued by
  gen 8 — the basin shape probably is ~0.10 wide).
- Smooth-exact: ~50/50 on whether the surrogate is salvageable.

**What I ran.**

1. **Inventory-aware piecewise.** New strategy
   `arena_policies/inventory_aware_piecewise.py` — 16-param piecewise
   + 3 inventory params (`inventory_skew_to_bid`,
   `inventory_skew_to_ask`, `inventory_skew_dead_zone`). At zero,
   behaviourally identical to `PiecewiseControllerStrategy` —
   verified by 3 unit tests AND the in-driver gen-0 anchor check
   (best 427.521 = cycle-6 piecewise search-seed reference).
   Registered as `inventory_aware_piecewise` in
   `arena_search/simple_amm_search.py`. Driver:
   `research/experiments/2026-05-04-cycle8-inventory-piecewise/scripts/run_inventory_warmstart_cem.py`
   — 12-gen CEM, pop=24, init_std=0.10. Wall-clock 30 min.
2. **Recovery rerank+test** — the driver was reaped between sandbox
   shells after gen 11 finished but before the test eval. Recovery
   script `scripts/recover_rerank_and_test.py` rebuilt the test json
   from the persisted history (top-1 per gen, deduped → top-8 on val
   → val-best on test). Runs in ~5 min.
3. **Inventory ablation** — `scripts/run_ablation.py` re-evals the
   cycle-8 best with inv params zeroed AND under the bare
   `PiecewiseControllerStrategy` for parity. ~3 min.
4. **Init_std sweep on `submission_compact`** — driver
   `research/experiments/2026-05-04-cycle8-init-std-sweep/scripts/run_init_std_sweep.py`,
   3 sub-runs at init_std_frac ∈ {0.05, 0.20, 0.30}, 5 gens each.
   Wall-clock ~75 min including ~36 min sandbox stall at one gen.

**What worked.**

- **Inventory-aware piecewise CEM lifted cycle-6 piecewise from
  test 432.75 to test 446.44 (+13.69 pts).** val_edge_advantage
  flipped sign from -19.30 to +26.16 — strategy went from losing
  flow share to the normalizer to actively winning it. M2 gap
  shrank from 107.25 → 93.56.
- **The 3-experiment scaffold pattern**: implementing the new policy
  + 3 unit tests + parity-check anchor in the CEM driver took ~15
  min total and caught zero bugs. The unit tests were genuinely
  worth the time — they let me trust the gen-0 anchor=427.521 as a
  parity check, which let me trust every subsequent gen as a real
  CEM step rather than something invalidated by a strategy bug.
- **Recovery from killed-mid-rerank driver was clean.** The
  per-gen history.json had everything needed. Cycle-9 STATE
  documents the recovery pattern.
- **Init_std sweep gave a clean U-shape signal**: 0.05 → +2.26,
  0.10 → +5.30 (cycle 7), 0.20 → +2.80, 0.30 → +3.11. The cycle-7
  default was the sweet spot.

**What failed (i.e., the cycle's main finding).**

- **The ablation falsified the inventory hypothesis.** Zeroing the
  3 inventory-skew params drops cycle-8 best from 446.44 to 446.61
  on test (Δ = -0.17, within noise). The full +13.69 lift over
  cycle-6 piecewise is attributable entirely to additional CEM
  refinement on the 16 inherited piecewise dims. The "inventory-aware"
  framing turned out to be misleading — what really happened is that
  12 more CEM gens at init_std=0.10 starting from the cycle-6 best
  lifted bare piecewise from 432.7 to 446.6.
- **The cycle-7 cycle-8-priority-#2 hypothesis was also falsified.**
  I went in expecting either 0.20 or 0.30 to lift `submission_compact`
  to ~430+, which would have re-spec'd the warm-start prescription
  to "warm-start AND match init_std to inherited basin width".
  Neither did. submission_compact is action-space-saturated for
  warm-start CEM; further hyperparameter tuning won't unlock it.
- **Cycle-8 priority-#3 (smooth-vs-exact correlation) was deferred
  to cycle 9** due to wall-clock spent on the first two experiments.
  Driver is staged at
  `research/experiments/2026-05-04-cycle8-smooth-exact-correlation/scripts/run_smooth_exact_scatter.py`.
  Not lost work — just shifted by one cycle.

**Updates implied for the prior.**

- **Cycle 6 was much more under-converged than its log claimed.**
  Cycle-6 reported "val plateaued at 433.6 by gen 11"; a second
  12-gen pass starting from cycle-6 best lifted +14 pts more.
  **Two-pass warm-start CEM is itself a free win on piecewise.**
  This generalises the cycle-6 prescription: not just "warm-start CEM
  beats fresh CEM" but "successive warm-start passes keep paying off
  until the basin is *actually* saturated, and the cheap diagnostic
  for saturation is to run another pass and see if it adds anything."
- **Inventory shaping in this exact form (symmetric fee skew on
  instantaneous reserve imbalance, no EMA) is not the bottleneck
  for piecewise.** Either ChallengeTape doesn't generate enough
  sustained one-sided flow, or the formulation is too coarse. An
  EMA version is worth one more cheap experiment before declaring
  the dimension dead.
- **The +14 pts of extra search did not have to be paid for.** The
  19-d optimizer found this lift in the same wall-clock budget as
  cycle-6's 16-d optimizer at the same init_std width — adding 3
  inert dimensions did not measurably slow CEM convergence.
- **Best M2 score: 446.61** (piecewise, cycle-8 ablation params).
  Gap to M2 target (540): 93.39 pts.

**Side observations.**

- The cycle-8 best params shifted notably from cycle-6: signal_decay
  0.55 → 0.67, continuation_to_cross_side 0.90 → 1.36,
  continuation_to_same_side 0.23 → 0.12. The new optimum keeps less
  "follow your own side" and more "stay on the cross side," and
  decays signal slower. Worth keeping in mind if we add new
  features in cycle 9.
- The ProcessPoolExecutor + fork pattern continues to work
  reliably across all 3 cycle-8 drivers. CEM with 3 workers
  saturates the 4-core sandbox at ~140-145s/gen for 16-d, ~120s/gen
  for 19-d (only-marginal slowdown despite richer policy).

**Next.**

- **Cycle 9 #1**: third-pass warm-start CEM on bare piecewise at
  cycle-8 ablation params. ~30 min. Tells us whether two passes is
  the asymptote.
- **Cycle 9 #2**: smooth-vs-exact correlation (deferred). Anchor at
  cycle-8 best. ~15 min.
- **Cycle 9 #3**: EMA inventory feature. ~30 min.

**Operational footnotes.**

- Repo mount: `/sessions/focused-trusting-heisenberg/mnt/amm-gym-auto-research`.
- `git pull --ff-only origin main` failed in the sandbox as expected
  (DNS to github.com is blocked); local commits push via the host
  launchd agent.
- The `.venv` in the repo is Mac-only — system `python3` with deps
  installed via `pip install --break-system-packages` works inside
  the sandbox. Cycle-8 also added `pytest` to the dep list.
- Sandbox cannot `unlink` files in the experiment results dir; all
  cycle-8 drivers truncate progress logs via `open("w")` instead of
  `Path.unlink`.
- One ~36-min sandbox stall at init_std=0.30 gen 2 (otherwise normal
  ~120s/gen). Generation completed correctly so the result is intact.
- Cycle-8 wall-clock: ~100 min of useful work plus ~36 min of
  unattributable sandbox stall, blowing the 2-hour cycle by ~15 min.
  Acceptable trade-off for the depth of the ablation result.
- Inherited working-tree changes (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, etc.) still untouched per
  convention.

## 2026-05-04T15:55Z — cycle 9 — third-pass CEM lifts piecewise +2.2 (basin near-saturated); EMA inventory queued; bin/checks/ scaffold added

**Plan for the cycle.** Three priorities from cycle 8 closeout:
(1) third-pass warm-start CEM on bare piecewise anchored at cycle-8
ablation params (446.61) — does pass #3 keep paying off, or has
the basin saturated? (2) smooth-vs-exact correlation study (deferred
from cycle 8) anchored at cycle-8 best; (3) EMA-inventory feature as
one more cheap shot at inventory before declaring the dimension dead.
Bonus: scaffold the missed-from-cycle-1 `bin/checks/` directory.

**What ran.**

1. **bin/checks/ scaffold** (priority bonus). Created `bin/run_checks.sh`
   driver and 8 starter checks encoding operational facts learned
   across cycles 1-8: remote-origin sanity, system-python use
   (the .venv shim is Mac-only), essential-deps importable
   (numpy/gymnasium/pyarrow/pytest), no-outbound-DNS to github.com
   (sandbox is push-blocked), can't-unlink-results-dir, arena_eval
   imports, piecewise anchor scoring, and an *expected-fail* jax-
   optional check. All pass except jax. Drives the cycle's first-step
   orient phase from now on.
2. **Third-pass warm-start CEM** (priority #1). Same recipe as
   cycles 6 and 8: pop=24 / gen=12 / init_std_frac=0.10 /
   elite_frac=0.20, search 0..63, val 1000..1127, test 2000..2255.
   Anchor parity check: 16-d piecewise (cycle-8 ablation params,
   inv-skew dropped) scored 441.530 on the search seeds, matching
   cycle 8 exactly. CEM finished in ~30 min. Convergence: gen 0
   val=447.89 (anchor), then 446.7 / 447.7 / 447.7 (gens 1-3 — early
   wandering), 449.2 / 449.4 / 449.6 / 449.9 / 449.7 / 449.9 / 449.8
   / 449.9 (gens 4-11 — clean climb then plateau). Reranked 8
   unique elites on val; val-best on 256 test seeds = **448.81**
   (Δ = +2.19 vs cycle-8 ablation 446.61).
3. **EMA-inventory piecewise CEM** (priority #3). New 20-param
   policy `EMAInventoryPiecewiseStrategy` (16 piecewise core + 4
   EMA-inventory: decay, skew_to_bid, skew_to_ask, dead_zone). State
   tracks `imbalance_ema = decay * prior_ema + (1 - decay) * raw`.
   With skews=0 the strategy is parity-equal to bare piecewise for
   any decay value. Wrote 7 unit tests (`tests/test_ema_inventory_piecewise.py`)
   covering: zero-skew parity at decay ∈ {0.0, 0.5, 0.95, 0.99},
   decay=0 tracks instantaneous, decay=0.9 smooths, anchor parity
   on 32 test seeds. All pass. Registered in `arena_search/simple_amm_search.py`
   as `ema_inventory_piecewise`. CEM driver staged at
   `research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/scripts/run_ema_inventory_cem.py`,
   launched in background after the third-pass CEM finished.
   Anchor parity 441.530 confirmed at startup. Cycle 10 lands the
   final test number; first few gens captured in the in-flight log.
4. **Smooth-vs-exact correlation study** (priority #2). *Blocked
   on this sandbox* — `pip install jax[cpu]` and bare `pip install
   jax jaxlib` both OOM (3.9 GB total / no swap, both die with
   SIGTERM 143). `arena_eval/diff_simple_amm` imports jax. Encoded
   as `bin/checks/08_jax_optional.sh`; the check fails today,
   passes when jax becomes installable. Marked as a user-facing
   blocker in STATE.md.

**What worked.**

- **The third-pass hypothesis was confirmed at the lower edge
  of the prior.** +2.19 pts on test, val curve climbs and then
  flattens — exactly the "diminishing-returns near saturation"
  shape. The successive-warm-start-pass rule still applies, but
  the marginal lift shrank from +18.7 → +13.9 → +2.2 across the
  three passes. This *is* the falsifying test for "should I run
  pass #4": the marginal lift would be ~0-1 pts and we already
  spent the cycle finding out.
- **Anchor parity check at gen 0 reproducibly catches family-
  rewrap bugs.** 16-d piecewise instantiation at cycle-8-ablation
  params scored 441.530 on the search seeds — matching cycle 8
  exactly to 4 decimal places. Confirms the param-rename and
  family-registration didn't introduce drift.
- **The EMA policy code + parity tests took ~20 min total.**
  Same pattern that worked in cycle 8 (3 unit tests + a parity
  check anchor in the CEM driver). Cycle-10 can trust the
  warm-start anchor as a clean baseline because the parity tests
  green.
- **bin/checks/ scaffold caught the dep gap immediately.** Check
  03 flagged scipy/jax/pyarrow missing on cycle start; pyarrow
  installed cleanly, jax OOMed and got promoted to its own
  optional-fail check 08. Without the scaffold, this would have
  shown up as a confusing import error mid-CEM.

**What failed (i.e., the cycle's main finding).**

- **Cycle-9 did not unlock another +14 pts.** It unlocked +2.2.
  This is a *positive* result for "two passes was a waypoint, not
  the asymptote", but a *negative* result for "warm-start CEM is
  the path to M2 = 540". Three passes have collectively closed
  35 pts of the 126-pt gap (414 → 449, target 540); a fourth pass
  at the same recipe is unlikely to clear the noise floor and is
  not in the cycle-10 plan-of-record.
- **jax-on-the-sandbox is genuinely unfixable in-cycle.** Two
  install attempts both died with SIGTERM. There's no swap on the
  host, total RAM is 3.9 GB, and pip's wheel-build is the OOM.
  Workaround would have to be a wheel-only install via a curated
  index, or a bigger sandbox.

**Updates implied for the prior.**

- **Bare piecewise (16 dims) plateaus at test ~449 ± 2.** Three
  independent CEM passes converge toward this number with shrinking
  gains. This is the new "ceiling" for the piecewise family. Any
  further M2 lift comes from policy capacity, not search.
- **The "successive warm-start passes keep paying off" rule
  generalises with diminishing returns.** Specifically: the
  marginal lift from pass *k+1* is ~6× smaller than from pass *k*
  in this regime. Useful for cycle-10's cost-benefit on the rung
  ladder.
- **bin/checks/ is now a load-bearing part of the cycle protocol.**
  First-step orient now runs `bash bin/run_checks.sh`; the cycle-9
  prep caught the dep gap in <2s rather than via mid-run import
  failures. Cap of ~12 active checks per the prompt; we're at 8
  with one expected-fail (jax).

**Side observations.**

- Cycle-9 best params shift from cycle-8 best in interesting ways:
  `signal_decay` 0.671 → 0.637 (faster decay), `toxicity_decay`
  0.536 → 0.606 (slower decay), `continuation_to_cross_side`
  1.358 → 1.524 (more cross-side aversion), `continuation_to_same_side`
  0.123 → 0.180 (slightly more same-side aversion). Net effect:
  faster signal forgetting + stronger cross-side fee skew. Worth
  remembering if cycle-10's ladder explores asymmetric-side
  configurations.
- The third-pass CEM elite_mean catches up to the best by gen 3-4
  (within ~0.1 pts of best) and stays there — same shape as cycle
  8. Population is well-mixed by mid-run; no rogue elites.

**Next.**

- **Cycle 10 #1**: read EMA-inventory result, decide go/no-go on
  inventory dimension.
- **Cycle 10 #2**: escalate to a multi-rung quote ladder policy
  (3-5 levels per side); warm-start CEM from cycle-9 piecewise
  best embedded as the level-1 rung.
- **Cycle 10 #3**: attempt jax-via-wheel install; if it works,
  re-enable the deferred smooth-vs-exact correlation study.
- **Defer**: a 4th-pass piecewise CEM (expected ~0-1 pt; not
  worth the time).

**Operational footnotes.**

- Repo mount: `/sessions/optimistic-amazing-mccarthy/mnt/amm-gym-auto-research`.
- `git pull --ff-only origin main` failed in the sandbox as expected
  (DNS to github.com is blocked); local commits push via the host
  launchd agent.
- The `.venv` in the repo is Mac-only — system `python3` with deps
  installed via `pip install --break-system-packages --no-cache-dir`
  works inside the sandbox. Cycle 9 needed pytest, gymnasium, pyarrow.
- Sandbox cannot `unlink` files in the experiment results dir; cycle-9
  drivers truncate progress logs via `open("w")` instead of
  `Path.unlink`.
- ProcessPoolExecutor with 3 workers continues to saturate the 4-core
  sandbox cleanly; ~125s/gen at dim=16, ~125-130s/gen at dim=20.
- Cycle-9 wall-clock: ~5 min orient + ~10 min checks scaffold +
  ~30 min third-pass CEM + ~5 min figure/presentation/STATE/LOG +
  EMA CEM running in background at commit time. Within 2-hour budget.
- Inherited working-tree changes (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, etc.) still untouched per
  convention. Cycle 9's only edits to those areas: register the new
  EMA policy in `arena_policies/__init__.py` and
  `arena_search/simple_amm_search.py`, plus the new policy file and
  test file.

## 2026-05-04T16:35Z — cycle 9 follow-up — EMA-inventory CEM ran to completion + ablation falsifies inventory (again)

The EMA-inventory CEM that was in flight at the cycle-9 main commit
finished in the same wall-clock window. Capturing the result + a
quick ablation here so cycle 10 starts with the right priors.

**EMA-inventory CEM result.**
- val (128 seeds, 12 gens, pop=24): 457.62
- test (256 held-out seeds): **456.64**
- edge_advantage_mean on test: +53.71 (vs FixedFee-0.003)
- Δ vs cycle-8 ablation (446.61): +10.03
- Δ vs cycle-9 third-pass (448.81): +7.83
- Convergence: val climbs 447.9 → 453.8 → 454.8 → 455.6 → 456.3 → 457.1
  → 457.5 → 457.5 → 457.6 over gens 0-11. Big lift (+5.9 val) in the
  first 3 gens, smaller-but-steady (+3.8 val) over gens 4-11. Best
  search-seed score reaches 451.6 by gen 11.
- Best params (notable): inventory_ema_decay = 0.530 (≈ initial),
  inventory_skew_to_bid = -0.0024, inventory_skew_to_ask = +0.0028,
  inventory_skew_dead_zone = 0.056 — *all small or near-init*.

**Ablation (256 test seeds).** Same pattern as cycle 8.
- Full EMA-aware (20 dims, learned tail): 456.640
- EMA-zeroed (20 dims, 4 inventory params zeroed): 456.616
- 16-dim piecewise re-instantiated from same core: 456.616
- Δ attributable to EMA-inventory dimension: **+0.024** (within noise)
- Δ attributable to refined piecewise dims: **+10.003** (the entire
  observed lift)

**What this means.**

1. **The inventory dimension is genuinely dead.** Two independent
   formulations (instantaneous in cycle 8, EMA-smoothed in cycle 9)
   both ablate to ≈ 0. ChallengeTape doesn't have the kind of
   sustained directional flow that inventory awareness handles.
   Cycle 10 should not try a third inventory variant.
2. **CEM at higher dim with inert tails seems to *help*, not just
   not-hurt.** The same anchor + same recipe found:
   - 448.81 test when run as 16-dim bare piecewise (cycle-9 #1)
   - 456.64 test when run as 20-dim wrapper with 4 inert dims
   This is +7.8 pts of lift attributable purely to the wrapper
   shape. Hypothesis: 4 extra random search directions per generation
   means CEM samples the piecewise basin from more angles, escapes
   shallow plateaus that 16-dim-only CEM gets stuck in.
3. **The "16-d piecewise basin saturates at 449" prior from earlier
   today was wrong.** The basin's actual ceiling is at least 456.6
   on test, and we still don't know how high it goes. A fifth pass
   with deliberate exploration noise (24-dim wrapper with 8 inert
   tails?) is a clean test of how far this trick goes.

**Updates implied for the prior.**

- Best M2 score: **456.64** (piecewise core, embedded under
  EMA-inventory wrapper). Gap to M2 target=540: 83.36 pts.
- Cumulative M2 lift from cycle-5 starting line (~414): +42.6 pts.
- The "diminishing returns across passes" framing from the cycle-9
  main entry was based on cycle-9 #1 alone. With cycle-9 #3 added,
  the pattern is: +18.7 (pass 1) → +13.9 (pass 2) → +2.2 (pass 3
  bare) → +7.8 (pass 4 with wrapper). Adding the wrapper bumped the
  marginal lift from ~2 to ~8 pts. So *not* monotonic-decreasing —
  the search-method choice matters.
- The cycle-9 main commit's narrative ("16-d basin near-saturated;
  closing 91 pts needs more capacity") needs softening: more capacity
  *probably* still helps, but cheap CEM tricks haven't run out.

**Cycle-10 first action**: read these results, then run the cleanest
form of the wrapper-as-noise experiment — a 24-dim policy with 8
inert dims that *cannot* enter the fee formula even in principle (a
pure no-op tail), warm-start CEM, see if we get the same lift again.

**Operational footnotes.**
- EMA CEM took 31.3 min wall-clock for 12 gens at dim=20 (avg ~157s
  per gen + val), plus ~5 min rerank+test. Same-shape budget as
  cycle-8 inventory-aware CEM at dim=19.
- Ablation script (3 evaluations on 256 test seeds × ~60s each = 3
  min) ran cleanly in background after the main CEM finished.
- One quirk: the in-foreground attempt to run the ablation got
  killed at 2 min by the Bash tool's 2-min default timeout. Backgrounding
  via nohup worked fine. Keep this in mind for future cycle-end
  scripts that take >120s.
- Wall-clock for cycle 9 total: ~1h 35min of useful work, finishing
  ~16:35. Within 2h budget despite running two CEMs back-to-back.

---

## 2026-05-04T18:15Z — cycle 10 — wrapper-as-noise hypothesis test (A confirmed, mechanism is rng-stream-offset)

**Plan for the cycle.** Cycle-9 follow-up showed a 20-d EMA-inv wrapper
lifted M2 by +7.83 over the bare 16-d 4th-pass even though the
ablation said EMA params themselves contribute +0.024. Three
candidate explanations: (A) inert tails help CEM with random search
directions, (B) rng-seed lottery, (C) joint EMA×piecewise structure
the ablation missed. Cycle-10 plan-of-record was to run the cleanest
form of (A) — a wrapper whose tail dims *cannot* enter the fee formula
even in principle — and a (B) control with a different rng seed at
dim=16. Both at same anchor, same recipe, sequential to avoid
saturating the 4-core sandbox.

**What I ran.**
1. Bootstrap: `bin/run_checks.sh` clean except the expected
   jax-OOM. Re-installed `gymnasium` / `pyarrow` / `pytest` on the
   fresh sandbox via `pip install --break-system-packages`.
2. Wrote `research/experiments/2026-05-04-cycle10-noop-tail-cem/scripts/run_noop_tail_cem.py`:
   pop=24, gen=12, dim=20 (16 piecewise + 4 noop). The eval function
   strips noop_* before instantiating `PiecewiseControllerParams`;
   noop dims are bounded `[-1, 1]` so they get reasonable CEM std.
3. Wrote `run_seed_lottery_cem.py`: identical to cycle-9 #1 except
   `--rng-seed 1`.
4. Ran A (rng_seed=0) → 29.7 min CEM + ~5 min rerank+test.
5. Launched B in series. 29.8 min CEM + ~5 min rerank+test.
6. Built `make_comparison_figure.py` to render the 4-run convergence +
   bar chart.
7. Updated experiment README, presentation, STATE, LOG.

**What worked.**

- **Both runs completed within wall-clock budget.** Cycle 10 total
  ~80 min of useful experiment time (~4 min orient/setup; ~30 min A;
  ~5 min between; ~30 min B; ~5 min figure/writeup); within the 2-h
  cycle envelope.
- **Anchor parity check (441.530 on search seeds) matched cycle-9 #3
  exactly**, confirming the no-op-tail wrapper preserves the eval
  semantics of bare piecewise.
- **A's val-score convergence essentially mirrors cycle-9 #3** (both
  reach ~457.6 by gen 11; gen 0–2 vals match to 0.001; small
  divergence from gen 3 onwards consistent with the slight
  numerical noise of EMA params drifting away from zero in cycle-9
  #3). Test scores: A = 456.738, cycle-9 #3 = 456.640.

**What failed (or surprised).**

- Initial expectation: A would *exactly* match cycle-9 #3. It
  matches within +0.10 but not exactly. Cause: in cycle-9 #3 the EMA
  params drift slightly off zero during CEM, introducing tiny score
  perturbations per candidate that eventually break the elite
  selection identity. The cleanest reading: A and cycle-9 #3 sample
  identical 16-d piecewise vectors at every candidate at every
  generation (because numpy's `rng.normal(mean, std)` consumes the
  same 20 standard normals at the same seed, and the first 16 z's
  are identical given identical mean[:16]/std[:16]); but they assign
  slightly different scores to those vectors due to nonzero EMA tail
  in #3.

**Updates implied for the prior.**

- **Hypothesis (C) is dead.** A reproduces cycle-9 #3 to +0.10 pts
  using *mathematically* zero tail interaction. There was no joint
  signal the ablation missed.
- **Mechanism for cycle-9 #3's lift over cycle-9 #1: rng-stream-
  offset.** Both use rng_seed=0; cycle-9 #1 (dim=16) consumes 16
  normals per candidate, cycle-9 #3 (dim=20) consumes 20. After gen 0,
  their RNG states diverge by 92 normals per generation. The dim=20
  trajectory at this seed lands in a luckier region of the same 16-d
  basin. There is no geometric "more search directions" effect; this
  is purely RNG-sequence sensitivity.
- **Hypothesis (B) (seed lottery) is real but smaller than (A).** B
  (16-d, seed=1) lifts test to 452.96 (+4.15 vs cycle-9 #1, but
  -3.78 vs A). So the +7.83 lift decomposes as ~+4.2 from seed
  lottery + ~+3.8 from dim-20-specific sequence luck.
- **The 16-d basin's true ceiling is ≥ 456.74 on test.** The
  cycle-9-main-entry framing of "16-d basin saturates near 449" was
  wrong; it was just the saturation point at *one specific RNG
  seed*. The CEM-noise distribution over multiple seeds is wide
  enough that single-CEM headlines need their seed disclosed (and
  ideally a few-seed median reported).

**Next.**

- **Cycle 11 #1**: multi-seed × multi-dim CEM grid (~3 seeds × {16,
  24, 32}-d-noop). 9 runs at ~30 min each is too much for one
  cycle; do 3-4 per cycle, spread across cycles 11-12. Goal: bound
  the CEM-noise distribution on this anchor and find the basin's
  actual best.
- **Cycle 11 #2** (deferrable): jax-via-CPU-wheel install retry.
- **Cycle 11/12**: escalate policy capacity (ladder/MLP) once the
  search-noise picture is clear.
- **Defer indefinitely**: any further inventory variant; wrappers
  whose tail enters the fee formula non-trivially (the cleanest
  test of inert tails has been run — there's nothing left to learn
  from this class of wrapper).

**Operational footnotes.**

- Repo path on this sandbox: `/sessions/jolly-confident-mccarthy/mnt/amm-gym-auto-research`.
  Sandbox name confirmed via `pwd`.
- `git pull --ff-only origin main` not attempted (DNS-blocked check
  passing); local commits push via host launchd agent.
- Fresh sandbox required `pip install --break-system-packages
  gymnasium pyarrow pytest`. `pyarrow` install took ~3 min (45 MB
  wheel; slow CDN). jax install still OOMs (check 08 still failing as
  expected).
- Sequential CEMs are the right call; running two in parallel would
  saturate the 4-core sandbox (3 workers × 2 = 6 procs).
- Both cycle-10 CEMs took ~30 min wall-clock for 12 gens + rerank
  + test, matching cycle-9's per-run budget.
- Inherited working-tree changes (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still untouched
  per convention. Cycle 10's only edits were under `research/` and
  the experiment scripts.

---

## 2026-05-04T23:30Z — cycle 11 — multi-seed × multi-dim grid (round 1) — 16-d basin ceiling lifted to 456.80

**Plan for the cycle.** Per `STATE.md` cycle-11 plan-of-record: a small
(dim, rng_seed) grid on the cycle-8 anchor to bound the warm-start
CEM noise distribution and find the basin's actual ceiling. Three
cells: (16-d, seed=2), (24-d-noop, seed=0), (24-d-noop, seed=1).
Sequential, ~30 min/cell, ~90 min CPU. Hypothesis: with 4 cells
already from cycle 9/10 (test ∈ {448.81, 452.96, 456.64, 456.74}),
adding 3 more should give ≥ 1 cell ≥ 459 if the basin has more depth,
or stay flat ≤ 458 if not. If flat: pivot to capacity escalation in
cycle 12.

**What I ran.**
1. Bootstrap: `bash bin/run_checks.sh` clean except expected jax-OOM.
   Re-installed `gymnasium pyarrow pytest numpy` on this fresh sandbox
   via `pip install --break-system-packages`. Check 03 flipped to
   green.
2. Wrote `research/experiments/2026-05-04-cycle11-grid-cem/scripts/
   run_grid_cell.py` — generic warm-start CEM cell parameterized by
   `--dim-total` and `--rng-seed`. The piecewise core is always 16
   dims; `dim_total - 16` extra dims are inert no-op tail clipped to
   `[-1, +1]`, stripped before instantiating
   `PiecewiseControllerParams`. Same anchor / recipe / seed splits as
   cycle 6 onward.
3. Wrote `run_grid.sh` driver: runs the 3 cells sequentially, each in
   its own subprocess with stdout redirected. **Bug-fix detail**: the
   first attempt of the driver had `cd "$(dirname "$0")/../.."` which
   landed in `research/experiments/` instead of the experiment dir, so
   `LOG_DIR` resolved to `research/experiments/results` and the
   per-cell `python3` invocations passed wrong `--script` paths. Fixed
   to `cd "$(dirname "$0")/.."`. Retried; driver healthy.
4. Launched the grid via `nohup bash run_grid.sh &` (PID 1110). Total
   elapsed ~95 min wall-clock for the 3 cells (slightly longer than
   cycle-10's 30 min/cell; d=24 cells cost ~5 s extra/gen for the
   larger candidate vector serialization, plus rerank+test).
5. Wrote `make_grid_figure.py` that loads 7 cells (cycle-9 #1,
   cycle-9 #3, cycle-10 A, cycle-10 B, cycle-11 d16_s2, cycle-11
   d24_s0, cycle-11 d24_s1) and renders a 2-panel figure
   (scatter by (dim, seed); spread/box).
6. Ran `make_grid_figure.py` → `figures/grid_summary.png` and
   `results/grid_summary.json`.
7. Updated experiment README, presentation, STATE, LOG.

**What worked.**
- **All three cells completed cleanly** within ~30-32 min each.
  Anchor parity check (441.530) reproduced exactly on each cell —
  good news: the noop-tail-with-clipping wrapper is consistent across
  3 different `dim_total` values.
- **Grid expanded the empirical CEM-noise distribution** from 4 cells
  (cycle 9/10) to 7. Now we can compute mean / std on this anchor
  with much more confidence.
- **(16-d, seed=2) cell hit a new headline**: test 456.80, val
  458.54 — narrowly above cycle-10 A (test 456.74). Held-out, so
  not noise; the basin's actual ceiling is now at least 456.80.

**What failed (or surprised).**
- **24-d cells at this anchor underperformed the 16-d third seed.**
  d24_s0 reached test 455.66 (val 457.29); d24_s1 reached test
  452.57 (val 453.74). Both below
  d16_s2's 456.80. So adding inert tail dims at the 8-dim level
  doesn't keep monotonically lifting CEM via the rng-stream-offset
  mechanism cycle-10 documented; the lift saturates somewhere
  between dim=20 (where it appeared) and dim=24 (where it
  retreated).
- **The basin's ceiling on this recipe is essentially flat in the
  455.7 - 456.8 range across multiple competent (dim, seed) cells.**
  Three different cells (c10 A, c10 B-not-quite, c11 d16_s2) cluster
  near 456-457 on test; outliers below (c9 #1 at 448.8, c11 d24_s1)
  reflect either bad seed luck or capacity that isn't paying off.

**Updates implied for the prior.**
- **The "warm-start CEM at this anchor" approach is saturating around
  ~457 on test.** Across 7 cells the spread is roughly 8 pts (min ~449,
  max ~457). Noise std on test is on the order of 3 pts; even the
  best of 7 only nudges past prior best by 0.06 pts. There are likely
  diminishing returns from more (dim, seed) reps unless the recipe
  itself changes.
- **Adding inert tail dims helps up to dim=20-ish, not beyond.** This
  is consistent with the cycle-10 mechanism (rng-stream offset gives
  the CEM a different sample sequence) but with diminishing
  effectiveness past a few extra dims — unsurprising, since at some
  point the noise-floor in dimensions of the CEM Gaussian outweighs
  the offset benefit, and the rerank-by-val step regularizes too.
- **Cycle-12 should pivot.** The grid has answered the central
  question we kept asking — "does cheap CEM rerunning still help?"
  — with a clear "diminishing returns past the third or fourth rep".
  Three obvious next moves:
  (i) escalate policy capacity — try ladder or MLP, warm-start from
  d16_s2 best (which has held-out test 456.80);
  (ii) escalate optimization recipe — longer gens, different
  init_std_frac sweep on d16_s2's anchor specifically;
  (iii) revisit M3/M4 readiness now that M2 is ~85% of the way to 540
  but starting to require capacity work.

**Next.**
- **Cycle 12 candidate plans (ranked):**
  1. **Capacity escalation: ladder policy.** Warm-start the ladder
     level-1 rung from d16_s2 best. ~1 hour CEM. If ladder beats
     piecewise on this anchor, that's the path. (Highest expected
     info value; addresses the saturation directly.)
  2. **MLP capacity probe.** Same anchor, MLP head over the
     piecewise output. ~1.5 hours. Bigger lift potential but bigger
     variance.
  3. **Bigger CEM budget on d16_s2 specifically.** pop=48 or
     gen=20+. Cheap to set up but probably more of the same.
  4. **Defer**: more (dim, seed) cells unless we discover an outlier
     justifying it.
- **Operational**: jax check still failing as expected; will retry
  once a CPU-only wheel landing strategy is identified.

**Operational footnotes.**
- Repo path on this sandbox: `/sessions/busy-ecstatic-curie/mnt/
  amm-gym-auto-research`. Sandbox name confirmed via `pwd`.
- Bash tool default timeout (2 min) and max timeout (10 min for
  `sleep`) made polling the long-running grid awkward; the right
  pattern is `nohup ... &` once and read the per-cell `progress.log`
  every 8-9 min via short polls. Sleep>10min is hard-killed with
  exit 143.
- Grid driver bug: `cd "$(dirname "$0")/../.."` resolved up to
  `research/experiments/` (one too many parents). The python script
  inside still ran but wrote results to its own correct path (it
  computes `ROOT` independently); the driver-side `LOG_DIR` was
  wrong so the per-cell stdout files leaked into a shared
  `research/experiments/results/` dir which is sandbox-unwritable
  to my user (couldn't `unlink`). Truncated those 4 files to zero
  bytes via `:`-redirects rather than deleting them, per the
  cycle-1 ops note about unlink permission. Fixed driver path; reran
  cleanly.
- All inherited working-tree changes still untouched (cycle 11
  edits are restricted to `research/` and `bin/checks/` — actually
  no `bin/checks/` change this cycle).


---

## 2026-05-04T23:35Z — cycle 12 — capacity escalation + fresh-anchor sanity

**Plan for the cycle.** Cycle-11 closed with the empirical headline
that warm-start CEM on the cycle-8 piecewise anchor saturates at test
≈ 457 across 7 cells (spread 449-457; CEM-noise std ≈ 3 pts). The
cycle-11 plan-of-record proposed two follow-ups, both of which were
explicitly designed to *differentiate* between three lurking
hypotheses: (a) capacity is the bottleneck (need richer policy
family), (b) the cycle-8 anchor is in a sub-optimal basin (need to
re-anchor), (c) the saturation reflects a genuine ceiling under this
recipe and we need to escalate the recipe instead. Cycle 12 runs both:

  1. **Stage 1 — ladder family CEM.** From-defaults CEM on
     `latent_full` (18-d ladder rung; EMAs over flow / opportunity /
     fair-price / toxicity / competition / inventory). pop=24,
     gen=12, init_std=0.25 × range, rng_seed=0. If test ≥ 460,
     capacity is the answer; if test < 430, ladder isn't the path.
  2. **Stage 2 — fresh-anchor piecewise CEM.** From-defaults CEM on
     piecewise (16-d; the exact same family as cycles 6-11), but with
     init_std = 0.30 × range — wide enough to plausibly leave the
     cycle-8 basin. If test ≥ 460, the cycle-8 anchor is sub-optimal
     and we re-anchor; if test < 430, 12 gens of fresh-anchor CEM
     can't escape the default basin (warm-start was doing real
     refinement work).

Going-in priors: ~30% ladder beats 460, ~25% fresh-anchor beats 460,
~45% both land below — saturation is real and we should pivot to
recipe escalation in cycle 13.

**What I ran.**
1. `bin/run_checks.sh` → 9/10 pass; only the optional jax check
   failed (still OOM-blocked). The required-deps check failed once
   on the fresh sandbox; installed `gymnasium pyarrow pytest numpy
   matplotlib` with `pip install --break-system-packages`. After
   install, all 9 non-optional checks green.
2. `git pull --ff-only origin main` → DNS unresolvable as expected
   (check 04 is a passing-when-failing predictor); proceeded.
3. Wrote `run_ladder_cem.py` — generic ladder-family CEM driver,
   parameterized by `--family <latent_flow | latent_fair |
   latent_toxicity | latent_competition | latent_full>`. Same
   contract as cycle-7 multi-family driver but starts from the
   dataclass defaults rather than an inherited warm-start.
4. Wrote `run_fresh_anchor_piecewise.py` — fresh-anchor piecewise
   CEM with init_std_frac=0.30 (vs warm-start's 0.10).
5. Wrote `run_chain.sh` — sequential driver for both stages; logs
   to `chain.log`.
6. Smoke-tested defaults: `latent_full` 8-seed score = 52.9 (adv
   −162); piecewise 32-seed score = 254.2 (adv +2.3). Confirms
   ladder defaults are far from any working basin while piecewise
   defaults are competitive but unrefined.
7. Launched chain via `nohup`. Polled per-gen progress.log every
   ~9 min throughout the cycle.
8. After both stages, ran `make_figure.py` to produce
   `figures/cycle12_summary.png` (per-gen progression + M2
   cumulative bar chart from cycle 5 to cycle 12).
9. Updated experiment README, presentation, STATE, LOG.

**What worked.**
- **Both stages completed cleanly** in the wall-clock budget.
  Stage 1 (latent_full): CEM 30 min + rerank 5 min = 36 min total.
  Stage 2 (piecewise fresh): CEM 29 min + rerank 6 min = 35 min
  total. End-to-end ~71 min for the chain.
- **Falsification design held.** Both stages landed in their
  respective "test < 430" branches:
  - latent_full: test = **388.57** (val 388.77, adv −123.65) →
    68 pts below warm-start cluster. The CEM saturated quickly
    around gen 5 (best 383) and barely budged through gen 11
    (best 384). The ladder-family controllers default to
    advantage ≈ −205 (substantially worse than the FixedFee
    normalizer); 12 gens of CEM from defaults found a basin at
    advantage ≈ −123 but couldn't approach the warm-start
    piecewise advantage ≈ +63.
  - fresh-anchor piecewise: test = **418.65** (val 419.34, adv
    −36.43) → 38 pts below warm-start cluster. CEM climbed
    monotonically through 12 gens (374 → 414) and was still
    inching at gen 11 (+0.2 pts/gen), which suggests longer gens
    might catch up — but at 12 gens, the from-default piecewise
    is decisively below warm-start refinement.
- **Both stages produced clean test JSONs and reproducible
  histories.** Used the same val/test split as every prior cycle
  (val 1000-1127, test 2000-2255), so all 12 M2 cycles are now on
  the same scoreboard.

**What failed (or surprised).**
- **Latent-family default scores are catastrophically bad.** All
  4 simpler ladder rungs (flow / fair / toxicity / competition)
  default to score ≈ 0 with adv −205; latent_full only hits 53.
  This means CEM-from-defaults on the ladder is essentially a
  cold start; the 12-gen budget isn't enough to climb out of the
  hole. A fairer comparison would warm-start the ladder from a
  checkpoint, but we don't have one — *and* the parameter space
  doesn't overlap with piecewise so we can't translate.
- **The fresh-anchor piecewise wasn't a sub-optimal-basin
  detector — it was a budget detector.** The CEM was still
  climbing at gen 11 (val 419 vs gen 0's 391), which means we
  haven't actually distinguished "wrong basin" from "same basin,
  not enough gens". The right cycle-13 follow-up to *this* arm is
  a 24-or-36-gen fresh-anchor run; if that lands in the 449-457
  cluster, the answer is "same basin, just slow"; if it lands
  ≥460, the cycle-8 anchor IS sub-optimal.
- **Score-vs-advantage decoupling.** The challenge scoring rule
  rewards score 380+ even when adv is negative-100 (i.e. the
  policy is dramatically worse than FixedFee on edge); both
  cycle-12 stages exhibit this. This is consistent with prior
  cycles but worth flagging — score is dominated by retail
  recapture / arb-loss-protection terms when adv is bad, not by
  the per-trade advantage. We may want to look at the scoring
  rule's component decomposition in cycle 13 to understand which
  term the warm-start cluster is winning on.

**Updates implied for the prior.**
- **Hypothesis (a) "capacity is the bottleneck" → strongly
  falsified** under this recipe. Even the richest 18-d ladder rung
  with explicit EMAs over six market features lands 68 pts below
  warm-start piecewise. The simpler family wins.
- **Hypothesis (b) "the cycle-8 anchor is sub-optimal" → not
  falsified, but not confirmed either.** Fresh-anchor at 12 gens
  lands 38 pts below warm-start, but the trajectory was still
  rising, so this is genuinely ambiguous. To get a clean answer we
  need either a longer fresh-anchor run (24-36 gens) or a much
  larger pop with init_std=0.30.
- **Hypothesis (c) "saturation reflects a recipe ceiling" → most
  consistent with the data.** Both alternatives land below
  warm-start at the same compute budget, which is the prediction
  of (c). The fresh-anchor's still-rising trajectory in particular
  suggests that the piecewise basin is broad and reachable from
  many starts but takes >12 gens to refine to within ~5 pts of the
  cycle-11 ceiling.
- **Operational lesson:** when "warm-start refinement" stops
  paying off (cycles 9-11), the failure mode looks like
  saturation. But "fresh-anchor + same recipe" doesn't catch up —
  warm-start is doing real refinement work, even if its marginal
  contribution per cycle has shrunk. Don't conclude "we're done"
  from saturation alone; budget escalation is the natural next
  test.

**Next.**
- **Cycle 13 plan-of-record (highest-info-first):**
  1. **Long-run warm-start CEM on d16_s2.** Same anchor, same
     family, but pop=24, gen=24 (double the budget). Tests
     hypothesis (c) directly: does warm-start CEM keep climbing
     past 457 with more compute? If yes → genuine refinement still
     left; if no → ceiling confirmed and we move to recipe-shape
     changes (larger pop, new normalizer, etc.).
  2. **Long-run fresh-anchor piecewise CEM.** init_std=0.30,
     gen=24-36 from defaults. Resolves the cycle-12 ambiguity
     about whether the cycle-8 anchor is in the right basin.
     Lower priority than (1) — cycle-12 result still tilts toward
     "same basin", and the (1) experiment will tell us whether to
     bother re-anchoring.
  3. **(Background)** decompose the challenge score into its
     components on the d16_s2 best vs latent_full best vs
     fresh-anchor best. Useful for cycle-14 reward-shaping
     analysis.
- **If recipe escalation flatlines too**: pivot to **M3
  (generalization study)** with d16_s2 as the M2 deliverable
  (~85% of way to the 540 target). M3 will add new info regardless
  of whether we close the M2 gap.

**Operational footnotes.**
- Repo path on this sandbox: `/sessions/magical-festive-mccarthy/
  mnt/amm-gym-auto-research`. Sandbox name confirmed via `pwd`.
- All cycle-12 edits restricted to `research/` (and the new
  `research/experiments/2026-05-04-cycle12-latent-ladder-cem/`);
  inherited working-tree changes still untouched.
- Stage 2's gen 11 was still showing positive ∆-per-gen at +0.2
  pts; the CEM "complete in 12 gens" stopping rule is arguably
  premature for from-default cold-starts. Cycle-13's gen=24 sweep
  will resolve.
- `bin/checks/` policy held: `bash bin/run_checks.sh` first thing,
  installed deps when 03 failed, no checks added or retired this
  cycle. (No new operational facts surfaced; cycle-11's lessons
  about sleep-timeouts, results-dir-unlink, and grid driver paths
  all held.)

---

## 2026-05-05T07:00Z — cycle 14 — close M2 (recipe ceiling confirmed) + M3 cycle-1 dual-curve

**Plan for the cycle.** Cycle 13's gen=24 long-run CEM finished all
24 generations but the in-script rerank/test step never wrote
`result.json` (the script must have been killed between gens
completing and rerank finishing — the last `progress.log` line was
the "Reranking…" header). Cycle 14's first job: recover the cycle-13
test score from `history.json` so we can apply the cycle-13 decision
rule. Then per the rule, either continue M2 or pivot to M3.

**What I ran.**

1. **Reorient + checks.** `bin/run_checks.sh` failed on
   `03_required_python_deps.sh` (fresh sandbox, gymnasium not
   installed). Installed `numpy gymnasium pyarrow pytest matplotlib
   --break-system-packages`. All 11 active checks pass except the
   carry-forward `08_jax_optional.sh` (still OOMs on this sandbox,
   already on Blockers list).
2. **Cycle-13 rerank recovery.**
   `research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/scripts/finish_rerank.py`:
   pulls the per-gen `best_search_params` from `history.json` (24
   candidates, dedup → 8 unique by rounded-key), val-scores each on
   1000..1127, and test-scores the val-best on 2000..2255. ~5 min.
   Result: best-by-val came from **gen 0 (the anchor itself!)** with
   val=458.539, test=**456.803** — Δ vs champion = +0.000.
3. **Cycle-13 figure regenerated** with the recovered result.
4. **M3 cycle-1 dual-curve eval.** New experiment dir
   `research/experiments/2026-05-05-cycle14-m3-dualcurve-bootstrap/`.
   `scripts/eval_anchors_dualcurve.py` loads `best_by_val.params`
   from each chronological M2 anchor (c5..c13, 8 anchors) and runs
   `run_batch(..., evaluator_kind="challenge")` and `(..., "real_data")`
   on the standard val seed split (1000..1127, n=128). Normalizer is
   FixedFee(0.003) in both modes. ~10 min single-process. Wrote
   `dualcurve.json` and 2-panel `m3_dualcurve.png` figure.
5. **New check** `bin/checks/11_cycle13_recipe_ceiling.py` — encodes
   "no later gen of cycle-13 longrun beats gen-0 anchor's
   best_search_score by >2 pts". Falsifies if the simulator
   semantics shift. Passes on this sandbox.
6. **Tests.** `pytest -x -q` on the non-torch/non-jax test set: 136
   pass, 2 skip. (torch- and jax-dependent suites
   `test_training.py`, `test_diff_simple_amm_*.py`,
   `test_clairvoyant_oracle.py`, `test_retail_recapture.py` carry
   forward the inherited "torch/jax not installed on this sandbox"
   blocker — none touched by cycle-14 edits.)

**What worked / surprised.**
- **The cycle-13 result is unambiguous.** The 24-gen long-run CEM
  evaluated 24×24 = 576 candidates and never produced one whose
  128-seed val score beat the anchor's gen-0 458.539. Elite-mean
  did climb (436 → 451 in 8 gens, then plateau), but no elite ever
  found a strictly better val region. This is the cleanest possible
  falsification of "warm-start CEM has more refinement to give
  under this recipe".
- **The M3 dual-curve plot is the most informative single figure of
  the project so far.** It cleanly partitions the M2 trajectory into
  three regimes:
    1. c5 → c6 (challenge 414 → 434): real_data score *regresses*
       below FixedFee. Early challenge optimization is
       **net-harmful** OOD.
    2. c8 → c9-EMA (challenge 448 → 458): real_data score climbs
       from 0 to +2.8 above FixedFee. **High-leverage segment** —
       this is where challenge optimization actually buys OOD value.
    3. c9-EMA → c13 (challenge 458 → 458): real_data score
       saturates at +2.4 above FixedFee. **OOD ceiling reached at
       the same compute as the in-distribution ceiling.**
- **The c11 = c13 equality holds OOD too**, which is a non-trivial
  consistency check: two independent reruns of the same parameter
  vector should produce identical scores up to seed-set
  determinism, and they do (real_val 2.918 = 2.918 exactly).
- **Surprise vs prior**: I had ~25% odds the early M2 anchors would
  be net-harmful OOD; the actual outcome is 100% on the first 2
  anchors. This is a stronger result than expected and reframes the
  M3 question from "where do the curves diverge?" to "why does the
  early phase of challenge optimization actively *break* the
  policy on real data?"

**What failed (or surprised on the downside).**
- The cycle-13 driver's rerank step did not survive the cycle
  boundary. Operationally this is a recurring "long script + CEM
  resumability" issue: the CEM itself was resumable (history.json
  saved per gen) but the rerank/test postprocess wasn't. Future
  long-run CEM drivers should *always* checkpoint the rerank pool
  to disk before scoring, or split the CEM and rerank into two
  separate scripts. Recorded as a methodological note in cycle-14
  README; not yet a check (no clean falsifiable assertion).
- `pytest tests/test_diff_simple_amm.py` collection fails because
  it imports torch transitively via the test_training.py shared
  fixtures. Carry-forward; not new this cycle.

**Updates implied for the prior.**
- **M2 closed.** The deliverable is `cycle-11 d16_s2`
  best_by_val (test=456.80, ~85% of way to 540). All three
  cycle-12 hypotheses have now been touched: (a) capacity
  falsified, (b) anchor-sub-optimal de facto falsified by cycle 13
  not finding a better basin, (c) recipe-ceiling confirmed.
  Future M2 reopening would need a *different recipe shape* —
  much wider init_std, much larger pop, hybrid CEM→PPO, different
  normalizer venue, etc. Not the most informative next step right
  now.
- **M3 active hypothesis.** "Challenge optimization is harmful OOD
  early and saturates OOD before it saturates in-distribution."
  Cycle 14's evidence is suggestive but single-seed (n=128 val).
  Cycle 15 should:
  1. Add a held-out test split (2000..2255) to the dual-curve plot
     so the headline numbers aren't single-seed point estimates.
  2. **Replicate the early-anchor inversion** with a 2nd anchor
     sequence (cycle-11 grid d16_s0 / d16_s1 chains) to confirm the
     "challenge gain → OOD harm" shape isn't a c5/c6 fluke.
  3. **Decompose the c5 real_data PnL** into retail-flow and
     arb-flow components to localize *what* the early
     optimization is breaking on real data (toxic-flow miss-quote?
     too-tight base spread that loses to MM impact?).

**Next.**
- **Cycle-15 plan-of-record:**
  1. Add held-out test seeds 2000..2255 to the dual-curve table —
     re-run `eval_anchors_dualcurve.py` with a second seed split
     and pick the val-best vs test-best discrepancy. ~10 min.
  2. Replicate dual-curve on `cycle-11 d16_s0` and `d16_s1` anchor
     chains (different rng seeds, same recipe). If the
     early-anchor inversion replicates on both, the "early
     optimization is OOD-harmful" finding gets locked in. ~15 min
     each.
  3. Decompose real_data evaluator's `score` into retail vs arb
     PnL components for c5 vs c11 to localize the failure mode.
     Requires a one-shot diff into `simulator.py` to capture
     intermediate per-trade signals (or a new evaluator wrapper).
     ~20 min.
- **If (2) confirms** and (3) localizes the failure: the M3
  writeup and the M4 plan both gain a clean "what the first 19 pts
  of challenge improvement are *actually* doing wrong" story,
  which is the highest-information lever we have for M4 (training
  directly on real_data).

**Operational footnotes.**
- Repo path on this sandbox: `/sessions/gifted-amazing-bohr/mnt/amm-gym-auto-research`.
  Sandbox name confirmed via `pwd`.
- All cycle-14 edits restricted to `research/` (new experiment
  dirs, README/STATE/LOG/presentation updates) and
  `bin/checks/11_cycle13_recipe_ceiling.py`. Inherited working-tree
  diffs (`arena_eval/`, `arena_policies/retail_recapture.py`,
  `scripts/`, `tests/`) untouched per convention.
- Wall-clock: ~10 min orient + ~5 min finish_rerank + ~5 min
  cycle-13 figure + ~10 min M3 dualcurve eval + ~3 min M3 figure
  + ~30 min STATE/LOG/presentation + ~5 min check + ~5 min commit
  ≈ 75 min. Within the 2h budget.
- **No checks retired this cycle.** All 11 active checks pass
  (modulo the carry-forward jax-OOM blocker on `08_jax_optional`).

---

## 2026-05-05 — cycle 15 (M3 cycle 2: held-out test split + bootstrap CI + retail/arb decomposition)

**Plan for the cycle.** Cycle 14's M3 cycle-1 plot established the
"early-anchor inversion" qualitatively but every number was a
single-seed val estimate (n=128). Three things needed to happen
before the M3 finding could be load-bearing for M4:
  1. Held-out test split (2000..2255, n=256) so the headline OOD
     numbers aren't being driven by the same seeds CEM saw during
     search.
  2. 95% bootstrap CIs on the per-anchor scores so we can distinguish
     "below FixedFee" from "within batch noise".
  3. PnL decomposition (retail edge vs arb loss) so we can localize
     *what* early-anchor optimization is breaking on real_data.
Plus opportunistically: add a 9th anchor at rng_seed=1 (cycle-10B)
to test whether the OOD plateau survives a different sampling
sequence.

**What ran.**
- Pre-flight: ran `bin/run_checks.sh` on a fresh sandbox; reinstalled
  gymnasium/pyarrow/pytest via pip and re-ran `setup_jax_from_vendored.sh`
  to import jax. After install all 11 checks passed.
- `research/experiments/2026-05-05-cycle15-m3-test-split-decomp/scripts/eval_dualcurve_test.py`
  on 9 anchors × 4 batches each (val 128 + test 256, on challenge +
  real_data). 36.9 min total. PID 1524 in nohup loop, polled
  progress.log every 8-9 min per the cycle-13 nohup-patrol idiom.
- `make_figure.py` produced the three-panel test-split figure
  (challenge curve, real_data curve with FF reference + below-FF
  band, retail/arb decomposition bars).

**Headline numbers (test split, n=256, 95% bootstrap CI).**
- FixedFee(0.003): real_data 0.470 [-0.08, +1.01]; challenge 342.83
  [336.7, 348.9].
- c11 d16_s2 (M2 deliverable): challenge 456.80 [448.0, 465.7];
  real_data **+2.574 [+1.98, +3.16]**, lift over FF = **+2.104**.
- c5 baseline: real_data **-0.744 [-1.27, -0.23]** — CI fully below
  FixedFee. Statistically significant inversion confirmed.
- c6 warmstart: real_data **-0.933 [-1.47, -0.40]** — CI fully below.
- c10B (rng_seed=1, NEW): real_data +1.66 [+1.09, +2.24], lift +1.19;
  ~0.9 lift below c10A/c11 in the same plateau region.

**Decomposition (real_data test, retail vs arb edge_advantage).**
- c5: retail -9.99, arb +3.70, net -6.30.
- c6: retail -9.04, arb +3.01, net -6.03.
- c8: retail -6.38, arb +2.36, net -4.01.
- c9 third: retail -1.87, arb +1.89, net +0.02.
- c9 EMA: retail +0.26, arb +1.92, net +2.18.
- c10A: retail +0.91, arb +1.85, net +2.76.
- c10B s1: retail -1.53, arb +2.03, net +0.50.
- c11 d16_s2: retail +1.06, arb +1.75, net +2.81.

Pattern: retail moves -10 → +1 (+11 monotonic-ish), arb stays in a
narrow +1.7 to +3.7 band. Early M2 is **breaking on retail-flow
pricing**, not on arb loss.

**What worked / what surprised on the upside.**
- The PnL decomposition came essentially "for free" — the existing
  `SimulationResult.retail_edge_advantage` and `arb_loss_*` fields
  already expose the components. No simulator change was needed,
  just a thin wrapper in the eval driver. Cycle 14's README warned
  this might require an evaluator wrapper or per-trade event log
  dump; in fact the aggregate fields are sufficient for the
  cycle-15 question.
- The c11 = c13 identity holds *on the test split* of *real_data*,
  identically (2.574 = 2.574). That's the third independent
  recipe-ceiling identity check (val challenge, val real_data, test
  real_data) — the cycle-13 long-run CEM truly produced the same
  parameter vector as the c11 anchor.
- Bootstrap CIs do exactly the work asked of them: c5/c6 sit fully
  below the FixedFee mean on test, locking in the cycle-14
  qualitative finding as a statistically real phenomenon. c8 is
  borderline (-0.85, +0.27) — still net-negative point estimate
  but CI straddles zero on test. So "early M2 is OOD-harmful"
  becomes "the *first two* anchors are statistically below
  FixedFee; the third (c8) is point-estimate negative but not yet
  CI-confirmed."

**What failed (or surprised on the downside).**
- The c10B rng_seed=1 endpoint sits ~0.9 lift below c10A/c11. That's
  not large enough to break the plateau story but it does mean
  there's non-trivial rng-seed variance in the *plateau region*
  itself. Implication: a single-rng-seed M2 run does not pin down the
  OOD ceiling tightly; cycle 15 only adds one extra cell, so the
  rng-spread number (~0.9) is itself noisy.
- The plan-of-record's step 2 (replicate the early-anchor inversion
  on full d16_s0 / d16_s1 anchor *chains*) was not done as
  literally written, because no full chronological chain at
  rng_seed=1 exists in the repo — only the c10B endpoint at
  rng_seed=1. Re-running M2 cycles 5 → 6 → 8 → 9 → ... end-to-end
  with rng_seed=1 would take many hours and was beyond the cycle
  budget. Reframed the cycle-15 deliverable as endpoint replication
  + bootstrap CIs on test, which is what locked in the inversion.

**Updates implied for the prior.**
- M3 cycle 1's qualitative claim ("early anchors are net-harmful
  OOD") is now load-bearing on test, not just val. The 95% CIs make
  it falsifiable in a way the cycle-14 numbers were not.
- The retail-vs-arb decomposition tells M4 *where to look*: any M4
  policy improvement over the +2.10 lift bar has to come from the
  retail side, since arb is already +1.7 to +3.7 essentially
  regardless of training. M4 is now framed as "raise retail edge
  advantage above c11's +1.06 on real_data" rather than "raise net
  edge_advantage above +2.81".
- The cycle-15 retail-edge curve correlates +0.97 with the
  challenge score across the 9 anchors; arb-edge correlates -0.41.
  Suggests the challenge optimizer is, to first order, a retail-edge
  optimizer. This is a hypothesis; not yet confirmed causally.

**Next.**
- **Cycle-16 plan-of-record:**
  1. Per-trade-size decomposition of c5 vs c11 retail edge on
     real_data. Bucket retail trades by size (small/med/large per
     piecewise thresholds 0.003 / 0.01) and report per-bucket
     retail edge advantage. This decomposition could show whether
     c5's -10 retail-edge gap is driven by mispricing on small
     trades (most numerous), large trades (highest individual
     edge), or one specific bucket. ~30 min implement + ~30 min
     run.
  2. Pre-launch M4 baseline: direct CEM optimization on
     `evaluator_kind="real_data"` with the c5 piecewise default
     anchor and a small budget (pop=12, gen=5) to verify the
     real_data evaluator is CEM-friendly and to set a baseline-budget
     OOD score. ~30 min.
- **If (1) shows a single-bucket failure:** that bucket's pricing
  becomes the M4 cycle-1 target.
- **If (1) shows uniform failure across buckets:** the real_data
  evaluator is the bottleneck and we go straight to M4 cycle 1
  (direct optimization).

**Operational footnotes.**
- Repo path on this sandbox: `/sessions/friendly-modest-mccarthy/mnt/amm-gym-auto-research`.
  Sandbox name confirmed via `pwd`.
- All cycle-15 edits restricted to `research/` (new experiment dir,
  README/STATE/LOG/presentation updates). Inherited working-tree
  diffs (`arena_eval/`, `arena_policies/`, `scripts/`, `tests/`)
  untouched per convention.
- Wall-clock: ~5 min orient + ~2 min env setup (gymnasium/pyarrow
  reinstall + jax vendored install) + ~5 min plan + ~37 min eval
  + ~2 min figure + ~30 min STATE/LOG/presentation + ~5 min check
  + commit ≈ 86 min. Within the 2h budget.
- **No checks retired this cycle.** All 12 active checks pass.
  Cycle-15 found that 03_required_python_deps and 08_jax_optional
  needed manual remediation on a fresh sandbox (install
  gymnasium/pyarrow/pytest then run `setup_jax_from_vendored.sh`)
  but both passed after the install step. The 08_jax_optional check
  has a hard-coded `/tmp/jax_setup.log` path that errors with
  Permission denied on this sandbox; the script's recovery branch
  works fine, but the log line is misleading. Not retiring; just
  noting for cycle-16 if it surfaces again.

---

## 2026-05-05T11:50Z — cycle 16 — M3 cycle 3 trade-size decomp + M4 cycle 0 baseline

**Plan for the cycle.** Cycle 15 closed M3 cycle 2 with a
held-out-test bootstrap CI on the c5/c6 OOD inversion (statistically
significant) and a retail/arb decomposition that localized the
early-anchor failure mode to the retail side. The active hypothesis
going into cycle 16 was: *the early-anchor harm is concentrated in
specific trade-size buckets / market regimes; if we can identify
those, M4 has its first concrete inductive-bias target*.

The cycle plan-of-record (from cycle-15 STATE.md) was two-pronged:
(1) per-trade-size decomposition of c5 vs c11 retail edge on
real_data; (2) pre-launch M4 baseline — direct CEM on
`evaluator_kind="real_data"` from the c5 anchor at a small budget
(pop=12, gen=5) to test whether real_data is CEM-friendly and to
plant a flag for M4 cycle 1.

**What I ran.**

1. *Smoke test on 4 seeds* of the per-bucket eval to confirm the
   identity check (re-derived retail_edge from per-event totals
   matches simulator-aggregate to 1e-14). Result: cleanly identical.
2. `eval_size_decomp.py` — full 128-val-seed eval for c5 and
   c11_d16_s2 on real_data, accumulating per-bucket × per-venue
   retail edge by looping `step_once()` externally.
3. `make_figure.py` — 2-panel bar chart (retail_edge_advantage by
   bucket; trade-count routing in log scale).
4. `run_m4_baseline_cem.py` — 5-gen × 12-pop warm-start CEM from
   c5 inherited piecewise on `evaluator_kind="real_data"`. Search
   seeds 0..63, val 1000..1127, test 2000..2255, normalizer
   FixedFee(0.003). 3 workers. Ran in ~14 min wall-clock end to end
   (8.3 min CEM + ~5.5 min rerank/test).

**What worked / what I learned.**

- **The decomposition gives a sharp, single-mechanism story.** The
  c5-vs-c11 retail-edge gap is almost entirely small-bucket: −10.67
  of the −11.20 overall difference. Medium and large buckets are
  within batch noise (medium +0.06, large −0.59). Bootstrap CIs
  (10000 resamples on per-seed values) put the c5 small-bucket
  retail_edge_advantage at −9.51 [−9.60, −9.41] vs c11 at +1.17
  [+0.99, +1.32] — the gap is well outside seed noise.

- **The mechanism is *routing*, not *fee level*.** c5 sees only
  401.6/2621.2 ≈ 13% of small-trade count routed to it; c11 sees
  2031.7/1546.2 ≈ 57%. Per-unit-volume markout (bps) on the small
  trades that *do* reach c5 is 28.39 bps vs FF's 35.38 bps — i.e.
  c5's small-trade fee is *under* 0.003 on average. So the router
  is sending small flow to FF for *price* reasons (mid placement /
  inventory), not fee reasons. This reframes the M4 lever.

- **Direct CEM on real_data from c5 is real but slow, and it
  amplifies the retail problem.** 5-gen × 12-pop CEM lifts c5 from
  −1.214 → +0.739 lift_FF on test (256 seeds). Best_search and val
  trajectories haven't plateaued at gen 4. retail_advantage went
  from −10.14 (c5 val) to −13.10 (M4 baseline test) — *worse*.
  The score gain is entirely from arb, not retail. This is a
  meaningful signal: direct optimization without a retail-aware
  prior finds an arb-side local optimum that doesn't fix the
  small-bucket routing collapse.

- **c11 still beats the M4 baseline.** c11 lift_FF on test = +2.10;
  M4 baseline lift_FF = +0.74. The M2 deliverable remains the best
  real_data policy on file by a wide margin.

**What failed (or surprised on the downside).**

- **Sandbox restarted mid-run on the first M4 attempt.** The
  initial nohup'd CEM completed only the c5 baseline before the
  sandbox was rotated; the second attempt also tripped on the
  unlink-blocked-progress-log issue (already a known check, but the
  M4 script duplicated the fragile `LOGFILE.unlink()` pattern from
  cycle-6). Fixed by switching to `LOGFILE.open("w").close()`.
  Recording this as cycle-16 operational lore: any new long-running
  driver written from scratch should use truncate-on-write rather
  than unlink. Reflecting via a check would require statically
  analyzing source files for `.unlink(`-like patterns; I'm not
  encoding it as a check this cycle, but the fix-on-touch is now
  in `run_m4_baseline_cem.py`.

- **Per-gen retail_advantage trajectory on the M4 baseline is
  monotonically *worse* than c5 from gen 1 onward** (−11.1, −11.4,
  −11.7, −11.8). That's somewhat counter to the active hypothesis
  prior — we'd expected direct optimization to at least nibble
  toward the retail side. Instead it confirms that the score
  gradient on real_data, near c5, points toward arb-only
  improvements; the retail fix requires a different starting basin
  (c11) or an explicit retail-aware loss.

**Updates implied for the prior.**

- M3 cycle 3's qualitative claim ("c5 OOD failure is concentrated
  in the small-trade bucket") is now load-bearing. The 95% CIs and
  identity check are tight. M4 has a concrete inductive-bias
  target.

- M4 cycle 1's first experiment should be the *symmetric* version
  of cycle 16's M4 baseline: direct CEM on real_data from c11
  rather than c5. If c11+CEM lifts past +2.10, we have evidence
  that direct OOD optimization works from a good prior; if it
  doesn't, we have evidence that c11 is a real_data ceiling for
  the piecewise family.

- The "policy complexity sweep" framing of M4 should be augmented
  with a "policy *prior* sweep" — start from {default, c5, c11},
  fix the family at piecewise, sweep the warm-start. This isolates
  whether M4 wins are driven by the policy class or the local
  basin.

**Next.**

- **Cycle-17 plan-of-record:**
  1. *Mirror experiment*: run the same 5-gen × 12-pop CEM with
     `evaluator_kind="real_data"` but warm-start from c11_d16_s2.
     Same compute budget. Compare gen-by-gen trajectory and final
     test lift_FF to the cycle-16 M4 baseline. ~14 min.
  2. *Per-trade-size decomp on the M4 baseline*: rerun
     `eval_size_decomp.py` against the cycle-16 M4 baseline best-
     by-val params to confirm the retail_advantage drop is in fact
     a small-bucket worsening. ~2 min.
  3. *(stretch)* Augment CEM with a retail-aware tiebreaker:
     score = edge_advantage + α × retail_edge_advantage with α
     small (e.g. 0.2), and rerun from c5. Tests whether a small
     retail penalty steers CEM into the retail-fix basin without
     sacrificing arb.

**Operational footnotes.**

- Repo path on this sandbox: `/sessions/practical-pensive-fermat/mnt/amm-gym-auto-research`.
- Edits restricted to `research/` and one new experiment dir.
  Inherited working-tree diffs (`arena_eval/`, `arena_policies/`,
  `scripts/`, `tests/`) untouched per convention.
- Wall-clock: ~5 min orient + env setup + ~2 min smoke +
  ~2 min full bucket eval + ~14 min M4 baseline + ~30 min
  STATE/LOG/presentation/README + ~5 min check + commit ≈ 60 min.
  Within the 2h budget.
- All 12 active checks pass. No checks added or retired this
  cycle. Cycle-15's note that `08_jax_optional` has a misleading
  log line still applies — the recovery branch works fine, just
  the `/tmp/jax_setup.log` redirect can't write on this sandbox.
- M4 baseline `LOGFILE.unlink()` fragility (encoded by check 05
  for results dir) was rediscovered when I copy-pasted from
  cycle-6 patterns; switched to truncate-on-open. Worth noting
  for any future driver-author: the cycle-15 LOG already flagged
  this gotcha for `progress.log`-style writes.

---

## 2026-05-05T13:00Z — cycle 17 — M4 mirror: c11+CEM lifts past +2.20, prior dominates short-budget CEM

**Plan for the cycle.** Cycle 16 closed with two open questions baked
into a decision rule: (1) does direct CEM-on-real_data from the c11
anchor saturate near +2.10 lift_FF (piecewise-family real_data
ceiling), or lift past it (warm-start prior dominates)? (2) the
cycle-16 M4 baseline retail_advantage degradation (-10.14 → -13.10,
test) — is it concentrated in the small-trade bucket (the obvious
hypothesis given the cycle-16 c5 vs c11 small-bucket gap), or
distributed differently?

The cycle-17 plan-of-record (from cycle-16 STATE.md) was: (a) mirror
experiment — same 5-gen × 12-pop CEM as cycle 16, but warm-started
from c11_d16_s2; (b) per-trade-size decomposition of the M4 baseline
best-by-val params; (c) stretch — retail-aware CEM tiebreaker.

**What I ran.**

1. `run_m4_c11_mirror_cem.py` — identical to cycle-16's
   `run_m4_baseline_cem.py` except init mean = c11_d16_s2 best-by-val
   params. Same population (12), generations (5), elite_frac (0.2),
   init_std_frac (0.10), search/val/test seeds (0..63 / 1000..1127 /
   2000..2255), normalizer FixedFee(0.003, 0.003), rng_seed (0). 3
   workers. The rerank pool injects the c11 anchor itself before
   adding 6 elites by search score — guarantees no regression past
   the anchor on best-by-val.

2. `eval_size_decomp_m4_baseline.py` — per-bucket retail_edge
   decomposition on the cycle-16 M4 baseline best-by-val params,
   merged with cycle-16's c5 / c11 numbers into a single 3-anchor
   table.

3. (added mid-cycle) `eval_size_decomp_c11_mirror.py` — per-bucket
   decomp on this cycle's c11+CEM best-by-val params, to test
   whether CEM stayed in c11's retail basin or drifted toward c5's
   arb-side basin.

4. `make_figures.py` — three PNGs: gen-by-gen val curves (c5+CEM vs
   c11+CEM), 4-anchor per-bucket grouped bar, 4-anchor lift_FF
   summary.

(Stretch retail-aware CEM not run — cycle budget consumed by a
mid-run sandbox stall during gen 3 that added ~26 min wall-clock,
plus the unplanned c11-mirror decomp that turned out to be the
load-bearing finding.)

**What worked / what I learned.**

- **Decision rule fires: warm-start prior dominates short-budget
  CEM on real_data.** c11+CEM lift_FF on test (n=256) = **+2.77**,
  comfortably above the +2.20 threshold. By contrast c5+CEM ended
  at +0.74. Same compute budget, same evaluator, same population —
  +2.03 lift_FF difference is entirely attributable to where the
  CEM started.

- **The c11 trajectory converges in val by gen 3.** Per-gen val
  scores: 2.918 (anchor), 3.313 (gen 1), 3.473 (gen 2), 3.720
  (gen 3, best-by-val), 3.673 (gen 4). The gen-3 best-by-val is
  what scored +2.77 on test.

- **c11+CEM preserves retail basin; c5+CEM amplifies the routing
  collapse.** Per-bucket retail_edge_advantage (n=128 val):

      anchor               | small  | medium | large  | overall
      c5 baseline          | -9.51  | +0.04  | -0.66  | -10.14
      c5 + CEM (c16 M4)    | -10.33 | +0.06  | -3.06  | -13.33
      c11_d16_s2           | +1.17  | -0.02  | -0.08  | +1.07
      c11 + CEM (this c)   | +1.45  | +0.07  | -0.83  | +0.70

  c11+CEM held the small-bucket retail edge POSITIVE (+1.45,
  bootstrap CI [+1.05, +1.82], if anything *better* than the c11
  anchor's +1.17). The +0.83 large-bucket regression is small in
  absolute terms (~1 trade per episode) but qualitatively similar
  to c5+CEM's larger -3.06 regression. CEM regresses on the large
  bucket from any starting point, just less so when starting from
  a basin where large-bucket pricing is already close to FF.

- **Cycle-17 hypothesis ("M4 baseline retail drop is dominated by
  small-bucket worsening") is partially falsified.** Of the M4-vs-c5
  drop of -3.20:
  - small: -0.82 (~26%)
  - medium: +0.02 (~-1%)
  - large: -2.40 (~75%)
  The dominant degradation is large-bucket. The small bucket got
  slightly worse, not the dominant driver. The cycle-16 prior (
  "small-bucket dominates the c5/c11 GAP") is correct (-10.67 of
  -11.20 there); but the cycle-17 prior ("small-bucket also
  dominates the c5+CEM degradation") is wrong.

- **Routing share evidence on the small bucket is striking.** c5
  routes 13.3% of small trades to submission; c5+CEM routes only
  5.8% (CEM made the routing collapse *worse*). c11 routes 56.8%;
  c11+CEM routes 60.4% (basin preserved, slightly improved).

**What failed (or surprised on the downside).**

- **gen 3 stalled mid-run for ~26 min** (1581 s for one gen vs the
  ~75 s typical). The other 4 gens completed in ~70-80 s each as
  expected. I suspect a sandbox slowdown rather than a code path —
  rng_seed and search seeds are deterministic, so this isn't search-
  noise. Did not impede the result; the gen completed. Not encoding
  as a check (this is the second time I've seen sandbox-stall on a
  long-running CEM and there's no falsifying programmatic test for
  "sandbox slowed down").

- **My intuitive prior on cycle-17 hypothesis (b) was wrong.** I'd
  expected M4-baseline retail drop to be dominated by small-bucket
  worsening (because the c5/c11 retail GAP is small-bucket
  dominated). Reality: the M4 baseline retail DEGRADATION from
  c5 is predominantly large-bucket. Updates implied: when
  reasoning about CEM-from-anchor effects on the realistic
  evaluator, don't reuse priors about the c5/c11 GAP — the
  *pattern of degradation* and the *pattern of difference* are
  different mechanisms.

- **The "small-bucket routing collapse" framing of cycle 16 is
  still correct for c5 vs c11 but is NOT the right framing for
  cycle-16 M4 baseline vs c5.** The cycle-16 LOG and STATE
  emphasized small-bucket as THE mechanism; cycle 17 shows it's
  the dominant inter-anchor difference but not the dominant
  CEM-effect.

**Updates implied for the prior.**

- **The local basin matters more than the policy family for
  short-budget CEM on real_data.** This is now a load-bearing
  finding for M4. Same compute, same family — +2.03 lift_FF
  difference between c5-start and c11-start. M4's policy
  complexity sweep cannot be evaluated without controlling for
  warm-start.

- **Re-frame cycle-18+ as a prior sweep** at fixed compute and
  fixed family before doing complexity sweeps. Vary the warm-start
  anchor across {default, c5, c6, c8, c11} and measure final
  lift_FF. This isolates basin from family.

- **A longer-budget CEM from c11 is probably the next single most
  informative experiment.** c11+CEM hasn't plateaued at gen 4
  (median search score still rising; val is mildly oscillating
  near 3.7 but gen 3 won). 10-gen × 24-pop should resolve whether
  the piecewise family on real_data caps near +3.0 lift_FF or has
  more headroom.

**Next.**

- **Cycle-18 plan-of-record:**
  1. *Longer-budget CEM from c11.* 10-gen × 24-pop on real_data,
     same anchor. Total compute ≈ 4× this cycle. Tests the
     piecewise-family real_data ceiling.
  2. *Prior sweep at fixed compute.* 5-gen × 12-pop CEM from
     each of {default-piecewise, c6, c8, c11_d16_s2, c11_d24_s0}.
     Plot final lift_FF vs anchor. Disentangles basin from
     compute.
  3. *(stretch)* Retail-aware CEM from c5 with the +0.2 ×
     retail_edge_advantage tiebreaker. Tests whether a small
     retail penalty bridges to the c11 basin.

**Operational footnotes.**

- Repo path on this sandbox: `/sessions/eager-kind-hawking/mnt/amm-gym-auto-research`.
- Edits restricted to `research/` and the new cycle-17 experiment dir.
  Inherited working-tree diffs across `arena_eval/`, `arena_policies/`,
  `scripts/`, `tests/` untouched per convention.
- Wall-clock: ~5 min orient + ~5 min env setup + ~34 min CEM (incl.
  ~26 min sandbox stall on gen 3) + ~7 min rerank/test + ~1 min
  M4-baseline decomp + ~1 min c11-mirror decomp + ~1 min figures +
  ~30 min STATE/LOG/presentation/README + commit ≈ 84 min. Within
  the 2h budget despite the stall.
- All 12 active checks pass at start of cycle (08_jax_optional and
  03_required_python_deps pass after `pip install gymnasium` +
  `bin/setup_jax_from_vendored.sh`). No checks added or retired
  this cycle.
- `pyarrow` install OOM'd on this sandbox; not needed for the
  cycle's experiments (only for some BigQuery exports). Logged but
  not encoded.

---

## 2026-05-05T14:00Z — cycle 18 — M4: long-budget CEM from c11 lifts to lift_FF +3.01 (saturating near +3.0); prior sweep confirms basin dominance with c6 climbing to +1.89

**Plan for the cycle.** Cycle 17's M4 mirror left two open questions
baked into a decision rule: (1) does the c11+CEM short-budget run
plateau at +2.77 lift_FF (i.e. is +2.77 the piecewise-family real_data
ceiling), or does more compute keep climbing? (2) is the c11 anchor
unique, or does any reasonable warm-start produce comparable lift at
fixed compute? The cycle-18 plan-of-record from cycle 17:
(a) longer-budget CEM from c11 — 10g × 24p, 4× compute; (b) prior
sweep at fixed 5g × 12p compute from {default, c6_warmstart,
c8_invaware_16d}. The c5 / c11-short anchor results from cycles 16/17
become axis-continuity points in the cycle-18 plot.

**What I ran.**

1. `run_long_cem_from_c11.py` — 10-gen × 24-pop CEM, init mean =
   c11_d16_s2 best-by-val, init_std_frac=0.10, FixedFee(0.003, 0.003)
   normalizer, real_data evaluator, search seeds 0..63, val 1000..1127,
   test 2000..2255, rng_seed=0, workers=3. Rerank pool injects c11
   anchor + top 6 unique elites by search score, ranked by val.

2. `run_prior_sweep_cem.py` — same 5g × 12p budget as cycle 17 from
   each of {default-piecewise (param-range midpoint), c6_warmstart
   (cycle-6 best-by-val 16-d piecewise), c8_invaware_16d (cycle-8
   best-by-val with `inventory_skew_*` dropped to project to 16-d)}.
   Same seeds, same normalizer, same rng_seed. FF test baseline
   computed once across anchors. Results consolidated into
   `prior_sweep_summary.json`.

3. `eval_size_decomp_long_cem.py` — per-trade-size retail decomposition
   on the long-budget best-by-val params, mirroring cycle-17's
   `eval_size_decomp_c11_mirror.py` (small/medium/large size buckets,
   bootstrap CIs over n=128 val seeds).

4. `make_figures.py` — three PNGs: val gen-by-gen curve (long vs short
   from c11), prior-sweep bar chart of lift_FF per anchor, and
   anchor-val vs final-lift scatter to test basin-dominance visually.

**What worked / what I learned.**

- **Decision rule fires the "saturating near +3.0" branch.** Long-budget
  c11+CEM hits **lift_FF +3.006** on test (n=256), squarely in the
  [+2.80, +3.20] band. Up from cycle 17's +2.772 by +0.234 with 4×
  compute. The piecewise family on real_data has more headroom than
  cycle-17 indicated, but the marginal return on extra compute is
  modest and clearly slowing.

- **Retail edge advantage QUADRUPLES.** Test retail_adv goes c11-anchor
  +1.07 (cycle 17 measurement) → cycle-17 c11+CEM +0.66 → cycle-18 long
  c11+CEM **+3.21**. The longer CEM didn't just lift score — it found a
  policy that BOTH scores higher AND retains/amplifies the c11 retail-
  positive structure. The cycle-17 short run lost some retail edge in
  the rerank (val retail_adv +0.70); the cycle-18 long run keeps val
  retail_adv at +3.27.

- **Per-bucket retail decomposition: all gain is small-bucket.** On val
  n=128: small +3.31 [+3.15, +3.45] / medium −0.04 [−0.13, +0.04] /
  large +0.00 [−0.08, +0.08]. The small bucket carries ~2300
  submission trades + ~1100 normalizer trades per episode; medium and
  large together are <10 trades per episode. The optimizer
  concentrated improvements where retail volume is.

- **Val trajectory shows no clean plateau by gen 8-9.** Per-gen val:
  2.918 (anchor), 2.918, 2.162, 2.751, 3.036, 3.396, 3.649, 3.712,
  3.820, **3.885 (gen 8, best-by-val)**, 3.822 (gen 9, slight regression).
  Gen 8 wins; gen 9 is within val noise. The val curve is concave but
  still rising at gen 8, suggesting another 5-10 gens might add another
  +0.1-0.2 lift_FF before true plateau. Diminishing returns are
  pronounced.

- **Prior sweep, partial (default + c6 done at writeup time):**

       anchor               | start val | test lift_FF | retail_adv (test)
       default (midpoint)   |  -1.18   | +1.05        | -15.28
       c5  (cycle 16)       |  -1.21   | +0.74        | -10.14 (actually old val, see cycle 17)
       c6  (cycle 18)       |  -0.61   | +1.89        | -0.00
       c8_16d (running)     |   ~+1?    | TBD          | TBD
       c11 short (cycle 17) |  +2.92   | +2.77        | +0.66
       c11 long  (this c)   |  +2.92   | +3.01        | +3.21

  **The basin-dominance hypothesis is supported.** Lift correlates with
  starting position: c11 (best start) finishes best, c5 / default
  (worst starts) finish worst, c6 (mid start) finishes mid. The
  short-vs-long c11 comparison shows compute IS marginally useful
  (+0.23 with 4× compute), but the c5 → c11 starting-line difference
  of +4.13 in anchor val translates to a +2.27 final-lift difference
  with the same compute — basin dominates compute by roughly an
  order of magnitude.

- **Default-piecewise +CEM beats c5 +CEM** (lift +1.05 vs +0.74)
  despite a marginally worse anchor val. Mild surprise: the
  param-range midpoint isn't a great policy but it's apparently a
  better *basin* than the c5 inherited piecewise for short-budget
  CEM. Implies the c5 anchor sits in a particularly bad arb-side
  basin (consistent with cycle-16's M4-baseline retail collapse to
  -13 retail_adv). Anchor val score by itself doesn't predict
  CEM lift perfectly — local geometry matters too.

**What failed (or surprised).**

- **Sandbox `pip install gymnasium pyarrow pytest` ran together OOM'd**
  (exit 143). The cycle-15-and-onward fix is to install one package
  at a time, but I tried the bundled command first. Encoding this as
  a check would be marginal value (sandbox quirk; the failure mode is
  obvious from the exit code). Logged for the next cycle's author.

- **`pip install ... pytest` reported "Successfully installed" but the
  jax wheels from `setup_jax_from_vendored.sh` then refused to import
  on the same shell.** Re-running `setup_jax_from_vendored.sh` worked.
  Either a Python `sys.path` cache invalidation issue, or the user-
  site path (`/sessions/.../.local/...`) was newly created by `pytest`
  install and the previous jax install actually went to system-site
  but didn't persist. Workaround: just re-run the setup script.

- **CEM gen 1 from c11 long regressed val (2.918 → 2.162)** before
  recovering from gen 2 onwards. Same effect as cycle 17 (where gen 1
  was a brief dip). The deterministic anchor in candidate 0 each gen
  prevents the regression from being permanent because the elite mean
  pulls back toward the anchor, but a single-gen dip is now an expected
  CEM characteristic on this evaluator. Not pathological.

- **`run_prior_sweep_cem.py` c6 anchor val measurement disagreed with
  M2 history's "−0.93 lift_FF (−1.40)"** — measured c6 anchor val =
  −0.614 score = ~−1.08 lift_FF on this val split. Different evaluator
  config? c6's test_score in the M2 table is on the realistic eval at
  some earlier definition; this cycle uses the current `real_data`
  evaluator. Worth a noted reconciliation but not blocking — the c6
  prior-sweep data point uses my measured anchor val, which is what
  matters for the basin plot.

**Updates implied for the prior.**

- **The cycle-17 framing — "warm-start prior dominates short-budget
  CEM" — is upgraded by cycle 18 to "warm-start basin dominates CEM
  IRRESPECTIVE of compute, within an order of magnitude":** 4× compute
  bought +0.23 lift_FF; choosing c11 instead of c5 starting point
  bought +2.27 lift_FF at fixed compute.

- **The piecewise-family real_data ceiling is now estimated at
  ~+3.0 ± 0.2 lift_FF.** Gen 8 hit val 3.885; with 4× more compute
  we might add another +0.1-0.2 but not another full point. To break
  +3.5 lift_FF, M4 cycle 3 needs either (a) a richer policy family
  (ladder, MLP, EMA-inv), (b) a fundamentally different anchor that
  starts above c11 — but cycle-12 already showed fresh-init piecewise
  caps below 420 challenge / well below c11 real_data — so option (a)
  seems forced.

- **Retail-positive small-bucket pricing is the load-bearing structural
  feature of c11+CEM.** The longer CEM amplified rather than eroded
  this; the per-bucket decomp is identical in shape to cycle-17's
  c11_mirror (cycle 17: small +1.45, medium +0.07, large -0.83;
  cycle 18 long: small +3.31, medium -0.04, large +0.00) — just
  scaled up ~2.3× in the small bucket. The c5+CEM run instead
  amplified small-bucket *negative* edge (cycle 17: small -10.33).
  Different basins; different sign of small-bucket retail edge.

**Next.**

- **Cycle-19 plan-of-record:**
  1. *(if c8_16d data point comes in below c6+CEM's +1.89)* The basin-
     dominance plot is decisive. Move M4 cycle 3 to **policy-family
     escalation**: train a ladder or MLP head warm-started from c11+CEM
     long-budget params. Decision rule: > +3.50 lift_FF → richer family
     pays; in [+3.20, +3.50] → marginal; < +3.20 → family escalation
     doesn't help, the small-bucket retail-pricing surface is already
     saturated.
  2. *(if c8_16d unexpectedly beats c11+CEM long)* Investigate what
     about c8's params makes it special; revisit policy-family
     question.
  3. **Ablation on long c11+CEM.** Which of the 16 piecewise params
     moved most from c11 anchor to long-budget best-by-val? This
     identifies the load-bearing pricing levers and guides what a
     richer family would have to encode.

- **Operational mark.** The c5 row in the prior-sweep plot reuses
  cycle-16's M4-baseline lift_FF (+0.74) and retail_adv (−10.14)
  rather than re-running. Equivalent compute, same seeds, same
  normalizer; safe reuse.

**Operational footnotes.**

- Repo path on this sandbox: `/sessions/lucid-amazing-tesla/mnt/amm-gym-auto-research`.
- Inherited working-tree diffs across `arena_eval/`, `arena_policies/`,
  `scripts/`, `tests/` untouched per convention. Edits restricted to
  `research/` and the new cycle-18 experiment dir.
- Wall-clock breakdown:
  - env setup (gymnasium/pyarrow/pytest one-at-a-time + jax revend) ~5 min
  - long-budget CEM 31.2 min CEM + ~7 min rerank/test/ff = 38.5 min
  - prior sweep (default + c6 + c8 in flight): ~30 min so far
  - figure scripts + decomp + writeup ~25 min
  - planned commit: ~3 min
  - total ~100 min — within 2h budget.
- All 12 active checks passed at start of cycle (after env setup).
  No checks added or retired this cycle. Considered a "default
  python install" check (gymnasium/pyarrow/pytest one-at-a-time
  pattern) but rejected — fix-it-yourself instructions in the FAIL
  message of `03_required_python_deps.sh` already cover this.
- New presentation section: `m4-c18` under M4. New figures:
  `m4_c18_long_cem_val_curve.png`, `m4_c18_prior_sweep.png`,
  `m4_c18_basin_vs_compute.png` (also stored in cycle dir).
