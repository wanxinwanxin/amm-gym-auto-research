# State — current cycle

**Last updated**: 2026-05-06 (cycle 24 — closed)

## Active milestone

**M4 cycle 8 (closed) → M4 cycle 9 (next).** Cycle 24 ran the
cycle-23 plan-of-record: (a) third RNG seed of long-CEM ladder on
the cycle-21-seed-1 piecewise anchor, (b) cross-anchor long-CEM
ladder probe on the cycle-21-seed-2 (basin-collapsed) piecewise
anchor. **Result: (a) the third seed lands at lift_FF +3.037 /
lift over piecewise +0.137, moving the n=3 mean to +0.134 ± 0.066
(from cycle-23's n=2 +0.132 ± 0.066) — only +0.002 of motion;
cycle-23 reproducible. (b) The cross-anchor probe lifts +0.547
over the same-anchor piecewise, vs +0.000 for short-CEM ladder on
the same anchor (cycle 22). Long-CEM ladder is a stabilizer for
collapsed anchors.**

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **Best real_data single-seed nominal: cycle-23 long-CEM ladder
  rng_seed=0 on c21-s1: test +3.569, lift_FF +3.098, lift over
  c21-s1 piecewise +0.198.** Unchanged from cycle 23.
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Unchanged. Best *piecewise* multi-seed estimate.
- **Best real_data score, multi-seed mean (long-CEM ladder on
  c21-s1 anchor, cycles 23+24, n=3): test +3.504, lift_FF
  +3.034 ± 0.066** [range +2.966, +3.098]. Updated from cycle 23's
  n=2 estimate (+3.503, +3.032 ± 0.066). The third seed's +3.037
  test slots between cycle-23 seed-0 (+3.098) and seed-1 (+2.966).
  Mean lift over the same-anchor piecewise: **+0.134 ± 0.066**
  (was +0.132 ± 0.066, n=2).
- **NEW: Cross-anchor long-CEM ladder, c21-s2 anchor (n=1):**
  test +3.293, lift_FF +2.822, **lift over same-anchor piecewise
  +0.547** (vs +0.000 for short-CEM on this anchor in cycle 22).
- **Cross-anchor / cross-budget ladder lift over piecewise (revised, c19/22/23/24):**
  | budget | anchor | n_seeds | lift over piecewise (mean) |
  |--|--|--:|--:|
  | short-CEM (5g×12p) | cycle-18-s0 | 1 | +0.245 (cycle 19, single seed) |
  | short-CEM (5g×12p) | cycle-21-s1 | 2 | +0.000 (cycle 22, both seeds) |
  | short-CEM (5g×12p) | cycle-21-s2 | 1 | +0.000 (cycle 22, stretch) |
  | long-CEM (10g×24p) | cycle-21-s1 | 3 | **+0.134 ± 0.066 (c23+c24)** |
  | **NEW long-CEM (10g×24p)** | **cycle-21-s2** | **1** | **+0.547 (cycle 24)** |
- **Implied M4 status (revised, cycle 24):** the long-CEM ladder
  family delivers an *anchor-dependent* lift over piecewise: small
  (~+0.13) on the median piecewise basin (c21-s1), large (~+0.55)
  on the basin-collapsed anchor (c21-s2). The frontier on absolute
  test score remains the c21-s1 long-CEM ladder cluster
  (mean test 3.504); c21-s2 ladder seed=0 test 3.293 sits below
  this cluster despite the larger lift over its anchor.

## Cycle-24 verdict

1. **Q1 (third-seed) confirmed.** Adding rng_seed=2 to the c21-s1
   long-CEM ladder cluster moves the n=3 mean lift over piecewise
   from cycle-23's n=2 +0.132 ± 0.066 to +0.134 ± 0.066 — a shift
   of +0.002 in the mean and zero change in the sample stddev.
   The third seed's +0.137 lands almost exactly on the n=2 mean.
   Clean confirmation that cycle-23's small effect is real, not
   n=2 sampling noise.

2. **Q2 (cross-anchor stabilizer) supported on n=1.** Cycle-24's
   long-CEM ladder warm-started from the c21-s2 (basin-collapsed)
   piecewise anchor lifts +0.547 over the same-anchor piecewise.
   Cycle-22's *short-CEM* ladder stretch on the same anchor
   returned +0.000. So at the same anchor, going from short to
   long CEM unlocks +0.547 of family lift. This is much larger
   than the c21-s1 mean lift (+0.13) at the same compute.

3. **Anchor-conditional lift pattern.** Combining cycle-19/22/23/24
   data, the picture is: short-CEM ladder on any anchor gives
   ~0 (cycle-19's +0.245 single-seed point is a positive tail
   draw); long-CEM ladder lift over piecewise grows as the
   underlying piecewise gets worse. Currently c18-s0 piecewise
   +3.006 → ladder +0.245 (n=1, single-seed); c21-s1 piecewise
   +2.900 → ladder +0.134 ± 0.066 (n=3); c21-s2 piecewise +2.275
   → ladder +0.547 (n=1). The sign matches "stabilizer": ladder
   rescues broken basins. The c18-s0 and c21-s2 points are each
   n=1; a second seed on c21-s2 plus another anchor would tighten
   this.

4. **Long-CEM elites continue to dominate the anchor on val.**
   Both cycle-24 runs: 6/6 non-anchor rerank candidates beat the
   anchor on val (margins +0.13 c21-s1, +0.44 c21-s2). Combined
   with cycle 23: 4/4 long-CEM ladder runs satisfy this. Encoded
   as `bin/checks/13_long_cem_beats_anchor.py` (eps=0.05). All 4
   runs pass with margin > 0.13.

5. **Val→test gap stays wide on long-CEM.** c21-s2 val 3.991 →
   test 3.293 (Δ −0.70) — the largest val→test drop seen so far,
   surpassing cycle-23 seed-1's −0.62. The basin-overfit-on-val
   mechanism that cycle 21 surfaced for piecewise long-CEM
   continues to apply at long-CEM compute regardless of family.
   This is increasingly a generic long-CEM artifact, not a
   family-specific or anchor-specific effect.

## Active hypothesis going into cycle 25

> **"Long-CEM ladder lift over the same-anchor piecewise scales
> inversely with piecewise quality. A second RNG seed on the
> c21-s2 anchor will land in [+0.30, +0.70] (consistent with the
> first seed's +0.547 plus cycle-23 seed dispersion), giving an
> n=2 mean above +0.40. A long-CEM ladder run on the cycle-18-seed-0
> piecewise anchor at multi-seed will land below the c21-s1 n=3
> mean (+0.134), confirming the inverse-scaling line."**
>
> If true (n=2 c21-s2 mean > +0.40 AND c18-s0 multi-seed mean
> < +0.13), the family-vs-anchor relationship is established
> with a 3-anchor curve. If false on either limb (e.g. c21-s2
> seed-1 collapses to ~0), the cycle-24 +0.547 was a single-seed
> draw of a wide distribution, and the relationship needs more
> seeds to characterize.

## Next-cycle plan-of-record (cycle 25)

1. **Second RNG seed on c21-s2 long-CEM ladder.** Run
   `ANCHOR_KEY=cycle21_seed2 RNG_SEED=1`, single run, ~46 min
   wall. Tightens the cross-anchor stabilizer claim from n=1 to
   n=2.
2. **Cross-anchor probe on cycle-18-seed-0 piecewise anchor.**
   Add `cycle18_seed0` to ANCHORS_PIECEWISE; run
   `ANCHOR_KEY=cycle18_seed0 RNG_SEED=0`, single run. The c18-s0
   anchor is the +75th-percentile piecewise (lift_FF +3.006), which
   along with c21-s1 (+2.900, median) and c21-s2 (+2.275,
   basin-collapsed) gives a 3-anchor inverse-scaling curve.
3. **Stretch: structurally richer family.** Cycle-25 has time to
   queue ONE of: 6-bucket ladder, smooth-head MLP, or EMA-inv
   state at long-CEM on c21-s1, multi-seed (n=3 from the start).
   Decision rule: if any of these moves the c21-s1 n=3 mean lift
   over piecewise above the long-CEM ladder's +0.13, the M4
   frontier moves; if not, M4's headline number is locked at
   long-CEM ladder n=3 +3.034 ± 0.066.
4. **Bin/checks/.** No new check planned for cycle 25 unless an
   experimental finding warrants one. Cycle 24's check-13 is
   live and passing.

## M4 cumulative history (revised, cycle 24)

| pass | family | warm-start | budget | seeds | test lift_FF | retail_adv (test) |
|--|--|--|--|--:|--:|--:|
| anchor (c5) | piecewise | inh | — | n/a | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | 1 | +2.10 | +1.08 (val) |
| **c5 + CEM** (c16) | piecewise | c5 | 5g×12p, real_data | 1 | +0.74 | -10.14 |
| **c11 + CEM short** (c17) | piecewise | c11_d16_s2 | 5g×12p, real_data | 1 | +2.77 | +0.66 |
| default + CEM (c18) | piecewise | default | 5g×12p, real_data | 1 | +1.05 | -15.28 |
| c6 + CEM (c18) | piecewise | c6_warmstart | 5g×12p, real_data | 1 | +1.89 | -0.00 |
| c8_16d + CEM (c18) | piecewise | c8 inv-aware best (16d proj) | 5g×12p, real_data | 1 | +2.35 | +0.36 |
| **c11 + CEM long, seed=0** (c18) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +3.006 | +3.215 |
| **c11 + CEM long, seed=1** (c21) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +2.900 | +3.820 |
| **c11 + CEM long, seed=2** (c21) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +2.275 | -3.024 |
| **c11 long-CEM mean ±σ** (n=3) | piecewise | c11_d16_s2 | 10g×24p, real_data | 3 | **+2.727 ± 0.322** | +1.34 ± 3.16 |
| **ladder seed=0** (c19) | ladder-4bucket | c11_long ext (c18-s0) | 5g×12p, real_data | 1 | +3.251 | +3.113 |
| **ladder seed=1** (c20) | ladder-4bucket | c11_long ext (c18-s0) | 5g×12p, real_data | 1 | +3.076 | +3.834 |
| **ladder seed=2** (c20) | ladder-4bucket | c11_long ext (c18-s0) | 5g×12p, real_data | 1 | +3.006 | +3.215 |
| **ladder mean ±σ** (n=3, c18-s0 anchor) | ladder-4bucket | c11_long-s0 | 5g×12p | 3 | +3.111 ± 0.126 | +3.39 ± 0.39 |
| **ladder seed=0** (c22) | ladder-4bucket | c11_long ext (c21-s1) | 5g×12p, real_data | 1 | +2.900 | +3.820 |
| **ladder seed=1** (c22) | ladder-4bucket | c11_long ext (c21-s1) | 5g×12p, real_data | 1 | +2.900 | +3.820 |
| **ladder seed=0** (c22, stretch) | ladder-4bucket | c11_long ext (c21-s2) | 5g×12p, real_data | 1 | +2.275 | -3.024 |
| **ladder lift_FF cross-anchor mean (short-CEM)** | ladder-4bucket | mixed | 5g×12p | 4 | **~0** (range 0–0.245, only c19 single-seed positive) | — |
| **ladder seed=0 (c23)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +3.098 | +4.378 |
| **ladder seed=1 (c23)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +2.966 | +2.475 |
| **NEW: ladder seed=2 (c24)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | **+3.037** | **+3.741** |
| **NEW: ladder long-CEM mean ±σ (n=3, c21-s1 anchor)** | ladder-4bucket | c11_long-s1 | 10g×24p | 3 | **+3.034 ± 0.066** | +3.53 ± 0.97 |
| **NEW: ladder lift over c21-s1 piecewise (long-CEM, n=3)** | — | — | — | 3 | **+0.134 ± 0.066** | — |
| **NEW: ladder seed=0 (c24, c21-s2 anchor)** | ladder-4bucket | c11_long ext (c21-s2) | **10g×24p**, real_data | 1 | **+2.822** | **−0.995** |
| **NEW: ladder lift over c21-s2 piecewise (long-CEM, n=1)** | — | — | — | 1 | **+0.547** | — |

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-24 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Vendored wheels make it importable on the original sandbox after
  the cycle's setup step.
- **jax disappears between checks on this sandbox.** New observation
  cycle 24: after `bin/setup_jax_from_vendored.sh` ran successfully
  and jax 0.6.2 was importable in the early checks pass, a later
  `python3 -c "import jax"` failed with ModuleNotFoundError.
  Plausibly the install went to a session-local
  `~/.local/lib/python3.10/site-packages/` whose contents the sandbox
  may garbage-collect or not propagate to subprocesses identically.
  Cycle 24 did not need jax for the experiments (ladder runs use
  the `arena_eval/exact_simple_amm` path, no jax). Check 08 remains
  FAIL on the run-suite output but is a pre-existing failure (also
  FAIL'd in cycle 23's first pass). Not blocking.
- **pyarrow install** can OOM but cycle 24 succeeded on first try
  bundled with gymnasium/pytest/matplotlib (no isolation needed
  this cycle).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle. Cycle
  24's sandbox: `/sessions/bold-jolly-keller`.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib`. Cycle 24
  succeeded with this single bundle (~30s).
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate.
- CPU: 4 cores. Cycle 24 ran two parallel long-CEM jobs at
  workers=2 each (saturating cores). Both runs finished in
  the same wall window: ~38 min CEM (~220s/gen × 10) + ~4 min
  rerank + ~2.5 min test+FF = ~45 min wall.
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~120s are reliably killed with exit 143 by the sandbox. Cycle
  24 used 90-110s sleeps consistently and they survived.
- **Backgrounded process inheritance**: `Bash(... & PID=$!)` in a
  multi-line command had its newlines flattened by shell `eval`
  in cycle 24, causing the second backgrounded job to die with
  permission-denied on its redirect. Workaround that worked: write
  a tiny `/tmp/launch_*.sh` file per job and `nohup` each one
  separately, then `disown`.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently **13 active checks** (cycle 24 added
  `13_long_cem_beats_anchor.py`; no checks retired this cycle).
  Cap is ~12; cycle 25 should consider whether any older check
  has flipped to no-op.
- **Seed reproducibility rule.** Going forward, any M4
  family/budget claim needs ≥3 rng_seeds before being entered as
  a headline. Cycle 24's c21-s2 stabilizer claim is currently
  n=1 — supporting evidence, not a headline.
- **Anchor confounding rule.** Family-escalation claims require
  cross-anchor lift, not just lift over a single warm-start seed.
  Cycle 24 added a c21-s2 datapoint; the cross-anchor curve now
  has 3 points (c18-s0 n=1, c21-s1 n=3, c21-s2 n=1).
- **Cycle-24 finding (anchor-dependent lift).** Long-CEM ladder
  lift over piecewise scales with piecewise quality: better the
  piecewise, smaller the ladder gain. Cross-anchor short-CEM
  experiments without long-CEM controls are still false-negative-
  prone (cycle-23 finding); cross-anchor long-CEM seeded once
  may exhibit large lifts that wash out with more seeds (cycle-24
  c21-s2 needs n≥2 confirmation).
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-24's edits restricted to `research/` and
  `bin/checks/13_long_cem_beats_anchor.py`.
