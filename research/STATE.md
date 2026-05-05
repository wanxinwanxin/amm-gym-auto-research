# State — current cycle

**Last updated**: 2026-05-05 (cycle 18 — closed)

## Active milestone

**M4 cycle 2 (closed) → M4 cycle 3 (next).**
Cycle 18 ran the cycle-17 plan-of-record: (1) longer-budget CEM from
c11 (10g × 24p, 4× compute) and (2) prior sweep at fixed cycle-17
compute (5g × 12p) from {default, c6, c8_16d}, completing a 5-anchor
basin map together with c5 (cycle 16) and c11_short (cycle 17). Both
experiments produced clean signals; the load-bearing finding is that
basin dominates compute by roughly an order of magnitude within a
piecewise family on real_data, re-framing M4 cycle 3 as a
policy-family escalation rather than a further compute sweep.

## Headline numbers (held; reproduced cycle 18)

- **Best M2 score (challenge test, n=256): 456.80**
  [CI 448.0, 465.7] — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable).
- **Best real_data lift_FF (test, n=256): +3.006**
  for c11 + long-budget CEM (cycle 18, 10-gen × 24-pop CEM warm-started
  from c11_d16_s2). Up from cycle-17 c11+CEM short's +2.772, c5+CEM
  M4 baseline's +0.739, and c11 anchor's +2.10.
- **Test retail_advantage (held): +3.21**, more than 4× cycle-17
  c11+CEM's +0.66. The longer CEM moved DEEPER into the c11 retail-
  positive basin rather than away from it. Per-bucket: small +3.31,
  medium −0.04, large +0.00 (n=128 val, bootstrap 95% CI).
- **Basin-dominates-compute ratio: ~10×.** 4× more compute from c11
  buys +0.23 lift_FF; switching anchor c5 → c11 at fixed cycle-17
  compute buys +2.03 lift_FF.

## Cycle-18 verdict

1. **Decision rule from cycle 17 fires the "saturating near +3.0"
   branch.** Long c11+CEM lift_FF = +3.006, in the [+2.80, +3.20]
   band. The piecewise family on real_data has more headroom than
   cycle-17 indicated, but the marginal return on extra compute is
   modest and slowing fast (gen 8 best, gen 9 slight regression).
   Family escalation is now the bottleneck.

2. **Prior sweep at fixed compute is near-monotone in anchor val
   score.** Final lift_FF per anchor:

       anchor               | anchor val | test lift_FF | retail_adv
       default              |  -1.18     | +1.05        | -15.28
       c5 (cycle 16)        |  -1.21     | +0.74        | -10.14
       c6_warmstart         |  -0.61     | +1.89        | -0.00
       c8_invaware_16d      |  +0.04     | +2.35        | +0.36
       c11 short (c17)      |  +2.92     | +2.77        | +0.66
       c11 long (this c)    |  +2.92     | +3.01        | +3.21

   One mild non-monotonicity at the bottom (default beats c5 by
   +0.31 lift_FF despite slightly worse anchor val) — c5 sits in a
   particularly bad routing-collapse basin. Otherwise anchor val
   predicts ~80% of variance in final lift_FF. Basin dominates
   compute ~10× (4× compute = +0.23, c5→c11 = +2.03 same compute).

3. **Long c11+CEM moves DEEPER into the retail-positive basin, not
   away.** Per-bucket retail_edge_advantage (n=128 val) on long-CEM
   best-by-val:

       bucket  | this cycle  | cycle-17 c11+CEM | c11 anchor
       small   | +3.31       | +1.45            | +1.17
       medium  | -0.04       | +0.07            | -0.02
       large   | +0.00       | -0.83            | -0.08
       overall | +3.27       | +0.70            | +1.07

   All gain in small bucket (~3500 trades/episode); medium and
   large are noise (~10 trades/episode combined). Score gain and
   retail-edge gain are NOT in tension under c11+CEM — the
   optimizer found a small-bucket pricing surface that lifts
   both.

## Active hypothesis going into cycle 19

