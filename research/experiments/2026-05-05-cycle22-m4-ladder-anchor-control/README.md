# Cycle 22 — Apples-to-apples ladder vs piecewise (anchor-control)

**Date.** 2026-05-05 (cycle 22, M4)

## Question

Cycle 19 reported a +0.245 test lift_FF for the 4-bucket ladder family
over its piecewise warm-start. The warm-start was the cycle-18-seed-0
piecewise long-CEM result. Cycle 21 then revealed that
cycle-18-seed-0 was the **+75th-percentile** draw of the piecewise
long-CEM seed distribution (mean +2.727, max +3.006), not the median.

So the cycle-19 lift number conflates two effects:

1. **Family effect.** Does the ladder representation improve over
   piecewise when given the same starting point and the same CEM
   compute budget?
2. **Anchor effect.** Does starting from a luckier piecewise seed
   put CEM in a region where it can find more lift, regardless of
   the family?

Cycle 22 controls for the anchor by running the cycle-19 ladder CEM
warm-started from a *different* piecewise seed — specifically, the
**cycle-21-seed-1** piecewise (the median of the long-CEM
distribution at val-time, +2.900 lift_FF on test) — and reading off
whether ladder still lifts.

## Hypothesis

> Ladder warm-started from cycle-21-seed-1 piecewise (anchor lift_FF
> +2.900) will lift to lift_FF > +3.10 on test, replicating the
> +0.10–+0.20 family payoff seen at the cycle-19/20 budget on the
> cycle-18-seed-0 anchor.

Decision rule (multi-seed):

| Outcome | Interpretation |
|--|--|
| both seeds lift > +0.05 lift_FF over seed-1 piecewise | family effect confirmed, ~+0.10 cross-anchor |
| both seeds neutral or negative                       | cycle-19 was anchor-driven; pivot to plan (b) |
| one seed lifts strongly, the other doesn't           | family effect real but small; need 4 seeds |

## Method

Identical CEM mechanics to cycle 19's `run_ladder_cem.py`:

- Population 12, generations 5, elite_frac 0.2, dim 19.
- `init_std_frac` = 0.05 for the 16 inherited piecewise dims, 0.15
  for the 3 new ladder dims (`tiny_trade_threshold`,
  `continuation_tiny`, `reversal_tiny`).
- Normalizer: FixedFee(0.003, 0.003).
- Evaluator: `real_data`.
- Seed splits: search `range(0,64)`, val `range(1000,1128)`,
  test `range(2000,2256)`.
- Rerank: anchor + top-6 unique elites by search score → pick best
  by val score → eval on test.
- Identity warm-start: `tiny_trade_threshold = 0.5 *
  small_trade_threshold`, `continuation_tiny = continuation_small`,
  `reversal_tiny = reversal_small`.

The only difference vs cycle 19 is that the warm-start piecewise
dictionary is sourced from **cycle-21-seed-1** (median of the
distribution) rather than cycle-18-seed-0 (the +75th-percentile).

The script (`scripts/run_ladder_cem_anchor.py`) is parameterized on
`ANCHOR_KEY` and `RNG_SEED` env vars, so the same script also runs
the stretch experiment (cycle-21-seed-2 anchor, the basin-collapsed
+2.275 piecewise) by setting `ANCHOR_KEY=cycle21_seed2`.

## Result

### Primary experiment — cycle-21-seed-1 anchor (apples-to-apples)

| run | best_by_val source | val | test_score | lift_FF | lift over seed-1 piecewise |
|--|--|--:|--:|--:|--:|
| `cycle21_seed1_seed0` (rng_seed=0) | **anchor** | 3.651 | 3.370 | +2.900 | **+0.000** |
| `cycle21_seed1_seed1` (rng_seed=1) | **anchor** | 3.651 | 3.370 | +2.900 | **+0.000** |

**Key observation.** For both rng seeds, the rerank winner is the
anchor itself — the warm-start ladder. Every CEM-generated elite
(gen-0 through gen-4) lost to the anchor on the val seeds. Top val
scores in the rerank pool, rng_seed=0:

```
3.651 (anchor)
3.496 (gen-4 elite)  ← top non-anchor
3.489 (gen-3)
3.467 (gen-4)
3.454 (gen-3)
3.438 (gen-2)
3.407 (gen-2)
```

