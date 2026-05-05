# State — current cycle

**Last updated**: 2026-05-05 (cycle 21 — closed)

## Active milestone

**M4 cycle 5 (closed) → M4 cycle 6 (next).** Cycle 21 ran the cycle-20
plan-of-record multi-seed long-CEM. Result: **the +3.0 lift_FF
ceiling hypothesis is REJECTED.** The 3-seed mean of the cycle-18
recipe (10g × 24p, piecewise, warm c11) on real_data is
**+2.727 ± 0.322 lift_FF** (range +2.275 to +3.006). Cycle-18's
single-seed +3.006 was the maximum, not the median, of the seed
distribution; ~75th percentile, not the population center.

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **Best real_data score, single-seed nominal: cycle-19 ladder
  +3.721 (lift_FF +3.251).** Now reported as the upper-tail draw
  of a noisy distribution, not as a population estimate.
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. This replaces the previous "+3.0 ceiling"
  framing as the right-of-headline M4 number.
- **Best real_data score, multi-seed mean (cycle 20, ladder
  warm-started from cycle-18-seed-0, n=3): lift_FF
  +3.111 ± 0.126.** Confounded by anchor sampling — the warm-start
  is the lucky cycle-18 seed; the apples-to-apples ladder-vs-
  piecewise comparison is cycle-22's task.
- **Implied M4 status:** the multi-seed piecewise long-CEM mean
  on real_data is **+2.7**, not +3.0; the seed dispersion at this
  budget is ±0.32 (much wider than ±0.13 at the shorter ladder
  budget); and all single-seed M4 results from cycles 16-19
  carry ~±0.32 stddev that prior cycles did not measure.

## Cycle-21 verdict

1. **The "+3.0 lift_FF" headline carried since cycle 18 was a
   single-seed positive draw.** Cross-seed mean +2.727. Cycle-18's
   +3.006 sits at the seed distribution's max; cycle-21 seed=2
   came in at +2.275 (a basin-collapse trajectory). Strict
   quantitative claim: at this budget, the long-CEM piecewise
   family produces test lift_FF on real_data with mean +2.73,
   stddev ±0.32, n=3.

2. **Long-CEM dispersion is *larger* than short-CEM dispersion.**
   Pop=24 × gen=10 (cycle 21): ±0.322. Pop=12 × gen=5 (cycle 20
   ladder): ±0.126. The factor-of-2.5 increase contradicts the
   usual "more compute → less variance" expectation. Mechanism:
   the long trajectory occasionally locks into a basin-collapse
   (cycle-21 seed=2 at gen 6: retail_adv −18, never recovered),
   and the run finishes with a rerank pool dominated by an early
   gen elite at val ~3.2 instead of ~3.7-3.8. New term, **basin
   collapse**, added to glossary.

3. **All cycle-19/20 ladder-vs-piecewise lift numbers are
   confounded by anchor sampling.** The ladder runs were warm-
   started from the lucky cycle-18-seed-0 piecewise outcome,
   which we now know was the +75th-percentile draw of the
   piecewise distribution. So the "ladder lift" is mixing up
   family effect with anchor-quality effect. Apples-to-apples
   comparison: ladder warm-started from each cycle-21 piecewise
   seed.

4. **The basin-vs-compute conclusion (cycle 18) is qualitatively
   right but quantitatively shaky.** Single-seed across all
   anchors at the cycle-17/18 budgets; cycle-21 ±0.32 stddev means
   that fine-grained anchor rank-orderings are within seed noise.
   The large headline (c5 +0.74 vs c11_long +3.01 → +2.27 spread)
   is well beyond noise; the fine structure is not.

## Active hypothesis going into cycle 22

> **"The cycle-19 ladder family has a real positive effect over
> piecewise — even at the apples-to-apples comparison (ladder
> warm-started from each piecewise seed, not just from the lucky
> cycle-18-seed-0). Specifically, ladder warm-started from
> cycle-21-seed-1 (piecewise +2.900) will lift to lift_FF > +3.10
> on test, replicating roughly the same +0.10–+0.20 family payoff
> seen at the cycle-19/20 budget on the cycle-18-seed-0 anchor."**
>
> If true: the ladder result is real, but cycle-19 reported it
> with a confounding-inflated magnitude. The frontier is then
> ~+3.0 multi-seed on ladder, not +2.7 multi-seed on piecewise.
>
> If false (ladder from seed-1 stays at or below piecewise's
> +2.900): the cycle-19 ladder lift was an anchor artefact, not a
> family effect. Then family escalation needs to be designed
> from scratch with multi-seed evaluation — cycle 22 should pivot
> to a smooth-head MLP (the ablation-suggested follow-up).

