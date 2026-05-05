# State — current cycle

**Last updated**: 2026-05-06 (cycle 26 — closed)

## Active milestone

**M4 cycle 10 (closed) → M4 cycle 11 (next).** Cycle 26 ran the
cycle-25 plan-of-record: two additional rng_seeds (1, 2) of long-CEM
ladder on the cycle-18-seed-0 ("c18-s0") piecewise anchor, tightening
that anchor's ladder cluster from n=1 to n=3. **Result: both new
seeds in the find regime — no collapses. Tests +3.738 (rng=1, lift
+0.262) and +3.777 (rng=2, lift +0.301; new headline single-seed
real_data score). c18-s0 n=3 mean is now lift_FF +3.277 ± 0.027,
test +3.747, lift over piecewise +0.271 ± 0.027 — both higher and
2.5× tighter than the prior cross-seed best (c21-s1 n=3 cycles
23+24, lift_FF +3.034 ± 0.066). Δ between cross-seed means at the
two anchors is +0.243, far larger than either anchor's seed-
dispersion stddev — c18-s0 is the new M4 frontier on real_data, not
c21-s1.**

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **NEW: Best real_data score, multi-seed mean (long-CEM ladder
  on c18-s0 anchor, cycles 25+26, n=3): test +3.747, lift_FF
  +3.277 ± 0.027** [range +3.256, +3.307]. Lift over same-anchor
  piecewise +0.271 ± 0.027. **The new M4 cross-seed frontier on
  real_data.** Supersedes c21-s1 cluster.
- **Best real_data single-seed nominal: cycle-26 c18-s0 rng=2:
  test +3.777, lift_FF +3.307, lift over piecewise +0.301.**
  New record (n=1, supporting evidence). Supersedes cycle-25
  c18-s0 rng=0 (test +3.727).
- **Best real_data score, multi-seed mean (long-CEM ladder
  on c21-s1 anchor, cycles 23+24, n=3): test +3.504, lift_FF
  +3.034 ± 0.066** [range +2.966, +3.098]. Held for context as
  the prior frontier.
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Held for context as the piecewise-only baseline.
- **Cross-anchor long-CEM ladder, c21-s2 anchor (n=2):**
  mean test +3.020, mean lift_FF +2.549 ± 0.387, mean lift over
  piecewise +0.273 ± 0.387. Error bar contains zero. Unchanged.
- **Cross-anchor / cross-budget ladder lift over piecewise (revised, c19/22/23/24/25/26):**
  | budget | anchor | n_seeds | lift over piecewise (mean ± σ) |
  |--|--|--:|--:|
  | short-CEM (5g×12p) | cycle-18-s0 | 1 | +0.245 (cycle 19, single seed) |
  | short-CEM (5g×12p) | cycle-21-s1 | 2 | +0.000 (cycle 22, both seeds) |
  | short-CEM (5g×12p) | cycle-21-s2 | 1 | +0.000 (cycle 22, stretch) |
  | long-CEM (10g×24p) | cycle-21-s1 | 3 | +0.134 ± 0.066 (c23+c24) |
  | long-CEM (10g×24p) | cycle-21-s2 | 2 | +0.273 ± 0.387 (c24+c25) |
  | **NEW long-CEM (10g×24p)** | **cycle-18-s0** | **3** | **+0.271 ± 0.027 (c25+c26)** |
- **Aggregated long-CEM ladder lift over piecewise (n=8 seeds, 3 anchors):**
  mean +0.220, sample stddev ±0.167, range [+0.000, +0.547]. 7/8 in
  the find regime (margin ≥+0.10), 1/8 in the collapse regime
  (margin ≤−0.50). Empirical collapse rate stays ~12.5%.

## Cycle-26 verdict

1. **The cycle-25 +0.250 was real, not noise.** c18-s0 n=3 mean
   lift over piecewise = **+0.271 ± 0.027**, with both new seeds
   landing in [+0.262, +0.301]. The hypothesis "c18-s0 n=3 mean
   > +0.15 with at least one new seed in [+0.10, +0.40]" is
   confirmed at +0.271 with both new seeds in [+0.26, +0.31].
   The c18-s0 anchor delivers consistently more lift than c21-s1.

2. **The c18-s0 cluster is anomalously tight.** n=3 stddev ±0.027
   vs c21-s1 n=3 stddev ±0.066 — 2.4× tighter at the same family
   and budget. This is the most novel cycle-26 finding. Likely
   anchor-specific basin-shape property; cycle-27 could test by
   sweeping additional comparable-quality anchors or by running a
   larger n on c18-s0.

3. **The 3-anchor curve is non-monotone.** c21-s2 +0.27 (n=2,
   high σ), c21-s1 +0.13 (n=3, mid σ), c18-s0 +0.27 (n=3, tight σ)
   across piecewise lift_FF 2.275 / 2.900 / 3.006. Both the
   cycle-24 "stabilizer" framing and the cycle-25 inverse-scaling
   line are now decisively rejected.

