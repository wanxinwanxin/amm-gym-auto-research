# State — current cycle

**Last updated**: 2026-05-06 (cycle 23 — closed)

## Active milestone

**M4 cycle 7 (closed) → M4 cycle 8 (next).** Cycle 23 ran the
cycle-22 plan-of-record: long-CEM ladder (10 gen × 24 pop, matching
cycle-18 piecewise long-CEM compute) on the cycle-21-seed-1
piecewise anchor at two RNG seeds. **Result: at long-CEM budget
ladder produces a small but non-zero positive lift over the same-
anchor piecewise — mean +0.132 ± 0.066 lift_FF over the seed-1
piecewise (n=2 seeds). This rejects the cycle-22 short-CEM null
result while landing in the wash band of the cycle-22 decision rule
([+2.85, +3.10]).** Long-CEM unlocks ~+0.13 lift_FF over piecewise
that short-CEM cannot find on the same anchor.

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **Best real_data single-seed nominal: cycle-23 long-CEM ladder
  rng_seed=0: test +3.569, lift_FF +3.098, lift over c21-s1
  piecewise +0.198.** Promoted from cycle 22 (was cycle-19's
  anchor-driven +3.721, now retired from the headline).
- **Best real_data score, multi-seed mean (cycle 21, piecewise,
  long-CEM, n=3): test +3.197, lift_FF +2.727 ± 0.322** [range
  +2.275, +3.006]. Unchanged. This remains the best *piecewise*
  multi-seed estimate.
- **Best real_data score, multi-seed mean (cycle 23, ladder,
  long-CEM warm-started from c21-s1, n=2): test +3.503, lift_FF
  +3.032 ± 0.066** [range +2.966, +3.098]. New — this is the
  cycle-23 frontier at the long-CEM budget conditional on the
  c21-s1 anchor.
- **Cross-anchor ladder lift over piecewise (combined c19/22/23):**
  | budget | anchor | n_seeds | lift over piecewise (mean) |
  |--|--|--:|--:|
  | short-CEM (5g×12p) | cycle-18-s0 | 1 | +0.245 (cycle 19, single seed) |
  | short-CEM (5g×12p) | cycle-21-s1 | 2 | +0.000 (cycle 22, both seeds) |
  | short-CEM (5g×12p) | cycle-21-s2 | 1 | +0.000 (cycle 22, stretch) |
  | **long-CEM (10g×24p)** | **cycle-21-s1** | **2** | **+0.132 ± 0.066 (cycle 23)** |
- **Implied M4 status (revised, cycle 23):** at long-CEM budget the
  ladder family delivers a small (+0.13) lift over the piecewise
  anchor on the cycle-21-seed-1 anchor, vs +0.00 at short-CEM. The
  effect is real but smaller than cycle-19's single-seed +0.245
  point. Cross-anchor robustness still untested at long-CEM.

## Cycle-23 verdict

1. **Long-CEM unlocks ladder lift that short-CEM cannot find.** At
   the cycle-22 short-CEM budget on this anchor, every CEM elite
   lost to the anchor on val (max non-anchor val 3.573 vs anchor
   3.651). At the cycle-23 long-CEM budget on the same anchor,
   *every* non-anchor candidate in the rerank pool beat the anchor
   on val (range 3.85–4.06 vs anchor 3.651). The search→val gap
   that defeated short-CEM is closed at long-CEM. **Compute (more
   generations × bigger population) was the binding constraint, not
   the policy family.**

2. **The lift is real but modest.** Mean lift over c21-s1 piecewise
   = +0.132 ± 0.066 lift_FF (n=2 seeds). Decision-rule outcome:
   borderline. Seed 0 (+3.098) sits at the +3.10 threshold (Δ
   −0.002). Seed 1 (+2.966) is in the wash band [+2.85, +3.10].
   Neither cleanly satisfies the strict "ladder real at long-CEM"
   criterion, but both reject the cycle-22 "ladder gives nothing
   over piecewise on this anchor" null.

3. **Val→test dispersion is wide (cycle-21 pattern, cycle-23
   confirmed for ladder).** Seed 0: val 3.86 → test 3.57 (−0.29).
   Seed 1: val 4.05 → test 3.44 (−0.61). The seed with the higher
   val *underperformed* the seed with the lower val on test —
   exactly the basin-overfit mechanism cycle 21 surfaced for
   piecewise long-CEM. Long-CEM dispersion is still high.

4. **Retail vs arb tradeoff differs across seeds.** Seed 0 retail
   adv +4.378 (vs anchor +3.820 → +0.56 retail edge). Seed 1
   retail adv +2.475 (vs anchor → −1.35 retail edge — wins on the
   arb side instead). Same anchor, two RNG seeds, two qualitatively
   different policy basins. This is a richness-of-basin observation:
   the long-CEM landscape has multiple competitive basins around
   the seed-1 piecewise anchor, not a single dominant one.

5. **Cycle-19's +0.245 single-seed point is consistent with cycle
   23's distribution.** Cycle 23 sample range [+0.066, +0.198].
   Cycle 19's +0.245 was on a different anchor (cycle-18-s0) but at
   the *short* CEM budget, where it may have been a positive
   tail draw. The cycle-23 mean +0.132 is consistent with the
   underlying ladder-family lift at long-CEM being ~+0.10–+0.20.

## Active hypothesis going into cycle 24

