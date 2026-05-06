# State — current cycle

**Last updated**: 2026-05-06 (cycle 28 — closed)

> **Operational note (cycle 28).** SSH proxy to GitHub failed for
> the entire cycle (`Connection closed by UNKNOWN port 65535` on
> every `git push`). The cycle-28 commit `2b6bbeb` and the
> cycle-27 commit `9626515` are both local-only on this sandbox.
> Both pushes need to be retried at the start of cycle 29 (the
> standard cycle-protocol orient step already does this). No
> commit history rewrite needed — `git push origin main` from a
> healthy sandbox should publish both commits in order. This is
> a sandbox-network issue, not a credential/repo issue, so it's
> not paged to the user.

## Active milestone

**M4 cycle 12 (closed) → M4 cycle 13 (next).** Cycle 28 ran the
cycle-27 plan-of-record candidate (1): a 5-bucket ladder long-CEM
on c18-s0 with `init_std_frac_new` tightened from 0.15 → 0.05
(matching the inherited dims). **Result: cycle-28 confirms that the
cycle-27 5-bucket underperformance was variance-bounded, not
family-bounded. Tightening init_std_new lifts the 5-bucket cluster
from +3.093 ± 0.123 (cycle 27) to +3.253 ± 0.009 (cycle 28),
+0.160 mean and 13× tighter dispersion. However, the 5-bucket-tight
cluster mean (+3.253 ± 0.009) is still −0.024 below the cycle-26
4-bucket cluster mean (+3.277 ± 0.027) — within ~0.9σ of the
4-bucket cluster, statistically indistinguishable on n=2 vs n=3.
The M4 frontier on real_data stays at the 4-bucket cluster
+3.277 ± 0.027.**

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **M4 frontier on real_data, multi-seed mean (long-CEM 4-bucket
  ladder on c18-s0 anchor, cycles 25+26, n=3): test +3.747,
  lift_FF +3.277 ± 0.027** [range +3.256, +3.307]. Lift over
  same-anchor piecewise +0.271 ± 0.027. **The M4 cross-seed
  frontier on real_data — held since cycle 26.** Cycles 27 and 28
  attempted to move it with the 5-bucket family at two
  init_std_new settings; both failed.
- **Best real_data single-seed nominal: cycle-26 c18-s0 rng=2:
  test +3.777, lift_FF +3.307, lift over piecewise +0.301.**
  Held since cycle 26.
- **NEW (cycle 28): 5-bucket ladder long-CEM on c18-s0 with
  init_std_new=0.05, n=2 mean ±σ: test +3.723, lift_FF
  +3.253 ± 0.009, lift over piecewise +0.247 ± 0.009.**
  Per-seed: seed=0 lift_FF +3.246 (lift +0.241), seed=1 lift_FF
  +3.259 (lift +0.254). BOTH seeds in the find regime by
  best-by-val (val +4.089 each, +0.20 over anchor). Mean −0.024
  below the +3.28 frontier-move threshold; lift over piecewise
  +0.247 is +0.16 above cycle-27 (+0.087) but −0.024 below the
  4-bucket cluster.
- **PRIOR (cycle 27): 5-bucket ladder long-CEM on c18-s0 with
  init_std_new=0.15, n=2 mean ±σ: test +3.564, lift_FF
  +3.093 ± 0.123, lift over piecewise +0.087 ± 0.123.** Held
  for context as the cycle-28 contrast (init_std_new=0.15 → 0.05
  comparison).
