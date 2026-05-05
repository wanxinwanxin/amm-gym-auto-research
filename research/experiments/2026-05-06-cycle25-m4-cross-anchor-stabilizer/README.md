# Cycle 25 — long-CEM ladder cross-anchor stabilizer follow-up

## Question

Cycle 24 produced two cross-anchor data points for the long-CEM ladder
(POPULATION=24, GENERATIONS=10) over the cycle-21 piecewise long-CEM
anchors:

* **cycle21_seed1 (median basin, lift_FF +2.900):** n=3 mean lift over
  same-anchor piecewise = +0.134 ± 0.066.
* **cycle21_seed2 (basin-collapsed, lift_FF +2.275):** n=1 lift over
  same-anchor piecewise = +0.547. Single-seed; supporting evidence
  only.

Two open questions cycle 25 sets out to resolve:

* **Q1 (c21-s2 second seed).** Is +0.547 stable, or a positive-tail
  draw of a wide distribution? A second RNG seed (rng_seed=1) on
  c21-s2 should land in [+0.30, +0.70] (consistent with the first
  seed plus cycle-23/24 dispersion ±0.07–0.30) → n=2 mean above
  +0.40 confirms the stabilizer.
* **Q2 (c18-s0 cross-anchor).** The cycle-18-seed-0 piecewise anchor
  (lift_FF +3.006, the strongest piecewise basin in the family) gives
  the third anchor on the proposed inverse-scaling line. Single seed
  (rng_seed=0) probe.

Decision rules:

* If c21-s2 n=2 mean lift > +0.40 AND c18-s0 lift < +0.13: 3-anchor
  inverse-scaling line confirmed; ladder framing is "stabilizer, not
  frontier-mover."
* If c21-s2 second seed ≈ 0: cycle-24 +0.547 was a tail draw; the
  stabilizer hypothesis needs more seeds.
* If c18-s0 lift > c21-s1 mean (+0.13): inverse-scaling line is false.

## Method

Identical CEM mechanics to cycle 23/24 (19d ladder, init_std_inh=0.05,
init_std_new=0.15, elite_frac=0.2, normalizer FixedFee(0.003,0.003),
evaluator real_data, 64 search seeds, 128 val, 256 test, 6-deep rerank
on val) and identical budget (POPULATION=24, GENERATIONS=10).

Two runs in parallel:

| run | anchor_key | rng_seed | piecewise lift_FF | hypothesis |
|--|--|--:|--:|--|
| A | cycle21_seed2 | 1 | +2.275 (basin-collapsed) | second seed; tighten c21-s2 to n=2 |
| B | cycle18_seed0 | 0 | +3.006 (strongest basin) | new anchor; tests inverse-scaling |

## Files

```
scripts/run_ladder_longcem.py   # cycle-24 driver with cycle18_seed0 anchor added
scripts/ladder_strategy.py      # 19-dim ladder (copy from cycle 24)
scripts/make_figures.py         # figures + cross-seed summary
results/cycle21_seed2_seed1/{history,test,progress}.{json,log}
results/cycle18_seed0_seed0/{history,test,progress}.{json,log}
results/cross_seed_summary.json
figures/m4_c25_anchor_lift_curve.png
figures/m4_c25_long_cem_val_curves.png
figures/m4_c25_lift_summary.png
```
