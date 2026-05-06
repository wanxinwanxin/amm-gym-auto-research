# State — current cycle

**Last updated**: 2026-05-06 (cycle 27 — closed)

## Active milestone

**M4 cycle 11 (closed) → M4 cycle 12 (next).** Cycle 27 ran the
cycle-26 plan-of-record candidate (a): a 5-bucket ladder family
(split the cycle-26 4-bucket's `tiny` bucket into `ultra_tiny + tiny`,
+3 dims, 22-d total) at long-CEM on the c18-s0 anchor multi-seed.
**Result: cycle-27 falsifies the active hypothesis. Both seeds
land below the +3.28 decision threshold; the 5-bucket cluster
mean (n=2) is lift_FF +3.093 ± 0.123, lift over piecewise +0.087
± 0.123 — both −0.184 below the cycle-26 4-bucket cluster mean.
The M4 frontier on real_data stays at the 4-bucket cluster
+3.277 ± 0.027 (n=3, cycles 25+26).**

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **M4 frontier on real_data, multi-seed mean (long-CEM 4-bucket
  ladder on c18-s0 anchor, cycles 25+26, n=3): test +3.747,
  lift_FF +3.277 ± 0.027** [range +3.256, +3.307]. Lift over
  same-anchor piecewise +0.271 ± 0.027. **The M4 cross-seed
  frontier on real_data — held since cycle 26.** Cycle 27
  attempted to move it with the 5-bucket family and failed.
- **Best real_data single-seed nominal: cycle-26 c18-s0 rng=2:
  test +3.777, lift_FF +3.307, lift over piecewise +0.301.**
  Held since cycle 26.
- **NEW (cycle 27): 5-bucket ladder long-CEM on c18-s0, n=2 mean ±σ:
  test +3.564, lift_FF +3.093 ± 0.123, lift over piecewise
  +0.087 ± 0.123.** Per-seed: seed=0 lift_FF +3.180 (lift +0.174,
  basin-found-but-val→test gap −0.32); seed=1 lift_FF +3.006 (lift
  +0.000, rerank picked anchor — CEM never crossed anchor val on
  this seed). Both below the +3.28 frontier-move threshold;
  family-doesn't-help / compute-is-binding distinction left to
  cycle 28.
- **Best real_data score, multi-seed mean (long-CEM 4-bucket ladder
  on c21-s1 anchor, cycles 23+24, n=3): test +3.504, lift_FF
  +3.034 ± 0.066** [range +2.966, +3.098]. Held for context.
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Held for context as the piecewise-only baseline.
- **Cross-anchor / cross-family / cross-budget ladder lift over
  piecewise (revised, c19/22/23/24/25/26/27):**

  | budget | family | anchor | n_seeds | lift over piecewise (mean ± σ) |
  |--|--|--|--:|--:|
  | short-CEM (5g×12p) | 4-bucket | cycle-18-s0 | 1 | +0.245 (cycle 19, single seed) |
  | short-CEM (5g×12p) | 4-bucket | cycle-21-s1 | 2 | +0.000 (cycle 22, both seeds) |
  | short-CEM (5g×12p) | 4-bucket | cycle-21-s2 | 1 | +0.000 (cycle 22, stretch) |
  | long-CEM (10g×24p) | 4-bucket | cycle-21-s1 | 3 | +0.134 ± 0.066 (c23+c24) |
  | long-CEM (10g×24p) | 4-bucket | cycle-21-s2 | 2 | +0.273 ± 0.387 (c24+c25) |
  | **long-CEM (10g×24p)** | **4-bucket** | **cycle-18-s0** | **3** | **+0.271 ± 0.027 (c25+c26)** |
  | **NEW long-CEM (10g×24p)** | **5-bucket** | **cycle-18-s0** | **2** | **+0.087 ± 0.123 (c27)** |

- **Aggregated long-CEM 4-bucket ladder lift over piecewise
  (n=8 seeds, 3 anchors):** mean +0.220, sample stddev ±0.167,
  range [+0.000, +0.547]. 7/8 in find regime, 1/8 in collapse
  regime. Bimodal invariant holds on the 4-bucket subset.
- **NEW: 5-bucket family is NOT bimodal at long-CEM (10g×24p).**
  Both cycle-27 c18-s0 5-bucket runs land in the wash band
  (margin in (−0.50, +0.10)): seed 0 margin +0.075, seed 1 margin
  −0.405. Check 13 narrowed to the 4-bucket family; 5-bucket runs
  in OBSERVATIONAL_RUNS, not asserted on.

## Cycle-27 verdict

1. **The cycle-26 active hypothesis is rejected at long-CEM
   (10g × 24p) budget.** A structurally richer family (5-bucket)
   does NOT lift the M4 frontier above the 4-bucket cluster on
   c18-s0 at the same compute. Both seeds < +3.28 decision
   threshold; n=2 mean −0.184 below the 4-bucket cluster mean.

2. **The 22-d 5-bucket landscape has more search noise than the
   19-d 4-bucket at the same CEM budget.** Mechanistic evidence:
   4-bucket elite-mean exceeds anchor by gen 2; 5-bucket elite-mean
   does not exceed anchor until gen 4 (seed 0) or gen 9 (seed 1).
   This is likely the dominant cause of the cluster-mean gap, but
   the cycle-28 follow-up (longer CEM or smaller new-dim init_std)
   is needed to distinguish "family doesn't help" from "compute
   is binding".

3. **Rerank-by-val with anchor floor is the safety net.** Seed 1's
   gen-9 best by val (+3.539) was below the anchor (+3.885), so the
   rerank correctly picked the anchor — lift over piecewise = 0
   instead of regressing below piecewise. This confirms the cycle
   protocol is robust; future families can use the same protocol.

