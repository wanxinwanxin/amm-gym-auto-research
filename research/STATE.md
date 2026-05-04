# State — current cycle

**Last updated**: 2026-05-04 (cycle 9 — closed)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 9 ran two
12-gen warm-start CEMs back-to-back. The first (third-pass on bare
piecewise) lifted 446.61 → 448.81 (+2.19). The second (EMA-inventory
piecewise, 20 dims) lifted further to **456.64 on test** (val 457.62) —
but its ablation showed the entire +10 pt lift is from the CEM
exploring further within the 16 piecewise dims, *not* from the EMA
dimension itself (Δ attributable to EMA = +0.024, within noise).
**The inventory dimension is now genuinely dead** in two independent
formulations (cycle-8 instantaneous Δ = -0.17; cycle-9 EMA Δ = +0.024).

**Best M2 score: 456.64** (parameterised under
`ema_inventory_piecewise` but recoverable as bare piecewise — see
ablation; cycle-9 EMA best, 256 test seeds). Up from cycle-8's 446.61.
Gap to M2 target: 83.36 pts.

## Cycle-9 results (final)

1. **Third-pass warm-start CEM on bare piecewise** (priority #1) —
   complete. test 448.81 (val 450.05, edge_advantage +53.81 vs
   FixedFee). Δ vs cycle-8 ablation: +2.19. Convergence shape: val
   climbs 447.9 → 449.9 over gens 0-7, then flattens through gen 11.
   Headline figure at
   `research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/figures/three_pass_convergence.png`.
2. **EMA-inventory piecewise CEM + ablation** (priority #3) — complete.
   New 20-param policy `EMAInventoryPiecewiseStrategy` (16 piecewise
   core + 4 EMA-inventory: decay, skew_to_bid, skew_to_ask, dead_zone).
   Anchor parity 441.53 confirmed. CEM val climbs 447.9 → 457.6 over
   12 gens. Test 456.64 (Δ +10.03 vs cycle-8 ablation). **Ablation:**
   zeroing the 4 inventory params drops the score by Δ = +0.024 (i.e.
   negligible). The entire +10 lift is attributable to CEM finding
   refined 16 piecewise dims while wandering through 4 inert extra
   dimensions. Same pattern as cycle 8's inventory-aware result, with
   stronger lift in this case.
3. **Smooth-vs-exact correlation study** (priority #2) — *blocked
   on this sandbox*. `pip install jax` OOMs at the 3.9 GB / no-swap
   RAM budget; `arena_eval/diff_simple_amm` imports jax. Encoded as
   `bin/checks/08_jax_optional.sh`. Diagnostic value still high for
   revival of gradient-based optimization.

## Cumulative M2 history (post-cycle-9)

| pass | family | dims | test score | Δ vs prior | Δ attrib. inventory |
|--|--|--|--|--|--|
| start (c5) | piecewise | 16 | ~414 | — | — |
| pass 1 (c6) | piecewise | 16 | 432.75 | +18.7 | n/a |
| pass 2 (c8) | inv-aware piecewise | 19 | 446.61 | +13.9 | -0.17 |
| pass 3 (c9 #1) | piecewise | 16 | 448.81 | +2.2 | n/a |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | **456.64** | +7.8 | +0.02 |

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

The "16-d piecewise plateaus near 449" hypothesis from immediately
post-third-pass was wrong — the EMA-CEM (with 4 inert extra dims as
exploration noise) found another +7.8 pts on the same 16 piecewise
dims. So the right takeaway is: **CEM in higher-dim wraps with inert
inventory tails is a more effective optimizer of the piecewise core
than CEM directly on piecewise**. This is consistent with the cycle-7
finding that adding inert dims doesn't slow CEM; it strengthens that
into "adding inert dims appears to *help* CEM by giving it more
random search directions per generation."

The ceiling of bare piecewise is now at least 456.6 — we don't yet
know how much higher it goes. A 5th pass (24-d wrap with even more
inert tails? Or pop=48?) is probably the cheapest next experiment.
Prior: ~60% another +3-7 pts on test; ~30% diminishing returns kick
in around 458 ± 2; ~10% search has saturated this time.

The inventory hypothesis is **dead** (Δ ≈ 0 in two independent
formulations across cycles 8-9). Cycle 10 should not try a third
inventory variant; the mechanism is genuinely not what's holding
the score back.

## Cycle-10 plan-of-record

1. **Fifth-pass warm-start CEM with deliberate exploration noise.**
   Wrap the cycle-9 EMA-best (with inventory tail) under a 24-dim
   policy by adding 4 *random* but inert dimensions (e.g. extra
   normalized weights that don't enter the fee formula), and run
   pop=24/gen=12 warm-start CEM on those 24 dims. Test the
   "exploration-via-inert-dims" hypothesis directly. ~30 min.
2. **Escalate policy capacity in earnest.** Ladder/MLP. Warm-start
   CEM from cycle-9 best embedded as the level-1 rung. ~1 hr.
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