- **Best real_data score, multi-seed mean (long-CEM 4-bucket ladder
  on c21-s1 anchor, cycles 23+24, n=3): test +3.504, lift_FF
  +3.034 ± 0.066** [range +2.966, +3.098]. Held for context.
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Held for context as the piecewise-only baseline.
- **Cross-anchor / cross-family / cross-budget ladder lift over
  piecewise (revised, c19/22/23/24/25/26/27/28):**

  | budget | family | anchor | std_new | n_seeds | lift over piecewise (mean ± σ) |
  |--|--|--|--|--:|--:|
  | short-CEM (5g×12p) | 4-bucket | cycle-18-s0 | 0.15 | 1 | +0.245 (cycle 19, single seed) |
  | short-CEM (5g×12p) | 4-bucket | cycle-21-s1 | 0.15 | 2 | +0.000 (cycle 22, both seeds) |
  | short-CEM (5g×12p) | 4-bucket | cycle-21-s2 | 0.15 | 1 | +0.000 (cycle 22, stretch) |
  | long-CEM (10g×24p) | 4-bucket | cycle-21-s1 | 0.15 | 3 | +0.134 ± 0.066 (c23+c24) |
  | long-CEM (10g×24p) | 4-bucket | cycle-21-s2 | 0.15 | 2 | +0.273 ± 0.387 (c24+c25) |
  | **long-CEM (10g×24p)** | **4-bucket** | **cycle-18-s0** | **0.15** | **3** | **+0.271 ± 0.027 (c25+c26)** |
  | long-CEM (10g×24p) | 5-bucket | cycle-18-s0 | 0.15 | 2 | +0.087 ± 0.123 (c27) |
  | **NEW long-CEM (10g×24p)** | **5-bucket** | **cycle-18-s0** | **0.05** | **2** | **+0.247 ± 0.009 (c28)** |

- **Aggregated long-CEM 4-bucket ladder lift over piecewise
  (n=8 seeds, 3 anchors):** mean +0.220, sample stddev ±0.167,
  range [+0.000, +0.547]. 7/8 in find regime, 1/8 in collapse
  regime. Bimodal invariant holds on the 4-bucket subset (check 13).
- **5-bucket family find/collapse regime tally (cycles 27+28, c18-s0,
  n=4 across two std_new settings):** by check 13's worst-non-anchor
  margin: 1/4 find (cycle-28 seed 1, +0.157), 3/4 wash band (cycle-27
  seed 0 +0.075, cycle-27 seed 1 −0.405, cycle-28 seed 0 −0.004),
  0/4 collapse. The 4-bucket bimodal invariant does NOT generalise
  to the 5-bucket family at any tested CEM budget. However, this
  uses *worst* non-anchor val; *best-by-val* (which actually drives
  test score) puts both cycle-28 seeds and cycle-27 seed 0 firmly
  in the find regime — the wash-band entries are gen-2 outliers
  in the rerank pool, not the winners.

## Cycle-28 verdict

1. **The cycle-27 underperformance was variance-bounded, not
   family-bounded.** Tightening `init_std_frac_new` from 0.15 →
   0.05 lifts the 5-bucket cluster mean from +3.093 → +3.253
   (+0.160 in lift_FF, +0.160 in lift over piecewise). Both
   cycle-28 seeds individually exceed the +3.06 piecewise floor
   and exceed cycle-27 mean by ~0.16. **PARTIAL_OR_NO_LIFT verdict**:
   cluster mean does not exceed the +3.28 4-bucket frontier
   threshold, but the gap (−0.024) is within the 4-bucket cluster's
   own σ-band (±0.027).

2. **The 5-bucket-tight cluster is dramatically tighter than
   5-bucket-wide.** σ shrinks from 0.123 → 0.009, a 13× reduction.
   This is consistent with the mechanistic finding from cycle 27:
   most of the 5-bucket variance was driven by exploration noise
   on the 6 new dims (`ultra_tiny_*`, `tiny_*`) at init_std=0.15.
   With std=0.05, the new dims explore on the same scale as the
   inherited dims and the search converges quickly.

3. **CEM convergence dramatically faster at tight std.** At gen 2,
   cycle-28 seed-0 elite_mean=+3.079 (vs cycle-27 seed-0 elite_mean
   at gen 2=+2.853 in cycle 27 LOG); cycle-28 reaches elite_mean
   above the anchor (+2.901) by gen 1–2 in both seeds. Cycle-27
   reached the same level only at gen 4 (seed 0) or gen 9 (seed 1).

4. **The 5-bucket-tight family does NOT exceed the 4-bucket-wide
   on c18-s0 long-CEM.** Cluster mean +3.253 < +3.277. Two
   interpretations remain open: (a) the 4-bucket is a genuine
   family ceiling on c18-s0 at 10g×24p budget; (b) the 5-bucket-tight
   would catch up at higher CEM compute (15g×24p) — i.e. the
   family is more capable but consumes more compute to express.
   Cycle 29 should disambiguate by running 5-bucket-tight at
   15g×24p compute. n=2 vs n=3 sample sizes also leave open
   the possibility that an n=3 5-bucket-tight cycle-29 mean lands
   above +3.277 within sampling noise.

