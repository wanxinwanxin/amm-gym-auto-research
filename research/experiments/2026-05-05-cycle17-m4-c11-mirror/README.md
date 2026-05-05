# Cycle 17 — M4 mirror experiment: direct CEM on real_data from c11

## Question

Cycle 16 ran a 5-gen × 12-pop CEM directly on the real_data evaluator,
warm-started from the c5 anchor (the M2 starting line, lift_FF
−1.22). It lifted to lift_FF +0.74 on test (n=256). c11_d16_s2 (the
M2 deliverable, the highest-scoring real_data policy on file) measures
lift_FF +2.10 on the same test seeds. We did not know whether c11+CEM
would saturate near +2.10 (piecewise-family real_data ceiling) or
lift past it (the warm-start prior is what dominates and the policy
class still has room to improve on real_data).

Decision rule (set in cycle-16 STATE.md):

| c11+CEM lift_FF | implication |
|---|---|
| > +2.20 | warm-start prior dominates → M4 cycle 1 framing pivots to a prior-sweep |
| [+2.00, +2.20] | c11 is a piecewise-family real_data ceiling → need richer family or retail-aware loss |
| < +2.00 | CEM on real_data is regressing c11 → real_data evaluator is misleading the optimizer |

## Method

Identical to cycle-16's `run_m4_baseline_cem.py` EXCEPT init mean =
c11_d16_s2 best-by-val params (16-d piecewise, no noop tail) instead
of c5 inherited params. Same population (12), generations (5),
elite_frac (0.2), init_std_frac (0.10), search/val/test seed splits
(0..63 / 1000..1127 / 2000..2255), normalizer FixedFee(0.003, 0.003),
rng_seed (0), workers (cpu-1).

Rerank pool injects the c11 anchor itself before adding 6 elites by
search score; this guarantees `best_by_val` cannot regress past the
anchor (no candidate beats c11 on val ⇒ best_by_val = c11).

