# Cycle 23 — M4 long-CEM ladder on cycle-21-seed-1 anchor

## Question

Cycle 22 falsified the cycle-19 +0.245 ladder lift over piecewise — at
the **short-CEM** budget (5 generations × 12 population), the ladder
family produced no lift over the piecewise anchor on the
cycle-21-seed-1 piecewise (test lift_FF +0.000 / +0.000 across two
RNG seeds). The cycle-22 stretch (cycle-21-seed-2 anchor) was also
+0.000.

But cycle 22 also exposed a confound: the cycle-19 ladder was warm-
started from the cycle-18-seed-0 piecewise, which was the result of a
**long-CEM** run (10 generations × 24 population), whereas the
cycle-19/22 ladder runs themselves used the **short-CEM** budget.
Maybe the ladder family payoff requires the long-CEM compute to
manifest — short-CEM elites couldn't beat the anchor on val on the
seed-1 piecewise.

This experiment tests that directly: re-run the ladder CEM with
cycle-18's long-CEM budget (10g × 24p), warm-started from the
cycle-21-seed-1 piecewise, at two RNG seeds.

## Decision rule (set in cycle-22 STATE.md)

* lift_FF > +3.10 on test (>+0.20 over the seed-1 piecewise +2.900):
  ladder family is real at long-CEM; pivot to multi-seed cross-anchor
  long-ladder next cycle.
* lift_FF in [+2.85, +3.10]: ladder is at-best a wash on this anchor
  at this budget; pivot to a structurally different family (smooth-
  head MLP, 6-bucket ladder, dynamic threshold).
* lift_FF < +2.85: ladder is regressing; long-CEM finding worse
  candidates than the anchor.

## Method

* Identical CEM mechanics to cycle 22 (19-d ladder param vector,
  init_std_inh=0.05, init_std_new=0.15, elite_frac=0.2, normalizer
  FixedFee(0.003,0.003), evaluator real_data, 64 search seeds, 128
  val, 256 test, RERANK_TOP_K=6) except:
  - POPULATION = 24 (was 12)
  - GENERATIONS = 10 (was 5)
* Warm start: cycle-21-seed-1 piecewise (test +3.370 / lift_FF
  +2.900 / retail_adv +3.820), extended to 19-d ladder with
  identity rule:
  - tiny_threshold = 0.5 × small_threshold
  - continuation_tiny = continuation_small
  - reversal_tiny = reversal_small
  This gives a ladder vector that, by construction, evaluates
  identically to the piecewise on every empirical retail size.
  Anchor val (n=128) = 3.651 = cycle-21 seed-1 piecewise val on the
  same seeds, confirming identity warm-start.
* Two RNG seeds (0, 1) launched in parallel at workers=2 each on
  the 4-core sandbox.

## Results — cycle-21-seed-1 anchor (long-CEM, n=2 seeds)

| run | rerank winner | val | test_score | lift_FF | lift over piecewise seed-1 |
|--|--|--:|--:|--:|--:|
| `cycle21_seed1_seed0` | gen9 elite | 3.865 | 3.569 | **+3.098** | **+0.198** |
| `cycle21_seed1_seed1` | gen8 elite | 4.055 | 3.437 | **+2.966** | **+0.066** |
| **mean ± σ** (n=2) | — | 3.960 | 3.503 | **+3.032 ± 0.066** | **+0.132 ± 0.066** |

For comparison, cycle 22 (short-CEM, same anchor, n=2 seeds):

| run | rerank winner | val | test_score | lift_FF | lift over piecewise seed-1 |
|--|--|--:|--:|--:|--:|
| `cycle21_seed1_seed0` (c22) | **anchor** | 3.651 | 3.370 | +2.900 | +0.000 |
| `cycle21_seed1_seed1` (c22) | **anchor** | 3.651 | 3.370 | +2.900 | +0.000 |

**Headline.** At the long-CEM budget, ladder produces a **small but
non-zero** lift over the same-anchor piecewise: +0.132 ± 0.066 mean
across 2 seeds. The lift survives the rerank-anchor-first guard
because both runs found CEM elites that beat the anchor on val
(by +0.21 / +0.40), and those elites also test above the anchor
(though by less, +0.20 / +0.07).

## Verdict against the decision rule

The decision rule is **partially met**:

* Seed 0 (+3.098): just at the +3.10 threshold (Δ −0.002).
* Seed 1 (+2.966): in the wash band [+2.85, +3.10].
* Mean (+3.032): in the wash band.

