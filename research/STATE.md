# State — current cycle

**Last updated**: 2026-05-05 (cycle 22 — closed)

## Active milestone

**M4 cycle 6 (closed) → M4 cycle 7 (next).** Cycle 22 ran the
cycle-21 plan-of-record apples-to-apples ladder repro on the
cycle-21-seed-1 piecewise anchor. Result: **the cycle-19 +0.245
ladder lift_FF over piecewise is anchor-driven, not a real family
effect at the cycle-19 budget.** Both rng_seed=0 and rng_seed=1
ladder CEM runs produce a rerank winner equal to the *anchor itself*
(test lift_FF +2.900 = piecewise seed-1 +2.900); cycle-22 lift over
the seed-1 anchor is **+0.000** for both seeds.

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **Best real_data score, single-seed nominal: cycle-19 ladder
  +3.721 (lift_FF +3.251).** Now downgraded further: this was both
  a +75th-percentile piecewise anchor *and* a single-seed positive
  draw inside the ladder family, with lift over piecewise driven by
  anchor sampling rather than by the family.
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Unchanged.
- **Cross-anchor ladder lift over piecewise (cycle 22):**
  - cycle-18-seed-0 anchor (cycle-19, single-seed): **+0.245**
  - cycle-21-seed-1 anchor (cycle-22 seed=0): **+0.000**
  - cycle-21-seed-1 anchor (cycle-22 seed=1): **+0.000**
  - cycle-21-seed-2 anchor (cycle-22 seed=0, stretch): **+0.000**
  - **Cross-anchor mean (n=3 anchors, 4 runs) of ladder lift
    over same-anchor piecewise:** ~+0.061 lift_FF, with only one
    of four points positive. **Effectively zero at this budget.**
- **Implied M4 status:** the M4 frontier on real_data is ~+2.7
  multi-seed lift_FF (cycle-21 piecewise long-CEM mean), with no
  clean evidence that family escalation (ladder) provides
  cross-anchor lift at the cycle-19/22 budget. The ceiling at
  this budget appears to be in CEM's exploration regime, not in
  the policy family.

## Cycle-22 verdict

1. **Cycle-19's +0.245 ladder lift does NOT reproduce on a
   different anchor at the same budget.** Decision rule line 2 is
   met: both seeds neutral over the seed-1 piecewise anchor.
   The lift was anchor-driven, not a representational gain.

2. **CEM at the cycle-19 budget (5g × 12p) does not find any
   ladder candidate that beats the seed-1 piecewise warm-start on
   val.** Top non-anchor val score at gen-4: 3.496 (seed=0),
   3.573 (seed=1); anchor val: 3.651. The CEM mean drifts toward
   search-set elites that don't generalize to val. This is a
   **search→val generalization gap**, not a representational
   limit.

3. **The cycle-20 ladder multi-seed mean +3.111 ± 0.126 was
   measuring rng-seed dispersion conditional on the cycle-18-seed-0
   anchor, NOT a cross-anchor estimate.** Cross-anchor multi-seed
   mean (n=2 anchors × ≥2 seeds each) is ~+2.95-3.0 lift_FF —
   essentially the same as the piecewise mean, ±0.3 stddev.

4. **The cycle-21 anchor confounding rule is now operationally
   binding for any future M4 family-escalation claim.** Reporting
   form (a) "lift over the specific anchor used" alone has been
   shown to overstate effect sizes by enough to flip the sign of
   the conclusion (cycle 19's +0.245 → cycle 22's 0.000). Form (c)
   "cross-anchor lift" is required.

## Active hypothesis going into cycle 23

