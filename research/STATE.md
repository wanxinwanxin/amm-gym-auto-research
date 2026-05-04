# State — current cycle

**Last updated**: 2026-05-04 (cycle 8 — closed)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 8 closed
with a clean +13.7 pt M2 lift but the headline ablation flipped the
attribution: the "inventory-aware piecewise" framing turned out to be
a misnomer. The full lift came from a second pass of warm-start CEM
on bare piecewise, not from the new inventory dimension.

**Best M2 score: 446.61** (piecewise, cycle-8 ablation params, 256
test seeds). Up from cycle-6's 432.75. Gap to M2 target (540): 93.39
pts.

## Cycle-8 results (final)

1. **Inventory-aware piecewise warm-start CEM** — test 446.44 (val
   447.66, edge_advantage flipped from −19.30 to +26.16).
2. **Inventory ablation** — zeroing the 3 new inv-skew params drops
   the score by Δ = −0.17. Inventory dimension contributes nothing.
   The +13.69 pt lift over cycle-6 is entirely from refined 16-d
   piecewise dims found by the second-pass CEM.
3. **Init_std sweep on `submission_compact`** — clean U-shape:
   0.05 → +2.26, 0.10 → +5.30 (cycle 7), 0.20 → +2.80, 0.30 → +3.11.
   Cycle-7 default was the sweet spot; submission_compact is action-
   space saturated at this seed budget.
4. **Smooth-vs-exact correlation study** — *deferred to cycle 9* due
   to wall-clock spent on (1)+(3). Driver staged at
   `research/experiments/2026-05-04-cycle8-smooth-exact-correlation/scripts/run_smooth_exact_scatter.py`.

## Hypothesis going into cycle 9

The cycle-6 piecewise CEM was much further from convergence than its
log claimed. Two passes of warm-start CEM (cycle 6 then cycle 8)
added +33 pts over the cycle-5 starting line (414 → 446.6). Prior:
**~50/50 a third pass adds another +3-7 pts** before the basin is
truly converged.

## Cycle-9 plan-of-record

1. **Cycle-8b: third-pass warm-start CEM on bare piecewise.** Anchor
   at cycle-8 ablation params (446.61). Same 12-gen / pop=24 /
   init_std=0.10 recipe. Tells us whether two passes was a waypoint or
   the asymptote. Budget: ~30 min.
2. **Smooth-vs-exact correlation study** (deferred from cycle 8).
   Driver already staged at
   `research/experiments/2026-05-04-cycle8-smooth-exact-correlation/scripts/run_smooth_exact_scatter.py`.
   Anchor at cycle-8 best instead of cycle-6 best. ~15 min.
3. **EMA inventory feature.** Cheap second shot at inventory:
   replace instantaneous imbalance with an EMA over reserve deviation;
   warm-start CEM from the cycle-8 ablation params + EMA decay+weight
   defaults. ~30 min.
4. Update presentation; pick cycle-10 direction based on whichever
   signal is strongest.

## Blockers for user

None. Push topology unchanged: sandbox commits to local `main`; host
launchd agent ships to `origin` every 15 min.

## Operational notes

- **Repo path on this machine**:
  `/sessions/focused-trusting-heisenberg/mnt/amm-gym-auto-research`
  (each cycle gets a different sandbox name; always confirm with
  `pwd`).
- **The host `.venv/bin/python` is Mac-Homebrew-only** and points
  into a path that doesn't exist on the Linux sandbox. Use system
  `python3` (3.10.12) directly. Project deps to install once per
  fresh sandbox: `pip install --break-system-packages gymnasium
  pyarrow "jax[cpu]" pytest`.
- **Cannot `unlink` files in the sandbox results dir** — drivers open
  log files in `"w"` mode to truncate instead of deleting.
- **CPU**: 4 cores. Each CEM run uses 3 workers; ~120-145s/gen at
  pop=24.
- **Cycle-8 wall-clock**: ~30 min inventory CEM + ~5 min recovery
  rerank/test + ~12 min ablation/figures + ~45 min init_std sweep
  (with one 36-min sandbox stall at gen 2 of init_std=0.30) +
  ~10 min docs. Total ~100 min of useful work, plus ~36 min of
  unattributable sandbox stall.
- **Driver-killed-mid-rerank recovery pattern**: the inventory CEM
  process was reaped between sandboxes after gen 11 finished but
  before the test eval. Recovery is straightforward — the per-gen
  history JSON has every elite's params, so a recovery script can
  re-rerank the dedup'd top-N on val and re-score val-best on test.
  Pattern documented in
  `research/experiments/2026-05-04-cycle8-inventory-piecewise/scripts/recover_rerank_and_test.py`.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still
  untouched per the convention from earlier cycles.
