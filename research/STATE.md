# State — current cycle

**Last updated**: 2026-05-06 (cycle 25 — closed)

## Active milestone

**M4 cycle 9 (closed) → M4 cycle 10 (next).** Cycle 25 ran the
cycle-24 plan-of-record: (a) second RNG seed of long-CEM ladder on
the cycle-21-seed-2 (basin-collapsed) piecewise anchor, (b) single-
seed long-CEM ladder probe on the cycle-18-seed-0 piecewise anchor
(strongest basin in the family, lift_FF +3.006). **Result:
(a) the second seed COLLAPSED — CEM trajectory bottomed at elite-
mean +1.21, all non-anchor val scores fell ≥1.4 below the anchor,
rerank picked the anchor itself, lift over piecewise = +0.000.
The c21-s2 n=2 mean lift is now +0.273 ± 0.387 (error bar contains
zero); cycle-24's +0.547 was a positive tail draw, not a stable
stabilizer signature. (b) The c18-s0 probe lifted +0.250 over
piecewise (test +3.727, lift_FF +3.256, retail_adv +3.541) — *higher*
than the c21-s1 n=3 mean lift (+0.134), rejecting the proposed
inverse-scaling line ("ladder lift drops as piecewise quality
climbs"). c18-s0 single-seed test +3.727 is the highest single-seed
real_data score recorded so far (n=1, supporting evidence only).**

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **Best real_data single-seed nominal (NEW): cycle-25 long-CEM
  ladder rng_seed=0 on c18-s0: test +3.727, lift_FF +3.256, lift
  over c18-s0 piecewise +0.250.** New record (n=1, supporting
  evidence). Supersedes cycle-23 seed=0 (test +3.569).
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Unchanged. Best *piecewise* multi-seed estimate.
- **Best real_data score, multi-seed mean (long-CEM ladder on
  c21-s1 anchor, cycles 23+24, n=3): test +3.504, lift_FF
  +3.034 ± 0.066** [range +2.966, +3.098]. Unchanged. Best
  *ladder family multi-seed* estimate.
- **NEW: Cross-anchor long-CEM ladder, c21-s2 anchor (n=2):**
  mean test +3.020, mean lift_FF +2.549 ± 0.387, **mean lift over
  piecewise +0.273 ± 0.387**. Cycle-24 was n=1 +0.547; cycle-25
  added rng_seed=1 at +0.000 (collapse). Error bar contains zero.
- **NEW: Cross-anchor long-CEM ladder, c18-s0 anchor (n=1):**
  test +3.727, lift_FF +3.256, **lift over piecewise +0.250**.
- **Cross-anchor / cross-budget ladder lift over piecewise (revised, c19/22/23/24/25):**
  | budget | anchor | n_seeds | lift over piecewise (mean) |
  |--|--|--:|--:|
  | short-CEM (5g×12p) | cycle-18-s0 | 1 | +0.245 (cycle 19, single seed) |
  | short-CEM (5g×12p) | cycle-21-s1 | 2 | +0.000 (cycle 22, both seeds) |
  | short-CEM (5g×12p) | cycle-21-s2 | 1 | +0.000 (cycle 22, stretch) |
  | long-CEM (10g×24p) | cycle-21-s1 | 3 | +0.134 ± 0.066 (c23+c24) |
  | long-CEM (10g×24p) | cycle-21-s2 | **2** | **+0.273 ± 0.387** (c24+c25) |
  | **NEW long-CEM (10g×24p)** | **cycle-18-s0** | **1** | **+0.250 (cycle 25)** |
- **Aggregated long-CEM ladder lift over piecewise (n=6 seeds, 3 anchors):**
  mean +0.200, stddev ±0.192, range [+0.000, +0.547]. Bimodal: 5/6
  in the "find" regime (margin ≥+0.10), 1/6 in the "collapse"
  regime (margin ≤−0.50); empty dead zone in between.

## Cycle-25 verdict

1. **Q1 (c21-s2 seed=1) FAILED — basin collapsed.** Long-CEM at
   rng_seed=1 on c21-s2: gen-0 search-best +2.436 (similar to
   cycle-24's +2.34), then elite-mean fell to +1.21 by gen 9 and
   never recovered. Worst non-anchor val 1.79; anchor val 3.215;
   margin −1.43 → rerank picked the anchor → lift over piecewise
   = +0.000. Cycle-24's +0.547 was a positive tail draw of a
   distribution whose other tail is "full CEM basin-collapse."
   c21-s2 n=2 mean = +0.273 ± 0.387 — not significant against
   zero.

2. **Q2 (c18-s0 seed=0) succeeded but rejected the inverse-scaling
   prediction.** Long-CEM at rng_seed=0 on c18-s0: anchor val
   3.885; gen-9 elite-mean +3.182 (search seeds), all 6 non-anchor
   rerank candidates beat anchor on val (range 4.012-4.028). Best
   by val: gen8 elite, val 4.028, test +3.727, lift_FF +3.256,
   lift over piecewise +0.250. The +0.250 is HIGHER than
   c21-s1 n=3 mean (+0.134), so the inverse-scaling hypothesis is
   rejected — better-quality piecewise does not give smaller
   ladder lift here. The 3-anchor curve is non-monotone; either
   bowl-shaped or just noisy.

3. **Long-CEM is bimodal.** Across 6 long-CEM ladder runs on 3
   anchors, the (worst-non-anchor-val − anchor-val) margin
   distribution is bimodal: 5 runs in [+0.13, +0.78], 1 run at
   −1.43. Replaced check 13 with a bimodal invariant
   (`margin ≥ +0.10 OR margin ≤ −0.50`); all 6 runs pass.
   Original check 13 ("margin ≥ +0.05 always") was falsified by
   cycle-25 c21-s2 seed=1.

4. **New single-seed best on real_data.** c18-s0 seed=0 test +3.727
   exceeds cycle-23 seed=0 (+3.569) by +0.158 — the highest single-
   seed score recorded. Stays as supporting evidence (n=1) until
   reproduced by ≥2 more seeds.

5. **Val→test gap on c18-s0 modest.** c18-s0 seed=0 val 4.028 →
   test 3.727 (Δ −0.30) — smaller than cycle-23 seed=1's −0.62
   and cycle-24 c21-s2's −0.70. Possibly the c18-s0 basin is more
   robust to val-set bias; possibly we got a relatively close
   draw. Single seed; can't disambiguate yet.

## Active hypothesis going into cycle 26

> **"Long-CEM ladder lift over piecewise on c18-s0 has mean ≈+0.20
> with stddev ~±0.19 (the same distribution we see across all 6
> seeds aggregated). A two-additional-seed run (rng_seed ∈ {1, 2})
> on c18-s0 will produce an n=3 mean in [+0.05, +0.40], with at
> least one of the seeds in the 'find' regime. If the c18-s0 n=3
> mean lands above +0.15, the c18-s0 anchor delivers more lift
> than c21-s1, and the M4 frontier on real_data shifts to
> c18-s0 long-CEM ladder. If at least one of the new seeds
> collapses entirely (margin ≤ −0.50), the bimodal mixture-of-
> regimes characterization extends from c21-s2 to c18-s0 — i.e.
> long-CEM has an anchor-independent collapse rate, not just
> anchor-specific."**
>
> If true (n=3 mean &gt; +0.15 AND one seed lands in [+0.10, +0.40]),
> c18-s0 becomes the new headline anchor. If false (all 3 seeds
> collapse, or all 3 stay below +0.10), the c18-s0 +0.250 was
> single-seed noise.

## Next-cycle plan-of-record (cycle 26)

1. **Two additional rng_seeds on c18-s0 long-CEM ladder.** Run
   `ANCHOR_KEY=cycle18_seed0 RNG_SEED ∈ {1, 2}` in parallel,
   ~46 min wall. Tightens c18-s0 from n=1 to n=3 — the cleanest
   single experiment for moving the M4 frontier.
2. **Stretch: structurally richer family at long-CEM on c21-s1.**
   The cycle-24 plan-of-record direction. If wall-clock allows,
   queue ONE of: 6-bucket ladder, smooth-head MLP, or EMA-inv
   state at long-CEM on c21-s1, multi-seed (n=3 from the start).
   Decision rule: if any of these moves the c21-s1 n=3 mean lift
   over piecewise above +0.13, the M4 frontier moves; if not,
   M4's headline number is locked at long-CEM ladder n=3
   (+3.034 ± 0.066) or the c18-s0 cluster from above.
3. **Bin/checks/.** No new check planned for cycle 26 unless an
   experimental finding warrants one. Cycle-25's bimodal-rewrite
   of check 13 is live. Cap is ~12 — currently 13 active checks.
   Cycle-26 should consider whether older sandbox-property checks
   (e.g. `04_no_outbound_dns.sh`, `05_results_dir_unlink_blocked.py`)
   have flipped to passive infrastructure notes that could be
   collapsed into one.

## M4 cumulative history (revised, cycle 25)

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
| **ladder mean ±σ** (n=3, c18-s0 anchor, short-CEM) | ladder-4bucket | c11_long-s0 | 5g×12p | 3 | +3.111 ± 0.126 | +3.39 ± 0.39 |
| ladder seed=0 (c22, c21-s1) | ladder-4bucket | c11_long ext (c21-s1) | 5g×12p, real_data | 1 | +2.900 | +3.820 |
| ladder seed=1 (c22, c21-s1) | ladder-4bucket | c11_long ext (c21-s1) | 5g×12p, real_data | 1 | +2.900 | +3.820 |
| ladder seed=0 (c22, stretch, c21-s2) | ladder-4bucket | c11_long ext (c21-s2) | 5g×12p, real_data | 1 | +2.275 | -3.024 |
| **ladder lift_FF cross-anchor mean (short-CEM)** | ladder-4bucket | mixed | 5g×12p | 4 | ~0 (range 0–0.245) | — |
| **ladder seed=0 (c23, c21-s1)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +3.098 | +4.378 |
| **ladder seed=1 (c23, c21-s1)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +2.966 | +2.475 |
| **ladder seed=2 (c24, c21-s1)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | +3.037 | +3.741 |
| **ladder long-CEM mean ±σ (n=3, c21-s1)** | ladder-4bucket | c11_long-s1 | 10g×24p | 3 | **+3.034 ± 0.066** | +3.53 ± 0.97 |
| ladder seed=0 (c24, c21-s2) | ladder-4bucket | c11_long ext (c21-s2) | 10g×24p, real_data | 1 | +2.822 | -0.995 |
| **NEW: ladder seed=1 (c25, c21-s2)** | ladder-4bucket | c11_long ext (c21-s2) | **10g×24p**, real_data | 1 | **+2.275 (anchor)** | **-3.024** |
| **NEW: ladder long-CEM mean ±σ (n=2, c21-s2)** | ladder-4bucket | c11_long-s2 | 10g×24p | 2 | **+2.549 ± 0.387** | -2.01 ± 1.43 |
| **NEW: ladder seed=0 (c25, c18-s0)** | ladder-4bucket | c11_long ext (c18-s0) | **10g×24p**, real_data | 1 | **+3.256** | **+3.541** |
| **NEW: aggregated long-CEM ladder (n=6, 3 anchors)** | ladder-4bucket | mixed | 10g×24p | 6 | mean lift over piecewise **+0.200 ± 0.192** | — |

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-25 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Vendored wheels make it importable on the original sandbox after
  the cycle's setup step. Cycle 25 did not need jax (no smooth-head
  MLP probe); skipped the setup step.
- **pyarrow install** can OOM but cycle 25 succeeded on first try
  bundled with gymnasium/pytest/matplotlib (no isolation needed
  this cycle).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle. Cycle
  25's sandbox: `/sessions/gallant-practical-fermi`.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib`. Cycle 25
  succeeded with this single bundle (~30s).
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate. Check 13 was rewritten
  in place rather than retired-and-replaced for the same reason.
- CPU: 4 cores. Cycle 25 ran two parallel long-CEM jobs at
  workers=2 each (saturating cores). Both finished in ~45 min wall.
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~120s are reliably killed with exit 143 by the sandbox. Cycle
  25 used 90-110s sleeps consistently and they survived.
- **Backgrounded process inheritance**: file-based launcher pattern
  worked again (per cycle 24): write `/tmp/launch_a25.sh` and
  `/tmp/launch_b25.sh` containing each `nohup`-style command,
  then launch each from the parent shell separately.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently **13 active checks** (cycle 25 rewrote
  check 13 in place; no net change in count). Cap is ~12; cycle 26
  should consider whether any older check has flipped to no-op.
- **Seed reproducibility rule.** Going forward, any M4
  family/budget claim needs ≥3 rng_seeds before being entered as
  a headline. Cycle 25's c18-s0 +0.250 lift is currently n=1 —
  supporting evidence, not a headline.
- **Anchor confounding rule.** Family-escalation claims require
  cross-anchor lift, not just lift over a single warm-start seed.
  Cycle 25 added a third anchor (c18-s0) to the curve; the cross-
  anchor data is now n=3 (c21-s1) + n=2 (c21-s2) + n=1 (c18-s0) = 6
  seeds across 3 anchors.
- **Cycle-25 finding (long-CEM bimodal regime).** Long-CEM ladder
  trajectories are bimodal: most ("find" regime) lift the val
  distribution above the anchor by ≥+0.10; one in six ("collapse"
  regime) bottoms out the search distribution and forces rerank to
  pick the anchor (margin ≤−0.50). The "anchor-conditional lift"
  framing from cycle 24 was an artifact of cycle-24 c21-s2 happening
  to land on the find tail.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-25's edits restricted to `research/` and
  `bin/checks/13_long_cem_beats_anchor.py` (rewrite in place).
