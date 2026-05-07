# State — current cycle

**Last updated**: 2026-05-07 (cycle 29 — closed)

> **Operational note (cycle 29).** SSH proxy to GitHub remained
> down at the start of cycle 29 too: `git push origin main` and
> `git pull --ff-only origin main` both fail with the same
> `Connection closed by UNKNOWN port 65535` /
> `Could not resolve hostname github.com` error pattern. The
> repo is now `origin/main` + 2 local-only commits inherited
> from cycles 27 (`9626515`) and 28 (`2b6bbeb`). Cycle 29's
> commit will join them as ahead-by-3 unless the proxy recovers.
> No commit history rewrite needed — a healthy sandbox can
> publish all three in order. HTTPS proxy IS working (curl
> returns 200 for github.com), so a future cycle could switch
> remote URL to HTTPS if SSH stays broken; not done this cycle
> because credentials are not configured for HTTPS. This is a
> sandbox-network issue, not a credential/repo issue, so it's
> not paged to the user.

## Active milestone

**M4 cycle 13 (closed) → M4 cycle 14 (next).** Cycle 29 ran the
cycle-28 plan-of-record candidate (1): 5-bucket-tight ladder
long-CEM on c18-s0 at 15g × 24p (1.5× cycle-28 compute), n=2
seeds. **Result: cycle-29 cluster mean lift_FF +3.255 ± 0.008
(n=2), Δ +0.0025 vs cycle 28 (10g)** — within sampling noise. The
cycle-28 active hypothesis ("compute is the binding constraint
on the 5-bucket-tight cluster reaching the 4-bucket cluster on
c18-s0") is **rejected**. The −0.022 gap to the 4-bucket cluster
at 15g is statistically equal to the cycle-28 −0.024 gap at 10g.
**The 4-bucket family is the structural ceiling on c18-s0 at
long-CEM on this anchor's basin. M4 headline locks definitively
at +3.277 ± 0.027 (cycle-26 4-bucket cluster).**

The literal decision-rule label is MODEST_GAIN (both seeds > +3.20;
cluster mean +3.255 in (+3.253, +3.28)) but substantively cycle-29
cleanly rejects the compute-bounded reading. The 5-bucket-tight
optimization on c18-s0 is compute-converged at 10g — elite-mean
deltas gens 9→14 are ≤+0.012; the rerank pool's top elites at
gens 10–14 differ negligibly from the gen-9 elites; the rerank
picks at val +4.075/+4.080 are slightly *below* cycle 28's gen-9
picks at val +4.089/+4.089. Adding compute is wasted effort.

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
- **PRIOR (cycle 28): 5-bucket ladder long-CEM on c18-s0 with
  init_std_new=0.05, n=2 mean ±σ: test +3.723, lift_FF
  +3.253 ± 0.009, lift over piecewise +0.247 ± 0.009.**
  Per-seed: seed=0 lift_FF +3.246 (lift +0.241), seed=1 lift_FF
  +3.259 (lift +0.254). BOTH seeds in the find regime by
  best-by-val (val +4.089 each, +0.20 over anchor).
- **NEW (cycle 29): 5-bucket ladder long-CEM on c18-s0 with
  init_std_new=0.05 at 15g×24p (1.5× compute), n=2 mean ±σ:
  test +3.726, lift_FF +3.255 ± 0.008, lift over piecewise
  +0.250 ± 0.008.** Per-seed: seed=0 lift_FF +3.248 (lift +0.243),
  seed=1 lift_FF +3.263 (lift +0.258). Both rerank-picked gen-14
  elites (val +4.075 / +4.080). **Δ vs cycle 28 (10g): +0.0025 in
  cluster mean lift_FF — within sampling noise.** Δ vs cycle 26
  4-bucket cluster (10g, n=3): −0.022 — bit-equal to the cycle-28
  gap. **Cycle-28 active hypothesis (compute-bounded) rejected;
  4-bucket is the structural ceiling on c18-s0 at long-CEM.**
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
  | long-CEM (10g×24p) | 5-bucket | cycle-18-s0 | 0.05 | 2 | +0.247 ± 0.009 (c28) |
  | **NEW long-CEM (15g×24p)** | **5-bucket** | **cycle-18-s0** | **0.05** | **2** | **+0.250 ± 0.008 (c29)** |

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

## Cycle-29 verdict

1. **The cycle-28 active hypothesis (compute-bounded) is rejected.**
   Cluster mean lift_FF +3.255 ± 0.008 (n=2) at 15g × 24p vs
   +3.253 ± 0.009 (n=2) at 10g × 24p — Δ +0.0025, within sampling
   noise of either cluster. The −0.022 gap to the 4-bucket cluster
   at 15g is statistically equal to the −0.024 gap at 10g.

2. **The 5-bucket-tight optimization on c18-s0 is compute-converged
   at 10g.** Elite-mean improvement gens 9 → 14 (5 extra gens):
   seed 0 +0.005, seed 1 +0.012. The rerank pool grew but the
   unique top elites are near-identical points in parameter space;
   rerank-by-val picked gen-14 candidates at val +4.075 / +4.080,
   slightly *below* cycle 28's gen-9 picks at val +4.089 / +4.089.

3. **The 4-bucket family is the structural ceiling on c18-s0 at
   long-CEM (at this anchor's basin).** This is now backed by an
   independent compute-budget control. The cycle-28 verdict is
   strengthened, not weakened.

4. **Single-seed best on real_data unchanged.** Cycle-29 seed 1's
   lift_FF +3.263 is below cycle-26's single-seed best (+3.307)
   and below all cycle-25/26 c18-s0 4-bucket seeds. Headline
   single-seed real_data score remains cycle-26 c18-s0 rng=2:
   test +3.777, lift_FF +3.307.

5. **Wide val→test gap holds again.** Both cycle-29 seeds: val
   +4.075/+4.080 → test +3.718/+3.733 (gap −0.357 / −0.347). Same
   pattern as cycles 21/23/24/27/28 — long-CEM rerank-by-val has a
   systematic ~0.30–0.40 regression-to-mean from val to test on
   c18-s0/c21 basins. Not actionable yet, but candidate for an M4
   wrap-up diagnostic experiment.

6. **Cycle-30 plan-of-record candidate (cheap and falsifiable):**
   apply the cycle-28 tightening mechanism (init_std_new=0.15 → 0.05)
   to the 4-bucket family on c18-s0 at the cycle-26 budget. If the
   mechanism transfers, the 4-bucket cluster could exceed +3.30.

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

## Active hypothesis going into cycle 30

> **"The 4-bucket family on c18-s0 used init_std_new=0.15 in cycles
> 25/26; cycle 28 demonstrated that tightening to 0.05 dramatically
> improves CEM convergence and tightens cluster σ in the 5-bucket
> family. Applying the same tightening to the 4-bucket family on
> c18-s0 will push the cluster mean above +3.28 — the cheapest M4
> frontier-mover available, and one that has not been tested. If
> cycle-30's 4-bucket-tight cluster mean exceeds +3.30, the cycle-28
> tightening mechanism transfers cleanly across families and the M4
> frontier moves. If the cluster mean stays at +3.28 or below, the
> cycle-26 recipe was already at the family's basin convergence on
> this anchor and the M4 headline is locked."**

## Next-cycle plan-of-record (cycle 30)

1. **4-bucket-tight on c18-s0 (PRIMARY).** Re-run the cycle-25/26
   4-bucket ladder long-CEM recipe on c18-s0 piecewise warm-start
   at `init_std_frac_new=0.05` (was 0.15). Same budget (10g × 24p),
   same evaluator, same warm-start. Two RNG seeds in parallel, ~70
   min wall (assuming no sandbox stalls; 90–120 min with stalls).
   Decision rule:
   - **FRONTIER_MOVER**: cluster mean > +3.30 → cycle-28 tightening
     mechanism transfers across families; cycle 31 confirms with n=3
     and the M4 headline moves.
   - **MARGINAL_LIFT**: cluster mean in (+3.28, +3.30) → small
     improvement, n=3 stretch in cycle 31.
   - **CONVERGED_ALREADY**: cluster mean ≤ +3.28 → cycle-26 recipe
     was already at the family's basin convergence on c18-s0; M4
     headline locks at +3.277 ± 0.027.

2. **Stretch: 3rd c18-s0 5-bucket-tight 15g seed.** Single job,
   ~25 min wall. Tightens cycle-29 cluster from n=2 to n=3, gives
   a tighter ±σ for any future family-by-compute comparison.

3. **Stretch: 4th c18-s0 long-CEM 4-bucket-WIDE ladder seed (cycle-26
   recipe at std_new=0.15).** Single job, ~25 min wall. Tightens the
   cycle-26 cluster from n=3 to n=4 (σ ±0.027 → ±0.023). Useful as
   reference for the cycle-30 4-bucket-tight comparison.

4. **Bin/checks/.** Cycle 29 left active count at 12. No new check
   this cycle; observational entries in check 13 updated to include
   cycle-29 runs. **Retire candidate**: check 08 (jax_optional)
   currently passes with the cycle-29 /tmp-routing fix; if cycle 30
   confirms the fix is durable across the next sandbox restart, the
   check could be retired (its precondition no longer fails). For
   now: keep.

## M4 cumulative history (revised, cycle 29)

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
| 5-bucket-tight ladder (long-CEM) c18-s0 mean ±σ (n=2, c28) | 5-bucket | c18-s0 piecewise | 10g×24p, real_data | 0.05 | 2 | +3.253 ± 0.009 | +3.22 ± 0.44 |
| **5-bucket-tight ladder (LONG-CEM 15g) c18-s0 mean ±σ** (n=2, c29) | **5-bucket** | c18-s0 piecewise | **15g×24p**, real_data | **0.05** | 2 | **+3.255 ± 0.008** | +3.26 ± 0.50 |

**M4 frontier on real_data**: held at +3.277 ± 0.027 (4-bucket
ladder long-CEM, c18-s0 anchor, n=3 cross-seed, cycles 25+26).
Cycles 27, 28 and 29's 5-bucket attempts at the same anchor came
in below; cycle 29 confirms cycle-28's gap (Δ −0.022 to −0.024)
holds across 10g and 15g compute budgets. **The 4-bucket family
is the structural ceiling on c18-s0 at long-CEM.**

## Open questions (carried forward)

1. **(Cycle 29 answered.)** *Does the 5-bucket-tight family lift
   the M4 frontier at higher CEM compute (15g × 24p)?* **No.**
   Cluster mean +3.255 at 15g is bit-equal to +3.253 at 10g
   (Δ +0.0025, within sampling noise). The 5-bucket-tight
   optimization is compute-converged at 10g on c18-s0; gens 10–14
   add ≤+0.012 to elite_mean and rerank picks slightly *lower*
   val candidates than gen-9 picks. The 4-bucket family is the
   structural ceiling on c18-s0 at long-CEM.
2. **(NEW, cycle-30 plan-of-record.)** *Does tightening
   `init_std_frac_new` from 0.15 → 0.05 lift the 4-bucket cluster
   on c18-s0 (the way it did for the 5-bucket family in cycle
   28)?* The cycle-28 mechanism — that tighter exploration on
   newly-introduced dims accelerates CEM convergence and tightens
   cluster σ — has not been tested on the 4-bucket family. If it
   transfers, the 4-bucket cluster could exceed +3.28 cleanly
   and become the new M4 frontier.
3. **Does the 4-bucket bimodal invariant generalise to the
   5-bucket family at any compute/std combination?** Cycle 29
   added 2 more 5-bucket samples; aggregate 5-bucket tally
   (cycles 27+28+29, n=6 across 3 std/compute combos): by
   worst-non-anchor margin classifier, 1/6 find, 5/6 wash, 0/6
   collapse. The 5-bucket family does NOT exhibit the 4-bucket's
   clean bimodal regime structure — wash-band is allowed and
   common. By best-by-val (which drives test score), 5/6 are
   firmly in find regime — the wash-band entries are gen-2 outliers
   in the rerank pool, not the winners.
4. **Is the c18-s0 anchor's tight ±0.027 cycle-26 dispersion
   reproducible at n=4?** Stretch task, deferred again. Cycle-30
   plan includes it as stretch #3.
4. **Are c18-s0/c21-s1/c21-s2 anchors collapse-rate-different at
   short-CEM?** Cycle-26 stretch question, deferred again.
5. **Why is the val→test gap reliably −0.30 to −0.40 on long-CEM
   ladder warm-starts?** Pattern holds across cycles 21 (piecewise),
   23/24 (4-bucket), 27/28 (5-bucket). Suggests rerank-by-val
   has a systematic bias of this magnitude on the c18-s0/c21
   basin. Not actionable yet, but candidate for an M4 wrap-up
   diagnostic experiment.
