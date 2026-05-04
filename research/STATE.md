# State — current cycle

**Last updated**: 2026-05-04 (cycle 7)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 7 ran
warm-start CEM on `submission_compact` and `submission_basis`,
falsifying the cycle-6 hypothesis that warm-start CEM lifts ~+19 pts
across all policy families. Best M2 score remains 432.75
(piecewise, cycle 6). Gap to target: **107.25 pts**.

## Current sub-task

Cycle 7 finished:

- **`submission_compact` warm-start CEM** (rng_seed=0): 410.78 →
  416.08 on test (val 416.88). Δ = +5.30 pts. Wall-clock 28.6 min.
  Population still drifting upward at gen 11 (best_search +1.0
  pt/gen) but val plateaued by gen 8 — suggests the basin shape is
  flat or the val noise floor is ~1 pt.
- **`submission_basis` warm-start CEM** (rng_seed=0): 380.26 →
  380.82. Δ = +0.56 pts (≤ val noise floor). Wall-clock 27.8 min.
  Population fully collapsed by gen 5: gen-over-gen val change
  ≤0.05 from gen 4. The inherited 14×22 CEM was already converged
  in this basin; warm-start refinement at 0.10×range adds nothing.
- **Multi-family figure** (`figures/family_comparison.png`,
  `figures/family_lift_bar.png`) and presentation update (cycle-7
  section) committed.

## Hypothesis going into cycle 8

The cycle-6 +18.7 pt warm-start lift is **not family-agnostic** — it
depends on (a) how under-converged the inherited optimizer was and
(b) whether the policy's action-space has structure to refine. Three
priorities for cycle 8, in order of value-of-information:

1. **Inventory-aware piecewise**: piecewise's structural advantage
   (large/medium/small × continuation/reversal) is doing real work.
   Adding a 3-param inventory-skew term with warm-start CEM should
   tell us whether the family has more headroom than the current
   432.7 wall, or whether we're action-space-saturated.
2. **Init_std sensitivity on `submission_compact`**: was the +5.3 a
   ceiling or a width-of-noise artifact? Sweep init_std_frac ∈
   {0.05, 0.20, 0.30} with 6-gen CEM each. If 0.20 or 0.30 lifts to
   ~430+, the cycle-6 prescription should be re-spec'd to "warm-start
   AND match init_std to inherited basin width."
3. **Smooth-vs-exact correlation study**: gradient via tape_smooth
   is dead from CEM-best (cycle 6). A scatter of 64 random
   neighborhood points (smooth_score vs exact_score) tells us whether
   the surrogate is salvageable or fundamentally miscalibrated.

## Next action (cycle 8)

1. **Implement `InventoryAwarePiecewise`** — fork
   `arena_policies.PiecewiseControllerStrategy`, add 3 inventory-skew
   parameters, register in `POLICY_SPECS`. Warm-start CEM from
   cycle-6 best. Budget: ~45 min.
2. **Init_std sweep on `submission_compact`** — copy cycle-7 driver,
   parametrize `init_std_frac`, run 3 sub-runs of 6 gens each.
   Budget: ~45 min.
3. **Smooth-vs-exact scatter** — 64 sample points in a 0.10×range
   neighborhood of cycle-6 piecewise best, score each on both
   surrogates, plot. Budget: ~20 min.
4. Update presentation with the cycle-8 outcomes and pick cycle-9
   direction based on whichever signal is strongest.

## Blockers for user

None. Push topology unchanged: sandbox commits to local `main`; host
launchd agent ships to `origin` every 15 min. Sandbox-side
`git pull` fails on DNS to github.com — expected, no action needed.

## Operational notes

- **Repo path on this machine**:
  `/sessions/trusting-great-dijkstra/mnt/amm-gym-auto-research`
  (each cycle gets a different sandbox name; always confirm with
  `pwd`).
- **The host `.venv/bin/python` is Mac-Homebrew-only** and points
  into a path that doesn't exist on the Linux sandbox. Use system
  `python3` (3.10.12) directly. Project deps to install once per
  fresh sandbox: `pip install --break-system-packages gymnasium
  pyarrow "jax[cpu]"`. Cycle 6 lost ~5 min figuring this out;
  cycle 7 carried over the same setup in ~30 s.
- **Cannot `unlink` files in the sandbox results dir** — the cycle-7
  driver opens log files in `"w"` mode to truncate instead of
  deleting. Pattern: `with logfile.open("w") as _f: _f.write("")`.
- **CPU**: 4 cores. Cycle-7 used 3 workers per CEM run; ~145s/gen
  ≈ same wall-clock as cycle-6 piecewise despite differing param
  counts (16, 20, 32). The bottleneck is `run_batch` × 64 search
  seeds, not policy inference.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still
  untouched per the convention from earlier cycles.
- **Cycle-7 wall-clock**: ~57 min CEM (28.6 + 27.8) + 10 min
  setup/figs/docs = ~67 min, well under the 2-hour budget.
