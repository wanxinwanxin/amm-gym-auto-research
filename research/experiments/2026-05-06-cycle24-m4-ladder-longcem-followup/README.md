# M4 cycle 24 — long-CEM ladder follow-up to cycle 23

## Question

Cycle 23 produced n=2 long-CEM ladder runs warm-started from the
cycle-21-seed-1 piecewise anchor and found a small-but-positive lift
of `+0.132 ± 0.066 lift_FF` over the same anchor (whereas short-CEM
ladder on the same anchor produced exactly +0.000). Two open questions
emerged:

* **Q1 (third-seed).** Is the n=2 mean stable? A third RNG seed should
  land in the cycle-23 sample range (`+0.07, +0.20`) and produce an
  n=3 mean in `+0.05, +0.20`.
* **Q2 (cross-anchor stabilizer).** Cycle 22 stretch found that
  short-CEM ladder on the *cycle-21-seed-2* (basin-collapsed)
  piecewise produced +0.000 lift. Does long-CEM ladder *recover* lift
  on this anchor — i.e. does the ladder family act as a stabilizer at
  long-CEM compute?

## Method

Identical CEM mechanics to cycle 23 (19-d ladder, FF normalizer
0.003/0.003, 64 search seeds, 128 val, 256 test) at long-CEM budget
(POPULATION=24, GENERATIONS=10). Two parallel runs:

* `cycle21_seed1_seed2`: third RNG seed on the cycle-21-seed-1
  piecewise anchor (anchor val 3.651 / nominal piecewise lift_FF +2.900).
* `cycle21_seed2_seed0`: rng_seed=0 on the cycle-21-seed-2
  piecewise anchor (anchor val 3.215 / nominal piecewise lift_FF
  +2.275, basin-collapsed).

Both runs use identity warm-start (the ladder's three new dims —
`tiny_trade_threshold`, `continuation_tiny`, `reversal_tiny` — are
seeded from the corresponding "small" piecewise param so the gen-0
anchor candidate is exactly the piecewise policy under the ladder
parameterization).

## Results (held-out test, n=256)

### c21-s1 anchor — n=3 long-CEM ladder cluster

| run                 | rng_seed | val (n=128) | test (n=256) | lift_FF  | lift over c21-s1 piecewise | retail_adv (test) |
|---------------------|---------:|------------:|-------------:|---------:|---------------------------:|------------------:|
| cycle23 seed=0      |        0 |       3.865 |        3.569 |  +3.098 |                    +0.198 |             +4.378 |
| cycle23 seed=1      |        1 |       4.055 |        3.437 |  +2.966 |                    +0.066 |             +2.475 |
| **cycle24 seed=2**  |        2 |       3.796 |        3.507 |  +3.037 |                    +0.137 |             +3.741 |
| **mean ± σ (n=3)**  |          |       3.905 |        3.504 | **+3.034 ± 0.066** | **+0.134 ± 0.066** |     +3.53 ± 0.97 |

Cycle 23's n=2 mean of `+0.132 ± 0.066` and cycle 24's third seed's
`+0.137` are within `0.005 lift_FF` of each other. The n=3 mean
moves only `+0.002` from the cycle-23 n=2 mean and the std is
unchanged. **The cycle-23 result is reproducible.**

### c21-s2 anchor — cross-anchor probe (stabilizer test)

| run                 | rng_seed | val (n=128) | test (n=256) | lift_FF  | lift over c21-s2 piecewise | retail_adv (test) |
|---------------------|---------:|------------:|-------------:|---------:|---------------------------:|------------------:|
| anchor (c21-s2 piecewise) |    — |       3.215* |       2.745  |  +2.275 |                       0.000 |             −3.024 |
| **cycle24 seed=0**  |        0 |       3.991 |        3.293 |  +2.822 |                  **+0.547** |             −0.995 |

*Anchor val for `c21-s2` is the **ladder anchor val**, i.e. the
piecewise policy expressed in the ladder parameterization, evaluated
on the val seeds. The piecewise-policy val on the same seeds for the
cycle-21-seed-2 best_by_val is the same number under the identity
warm-start.