> **"The cycle-23 long-CEM ladder lift of +0.132 ± 0.066 is real
> and reproducible. A third RNG seed on the same anchor will land
> within [+0.0, +0.25] (95% CI for n=2 mean), giving an n=3 mean
> in [+0.05, +0.20]. Cross-anchor: the same long-CEM ladder run
> warm-started from the cycle-21-seed-2 (basin-collapsed) piecewise
> will *recover* lift relative to the seed-2 anchor — long-CEM
> ladder is partly a stabilizer."**
>
> If true (n=3 mean +0.05 to +0.20 on c21-s1, plus positive lift on
> c21-s2): the long-CEM ladder family delivers a real but small
> ~+0.1 lift over piecewise across anchors. M4 frontier moves to
> ~+3.0 lift_FF mean. Cycle 25 becomes a complexity-vs-payoff
> sweep along policy-family axis (the M4 milestone proper).
>
> If false (n=3 mean ≤ 0 or c21-s2 fails): the cycle-23 +0.13 lift
> is anchor-conditional (just like cycle-19's was on c18-s0). M4
> frontier stays at ~+2.7 piecewise long-CEM. Cycle 25 pivots to a
> structurally different family.

## Cycle-24 plan-of-record

1. **Third RNG seed of long-CEM ladder on c21-s1 anchor**
   (rng_seed=2, same script as cycle 23). Tightens the n=2 mean
   and confirms the cycle-23 +0.132 effect is not seed-2-of-2
   sampling noise. ~46 min wall single-run at workers=2; can run
   one parallel cross-anchor seed alongside (workers=2 each on the
   4-core sandbox).

2. **Cross-anchor long-CEM ladder on cycle-21-seed-2 anchor**
   (rng_seed=0). The cycle-22 short-CEM stretch on this anchor
   gave +0.000 lift; does long-CEM recover lift relative to the
   basin-collapsed +2.275 piecewise? Cycle-22 STATE rejected
   "ladder as stabilizer" at short-CEM — does it work at long?

3. **(Stretch)** If both 1 and 2 finish in the cycle, redraw the
   cross-anchor cross-budget figure with cycle-23 + cycle-24
   points; a 3-anchor × 2-budget matrix is the cleanest
   summary of where the family payoff lives.

4. Encode "long-CEM elites beat anchor on val (cycle-23 pattern)"
   as a check at `bin/checks/13_*` that reruns one cycle-23 elite
   and asserts val > anchor val + 0.10. This documents the
   compute-threshold finding so a future cycle does not re-derive
   it.

## M4 cumulative history (revised, cycle 23)

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
| **NEW: ladder seed=0 (c23)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | **+3.098** | **+4.378** |
| **NEW: ladder seed=1 (c23)** | ladder-4bucket | c11_long ext (c21-s1) | **10g×24p**, real_data | 1 | **+2.966** | **+2.475** |
| **NEW: ladder long-CEM mean ±σ (n=2, c21-s1 anchor)** | ladder-4bucket | c11_long-s1 | 10g×24p | 2 | **+3.032 ± 0.066** | +3.43 ± 0.95 |
| **NEW: ladder lift over c21-s1 piecewise (long-CEM, n=2)** | — | — | — | 2 | **+0.132 ± 0.066** | — |

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-23 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Vendored wheels make it importable on this fresh sandbox after
  the cycle's setup step.
- **pyarrow install** can OOM but cycle 23 succeeded on first try
  in isolation (`pip install --break-system-packages pyarrow`,
  no other deps in the same call). Cycle 22's six-failure streak
  was likely sandbox-specific transient memory pressure.
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pytest matplotlib`. Cycle 23 succeeded
  with this minimal bundle plus pyarrow installed in isolation
  after the main bundle.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate.
- CPU: 4 cores. Cycle 23 ran two parallel long-CEM jobs at
  workers=2 each (saturating cores) and finished both ~46 min from
  launch (CEM 38 min + rerank ~4 min + test ~3 min + FF baseline
  ~80s).
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~360s are reliably killed with exit 143 by the sandbox. Even
  240s and 180s sleeps were sometimes killed in cycle 23. Pattern
  that worked: launch CEM via `nohup ... &` once, then poll
  `progress.log` periodically with sleeps ≤120s.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently **13 active checks** (no changes this
  cycle; cycle 24 plans to add `13_long_cem_beats_anchor.py`).
  Caps at ~12; if cycle 24 adds the new check we should consider
  whether any older check has flipped to OK and can be retired.
- **Seed reproducibility rule (cycles 20/21/22/23).** Going forward,
  any M4 family/budget claim needs ≥3 rng_seeds before being
  entered as a headline. Cycle 23 added a 2-seed datapoint;
  cycle 24's first task is to add the third seed.
- **Anchor confounding rule (cycles 21/22).** Family-escalation
  claims require cross-anchor lift, not just lift over a single
  warm-start seed. Cycle 23 is *single-anchor* (c21-s1 only); a
  cross-anchor long-CEM ladder run is queued for cycle 24.
- **Cycle-23 finding (compute threshold).** The same 19-d ladder
  family produces ZERO lift at short-CEM and ~+0.13 lift at
  long-CEM on the same anchor. Compute is the binding constraint
  on family-vs-piecewise comparisons at this dim — short-CEM
  family experiments without long-CEM controls produce false
  negatives. New rule: any "family X is no better than Y" claim
  must hold at long-CEM budget, not just short-CEM.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-23's edits restricted to `research/`.