4. **The bimodal find/collapse framing was 4-bucket-specific, not
   universal.** Both cycle-27 5-bucket seeds land in the wash band
   (margins +0.075 and −0.405). The 4-bucket bimodal invariant
   (8/8 across cycles 23–26) does NOT generalise to the 5-bucket
   family at the same CEM budget. Check 13 narrowed in place.

5. **Single-seed best on real_data unchanged.** Cycle-27 seed 0's
   lift_FF +3.180 (test +3.651) is below cycle-26's single-seed
   best (+3.777) and below all cycle-25/26 c18-s0 ladder seeds.
   The headline single-seed real_data score remains cycle-26
   c18-s0 rng=2: test +3.777, lift_FF +3.307.

## Active hypothesis going into cycle 28

> **"At the cycle-27 CEM budget (10g × 24p, init_std_new=0.15), the
> 22-d 5-bucket search space is starved relative to the 19-d
> 4-bucket. Two natural fixes — (i) longer CEM (15g × 24p, 1.5×
> compute) and (ii) smaller new-dim init_std (0.05 instead of
> 0.15, matching the inherited dims) — would test whether the
> cycle-27 underperformance is compute-bounded or family-bounded.
> If either lifts the 5-bucket cluster mean above the +3.28
> frontier threshold on c18-s0 multi-seed, the family helps and
> cycle-27 was a budget artefact. If neither does, the 4-bucket is
> the c18-s0 ceiling and the M4 headline locks at +3.277 ± 0.027."**

## Next-cycle plan-of-record (cycle 28)

1. **5-bucket at lower init_std_new=0.05 on c18-s0, multi-seed.**
   This is the cheaper of the two cycle-27 follow-ups: same CEM
   budget as cycle 27 (10g × 24p) but with init_std_new tightened
   to match init_std_inh. Wall-clock budget: ~46 min for n=2 at
   workers=2. Decision rule: if n=2 mean lift_FF on c18-s0 > +3.28
   AND both seeds individually > +3.10, the 5-bucket family
   helps when given less search noise on the new dims; cycle 29
   tightens with n=3. If at least one seed < +3.06 (= piecewise
   level), the family is the binding constraint, not the
   exploration variance. Recommended primary because it's cheap
   AND distinguishes mechanism (compute vs noise).
2. **5-bucket at higher CEM compute (15g × 24p) on c18-s0,
   multi-seed.** ~70 min wall for n=2. More direct test of the
   "compute-bounded" hypothesis. Use as cycle-28 primary if
   workers/wall budget allows; otherwise hold for cycle 29.
3. **Stretch: 4th c18-s0 long-CEM 4-bucket ladder seed.** Single
   job, ~25 min wall. Tightens c18-s0 4-bucket cluster from n=3
   to n=4. Cycle-26 cluster σ=±0.027; n=4 would tighten to ±0.027/√(4/3)
   ≈ ±0.023. Useful for any future family-comparison test.
4. **Bin/checks/.** Cycle 27 narrowed check 13 to the 4-bucket
   family in place (no net change in active count; still 12).
   Cycle 28 should consider adding a check that ensures the
   cycle-27 5-bucket result is reproducible if cycle 28 expands
   to 5-bucket-with-tighter-std and confirms the family doesn't
   help.

## M4 cumulative history (revised, cycle 27)

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
| **c11 long-CEM mean ±σ** (n=3) | piecewise | c11_d16_s2 | 10g×24p, real_data | 3 | +2.727 ± 0.322 | +1.34 ± 3.16 |
| **4-bucket ladder (long-CEM) c21-s1 mean ±σ** (n=3, c23+c24) | 4-bucket | c21-s1 piecewise | 10g×24p, real_data | 3 | +3.034 ± 0.066 | +2.20 ± 0.95 |
| **4-bucket ladder (long-CEM) c21-s2 mean** (n=2, c24+c25) | 4-bucket | c21-s2 piecewise | 10g×24p, real_data | 2 | +2.549 ± 0.387 | -0.4 ± 4.5 |
| **4-bucket ladder (long-CEM) c18-s0 mean ±σ** (n=3, c25+c26) | 4-bucket | c18-s0 piecewise | 10g×24p, real_data | 3 | **+3.277 ± 0.027** | +3.43 ± 0.53 |
| **5-bucket ladder (long-CEM) c18-s0 mean ±σ** (n=2, c27) | **5-bucket** | c18-s0 piecewise | 10g×24p, real_data | 2 | **+3.093 ± 0.123** | +3.17 ± 0.06 |

**M4 frontier on real_data**: held at +3.277 ± 0.027 (4-bucket
ladder long-CEM, c18-s0 anchor, n=3 cross-seed, cycles 25+26).
Cycle 27's 5-bucket attempt at the same anchor and budget came
in below.

## Open questions (carried forward)

1. **Can a structurally richer family beat the 4-bucket on c18-s0
   at *higher* CEM budget?** Cycle 27 attempted this at the
   cycle-26 budget and failed; cycle 28's plan-of-record tests
   whether the failure is compute-bounded.
2. **Does the 4-bucket bimodal invariant generalise to richer
   families with more compute?** Cycle 27 produced 2 wash-band
   samples on the 5-bucket family at long-CEM. If cycle 28's
   5-bucket-with-more-compute moves the runs back into the find
   regime, the wash-band is a budget artefact; if not, it's a
   family property.
3. **Is the c18-s0 anchor's tight ±0.027 cycle-26 dispersion
   reproducible at n=4?** Stretch task, defer to cycle 28+.
4. **Are c18-s0/c21-s1/c21-s2 anchors collapse-rate-different at
   short-CEM?** Cycle-26 stretch question, deferred again.
