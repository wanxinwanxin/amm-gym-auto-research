# State — current cycle

**Last updated**: 2026-05-05 (cycle 16 — closed)

## Active milestone

**M3 cycle 3 (closed) → M4 cycle 0 (closed) → M4 cycle 1 (next).**
Cycle 16 (this cycle) ran the per-trade-size decomposition that the
cycle-15 plan-of-record requested, and ran the M4 pre-launch
baseline as a small-budget direct-CEM-on-real_data experiment from
the c5 anchor. Both produced sharp findings; M4 cycle 1 has a
concrete plan.

## Headline numbers (held; reproduced cycle 16)

- **Best M2 score (challenge test, n=256): 456.80**
  [CI 448.0, 465.7] — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable).
- **Best real_data lift_FF (test, n=256): +2.104**
  for c11 d16_s2 (same anchor; OOD).
- **M4 baseline lift_FF (test, n=256): +0.739**
  (cycle-16 5-gen × 12-pop CEM from c5 on real_data).

## Cycle-16 verdict

1. **Cycle-15's "early anchors are net-harmful OOD on retail
   side" finding now has a *single-mechanism* explanation.** The
   c5-vs-c11 retail_edge_advantage gap is almost entirely small-
   bucket: −10.67 of the −11.20 overall difference. Medium and
   large buckets are within batch noise (medium +0.06, large
   −0.59). 95% bootstrap CIs on the small-bucket gap put c5 at
   −9.51 [−9.60, −9.41] vs c11 at +1.17 [+0.99, +1.32].
2. **The mechanism is a *routing collapse*, not a fee-level
   problem.** c5 receives ~13% of small-trade count (401.6 vs
   2621.2 routed to FixedFee); c11 receives ~57% (2031.7 vs
   1546.2). Per-unit-volume markout (bps) on the small trades
   that *do* reach c5 is 28.39 bps vs FF's 35.38 bps — i.e.
   c5's small-trade fee is *under* 0.003 on average. The router
   is sending small flow to FF for *price* reasons (mid placement
   / inventory skew), not fee reasons.
3. **Direct CEM on real_data from c5 is real but slow, and
   amplifies the retail problem.** 5-gen × 12-pop CEM lifts c5
   from −1.214 → +0.739 lift_FF on test. retail_advantage went
   from c5's −10.14 → M4-baseline's −13.10 (worse). All score
   gain came from arb, not retail. c11 (M2 deliverable, +2.10
   lift_FF) still beats this baseline by +1.36 lift points.
4. **Identity check on the per-bucket re-derivation is tight.**
   Max abs error between simulator-aggregate `retail_edge_*` and
   the per-event sum: 4.8e-14 (sub), 4.1e-14 (norm). Float
   roundoff only. The per-bucket numbers are not introducing a
   new measurement bias.

## Active hypothesis going into cycle 17

> **"The local basin matters more than the policy family for M4
> on real_data. Direct CEM on real_data from c11 lifts past +2.10
> lift_FF; from c5 it converges to a different (arb-favoring) local
> optimum that doesn't fix the small-bucket routing."**
>
> If true: M4 cycle 1's "policy complexity sweep" should be
> augmented with a "policy prior sweep" (vary the warm-start anchor
> while fixing the family). The richest-policy story is dominated
> by where you start.
>
> If false (c11+CEM saturates near +2.10): we have strong evidence
> that c11 is a real_data ceiling for the piecewise family, and M4
> needs richer families (ladder, MLP) or a retail-aware
> auxiliary loss.

## Cycle-17 plan-of-record

1. **Mirror experiment.** Run the same 5-gen × 12-pop CEM with
   `evaluator_kind="real_data"` but warm-start from c11_d16_s2.
   Same compute budget. Compare gen-by-gen trajectory and final
   test lift_FF to cycle 16's M4 baseline (+0.739). Decision rule:
   - if c11+CEM > +2.20 lift_FF → "the warm-start prior dominates";
     M4 cycle 1 framing pivots to a prior-sweep.
   - if c11+CEM ∈ [+2.00, +2.20] → c11 is a piecewise-family
     real_data ceiling; need richer family or retail-aware loss.
   - if c11+CEM < +2.00 → CEM on real_data is regressing c11; the
     real_data evaluator is actively misleading the optimizer.
   ~14 min.