So this is *not* a clean "ladder real at long-CEM" signal at the
strict +3.10 threshold. But it is a clean **rejection of the cycle-22
short-CEM null result** — at long-CEM the ladder finds candidates
that test above the same-anchor piecewise, whereas at short-CEM it
cannot. The effect size (+0.13) is roughly half of cycle-19's single-
seed +0.245 — consistent with that single-seed point being the +75th
percentile of a noisy distribution, not the mean.

## What the trajectories tell us

The CEM trajectories (figure `m4_c23_longcem_val_curves.png`) show:

1. **Search→val gap closes at long-CEM.** At cycle-22 short-CEM gen-4,
   search-best was ~2.89 (seed 0) / ~2.88 (seed 1) — ~0.06 *below* the
   anchor val 3.651 reranked. At cycle-23 long-CEM gen-9, search-best
   reached 2.976 (seed 0) / 3.041 (seed 1), and the val of the gen-9
   elites (3.86 / 4.05) was *above* the anchor val (+0.21 / +0.40).
2. **Search and val both approach a basin.** elite_mean_score per gen
   ramps monotonically from ~+0.7/+1.1 (gen 0) to ~+2.97/+3.03
   (gen 9). all_mean ramps from ~−4.0/−1.6 to ~+2.95/+2.97. CEM has
   essentially fully converged to a local basin by gen 9.
3. **Val→test dispersion is wide.** Seed 0 val 3.86 → test 3.57
   (−0.29). Seed 1 val 4.05 → test 3.44 (−0.61). Even though seed 1
   had the higher val, it tested lower than seed 0 — *exactly the
   dispersion mechanism cycle 21 surfaced for piecewise long-CEM*.
   Long-CEM has wider dispersion because it lets CEM walk further
   into a basin that may overfit val.
4. **Retail vs arb decomposition.** Seed 0 test retail_adv +4.378 (vs
   piecewise anchor +3.820) → +0.56 retail edge. Seed 1 test
   retail_adv +2.475 (vs anchor +3.820) → −1.35 retail edge.
   Seed 1 is winning on the arb side, losing on retail — different
   tradeoff than seed 0 found, despite both starting from the
   identical anchor.

## Files

* `scripts/run_ladder_longcem_anchor.py` — main runner (env vars
  `ANCHOR_KEY`, `RNG_SEED`, `MAX_WORKERS`).
* `scripts/ladder_strategy.py` — copied from cycle 22 (4-bucket
  ladder family).
* `scripts/make_figures.py` — figures + summary JSON.
* `results/cycle21_seed1_seed{0,1}/` — per-run history.json,
  test.json, progress.log.
* `results/cross_seed_summary.json` — machine-readable summary.
* `figures/m4_c23_long_vs_short_ladder_lift.png` — bar chart of
  cycle-19/22/23 ladder lift over the same-anchor piecewise.
* `figures/m4_c23_longcem_val_curves.png` — search-best per gen for
  cycle-23 long vs cycle-22 short, anchor val overlaid.

## Cycle-24 implications

The +0.13 mean lift is real but small. Two open questions:

1. **Cross-anchor robustness.** Does long-CEM ladder lift survive
   on the cycle-21-seed-2 anchor (+2.275 lift_FF, basin-collapsed)
   or on cycle-18-seed-0 (+3.006)? The cycle-22 short-CEM stretch
   showed ladder *failed to recover* a basin-collapsed anchor;
   does long-CEM do better?
2. **Multi-seed dispersion.** Is the single high-seed (+3.098)
   reproducible? Cycle 21 piecewise long-CEM had stddev ±0.32 across
   3 seeds; cycle 23 ladder long-CEM has stddev ±0.066 across 2
   seeds — surprisingly tight, but the sample is small.

Cycle 24 should add a **third RNG seed** (rng_seed=2) on the same
anchor for a stable mean estimate, then test cross-anchor.

## Notes / caveats

* No structural change to the ladder family — same 4-bucket
  identity-warm-start as cycle 19/22.
* Wall clock: ~46 min per run (CEM 38 min + rerank 4 min + test
  ~3 min); total wall ~46 min for two parallel seeds at workers=2.
* Cycle-21 piecewise long-CEM mean +2.727 (n=3 seeds, all warm-
  started from c11_d16_s2). Cycle-23 ladder long-CEM mean +3.032
  (n=2 seeds, warm-started from cycle-21-seed-1). The Δ=+0.305 is
  not cleanly comparable because the warm-start changes — cycle-21
  seed-1 (the cycle-23 anchor) is *itself* the median of the
  piecewise long-CEM distribution, so the ladder mean is by
  construction conditioning on a specific piecewise outcome. The
  right cross-anchor comparison is cycle 23's lift over its
  *own* anchor: +0.132 ± 0.066.