5. **Single-seed best on real_data unchanged.** Cycle-28 seed 1's
   lift_FF +3.259 is below cycle-26's single-seed best (+3.307)
   and below all cycle-25/26 c18-s0 4-bucket seeds. Headline
   single-seed real_data score remains cycle-26 c18-s0 rng=2:
   test +3.777, lift_FF +3.307.

6. **Wide val→test gap holds for the 5-bucket family too.** Both
   cycle-28 seeds: val +4.089 → test +3.717 / +3.730 (gap −0.37 /
   −0.36). Same pattern as cycle-21 piecewise long-CEM (val ~+0.45
   above test) and cycle-23/24 4-bucket long-CEM (gap −0.30 to
   −0.40). Long-CEM rerank-by-val is biased — there is reliably
   ~0.3–0.4 of regression-to-mean from val to test.

## Active hypothesis going into cycle 29

> **"At init_std_new=0.05, the 5-bucket family is variance-matched
> to the 4-bucket family on c18-s0 long-CEM. The remaining
> −0.024 cluster-mean gap (−0.9σ of the 4-bucket cluster) is
> compute-bounded: at 15g×24p budget (1.5× compute), the
> 5-bucket-tight cluster will close the gap or exceed the 4-bucket
> cluster on c18-s0. If at 15g×24p budget the 5-bucket-tight
> cluster still does not exceed +3.28, the 4-bucket family is the
> structural ceiling on c18-s0 at long-CEM and adding `ultra_tiny_*`
> dimensions is not actionable on this anchor's basin."**

## Next-cycle plan-of-record (cycle 29)

1. **5-bucket at higher CEM compute (15g × 24p) on c18-s0,
   init_std_new=0.05, multi-seed.** ~70 min wall for n=2.
   Direct test of the cycle-28 active hypothesis. Decision rule:
   if n=2 mean lift_FF > +3.28 AND both seeds individually >
   +3.20, the 5-bucket family lifts the frontier with more
   compute → cycle 30 confirms with n=3. If at least one seed
   < +3.20, the 4-bucket is the c18-s0 ceiling at long-CEM and
   the M4 headline locks at +3.277 ± 0.027 (cycle-26 cluster).
2. **Stretch: 3rd c18-s0 5-bucket-tight seed.** Single job,
   ~25 min wall (assuming sandbox runs at normal speed). Tightens
   cycle-28 cluster from n=2 to n=3, gives a tighter ±σ for
   future comparisons. Use to confirm the cycle-28 verdict after
   the 15g×24p compute test.
3. **Stretch: 4th c18-s0 long-CEM 4-bucket ladder seed.** Single
   job, ~25 min wall. Tightens c18-s0 4-bucket cluster from n=3
   to n=4 (cycle-26 σ=±0.027; n=4 → ±0.023). Useful for any future
   family-comparison test.
4. **Bin/checks/.** Cycle 28 added cycle-28 5-bucket-tight runs
   to OBSERVATIONAL_RUNS in check 13 (no net change in active
   count; still 12). No new check this cycle. Consider retiring
   check 08 (jax_optional) if its sandbox-quirk failure mode
   persists into cycle 29 — the cycle 26 fix-up note suggests
   `/tmp` writes are now blocked, which is the actual failure
   mode (not a jax problem).

## M4 cumulative history (revised, cycle 28)