4. **The bimodal find/collapse invariant scales.** All 8 long-CEM
   ladder runs across 3 anchors fall cleanly into one of the two
   regimes (margin ≥ +0.10 or ≤ −0.50). 7 find / 1 collapse.
   c18-s0 has 0/3 collapses, c21-s1 has 0/3 collapses, c21-s2 has
   1/2. Anchor-specific collapse susceptibility, not universal.

5. **Val→test gap is anchor-dependent.** c18-s0 ladder val→test
   deltas across 3 seeds: −0.30 / −0.18 / −0.24. Mean −0.24,
   stddev ±0.06. c21-s1 ladder val→test deltas: −0.30 to −0.62.
   The c18-s0 basin appears to overfit val less, consistent with
   the tighter cross-seed dispersion. Probably the same mechanism.

## Active hypothesis going into cycle 27

> **"A structurally richer policy family at long-CEM on c18-s0
> can move the M4 frontier above +3.277 lift_FF cross-seed mean.
> Candidates: 6-bucket ladder (one extra small-bucket), smooth-head
> MLP (a 1-2 layer MLP head replacing the size-bucket logic), and
> EMA-inv state (toxicity decay augmented with an inventory-EMA).
> The c18-s0 basin's tight ±0.027 dispersion gives us cheap
> statistical power: any family that produces n=3 mean lift_FF
> above +3.31 at the same long-CEM budget on c18-s0 would be a
> real frontier-mover, distinguishable from cycle-26 noise. If
> none of these crosses +3.31, the 19-d ladder is the M4 ceiling
> on the c18-s0 basin and cycle 27 should pivot to a 4th c18-s0
> seed (tighten n=4) or to anchor-conditional collapse-rate
> measurement at cheap budget."**

## Next-cycle plan-of-record (cycle 27)

1. **Structurally richer family at long-CEM on c18-s0,
   multi-seed.** First candidate: 6-bucket ladder (split the
   tiny bucket from cycle-26's 4-bucket into tiny+ultra-tiny).
   Same warm-start construction as the 4-bucket ladder. Multi-seed
   (n=3 from the start, rng_seed ∈ {0, 1, 2}). Wall-clock budget:
   ~50-60 min for n=3 parallel at workers=1 each, or 90 min sequential.
   Decision rule: if n=3 mean lift_FF on c18-s0 exceeds +3.31
   (anchor cluster mean +0.027 above the ±σ of the cycle-26 anchor),
   the M4 frontier moves; if not, lock the M4 headline at long-CEM
   ladder n=3 +3.277 ± 0.027 and pivot to (2)/(3).
2. **Stretch: 4th rng_seed on c18-s0 long-CEM 19-d ladder.**
   Cheap (one job, ~25 min wall) and tightens the c18-s0 cluster
   from n=3 to n=4. Useful as a control for the family-escalation
   experiment in (1) and as additional evidence on the anchor-
   specific tight-distribution finding from cycle 26.
3. **Stretch: anchor-conditional collapse-rate measurement.**
   Run 3 short-CEM (cheap-budget) seeds on each of c18-s0, c21-s1,
   c21-s2, count find vs collapse per anchor. Tests the cycle-26
   "anchor-specific collapse susceptibility" hypothesis directly.
   Lower priority than (1)/(2).
4. **Bin/checks/.** No new check planned for cycle 27. Currently
   12 active checks (cycle 26 retired 04 + 05 by chmod -x and
   added 00_sandbox_quirks.py as their consolidation, net −1).
   Within the ~12 cap. Cycle 26 extended check 13 to cover cycle-26
   c18-s0 seed=1 and seed=2; both pass the bimodal invariant.

## M4 cumulative history (revised, cycle 26)

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
| **ladder seed=0** (c19) | ladder-4bucket | c11_long ext (c18-s0) | 5g×12p, real_data | 1 | +3.251 | +3.113 |
| **ladder seed=1** (c20) | ladder-4bucket | c11_long ext (c18-s0) | 5g×12p, real_data | 1 | +3.076 | +3.834 |
| **ladder seed=2** (c20) | ladder-4bucket | c11_long ext (c18-s0) | 5g×12p, real_data | 1 | +3.006 | +3.215 |
| **ladder mean ±σ** (n=3, c18-s0 anchor, short-CEM) | ladder-4bucket | c11_long-s0 | 5g×12p | 3 | +3.111 ± 0.126 | +3.39 ± 0.39 |
| ladder seed=0/1 (c22, c21-s1) | ladder-4bucket | c11_long ext (c21-s1) | 5g×12p, real_data | 2 | +2.900 / +2.900 | +3.82 / +3.82 |
| ladder seed=0 (c22, stretch, c21-s2) | ladder-4bucket | c11_long ext (c21-s2) | 5g×12p, real_data | 1 | +2.275 | -3.024 |
| **ladder seed=0 (c23, c21-s1)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +3.098 | +4.378 |
| **ladder seed=1 (c23, c21-s1)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +2.966 | +2.475 |
| **ladder seed=2 (c24, c21-s1)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +3.037 | +3.741 |
| **ladder long-CEM mean ±σ (n=3, c21-s1)** | ladder-4bucket | c11_long-s1 | 10g×24p | 3 | +3.034 ± 0.066 | +3.53 ± 0.97 |
| ladder seed=0 (c24, c21-s2) | ladder-4bucket | c11_long ext (c21-s2) | 10g×24p, real_data | 1 | +2.822 | -0.995 |
| ladder seed=1 (c25, c21-s2) | ladder-4bucket | c11_long ext (c21-s2) | 10g×24p, real_data | 1 | +2.275 (anchor) | -3.024 |
| **ladder long-CEM mean ±σ (n=2, c21-s2)** | ladder-4bucket | c11_long-s2 | 10g×24p | 2 | +2.549 ± 0.387 | -2.01 ± 1.43 |
| ladder seed=0 (c25, c18-s0) | ladder-4bucket | c11_long ext (c18-s0) | 10g×24p, real_data | 1 | +3.256 | +3.541 |
| **NEW: ladder seed=1 (c26, c18-s0)** | ladder-4bucket | c11_long ext (c18-s0) | **10g×24p**, real_data | 1 | **+3.268** | **+3.875** |
| **NEW: ladder seed=2 (c26, c18-s0)** | ladder-4bucket | c11_long ext (c18-s0) | **10g×24p**, real_data | 1 | **+3.307** | **+2.866** |
| **NEW: ladder long-CEM mean ±σ (n=3, c18-s0)** | ladder-4bucket | c11_long-s0 | **10g×24p** | 3 | **+3.277 ± 0.027** | **+3.43 ± 0.53** |
| **NEW: aggregated long-CEM ladder (n=8, 3 anchors)** | ladder-4bucket | mixed | 10g×24p | 8 | mean lift over piecewise **+0.220 ± 0.167** | — |

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-26 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Vendored wheels make it importable on the original sandbox after
  the cycle's setup step. Cycle 26 did not need jax (no smooth-head
  MLP probe); skipped the setup step. Cycle 27's family-escalation
  experiment may need jax for smooth-head MLP — re-test on the
  cycle-27 sandbox.
