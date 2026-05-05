# Cycle 18 — M4: long-budget CEM from c11 + prior sweep

## Question

Cycle 17 ran a 5-gen × 12-pop CEM from c11_d16_s2 on real_data and lifted
to **+2.77 lift_FF** on test (n=256), 4× the c5+CEM baseline (+0.74). Two
follow-ups are now decisive for M4:

1. **Is c11+CEM saturating, or does it keep climbing with more compute?**
   Cycle-17 best-by-val was at gen 3 (val 3.72), gen 4 was slightly worse
   (val 3.67) — could be plateau or noise.
2. **Is c11 a unique starting point, or is the prior dominance generic?**
   I.e. would CEM from any reasonable warm-start dominate CEM from a poor
   warm-start, or is the c11 retail-positive basin a special property?

## Method

Two experiments, same evaluator (real_data) and same seed splits as
cycle 17 (search 0..63, val 1000..1127, test 2000..2255):

1. **Long-budget CEM from c11.** 10 gens × 24 pop (4× cycle-17 compute),
   init mean = c11_d16_s2 best-by-val params, init_std_frac=0.10,
   normalizer FixedFee(0.003, 0.003), rng_seed=0, workers=3. Rerank
   pool = c11 anchor + top 6 unique elites by search score, ranked by
   val. Test on n=256 held-out seeds.

2. **Prior sweep at fixed compute.** 5g × 12p CEM (cycle-17 budget) from
   each of `{default-piecewise, c6_warmstart, c8_invaware_16d}`. The
   c5 and c11 short points are reused from cycles 16 / 17 for axis
   continuity, giving 5 anchors total in the basin-vs-compute plot.

   `default` = midpoint of `PIECEWISE_CONTROLLER_PARAM_RANGES`.
   `c8_invaware_16d` = c8 best params projected to 16-d (drop
   `inventory_skew_*` since the prior sweep keeps the policy family
   fixed at 16-d piecewise).

## Files

- `scripts/run_long_cem_from_c11.py` — long-budget CEM driver.
- `scripts/run_prior_sweep_cem.py` — prior sweep driver (3 anchors).
- `scripts/eval_size_decomp_long_cem.py` — per-bucket retail decomp on
  the long-budget best-by-val params.
- `scripts/make_figures.py` — generates 3 PNGs in `figures/`.
- `results/long_cem_from_c11/{history,test}.json` — long-budget output.
- `results/prior_sweep/<anchor_id>/{history,test}.json` — per-anchor.
- `results/prior_sweep_summary.json` — consolidated row per anchor.
- `results/size_decomp_long_cem_from_c11.json` — per-bucket retail decomp.
- `figures/fig_val_curve_long_cem.png` — val gen-by-gen curve.
- `figures/fig_prior_sweep.png` — final lift_FF per anchor (bars).
- `figures/fig_basin_vs_compute.png` — final lift_FF vs anchor val score.

## Decision rule (long-budget CEM)

| test lift_FF       | interpretation                                         |
|--------------------|--------------------------------------------------------|
| > +3.20            | real_data ceiling > +3.20; CEM still has headroom      |
| +2.80 to +3.20     | saturating near +3.0; family is the next bottleneck    |
| +2.60 to +2.80     | cycle-17 result reproduced; gen-3 plateau confirmed    |
| < +2.60            | CEM noise / val-overfit; investigate                   |

## Decision rule (prior sweep)

Compare final lift_FF across anchors at fixed compute (5g × 12p):
- If lift_FF positively correlates with anchor val score across the 5
  points, **basin-dominance** is the load-bearing finding.
- If lift_FF is roughly constant regardless of anchor, prior is
  irrelevant and the cycle-17 c5-vs-c11 gap was an outlier.
- If c11 alone produces a high lift, **c11 is anchor-special**, not a
  generic basin effect. Implies the next experiment is to find what
  about c11 makes it special (the retail-positive small bucket).
