# Cycle 16 — per-trade-size decomposition + M4 pre-launch baseline

**Date**: 2026-05-05
**Milestone**: M3 cycle 3 (decomp) → M4 cycle 0 (pre-launch baseline)

## Question (cycle entry)

Cycle 15 localized the early-anchor (c5) OOD failure to retail-flow
pricing: `retail_edge_advantage` swung -9.99 (c5) → +1.06 (c11) on
`real_data` test seeds, while `arb_loss_advantage` stayed in a narrow
+1.7 to +3.7 band. The active hypothesis going into cycle 16 was:

> **Early-anchor harm is concentrated in *specific* trade-size
> buckets / market regimes; if we can identify those, M4 has its
> first concrete inductive-bias target.**

Cycle 16 splits into two questions:

1. **Per-bucket decomposition.** Is the c5-vs-c11 retail-edge gap
   concentrated in a single trade-size bucket (small/medium/large), or
   uniform across buckets? If concentrated, M4 has a localized
   inductive-bias target. If uniform, the real_data evaluator is the
   bottleneck and we should go straight to direct optimization.

2. **M4 pre-launch baseline.** Is the `real_data` evaluator
   CEM-friendly enough that direct optimization can recover the
   challenge-ceiling lift? (At least matching c11's +2.10 lift_FF on
   real_data starting from c5's -0.93?)

## Method

### Part 1 — per-trade-size decomposition (`eval_size_decomp.py`)

We bucket retail trades by the same `size_ratio = amount_y /
reserve_y_post` quantity that the piecewise controller itself uses
([arena_policies/piecewise_controller.py:90][pw]), with cuts at the
c5 default thresholds (small < 0.003, medium ∈ [0.003, 0.012),
large ≥ 0.012).

The simulator's `step_once()` already records every trade event
including pre/post state, source ("retail"/"arb"), venue
("submission"/"normalizer"), `amount_x`, `amount_y`, and a `TradeInfo`
with post-trade reserves. We loop `step_once()` externally and
accumulate per-bucket × per-venue: edge, count, total amount_y. This
avoids modifying the simulator at all.

Trade-edge formula (matches `simulator.py:738`):
- if AMM bought x (trader sold x): `edge = amount_x * fair_price - amount_y`
- if AMM sold x (trader bought x): `edge = amount_y - amount_x * fair_price`

**Anchors**: c5 baseline (cycle-5 inherited piecewise) and c11_d16_s2
(cycle-11 grid-CEM best, M2 deliverable).
**Eval**: `evaluator_kind="real_data"`, n=128 val seeds (1000..1127),
normalizer FixedFee(0.003).
**Verification**: simulator-aggregate `retail_edge_submission` and
`retail_edge_normalizer` are re-derived from the loop accumulators —
max abs error per anchor reported.

### Part 2 — M4 pre-launch baseline (`run_m4_baseline_cem.py`)

Warm-start CEM from c5 inherited piecewise on
`evaluator_kind="real_data"`. Pop=12, gen=5, elite_frac=0.2,
init_std_frac=0.10. Search seeds 0..63 (64), val 1000..1127 (128),
test 2000..2255 (256), normalizer FixedFee(0.003). Three workers
(cpu_count − 1).

This is intentionally a *small-budget* "is direct optimization on
real_data viable" experiment, not a full M4 attempt. Its outputs are
(a) a yes/no signal on whether real_data is CEM-friendly, (b) a
baseline-budget headline number for M4 cycle 1 to beat, (c) a per-gen
trajectory of `retail_edge_advantage` to compare with the M2
challenge-CEM trajectory from cycle 14's dual-curve.

## Results

### Per-bucket decomposition (n=128 val, real_data)

| anchor | bucket | retail_edge_advantage | 95% CI         | n_sub | n_norm | edge/amt_y_sub (bps) | edge/amt_y_norm (bps) |
|--------|--------|----------------------:|----------------|------:|-------:|---------------------:|----------------------:|
| c5     | small  | **−9.508**            | [−9.60, −9.41] |   401.6 |  2621.2 |  28.39 |  35.38 |
| c5     | medium | +0.036                | [−0.15, +0.23] |     3.6 |     4.1 | 130.89 | 105.46 |
| c5     | large  | −0.665                | [−0.88, −0.47] |     0.6 |     0.9 | 190.26 | 173.43 |
| c11    | small  | **+1.167**            | [+0.99, +1.32] |  2031.7 |  1546.2 |  31.56 |  31.79 |
| c11    | medium | −0.022                | [−0.12, +0.08] |     3.9 |     4.0 | 104.09 | 103.57 |
| c11    | large  | −0.078                | [−0.19, +0.02] |     0.8 |     0.8 | 169.12 | 170.29 |

**c5 minus c11 by bucket**: small −10.67, medium +0.06, large −0.59.
**Identity check**: max abs error between simulator-aggregate
`retail_edge_*` and the per-event re-derivation: 4.8e-14 (sub),
4.1e-14 (norm) — float roundoff only.

The headline finding is unambiguous: **the cycle-15 gap is almost
entirely a small-trade phenomenon**. Medium-bucket retail edge is
indistinguishable between c5 and c11; large-bucket differs by only
~0.6 lift points. The −10.67 small-bucket gap accounts for ~95% of
the −11.20 overall retail_edge_advantage difference.

The mechanism is a **routing collapse**: c5 receives only ~13% of
small-trade count (401.6 vs 2621.2 routed to FixedFee), while c11
receives ~57% (2031.7 vs 1546.2). Per-unit-volume markout (bps) on
the trades that *do* reach c5 is actually slightly *lower* than
FixedFee on small trades (28.39 vs 35.38 bps), which means c5's
small-trade fee is on average *under* 0.003 — the router is sending
small flow to FixedFee for *price* reasons (presumably an inventory
or signal-driven mid shift), not because c5 charges more in fees per
se. c11 reaches a near-symmetric state: 31.56 vs 31.79 bps and
roughly 57/43 routing.

### M4 pre-launch baseline

c5 val on `real_data` (n=128, normalizer FixedFee(0.003)):
score=−0.353, edge_advantage=−6.10, retail_advantage=−10.14
(replicates cycle-15 c5 numbers).

Per-gen trajectory (best-of-pop on search seeds 0..63):

| gen | best_search | val score | val retail_adv | val edge_adv |
|----:|------------:|----------:|---------------:|-------------:|
|  0  |  +0.700     |  +1.853   |   −13.33       |  −4.98       |
|  1  |  −0.388     |  +0.684   |   −11.14       |  −5.47       |
|  2  |  −0.220     |  +0.897   |   −11.43       |  −5.37       |
|  3  |  −0.056     |  +1.111   |   −11.74       |  −5.27       |
|  4  |  −0.016     |  +1.139   |   −11.78       |  −5.25       |

**Final best-by-val on test (n=256)**:
- test score = **+1.210**
- lift_FF (vs FixedFee 0.470) = **+0.739**
- test edge_advantage = −5.42
- test retail_advantage = −13.10

For comparison:
- c5 starting point (cycle 15 test): score = −0.744, lift_FF = −1.214
- M4 baseline 5-gen CEM: score = +1.210, lift_FF = +0.739 (+1.95 lift gained)
- c11 M2 ceiling (cycle 15 test): score = +2.574, lift_FF = +2.104

**Two findings.**

1. **Direct real_data CEM is CEM-friendly but slower per unit
   compute than challenge CEM.** A 5-gen × 12-pop budget closes
   ~63% of the c5→c11 lift_FF gap (+1.95 / +3.18). It does not
   plateau by gen 4 — best_search and val are still rising.

2. **The local optimum direct CEM finds is *retail-worse* than c5,
   not retail-fixed.** retail_advantage went from c5's −10.14 to
   M4-baseline's −13.10 (test). All of the score gain came from
   the arb side. Direct CEM on real_data, starting from c5,
   *amplifies* the small-bucket failure rather than fixing it. The
   policy is finding a different OOD local optimum.

## What this changes

- **Active hypothesis confirmed.** Early-anchor OOD harm is
  concentrated in the small-trade bucket. M4 cycle 1 has a
  concrete target: keep the small-trade routing share near
  symmetric (50%) while preserving the medium/large pricing.

- **Mechanism is *routing*, not *fee level*.** Per-unit-volume
  markout on small trades is similar between c5 sub and FixedFee
  (28 vs 35 bps). The damage comes from the count split. This
  reframes the M4 lever from "lower the small-trade fee" to "fix
  the small-trade *price*" (mid placement / inventory skew).

- **M4 cycle 1 framing.** From this analysis, M4 should:
  1. include `retail_edge_advantage` (or even small-bucket retail
     count share) as an *auxiliary* signal alongside score, since
     it's the leading indicator of the OOD failure mode;
  2. consider warm-starting from c11 rather than c5 if the goal is
     "best lift on real_data", since c11 already lives near the
     50/50 routing equilibrium and any local CEM neighborhood
     around it is OOD-positive.

- **Empirical M4 baseline is +0.74 lift_FF**, ~63% of the c11
  ceiling. The pre-launch baseline tells us the M2 c11 deliverable
  is, today, a stronger real_data policy than what direct CEM finds
  in a 5-gen budget from c5. M4 cycle 1's first ablation should
  rerun this experiment from c11 to see if direct refinement on
  real_data can push past +2.10 lift_FF.

## Files

- `scripts/eval_size_decomp.py` — per-trade-size decomposition driver.
- `scripts/make_figure.py` — bar charts for retail_edge_advantage by
  bucket (panel 1) and trade-count routing (panel 2, log scale).
- `scripts/run_m4_baseline_cem.py` — M4 pre-launch CEM driver.
- `results/size_decomp.json` — full per-bucket × per-anchor JSON.
- `results/size_decomp.stdout` — streaming log.
- `results/m4_baseline/history.json` — per-gen CEM history.
- `results/m4_baseline/test.json` — final best-by-val + held-out test.
- `figures/retail_edge_by_bucket.png` — headline figure for the
  decomposition.

[pw]: ../../../arena_policies/piecewise_controller.py