For rng_seed=1, similarly: anchor 3.651, top non-anchor 3.573 (gen-4),
then 3.548, 3.547, 3.509, 3.497, 3.463. The anchor leads by 0.08–0.16
val points across all CEM-generated elites.

### Decision-rule outcome

Both seeds neutral (lift = 0.000). Decision rule line 2 is met:
**cycle-19's +0.245 ladder lift was anchor-driven, not a real family
effect at this budget.**

### Why CEM didn't beat the anchor

Two things show up in the trajectory:

1. **CEM gen-0 best > anchor val score.** Each generation includes
   the anchor as candidate 0 plus 11 random draws around it. Gen-0
   best for both rng seeds was +2.724 on the **search** seeds
   (n=64), which is higher than the anchor's val score on those
   same seeds. So at least one of the 11 random draws beat the
   anchor on search.
2. **CEM gen-4 best on search ≈ +2.6, val ≈ +3.5.** The drop from
   anchor val 3.651 → gen-4 elite val 3.5 means the search → val
   generalization gap shifted against CEM. The anchor was trained
   on a different set of search seeds (`range(0,64)` again, but
   from the piecewise CEM trajectory, not the ladder one), and
   that piecewise mean happens to live in a region where val
   generalization is slightly better than ladder CEM's
   search-elite region.

Neither this cycle nor cycle 19 alone disproves the existence of a
real ladder family effect — it is possible that a longer-budget
ladder CEM, or a different CEM exploration schedule, finds a
genuine improvement. What cycle 22 *does* establish is that **at
the cycle-19 budget (5g × 12p), the +0.245 lift cycle 19 reported
does not reproduce on a different anchor.** It looks like noise,
not signal.

## Stretch — cycle-21-seed-2 anchor (basin-collapsed piecewise)

| run | rerank winner | val | test_score | lift_FF | lift over piecewise seed-2 |
|--|--|--:|--:|--:|--:|
| `cycle21_seed2_seed0` | **anchor** | 3.215 | 2.746 | +2.275 | **+0.000** |

The CEM trajectory on this anchor walked *into* a worse basin —
gen-3 search-best dropped to +1.036 (from gen-0 +2.436), and
multiple gen-4 elites had retail_adv −15 to −18 on val. The rerank
recovered the anchor (val 3.215 vs gen-N elites at val ≤2.13)
and the test result is bit-equal to the seed-2 piecewise
(test 2.746, lift_FF +2.275).

So ladder is *not* a stabilizer either: it didn't recover a basin-
collapsed piecewise; it just preserved it via the rerank-anchor
rule. Combined with the primary result, the cross-anchor ladder
lift over piecewise is +0.000 at three of four data points and
+0.245 at the cycle-18-seed-0 single-seed; the family-effect
hypothesis is rejected at this CEM budget.

## What it changed

- The cycle-19/20 ladder lift numbers (+0.245 cross-family on
  cycle-18-seed-0) and the cycle-20 multi-seed mean of +3.111
  ladder lift_FF are now understood as anchor-conditional
  results; their cross-anchor counterpart on the seed-1 anchor is
  **0.000**. The single-anchor multi-seed mean is reproducible
  (cycle 20 confirmed that), but the cross-anchor mean was not
  computed previously and is now known to be much smaller —
  potentially zero at this budget.
- The "+3.0 ceiling" is back as the right framing of the M4
  frontier under a strict cross-anchor cross-seed protocol.
  The +3.111 ladder mean was over-counting the family contribution
  by ~+0.1 lift_FF.
- For cycle 23, the most informative next step is no longer
  "more multi-seed ladder runs" but "do family escalation at all"
  — i.e. test smooth-head MLP, or longer-budget ladder, or a CEM
  variant that does not collapse onto search-elites.

## Files

- `scripts/run_ladder_cem_anchor.py` — parameterized ladder CEM.
- `scripts/ladder_strategy.py` — copy of cycle-19's ladder family.
- `scripts/make_figures.py` — cross-anchor comparison plots.
- `results/cycle21_seed1_seed{0,1}/{progress.log, history.json,
  test.json}` — primary runs.
- `results/cycle21_seed2_seed0/{...}` — stretch run.
- `results/cross_anchor_summary.json` — concise cross-anchor table.
- `figures/m4_c22_cross_anchor_ladder_lift.png` — bar chart.
- `figures/m4_c22_seed1_anchor_val_curves.png` — CEM trajectories.