> **"At the cycle-19/22 budget (5 generations × 12 population, 19
> dimensions, real_data evaluator), the policy family does not
> determine the lift_FF ceiling — the CEM search→val generalization
> gap does. A longer-budget ladder CEM (e.g. 10g × 24p, matching
> cycle-18 long-piecewise) warm-started from cycle-21-seed-1
> piecewise will lift to lift_FF > +3.10 on test, replicating the
> compute:basin trade-off from cycle 18's piecewise long-CEM."**
>
> If true: the family escalation is real but only manifests at the
> long-CEM budget. The cycle-19/22 budget was below the threshold
> at which ladder's extra dim pays off.
>
> If false (long-CEM ladder still ≈ +2.9 on the seed-1 anchor):
> the ladder family is not delivering a ceiling-lift effect at any
> tested budget; cycle 24 should pivot to a structurally different
> family (smooth-head MLP, attention-over-history controller, or
> a ladder variant with different bucketing — e.g. 6 buckets, or
> dynamic threshold).

## Cycle-23 plan-of-record

1. **Long-CEM ladder on cycle-21-seed-1 anchor.** Run
   `run_ladder_cem_anchor.py` with `ANCHOR_KEY=cycle21_seed1`,
   `RNG_SEED=0`, `MAX_WORKERS=2`, but with `POPULATION=24`,
   `GENERATIONS=10`, matching cycle-18 long-piecewise budget on
   the same anchor. Expected wall: ~46 min single-run at
   workers=2 (cycle-21 pace).
   - If lift_FF > +3.10 → ladder is real at long-CEM budget,
     re-evaluate cycle-22 at long-CEM budget for cross-anchor
     repro (cycle 24).
   - If lift_FF in [+2.95, +3.10] → marginal; need ≥2 more seeds.
   - If lift_FF ≤ +2.90 → ladder is genuinely flat; pivot to
     smooth-head MLP family (cycle 24).

2. *(stretch)* Sanity-check the cycle-22 stretch run
   (cycle-21-seed-2 anchor, basin-collapsed piecewise +2.275). If
   the ladder anchor val (already +3.215 from the warm-start
   identity) > +3.0 by enough to lift the test score significantly
   above the piecewise +2.275, that's evidence that ladder is a
   *stabilizer* rather than a ceiling-lifter — interesting M4
   substory that informs cycle 24 family-design choice.

3. *(stretch)* Encode "cycle-19 ladder lift was anchor-conditional"
   as a check at `bin/checks/12_*` that re-runs cycle-22 seed=0
   from the seed-1 anchor and asserts test lift_FF in
   [+2.85, +2.95] — i.e. ladder on seed-1 anchor produces
   anchor-equivalent test, not a +0.245 bump. This documents the
   cross-anchor null result so a future cycle does not re-compute
   it.

## M4 cumulative history (revised, cycle 22)

| pass | family | warm-start | budget | seeds | test lift_FF | retail_adv (test) |
|--|--|--|--|--:|--:|--:|
| anchor (c5) | piecewise | inh | — | n/a | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | 1 | +2.10 | +1.08 (val) |
| **c5 + CEM** (cycle 16) | piecewise | c5 | 5g×12p, real_data | 1 | +0.74 | -10.14 |
| **c11 + CEM short** (cycle 17) | piecewise | c11_d16_s2 | 5g×12p, real_data | 1 | +2.77 | +0.66 |
| default + CEM (cycle 18) | piecewise | default | 5g×12p, real_data | 1 | +1.05 | -15.28 |
| c6 + CEM (cycle 18) | piecewise | c6_warmstart | 5g×12p, real_data | 1 | +1.89 | -0.00 |
| c8_16d + CEM (cycle 18) | piecewise | c8 inv-aware best (16d proj) | 5g×12p, real_data | 1 | +2.35 | +0.36 |
| **c11 + CEM long, seed=0** (cycle 18) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +3.006 | +3.215 |
| **c11 + CEM long, seed=1** (cycle 21) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +2.900 | +3.820 |
| **c11 + CEM long, seed=2** (cycle 21) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +2.275 | -3.024 |
| **c11 long-CEM mean ±σ** (n=3) | piecewise | c11_d16_s2 | 10g×24p, real_data | 3 | **+2.727 ± 0.322** | +1.34 ± 3.16 |
| **ladder seed=0** (cycle 19) | ladder-4bucket | c11_long ext (cycle-18 seed=0) | 5g×12p, real_data | 1 | +3.251 | +3.113 |
| **ladder seed=1** (cycle 20) | ladder-4bucket | c11_long ext (cycle-18 seed=0) | 5g×12p, real_data | 1 | +3.076 | +3.834 |
| **ladder seed=2** (cycle 20) | ladder-4bucket | c11_long ext (cycle-18 seed=0) | 5g×12p, real_data | 1 | +3.006 | +3.215 |
| **ladder mean ±σ** (n=3, anchor cycle-18-seed-0) | ladder-4bucket | c11_long-seed-0 | 5g×12p, real_data | 3 | +3.111 ± 0.126 | +3.39 ± 0.39 |
| **ladder seed=0** (cycle 22) | ladder-4bucket | c11_long ext (cycle-21 seed=1) | 5g×12p, real_data | 1 | +2.900 | +3.820 |
| **ladder seed=1** (cycle 22) | ladder-4bucket | c11_long ext (cycle-21 seed=1) | 5g×12p, real_data | 1 | +2.900 | +3.820 |
| **ladder mean** (n=2, anchor cycle-21-seed-1) | ladder-4bucket | c11_long-seed-1 | 5g×12p, real_data | 2 | **+2.900 ± 0.000** | +3.820 |
| **ladder seed=0** (cycle 22, stretch) | ladder-4bucket | c11_long ext (cycle-21 seed=2) | 5g×12p, real_data | 1 | +2.275 | -3.024 |
| **ladder lift_FF cross-anchor mean** (n=3 anchors, 4 runs) | ladder-4bucket | c18_s0 / c21_s1 / c21_s2 | 5g×12p, real_data | 4 | **~0** (range +0.000 to +0.245, only c19 positive) | — |