| pass | family | warm-start | budget | std_new | seeds | test lift_FF | retail_adv (test) |
|--|--|--|--|--:|--:|--:|--:|
| anchor (c5) | piecewise | inh | — | — | n/a | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | — | 1 | +2.10 | +1.08 (val) |
| **c5 + CEM** (c16) | piecewise | c5 | 5g×12p, real_data | — | 1 | +0.74 | -10.14 |
| **c11 + CEM short** (c17) | piecewise | c11_d16_s2 | 5g×12p, real_data | — | 1 | +2.77 | +0.66 |
| default + CEM (c18) | piecewise | default | 5g×12p, real_data | — | 1 | +1.05 | -15.28 |
| c6 + CEM (c18) | piecewise | c6_warmstart | 5g×12p, real_data | — | 1 | +1.89 | -0.00 |
| c8_16d + CEM (c18) | piecewise | c8 inv-aware best (16d proj) | 5g×12p, real_data | — | 1 | +2.35 | +0.36 |
| **c11 + CEM long, seed=0** (c18) | piecewise | c11_d16_s2 | 10g×24p, real_data | — | 1 | +3.006 | +3.215 |
| **c11 + CEM long, seed=1** (c21) | piecewise | c11_d16_s2 | 10g×24p, real_data | — | 1 | +2.900 | +3.820 |
| **c11 + CEM long, seed=2** (c21) | piecewise | c11_d16_s2 | 10g×24p, real_data | — | 1 | +2.275 | -3.024 |
| **c11 long-CEM mean ±σ** (n=3) | piecewise | c11_d16_s2 | 10g×24p, real_data | — | 3 | +2.727 ± 0.322 | +1.34 ± 3.16 |
| **4-bucket ladder (long-CEM) c21-s1 mean ±σ** (n=3, c23+c24) | 4-bucket | c21-s1 piecewise | 10g×24p, real_data | 0.15 | 3 | +3.034 ± 0.066 | +2.20 ± 0.95 |
| **4-bucket ladder (long-CEM) c21-s2 mean** (n=2, c24+c25) | 4-bucket | c21-s2 piecewise | 10g×24p, real_data | 0.15 | 2 | +2.549 ± 0.387 | -0.4 ± 4.5 |
| **4-bucket ladder (long-CEM) c18-s0 mean ±σ** (n=3, c25+c26) | 4-bucket | c18-s0 piecewise | 10g×24p, real_data | 0.15 | 3 | **+3.277 ± 0.027** | +3.43 ± 0.53 |
| 5-bucket ladder (long-CEM) c18-s0 mean ±σ (n=2, c27) | 5-bucket | c18-s0 piecewise | 10g×24p, real_data | 0.15 | 2 | +3.093 ± 0.123 | +3.17 ± 0.06 |
| **5-bucket-tight ladder (long-CEM) c18-s0 mean ±σ** (n=2, c28) | **5-bucket** | c18-s0 piecewise | 10g×24p, real_data | **0.05** | 2 | **+3.253 ± 0.009** | +3.22 ± 0.44 |

**M4 frontier on real_data**: held at +3.277 ± 0.027 (4-bucket
ladder long-CEM, c18-s0 anchor, n=3 cross-seed, cycles 25+26).
Cycles 27 and 28's 5-bucket attempts at the same anchor and budget
came in below; cycle-28 closed most of the cycle-27 variance gap
but did not move the frontier.

## Open questions (carried forward)

1. **Does the 5-bucket-tight family lift the M4 frontier at higher
   CEM compute (15g × 24p)?** Cycle-29 plan-of-record tests this
   directly. The cycle-28 result narrows the −0.024 gap to within
   0.9σ of the 4-bucket cluster, so a small compute boost could
   plausibly close or invert the gap.
2. **Does the 4-bucket bimodal invariant generalise to the
   5-bucket family at any compute/std combination?** Cycle 28
   added 2 more 5-bucket samples (1 find, 1 wash by worst-non-anchor
   margin); aggregate 5-bucket tally is now 1/4 find, 3/4 wash,
   0/4 collapse. The 5-bucket family appears to have a different
   regime structure — wash-band is allowed and common.
3. **Is the c18-s0 anchor's tight ±0.027 cycle-26 dispersion
   reproducible at n=4?** Stretch task, defer to cycle 29+ as
   stretch.
4. **Are c18-s0/c21-s1/c21-s2 anchors collapse-rate-different at
   short-CEM?** Cycle-26 stretch question, deferred again.
5. **Why is the val→test gap reliably −0.30 to −0.40 on long-CEM
   ladder warm-starts?** Pattern holds across cycles 21 (piecewise),
   23/24 (4-bucket), 27/28 (5-bucket). Suggests rerank-by-val
   has a systematic bias of this magnitude on the c18-s0/c21
   basin. Not actionable yet, but candidate for an M4 wrap-up
   diagnostic experiment.
