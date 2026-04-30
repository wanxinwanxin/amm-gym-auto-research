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