Per-trade-size bucket decomposition (small / medium / large with cuts
at size_ratio 0.003 and 0.012, matching cycle-16) was run on (a) the
M4 baseline's best-by-val params (decomp confirmation requested by
cycle-16 STATE), and (b) the c11+CEM best-by-val params (added this
cycle to confirm whether CEM stayed in the c11 retail basin or
drifted toward c5's arb-side basin).

## Headline result — c11+CEM > +2.20, warm-start prior dominates

| anchor | source | test lift_FF | test retail_adv | test edge_adv |
|---|---|---:|---:|---:|
| c5 | inherited piecewise | **−1.22** | −10.14 | (unrecorded; from STATE) |
| c5 + CEM | cycle-16 M4 baseline | **+0.74** | −13.10 | −5.42 |
| c11_d16_s2 | M2 deliverable | **+2.10** | +1.08 (val) | +3.05 (val) |
| c11 + CEM | cycle-17 mirror | **+2.77** | +0.66 | +3.76 |

c11+CEM lift_FF = **+2.77**, comfortably above the +2.20 threshold.
Decision rule fires: **the warm-start prior is what dominates short-
budget CEM on real_data; the local basin matters more than the
optimizer.**

Per-gen val trajectory:

| gen | c5+CEM val | c11+CEM val |
|---:|---:|---:|
| 0 (anchor) | (n/a) | 2.918 |
| 0 | 0.475 | 2.918 |
| 1 | 1.241 | 3.313 |
| 2 | 1.508 | 3.473 |
| 3 | 1.829 | **3.720** ← best-by-val |
| 4 | 1.853 | 3.673 |

c11+CEM converges in val by gen 3; the best-by-val params are from
gen 3.

## Per-bucket decomposition: c11+CEM stays in c11's basin; c5+CEM amplifies the routing collapse

`retail_edge_advantage` (sub minus norm), n=128 val seeds, bootstrap
95% CIs:

| anchor | small | medium | large | overall |
|---|---:|---:|---:|---:|
| c5 baseline | −9.51 [−9.60, −9.41] | +0.04 | −0.66 | −10.14 |
| c5 + CEM (M4 baseline) | −10.33 [−10.45, −10.21] | +0.06 | **−3.06** [−3.71, −2.45] | −13.33 |
| c11_d16_s2 | +1.17 [+0.99, +1.32] | −0.02 | −0.08 | +1.07 |
| c11 + CEM (this cycle) | +1.45 [+1.05, +1.82] | +0.07 | −0.83 | +0.70 |

Routing share (count_sub / count_norm) on the small bucket:

- c5: 401.6 / 2621.2 → 13.3% routed to submission
- c5+CEM: 164.7 / 2653.6 → **5.8%** (routing collapse *amplified*)
- c11: 2031.7 / 1546.2 → 56.8%
- c11+CEM: 1932.6 / 1265.4 → **60.4%** (basin preserved, slightly improved)

## What this changed

1. **The cycle-16 hypothesis "small-bucket worsening dominates the
   M4 baseline retail drop" is partially falsified.** Of the −3.20
   M4-vs-c5 retail drop, only −0.82 (~26%) is small-bucket; −2.40
   (~75%) is large-bucket. Mediums are unchanged. The M4 baseline
   regressed on the *high-magnitude tail* of trade size, not on the
   high-frequency small bucket.

2. **The mechanism is consistent across buckets and anchors: CEM-
   from-the-wrong-basin amplifies whatever routing/pricing problem
   the basin starts with.** From c5, both small and large buckets
   shifted *more* flow to FF; from c11, the c11 routing structure
   is preserved (small at 60%, large at 0.7/0.9 = 44% submission
   share).

3. **M4 cycle 1's plan pivots.** The "policy complexity sweep" of
   the original M4 plan-of-record is no longer the most informative
   next step. The most informative next step is a *prior sweep*:
   for a fixed family (piecewise), how do different warm-starts
   converge under direct CEM-on-real_data, and is there a
   piecewise-family real_data ceiling above +2.77?

## Cycle-18 plan-of-record

(see `research/STATE.md`)

1. **Longer-budget CEM from c11.** 10-gen × 24-pop (4× the budget of
   this cycle) on real_data, same anchor and seeds. Decision rule:
   does c11+CEM saturate by gen 5–6, or does the trajectory still
   have slope at gen 4? If it saturates near +3.0 lift_FF, we have
   strong evidence the piecewise family on real_data caps near +3.
   If it lifts past +3.5, M4 has more room.

2. **Prior sweep at fixed compute.** Run 5-gen × 12-pop CEM (this
   cycle's budget) from each of {default-piecewise, c6 (cycle 6
   warm-start), c8 (inv-aware), c11_d16_s2, c11_d24_s0} on
   real_data. Plot final lift_FF vs anchor. This isolates the basin
   effect: same compute, same family, varying prior.

3. *(stretch)* Retail-aware CEM from c5: score_modified =
   edge_advantage + 0.2 × retail_edge_advantage. Tests whether a
   small retail penalty steers c5+CEM into the c11 basin
   (retail-fix-then-arb instead of arb-only) or whether c5 is too
   far from the c11 basin to bridge with a tiebreaker.

## Files

- `scripts/run_m4_c11_mirror_cem.py` — main CEM driver, mirrors
  cycle-16's `run_m4_baseline_cem.py`.
- `scripts/eval_size_decomp_m4_baseline.py` — per-bucket decomp on
  cycle-16 M4 baseline best-by-val params.
- `scripts/eval_size_decomp_c11_mirror.py` — per-bucket decomp on
  this cycle's c11+CEM best-by-val params.
- `scripts/make_figures.py` — produces 3 PNGs.
- `results/m4_c11_mirror/test.json` — full rerank + best-by-val test
  results.
- `results/m4_c11_mirror/history.json` — per-gen CEM history.
- `results/size_decomp_m4_baseline.json` — combined 3-anchor
  per-bucket table (c5, m4 baseline, c11).
- `results/size_decomp_c11_mirror.json` — c11+CEM per-bucket numbers.
- `figures/gen_val_curves.png` — c5+CEM vs c11+CEM val trajectories.
- `figures/retail_edge_by_bucket.png` — 4-anchor grouped bars.
- `figures/lift_summary.png` — 4-anchor lift_FF summary.
