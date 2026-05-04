# State — current cycle

**Last updated**: 2026-05-04 (cycle 6)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 6 lifted
the warm-start CEM headline from 414 → 432.7 on the held-out test
split. Gap to target (540) now **107.3 pts**.

## Current sub-task

Cycle 6 finished:

- **Warm-start CEM on `piecewise`** — wrote a stand-alone CEM in
  `research/experiments/2026-05-04-cycle6-m2-warmstart-cem/scripts/run_warmstart_cem.py`
  because the library's `cross_entropy_search_with_validation` has no
  warm-start API. Mean = inherited best params; init_std = 0.10 ×
  range; 24 candidates × 12 generations × 64 search seeds; 3-worker
  ProcessPoolExecutor. Wall-clock 27.2 min.
- **Result**: held-out test score (256 seeds) = **432.748** (val
  on 128 seeds = 433.566). **+18.74 pts vs cycle-5 starting line**.
  CEM converged tightly — best/elite_mean/median within 0.5 pts at
  gen 11. `edge_advantage` drift from -86 → -9 over 12 gens shows
  the policy moved toward more competitive spreads, not just wider
  defensive ones.
- **Gradient probe** (cycle-6 side): the differentiable surrogate's
  gradient direction is uninformative near the CEM-best basin. At
  LR=1e-5, val moves by +0.06 in one Adam step; at LR=1e-4, val
  moves by -0.23; at LR=1e-3, val collapses 425 → 280 in 2 steps.
  Smooth-train objective is -2895 vs exact +433 (sign + scale
  miscalibrated). **Cycle 7 should NOT pursue gradient-on-piecewise
  from CEM-best.**
- **Updated `presentation/index.html`** with the cycle-6 warm-start
  CEM section (headline insight, method, convergence figure, what we
  learned, gradient-probe caveat, cycle-7 plan).
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still
  untouched — convention from earlier cycles.

## Hypothesis going into cycle 7

Three distinct but cheap-to-test sub-hypotheses, in priority order:

1. **The +19 pt warm-start CEM lift is family-agnostic** — i.e. the
   inherited `_cem_1h_*` runs were *all* under-converged, and a
   warm-start CEM on each will lift by similar amounts. If true,
   `submission_compact` should land around 411 + 19 = 430 ± noise,
   `submission_basis` around 380 + 19 = 399, etc. If `submission_compact`
   instead lifts to ~470, the action-space matters more than we
   thought and we should commit to that family.
2. **The +19 pts isn't a single-seed artifact**. Cycle-6 used
   RNG_SEED=0 only. Re-running with seeds 1, 2 should show similar
   lifts (within ±2-3 pts).
3. **Gradient via `tape_smooth` is broken near optima**. The gradient
   probe falsified the cycle-5 prior that gradient would help past
   CEM. Revisit only after a smooth-vs-exact calibration study.

## Next action (cycle 7)

1. **Multi-family warm-start CEM**: copy
   `run_warmstart_cem.py` into a parametric driver, run on
   `submission_compact` and `submission_basis` (each ~30 min). Commit
   per-family. Compare deltas vs each family's inherited best. **(#1
   priority — directly addresses the "is this lift family-agnostic"
   question.)**
2. **RNG-seed sanity**: re-run cycle-6's piecewise warm-start CEM
   with `RNG_SEED=1` (and ideally seed=2). Same hyperparameters.
   Reports headline lift mean ± std over 3 seeds. ~30 min × N seeds.
   Can be queued as a low-priority background while #1 runs first.
3. **Update presentation** with the family-comparison table and the
   seed-sanity confidence interval. Pick the cycle-8 direction based
   on what cycle 7 reveals.

## Blockers for user

None. Push topology unchanged: sandbox commits to local main; host
launchd agent ships to origin every 15 min. Sandbox-side `git pull`
fails on DNS to github.com — expected, no action needed.

## Operational notes

- **Repo path on this machine**:
  `/sessions/vibrant-dreamy-volta/mnt/amm-gym-auto-research`
  (each cycle gets a different sandbox name; always confirm with
  `pwd`).
- **The host `.venv/bin/python` is Mac-Homebrew-only** and points
  into a path that doesn't exist on the Linux sandbox. Use system
  `python3` (3.10.12) directly. Project deps to install once per
  fresh sandbox: `pip install --break-system-packages gymnasium
  pyarrow "jax[cpu]"` (others — numpy, pandas, matplotlib — are
  preinstalled). Cycle 6 lost ~5 min figuring this out; subsequent
  cycles have this documented.
- **CPU**: 4 cores. Cycle-6 CEM used 3 workers and got a ~3x
  speedup on candidate evals (from ~300 s/gen sequential to 110
  s/gen parallel). Cycle 7's multi-family CEM should keep the
  3-worker convention.
- **Cycle-5 deferred items** still deferred: fixed-fee fine grid
  (50–200 bps × 1 bps step) — cheap but not on the critical path;
  pick up if cycle 7 has spare wall-clock.
- **`pip install --break-system-packages "jax[cpu]"`** newly required
  for cycle 6's gradient probe; jax not installed by default in the
  sandbox.
- **Wall-clock ledger**: cycle 6 ran ~30 min CEM + ~5 min docs + ~5
  min gradient probe ≈ 40 min. Well under the 2-hour budget. Most
  of the cycle was waiting on the CEM.
