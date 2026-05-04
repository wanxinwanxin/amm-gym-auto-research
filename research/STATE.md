# State — current cycle

**Last updated**: 2026-05-04 (cycle 9 — closed; EMA CEM running)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 9 closed
the third-pass piecewise question: a 12-gen warm-start CEM anchored
at the cycle-8 ablation best lifted bare piecewise from 446.61 to
**448.81** on test (Δ = +2.19). The diminishing-returns pattern
across three independent passes (+18.7, +13.9, +2.2) says the 16-d
piecewise basin is finally near saturated. Closing the remaining
~91 pts to M2 target=540 will require a richer policy class.

**Best M2 score: 448.81** (piecewise, cycle-9 third-pass best, 256
test seeds). Up from cycle-8's 446.61. Gap to M2 target: 91.19 pts.

## Cycle-9 results (final + queued)

1. **Third-pass warm-start CEM on bare piecewise** (priority #1) —
   complete. test 448.81 (val 450.05, edge_advantage +53.81 vs
   FixedFee). Δ vs cycle-8 ablation: +2.19. Convergence shape: val
   climbs 447.9 → 449.9 over gens 0-7, then flattens through gen 11.
   Headline figure at
   `research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/figures/three_pass_convergence.png`.
2. **EMA-inventory piecewise CEM** (priority #3) — *in flight* at
   commit time. New policy `EMAInventoryPiecewiseStrategy` (20 params)
   added at `arena_policies/ema_inventory_piecewise.py`; 7-test parity
   suite green; CEM driver staged at
   `research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/scripts/run_ema_inventory_cem.py`.
   Anchor parity check (search-seed 441.53) confirms warm-start is
   well-defined. Cycle 10 lands the result.
3. **Smooth-vs-exact correlation study** (priority #2) — *blocked
   on this sandbox*. `pip install jax` OOMs at the 3.9 GB / no-swap
   RAM budget; `arena_eval/diff_simple_amm` imports jax. Encoded as
   `bin/checks/08_jax_optional.sh` so future cycles re-test the
   blocker rather than rediscover it. Diagnostic value still high
   for revival of gradient-based optimization.

## Cycle-9 infrastructure

- **`bin/checks/` scaffold landed.** 8 active checks (1 jax-optional
  expected to fail). `bin/run_checks.sh` driver iterates over
  executable scripts, reports one-line summary per check, exits
  nonzero on any failure. Per the prompt, cycle 1's missed scaffolding
  obligation was fulfilled here.
- Active checks: remote-origin sanity, system-python use,
  essential-deps importable, no-outbound-DNS, results-dir-unlink-
  blocked, arena_eval-imports, piecewise-anchor-score, jax-optional.

## Hypothesis going into cycle 10

The 16-d piecewise basin is near-saturated. Three CEM passes converge
toward test ~449 ± 2; a fourth pass at the same recipe is unlikely
to clear the noise floor. **Expected lift from a 4th pass: ~0-1 pt.**
The remaining 91 pts to target need policy capacity, not more search.

EMA-inventory result (pending): prior is ~30% it adds ≥ +2 pts on
test. The ablation in cycle 8 was strong evidence the dimension is
dead in instantaneous form; EMA is just a smoothed variant of the
same signal, so the underlying question — whether ChallengeTape
generates sustained directional flow at any horizon — should be
informed but probably not flipped by this experiment.

## Cycle-10 plan-of-record

1. **Land the EMA-inventory result.** Read the result file when the
   cycle starts, decide go/no-go for further inventory work.
2. **Escalate policy capacity.** First step: a multi-rung quote
   ladder (3-5 levels per side) anchored at cycle-9 best, warm-start
   CEM. ~1 hr.
3. **Unblock jax** if a small-footprint install is feasible (e.g.
   wheel index, CPU-only without `pip` build), so the smooth-vs-exact
   diagnostic and gradient methods come back online.
4. Update presentation; pick cycle-11 direction based on whichever
   signal is strongest.

## Blockers for user

- **jax install OOMs on this sandbox.** 3.9 GB total RAM, no swap.
  `pip install jax[cpu]` and `pip install jax jaxlib` both die with
  exit 143 (SIGTERM, OOM). Either the sandbox needs more RAM/swap, or
  we need a host-side install path. Documented as a passing-when-
  failing check (`bin/checks/08_jax_optional.sh`). Push-topology
  unchanged: sandbox commits to local `main`; host launchd agent
  ships to `origin` every 15 min.

## Operational notes

- **Repo path on this machine**:
  `/sessions/optimistic-amazing-mccarthy/mnt/amm-gym-auto-research`
  (sandbox name changes each cycle; always confirm with `pwd`).
- **The host `.venv/bin/python` is Mac-Homebrew-only** and points
  into a path that doesn't exist on the Linux sandbox. Use system
  `python3` (3.10.12) directly. Project deps to install once per
  fresh sandbox: `pip install --break-system-packages --no-cache-dir
  numpy gymnasium pyarrow pytest`. Skip jax until the OOM is
  resolved.
- **Cannot `unlink` files in the sandbox results dir** — drivers
  open log files in `"w"` mode to truncate instead of deleting.
- **CPU**: 4 cores. Each CEM run uses 3 workers; ~120-125s/gen at
  pop=24, dim=16. ~125-130s/gen at dim=20.
- **Cycle-9 wall-clock**: ~5 min orient + ~10 min checks scaffold
  + ~30 min third-pass CEM + ~5 min figure/presentation/STATE/LOG
  + ~30 min EMA CEM (started in parallel with the cleanup work,
  will run for a few more minutes after the cycle's commit).
- **`bin/checks/` enforced policy** (per AUTORESEARCH_PROMPT.md):
  every cycle should run `bash bin/run_checks.sh` first thing in
  the orient phase. Cycle-9 confirmed all checks green except
  the optional jax check.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still untouched
  per convention; cycle-9's only edits to those areas were:
  + `arena_policies/__init__.py` — exported new EMA policy
  + `arena_policies/ema_inventory_piecewise.py` — new file
  + `arena_search/simple_amm_search.py` — registered new policy
  + `tests/test_ema_inventory_piecewise.py` — new file