The ladder mean is now reported per anchor; the cross-anchor mean
(c18-s0 +3.251 single, c21-s1 +2.900 double, c21-s2 stretch pending)
is the right cross-anchor estimate for the family.

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-22 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Vendored wheels make it importable on this fresh sandbox after
  the cycle's setup step.
- **pyarrow install OOMs on this sandbox** when bundled with other
  deps; install it alone or in a small bundle. Cycle 22 OOM'd six
  times in a row even with `--no-deps`; `pyarrow` was *not*
  required for cycle-22's experiment so the run proceeded without
  it. Future cycles that need pyarrow should retry several times
  or install on a fresh sandbox before any large memory operations.
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pytest matplotlib`. Cycle 22 succeeded
  with this minimal bundle (pyarrow not needed for the cycle's
  experiments). If a cycle needs pyarrow, install alone after a
  fresh sandbox restart.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate.
- CPU: 4 cores. Cycle 22 ran two parallel CEM jobs at workers=2
  each (saturating cores) and finished both ~17 min from launch
  (CEM ~10 min + rerank ~4 min + test ~2 min). The single stretch
  run at workers=3 finishes in ~13 min.
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~360s may be killed with exit 143 by the sandbox. Pattern that
  works: launch CEM via `nohup ... &` once, then poll
  `progress.log` periodically with shorter `sleep`s (≤300s).
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently **13 active checks** (cycle 22 added
  `12_cycle22_anchor_conditional_lift.py` — asserts that all
  cycle-22 ladder runs rerank-pick the anchor and that ladder
  test_score is bit-equal to the same-anchor piecewise test_score,
  documenting the identity-warm-start cross-anchor null-lift). No
  retirements this cycle.
- **Seed reproducibility rule (cycles 20/21/22).** Going forward,
  any M4 family/budget claim at the cycle-19/22 CEM budget needs
  ≥3 rng_seeds before being entered as a headline. Long-budget has
  stddev ~0.32; short-budget has stddev ~0.13. Cycle-22 added a
  qualifier: **single-anchor multi-seed is not enough — cross-anchor
  is required for any family-escalation claim.**
- **Anchor confounding rule (cycle-21 + cycle-22).** Family-
  escalation experiments require cross-anchor lift, not just
  lift over a single warm-start seed. Cycle 22 demonstrated that
  the cycle-19 single-anchor lift of +0.245 collapses to +0.000
  on a different anchor at the same budget.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-22's edits restricted to `research/`.