- **pyarrow install** can OOM but cycle 26 succeeded on first try
  bundled with gymnasium/pytest/matplotlib (no isolation needed
  this cycle).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle. Cycle
  26's sandbox: `/sessions/gracious-charming-ritchie`.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib`. Cycle 26
  succeeded with this single bundle (~30s).
- Cannot `unlink` files in the sandbox — affects results dirs and
  `git rm` (cycle 26 verified). Drivers must open log files in `"w"`
  mode to truncate. To "retire" a check, `chmod -x` it (cycle 26
  pattern; the run_checks.sh driver SKIPs non-executable scripts).
- CPU: 4 cores. Cycle 26 ran two parallel long-CEM jobs at
  workers=2 each (saturating cores). Both finished in ~45 min wall.
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~120s are reliably killed with exit 143 by the sandbox. Cycle
  26 used 90-110s sleeps consistently and they survived.
- **Backgrounded process inheritance**: file-based launcher pattern
  worked again (per cycle 24/25): write `/tmp/launch_a26.sh` and
  `/tmp/launch_b26.sh` containing each `nohup`-style command,
  then launch each from the parent shell separately and `disown`.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. **Currently 12 active checks** (down from 13 — cycle
  26 retired 04 + 05 by chmod -x and added 00_sandbox_quirks.py
  as their consolidation, net −1). Within the ~12 cap. Cycle 26
  extended check 13 to cover cycle-26 c18-s0 seed=1 and seed=2.
- **Seed reproducibility rule.** Going forward, any M4
  family/budget claim needs ≥3 rng_seeds before being entered as
  a headline. Cycle 26's c18-s0 cluster is now n=3, headline-ready.
- **Anchor confounding rule.** Family-escalation claims require
  cross-anchor lift, not just lift over a single warm-start seed.
  Cycle 26 added a third anchor (c18-s0) at n=3; the cross-anchor
  data is now n=3 (c21-s1) + n=2 (c21-s2) + n=3 (c18-s0) = 8
  seeds across 3 anchors.
- **Cycle-26 finding (anchor-specific dispersion).** c18-s0's
  long-CEM ladder cross-seed stddev is ±0.027, while c21-s1's is
  ±0.066 — a 2.4× difference at the same family and budget. The
  cross-seed variance is anchor-specific, separate from the
  cross-anchor mean. Likely anchor-basin-shape-driven; tested
  formally only at n=3, but consistent across the 6 c18-s0 ladder
  scores we have (3 long-CEM + 3 short-CEM cycle-19/20).
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-26's edits restricted to `research/`,
  `bin/checks/13_long_cem_beats_anchor.py` (extension to 8 runs),
  `bin/checks/04*.sh` and `bin/checks/05*.py` (chmod -x), and
  new `bin/checks/00_sandbox_quirks.py`.