## Cycle-22 plan-of-record

**Pick (a) below — apples-to-apples ladder repro — over (b)
smooth-head MLP, on the grounds that it's the more informative
single experiment for the smaller budget. Re-evaluate after.**

1. **Apples-to-apples ladder repro on cycle-21-seed-1 anchor.**
   Run cycle-19's ladder CEM (5g × 12p) warm-started from the
   cycle-21-seed-1 piecewise best (test +3.370, lift_FF +2.900,
   16 params packed). Run with rng_seed=0 and rng_seed=1; if
   both lifts are positive vs the seed-1 piecewise anchor, the
   ladder family effect is real. Decision rule:
   - both seeds lift > +0.05 lift_FF over seed-1 piecewise →
     family effect confirmed, ~+0.10 cross-anchor.
   - both seeds neutral or negative → cycle-19 was anchor-driven;
     pivot to (b) next cycle.
   - one seed lifts strongly, the other doesn't → the family
     effect is real but small enough that 4 seeds were needed
     to detect — note for cycle 23 design.

   Cost: ~25 min wall (5g × 12p, 19d) × 2 seeds in parallel ≈
   25 min wall. Plus ~5 min for warm-start re-pack and ~5 min
   per-seed test eval. Total ~40 min.

2. *(stretch)* Run the same comparison from cycle-21-seed-2
   piecewise (the basin-collapsed run) to see whether ladder
   *recovers* lift_FF when anchored on a poor piecewise. If yes,
   ladder might be a stabilizer, not a ceiling-lifter. Cost:
   another ~25 min wall in parallel with (1).

3. *(stretch)* Encode "cycle-18-seed-0 was the +75th-percentile
   piecewise draw, not the median" as a check that re-runs the
   anchor and asserts it scores in [+2.275, +3.006] on test.
   This documents the multi-seed range so a future cycle won't
   re-treat cycle-18 numbers as the population.

## M4 cumulative history (revised)

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
| **ladder seed=0** (cycle 19) | ladder-4bucket | c11_long extended (cycle-18 seed=0) | 5g×12p, real_data | 1 | +3.251 | +3.113 |
| **ladder seed=1** (cycle 20) | ladder-4bucket | c11_long extended (cycle-18 seed=0) | 5g×12p, real_data | 1 | +3.076 | +3.834 |
| **ladder seed=2** (cycle 20) | ladder-4bucket | c11_long extended (cycle-18 seed=0) | 5g×12p, real_data | 1 | +3.006 | +3.215 |
| **ladder mean ±σ** (n=3) | ladder-4bucket | c11_long-seed-0 | 5g×12p, real_data | 3 | +3.111 ± 0.126 | +3.39 ± 0.39 |

The ladder mean is conditional on the +75th-percentile piecewise
anchor; the cycle-22 task is to compute ladder lift conditional on
each cycle-21 piecewise anchor.

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-21 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Vendored wheels make it importable on this fresh sandbox after
  the cycle's setup step.
- **pyarrow install OOMs on this sandbox** when bundled with other
  deps; install it alone or in a small bundle. Cycle 21 had to
  retry pyarrow once before succeeding.
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib`. Cycle 21
  had to install pyarrow alone after the bundle OOM'd.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate.
- CPU: 4 cores. CEM at pop=24 / dim=19 / 2 workers ≈ 218 s/gen
  on real_data with 64 search seeds (cycle 21); pop=24 / 3 workers
  ≈ 150 s/gen (cycle 18). Two parallel runs at workers=2 each
  saturate the 4-core budget at minimal cross-process contention.
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~360s may be killed with exit 143 by the sandbox. Pattern that
  works: launch CEM via `nohup ... &` once, then poll
  `progress.log` periodically with shorter `sleep`s. Encoded in
  cycle-21's polling pattern.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 12 active checks. No additions or
  retirements this cycle.
- **Seed reproducibility rule (cycle-20, re-confirmed cycle-21).**
  Going forward, any M4 family/budget claim at the cycle-19/20/21
  CEM budget needs ≥3 rng_seeds before being entered as a
  headline. Single-seed gen-4-best-on-val scores at short budget
  have stddev ~0.13; long-budget has stddev ~0.32 — both larger
  than typical claimed effect sizes.
- **Anchor confounding rule (cycle-21 new).** When a family-
  escalation experiment is warm-started from a single-seed result
  of the prior family, report results in three forms: (a) lift
  over the specific anchor used; (b) lift over the multi-seed
  mean of the prior family if known; (c) cross-anchor lift,
  obtained by re-running the new family from each anchor seed.
  Cycle-19/20 only computed (a); cycle 21 added (b); cycle 22
  should compute (c).
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-21's edits restricted to `research/`.
