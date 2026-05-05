# Cycle 19 — M4 cycle 3: param-importance ablation + 4-bucket ladder

## Question

After cycle 18 estimated the piecewise-family real_data ceiling at
~+3.0 ± 0.2 lift_FF, two questions:

1. **What did c11+CEM long actually change?** Per-param "step-back-to-
   anchor" ablation: which of the 16 piecewise params carry the +0.97
   val-score gap (anchor 2.918 → long 3.885)?
2. **Is the +3.0 ceiling representational or compute-limited?** Does a
   4-bucket "ladder" family (split small bucket, +3 dims) warm-started
   from c11+CEM long lift past +3.5 (structural), into [+3.20, +3.50]
   (marginal), or below (saturated)?

## Method

- `scripts/run_param_importance_ablation.py` — for each of 16 piecewise
  params, evaluate the c11+CEM long params with that param reset to
  the c11 anchor value. n=128 val seeds, real_data, FixedFee(0.003)
  normalizer. 18 candidates total (16 ablations + baseline + full
  anchor). Workers=3, ~3.7 min wall clock.
- `scripts/ladder_strategy.py` — 4-bucket ladder (`tiny < small <
  medium < large`) controller; 19 dims (16 inherited + tiny_threshold
  + continuation_tiny + reversal_tiny). Identity warm-start: setting
  tiny=small in both threshold and bucket params reproduces the
  piecewise behaviour exactly (verified 0.000 score diff on 8
  challenge seeds).
- `scripts/run_ladder_cem.py` — 5g × 12p CEM, 19d, real_data;
  init_std_frac = 0.05 inherited / 0.15 new; rerank pool = anchor +
  top 6 unique elites by search score; n=256 test on best-by-val.
  Workers=3, ~13 min wall clock.

## Results

### Ablation

| rank | param | Δ score | Δ retail_adv | Δ edge_adv |
|--|--|--:|--:|--:|
| 1 | base_fee | +1.946 | +5.477 | +5.005 |
| 2 | reversal_small | +0.755 | +2.190 | +1.993 |
| 3 | continuation_to_same_side | +0.314 | −1.114 | −0.337 |
| 4 | continuation_to_cross_side | +0.301 | +2.593 | +1.597 |
| 5 | large_trade_threshold | +0.133 | −0.193 | +0.036 |
| 6+ | (other 11 params) | <+0.07 | varies | varies |

base_fee + reversal_small carry 81% of the per-param sum-of-Δ-score.
Sum-of-Δ = +3.31 vs full anchor reset Δ = +0.967 → parameters
interact non-additively.

### Ladder CEM

| | val (n=128) | test (n=256) | lift_FF | retail_adv |
|--|--:|--:|--:|--:|
| c11 anchor | +2.918 | +2.57 | +2.10 | +1.07 |
| c11+CEM long (cycle 18) | +3.885 | +3.476 | +3.006 | +3.215 |
| **ladder (cycle 19)** | **+4.030** | **+3.721** | **+3.251** | +3.113 |

Ladder lifts test by +0.245 / lift_FF by +0.245 over c11+CEM long.
In the [+3.20, +3.50] "marginal" band of the cycle-18 decision rule.
Best-by-val ladder pushed reversal_small to its lower bound (−0.01).

## Files

- `results/ablation/` — `progress.log`, `results.json`
- `results/ladder_cem/` — `progress.log`, `history.json`, `test.json`
- `figures/` — `m4_c19_param_importance.png`,
  `m4_c19_ladder_val_curve.png`

## Next

Cycle-20 plan: (1) reproducibility check ladder rng_seed=1; (2)
smooth-head MLP escalation on size_ratio; (3) stretch — k=8 finer ladder.