2. **Decomp the cycle-16 M4 baseline.** Rerun
   `eval_size_decomp.py` against the M4-baseline best-by-val
   params to confirm the retail_advantage drop (−10.14 → −13.10)
   is a small-bucket worsening (the obvious hypothesis), and to
   measure how the medium/large buckets moved. ~2 min.
3. *(stretch, only if 1+2 finish in <30 min)* Retail-aware CEM:
   redefine score = edge_advantage + α × retail_edge_advantage
   with α=0.2, rerun from c5 with same budget. Tests whether a
   small retail penalty steers CEM into the retail-fix basin.

## M2 cumulative history (closed; reproduced for context)

| pass | family | dims | init | seed | challenge test | real_data test (lift_FF) |
|--|--|--|--|--|--:|--:|
| start (c5) | piecewise | 16 | inh | — | 414.01 | -0.74 (-1.22) |
| pass 1 (c6) | piecewise | 16 | warm | 0 | 432.75 | -0.93 (-1.40) |
| pass 2 (c8) | inv-aware piecewise | 19 | warm | 0 | 446.44 | -0.28 (-0.75) |
| pass 3 (c9 #1) | piecewise | 16 | warm | 0 | 448.81 | +1.40 (+0.93) |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | warm | 0 | 456.64 | +2.36 (+1.89) |
| pass 5 (c10 A) | piecewise + noop | 20 | warm | 0 | 456.74 | +2.55 (+2.08) |
| pass 6 (c10 B) | piecewise | 16 | warm | 1 | 452.96 | +1.66 (+1.19) |
| pass 7 (c11 d16_s2) | piecewise | 16 | warm | 2 | **456.80** | **+2.57 (+2.10)** |
| pass 8 (c11 d24_s0) | piecewise + noop×8 | 24 | warm | 0 | 455.66 | (not in dualcurve) |
| pass 9 (c11 d24_s1) | piecewise + noop×8 | 24 | warm | 1 | 452.57 | (not in dualcurve) |
| c12 stage 1 | latent_full | 18 | default | 0 | 388.57 | (not OOD-evaluated) |
| c12 stage 2 | piecewise (fresh) | 16 | default+wide | 0 | 418.65 | (not OOD-evaluated) |
| c13 longrun | piecewise | 16 | warm | 0 | 456.80 | +2.57 (+2.10) — same as c11 |
| c16 M4 baseline | piecewise | 16 | c5 warm + real_data CEM | 0 | (not measured) | +1.21 (+0.74) |

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-15 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh` (vendored wheels make it
  importable on this fresh sandbox after the cycle's setup step).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
  Passes through `--ignore`d list during `pytest -x -q`. Either
  install torch host-side or treat as an acknowledged-skipped suite.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.
  Cycle-1 `checks/04_no_outbound_dns.sh` already encodes this as a
  passing-when-failing predictor.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken on
  this Linux sandbox.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib`. (numpy is
  preinstalled.) jax via `bin/setup_jax_from_vendored.sh`.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate instead of deleting.
  **Cycle-16 reminder**: when authoring a new long-running driver,
  do NOT copy `LOGFILE.unlink(missing_ok=True)` from cycle-6 etc.
  Use `LOGFILE.open("w").close()` instead. (Encoded as the
  passing-when-failing check 05.)
- CPU: 4 cores. CEM at pop=12 / dim=16 / 3 workers ≈ 67 s/gen on
  real_data (vs ~125 s/gen on challenge with pop=24); scaling
  roughly linear in pop. Real_data eval is slightly slower per
  candidate (10000 episode steps reading from empirical
  distribution).
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143. Pattern that
  works: launch via `nohup ... &` once, then poll `progress.log`
  every 8-9 min. Cycle 16 used this pattern for the 14-min M4
  baseline.
- **Sandbox can rotate mid-run**: cycle 16 saw a sandbox restart
  during the first M4 attempt. Always set up incrementally-saved
  checkpoints (`history.json` written every gen) so a restart
  doesn't lose the search trajectory.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 12 active checks (no addition or
  retirement cycle 16). Carry-forward `08_jax_optional` and
  `04_no_outbound_dns` are passing-when-failing predictors
  documenting the sandbox topology, not work-to-do — keep them.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) untouched per
  convention; cycle-16's only edits were under `research/`.