The c21-s2 long-CEM ladder lift over the same-anchor piecewise is
**+0.547**, an order of magnitude larger than the c21-s1 long-CEM
ladder lift (+0.13 mean). At the same long-CEM budget on the same
ladder family, the lift is highly anchor-dependent: large where the
underlying piecewise is collapsed (s2), small where the underlying
piecewise is competitive (s1).

### Long-CEM elites vs anchor on val (cycle-23 pattern repeated)

For both runs, every non-anchor candidate in the rerank pool
(top-6 unique elites by search score) beats the anchor on val:

| run                  | anchor val | non-anchor val range | min lift on val |
|----------------------|-----------:|---------------------:|----------------:|
| cycle21_seed1_seed2  |      3.651 |        3.784 – 3.796 |          +0.133 |
| cycle21_seed2_seed0  |      3.215 |        3.651 – 3.991 |          +0.436 |

This is exactly the cycle-23 pattern. The rerank pool at long-CEM
contains *quality* elites, not just lucky-search elites. Encoded as
`bin/checks/13_long_cem_beats_anchor.py`.

## What it changed

1. **The cycle-23 c21-s1 result is reproducible (n=3).** The mean
   lift of long-CEM ladder over the c21-s1 piecewise is `+0.134 ±
   0.066` (n=3, sample range `[+0.066, +0.198]`). The cycle-23 n=2
   estimate of `+0.132 ± 0.066` did not move when we added the third
   seed.

2. **The "ladder as stabilizer at long-CEM" hypothesis is supported
   on n=1.** Long-CEM ladder on the basin-collapsed c21-s2 anchor
   produces `+0.547` lift over the same-anchor piecewise, vs `+0.000`
   for short-CEM ladder on the same anchor (cycle 22 stretch).
   Long-CEM ladder appears to rescue the collapsed-basin anchor much
   more than it lifts the median-basin anchor.

3. **Best test score on real_data is still inside the c21-s1 cluster.**
   c21-s1 long-CEM ladder n=3 mean test = 3.504; c21-s2 long-CEM
   ladder seed=0 test = 3.293. The frontier remains piecewise long-CEM
   on c21-s1 (ladder mean) — the family lift over piecewise on c21-s1
   is real but small (+0.13 → mean test 3.504 vs piecewise mean test
   3.197).

4. **The cycle-23 "every non-anchor candidate beats anchor on val"
   pattern reproduces for both anchors.** Encoded as a check.

5. **Val→test gap is wide on c21-s2.** Val 3.991 → test 3.293
   (`Δ −0.70`). Same basin-overfit-on-val mechanism as cycle 21
   piecewise long-CEM and cycle 23 ladder long-CEM. This is a
   long-CEM artifact across families.

## Next

* **Cycle 25 plan-of-record.** Two parallel directions worth a
  cycle:
  - **Cross-anchor confirmation of the stabilizer effect.** A
    second rng_seed on the c21-s2 anchor and a third anchor (e.g.
    c21-s0, the cycle-18 single-seed anchor that produced lift_FF
    +3.006) — does long-CEM ladder lift scale inversely with
    piecewise quality?
  - **Move the M4 frontier directly.** With the cycle-23/24 picture
    settled, the most informative next step for the headline number
    is *not* another ladder run but a structurally richer policy
    family at long-CEM (e.g. 6-bucket ladder, smooth-head MLP) on
    the c21-s1 anchor. The ladder ceiling at this anchor is
    plausibly `+0.13 ± 0.07` lift over piecewise; richer families
    should be tested there.

## Files

* `scripts/run_ladder_longcem.py` — extends cycle 23 driver with an
  ANCHORS_PIECEWISE entry for c21-s2.
* `scripts/ladder_strategy.py` — copied from cycle 23 (unchanged).
* `scripts/make_figures.py` — three-anchor / three-budget summary.
* `results/cycle21_seed1_seed2/` — third c21-s1 RNG seed (long-CEM,
  ladder).
* `results/cycle21_seed2_seed0/` — cross-anchor c21-s2 long-CEM
  ladder.
* `results/cross_seed_summary.json` — combined c23+c24 numerical
  summary (n=3 c21-s1 mean + c21-s2 single-seed).
* `figures/m4_c24_lift_summary.png`, `figures/m4_c24_long_cem_val_curves.png`.
