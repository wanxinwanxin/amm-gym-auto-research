# M4 cycle 26 — multi-seed long-CEM ladder on c18-s0

## Question

Cycle 25 produced a single-seed long-CEM ladder probe on the
**c18-s0** anchor (the strongest piecewise basin in the family,
piecewise lift_FF +3.006). The single seed (rng_seed=0) lifted
**+0.250** over the same-anchor piecewise (test +3.727, lift_FF
+3.256, retail_adv +3.541) — the highest single-seed real_data score
on the M4 leaderboard, and *higher* than the c21-s1 n=3 mean (+0.134).
That falsified the cycle-24 inverse-scaling hypothesis ("ladder lift
drops as piecewise quality climbs"), but n=1 is supporting evidence
only.

Cycle 26 tightens c18-s0 from n=1 to n=3 with two more rng_seeds:

* If the c18-s0 n=3 mean lands above +0.15 with at least one more
  seed in the find regime, the M4 multi-seed headline anchor for the
  ladder family shifts from c21-s1 (n=3 mean +0.134) to c18-s0.
* If at least one seed collapses (margin ≤ −0.50), the bimodal
  mixture-of-regimes characterization extends from c21-s2 to c18-s0
  — i.e. long-CEM has an anchor-independent collapse rate.
* If both seeds come in below +0.05 OR both collapse, the cycle-25
  +0.250 was a positive-tail draw and c18-s0 is not the M4 frontier.

## Method

Identical CEM mechanics to cycles 23/24/25 (19d ladder controller,
init_std_inh=0.05, init_std_new=0.15, elite_frac=0.2, normalizer
FixedFee(0.003,0.003), evaluator=`real_data`, 64 search seeds, 128
val seeds, 256 test seeds, 6-deep rerank on val) and identical
budget (POPULATION=24, GENERATIONS=10). Identity warm-start from
**c18-s0** piecewise long-CEM best params (cycle 18, rng_seed=0).

Two runs in parallel (workers=2 each on a 4-core sandbox):

* **A.** `ANCHOR_KEY=cycle18_seed0 RNG_SEED=1`
* **B.** `ANCHOR_KEY=cycle18_seed0 RNG_SEED=2`

## Files

* `scripts/run_ladder_longcem.py` — driver (cycle 25 driver with
  the c18-s0 anchor as default and rerouted output path).
* `scripts/ladder_strategy.py` — identical to cycle 25.
* `scripts/make_figures.py` — emits the cycle-26 figures and the
  aggregated cross-seed summary JSON.
* `results/cycle18_seed0_seed1/{history.json, test.json, progress.log,
  stdout.log}` — run A.
* `results/cycle18_seed0_seed2/{history.json, test.json, progress.log,
  stdout.log}` — run B.
* `results/cross_seed_summary.json` — aggregated across cycles
  23-26 (n=8 long-CEM ladder runs).
* `figures/m4_c26_anchor_lift_curve.png` — 3-anchor lift curve
  with c18-s0 now n=3.
* `figures/m4_c26_long_cem_val_curves.png` — CEM val trajectories
  for the two new runs.
* `figures/m4_c26_lift_summary.png` — bar chart of cross-anchor
  long-CEM ladder lift over piecewise.

## Key numbers

See `results/cross_seed_summary.json` and the M4 c26 section of
`research/presentation/slides.html`.