> **"The piecewise-family real_data ceiling is at ~+3.0 ± 0.2
> lift_FF. To break +3.5 lift_FF, M4 cycle 3 must escalate the
> policy family — adding e.g. ladder bucketing, an MLP head, or
> EMA-inventory state — warm-started from c11+CEM long. A
> retail-aware auxiliary loss is unlikely to bridge the c5 → c11
> gap because the prior sweep showed those basins are far apart in
> anchor val (~4 units) and a small retail-tilt term can't make
> up that distance."**
>
> If true: a richer-family policy warm-started from c11+CEM long
> lifts test lift_FF to >+3.50 within a comparable training
> budget and beats c11+CEM long on both score and retail edge.
>
> If false (richer family doesn't help): the small-bucket pricing
> surface c11+CEM long discovered is already saturated. The next
> move is either more compute (10× the current budget) or a
> different evaluator structure (e.g. larger holdout with
> different distributional draws).

## Cycle-19 plan-of-record

1. **Policy-family escalation: ladder or MLP head, warm-started
   from c11+CEM long.** Pick the simpler family first (ladder
   bucketing — replace 3-bucket continuation/reversal with a
   k-bucket version, k ∈ {5, 8, 16}, parameters initialized to
   piecewise values via interpolation). Train 5-gen × 12-pop CEM
   with c11_long params as the 16-d projection, free the extra
   ladder params from a smaller std (e.g. 0.05 init_std_frac for
   the new params, 0.10 for the inherited).
   - Decision rule: > +3.50 lift_FF → richer family pays;
     [+3.20, +3.50] → marginal; < +3.20 → escalation doesn't help,
     small-bucket pricing surface saturated.
   - Wall-clock: ~30-40 min for ladder-5 (~30% more dims).

2. **Param-importance ablation on c11+CEM long.** For each of the
   16 piecewise params, evaluate the "step-back-to-anchor"
   counterfactual: hold all params at c11_long best-by-val except
   reset param i to the c11 anchor value, measure val score
   change. Identifies which 2-4 levers carry the load. Direct
   input to which features the richer family must encode.
   - Wall-clock: ~16 × ~35s val = ~10 min.

3. *(stretch)* Re-run the long c11+CEM with rng_seed=1 to confirm
   the +3.01 lift_FF is reproducible across CEM stochasticity, not
   a single-seed artifact.
   - Wall-clock: ~38 min (full re-run).

## M4 cumulative history

| pass | family | warm-start | budget | test lift_FF | retail_adv (test) |
|--|--|--|--|--:|--:|
| anchor (c5) | piecewise | inh | — | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | +2.10 | +1.08 (val) |
| **c5 + CEM** (cycle 16) | piecewise | c5 | 5g×12p, real_data | **+0.74** | -10.14 (M4 baseline; -13.10 is the c5 anchor for cycle-17 mirror context, see cycle-17 LOG) |
| **c11 + CEM short** (cycle 17) | piecewise | c11_d16_s2 | 5g×12p, real_data | **+2.77** | +0.66 |
| default + CEM (cycle 18) | piecewise | default | 5g×12p, real_data | +1.05 | -15.28 |
| c6 + CEM (cycle 18) | piecewise | c6_warmstart | 5g×12p, real_data | +1.89 | -0.00 |
| c8_16d + CEM (cycle 18) | piecewise | c8 inv-aware best (16-d projection) | 5g×12p, real_data | +2.35 | +0.36 |
| **c11 + CEM long** (cycle 18) | piecewise | c11_d16_s2 | 10g×24p, real_data | **+3.01** | **+3.21** |

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
| **c17 M4 mirror** | piecewise | 16 | c11 warm + real_data CEM | 0 | (not measured) | **+3.24 (+2.77)** |
| **c18 M4 long c11** | piecewise | 16 | c11 warm + real_data CEM (10g×24p) | 0 | (not measured) | **+3.48 (+3.01)** |

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-16 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh` (vendored wheels make it
  importable on this fresh sandbox after the cycle's setup step).
- **pyarrow install OOMs on this sandbox** (added cycle 17). Not
  needed for current cycle's experiments; flagged for any future
  driver that wants Parquet round-trips. Workaround: use JSON or
  feather via `pandas.to_feather` (pandas dep is preinstalled).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
  Either install torch host-side or treat as an
  acknowledged-skipped suite.
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
  --no-cache-dir gymnasium pytest matplotlib` — install one package at
  a time. Bundling `gymnasium pyarrow pytest` in one pip command OOMs
  on this sandbox (cycle-18 rediscovered this). pyarrow itself can be
  installed separately and DID succeed cycle 18 — it's an issue with
  the bundled multi-package resolver, not pyarrow specifically. jax
  via `bin/setup_jax_from_vendored.sh`. Cycle-18 footnote: after a
  fresh `pip install ... pytest` created the user-site directory,
  the previous-shell jax install was gone — re-run setup script.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate instead of deleting.
  Cycle-16+17 reminder: when authoring a new long-running driver,
  do NOT copy `LOGFILE.unlink(missing_ok=True)` from cycle-6 etc.
  Use `LOGFILE.open("w").close()` instead. (Encoded as the
  passing-when-failing check 05.)
- CPU: 4 cores. CEM at pop=12 / dim=16 / 3 workers ≈ 70-80 s/gen on
  real_data; pop=24 ≈ ~125 s/gen extrapolating from cycle 6. Real_data
  eval slightly slower per candidate (10000 episode steps reading
  from empirical distribution) than challenge eval.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143. Pattern that
  works: launch via `nohup ... &` once, then poll the experiment's
  `progress.log` every 8-9 min.
- **Sandbox can stall mid-run**: cycle 17 saw a ~26-min stall on
  gen 3 of an otherwise ~70 s/gen CEM. Always set up
  incrementally-saved checkpoints (`history.json` written every
  gen) so a stall (or restart) doesn't lose the search trajectory.
- **Rerank pool injection trick (added cycle 17)**: when running
  CEM from a known-good warm-start anchor on real_data, inject the
  anchor itself into the rerank pool BEFORE adding elites by
  search score. Guarantees `best_by_val` cannot regress past the
  anchor — important when CEM gen-by-gen val noise (~0.1-0.4 score
  units on n=128) could otherwise let a candidate with a lucky
  val draw be picked over the anchor.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 12 active checks (no addition or
  retirement cycle 17). Carry-forward `08_jax_optional` and
  `04_no_outbound_dns` are passing-when-failing predictors
  documenting the sandbox topology, not work-to-do — keep them.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) untouched per
  convention; cycle-17's only edits were under `research/`.
