# Cycle 12 — capacity escalation: ladder family + fresh-anchor sanity (M2)

## Question

Cycle 11 closed with the empirical headline that warm-start CEM on
the cycle-8 piecewise anchor saturates near **test ≈ 457** under a
(pop=24, gen=12) recipe. Spread across 7 cells (different
`(dim_total, rng_seed)` tuples) was 449–457; CEM-noise std on test is
≈ 3 pts. Cycle 12 asks two distinct questions, both designed to
*differentiate* the cycle-11 saturation hypothesis:

1. **Is policy capacity the bottleneck?** Run a CEM on the richest
   ladder rung — `latent_full` (18 params, with EMAs over flow,
   opportunity, fair-price, toxicity, competition, inventory). If
   ladder beats 457, capacity is the bottleneck and we move to
   ladder/MLP. If ladder is decisively below 457, the family isn't
   the wall.
2. **Is the cycle-8 anchor itself sub-optimal?** Run a from-defaults
   piecewise CEM with init_std = 0.30 × range (wide enough to
   plausibly leave the cycle-8 basin). If this fresh-anchor CEM
   lands within the 449–457 cluster, the cycle-8 basin IS the right
   basin and we should stop re-anchoring on it. If it lands
   materially higher, cycle 13 should re-anchor.

These two CEMs are the two items in the cycle-11 plan-of-record;
running them in one cycle gives us a clean falsifiability test of
both narratives at once.

## Method

Generic CEM driver matching the cycle-7 multi-family driver, with two
added init strategies: "defaults_wide_init_std_0.25" for ladder
families and "defaults_wide_init_std_0.30" for piecewise. Same
training/val/test split as every prior M2 cycle:

- search seeds: range(0, 64)
- val seeds: range(1000, 1128) — fixed across cycles
- test seeds: range(2000, 2256) — held-out
- normalizer: FixedFee(0.003, 0.003) on every leg
- evaluator: "challenge" scoring rule
- pop=24, gen=12, elite_fraction=0.2 (elite_n=4)
- 3 worker processes (3 of 4 cores; piecewise sandbox baseline)

Cycle-12 specifics:
- **Stage 1** (`run_ladder_cem.py --family latent_full`): mean =
  `LatentFullParams()` defaults (clamped to range), init_std = 0.25 ×
  range, rng_seed=0.
- **Stage 2** (`run_fresh_anchor_piecewise.py`): mean =
  `PiecewiseControllerParams()` defaults (clamped), init_std = 0.30 ×
  range, rng_seed=0.

Final scoring follows the same protocol as every prior cycle: rerank
the top-8 unique elites on val, take val-best, score on the held-out
test seeds.

## Falsification design

Anchor falsifying outcomes per stage:

**Stage 1 (ladder):**
- If `latent_full` test ≥ 460 → ladder family is the path; warm-start
  it in cycle 13 and ablate which ladder feature gives the lift.
- If 440 < test < 460 → within noise of warm-start cluster; capacity
  is plausibly fine but doesn't help. Cycle 13 looks at recipe.
- If test < 430 → ladder family is worse than warm-start piecewise
  *under this recipe*; either the ladder controller is poorly suited
  to this scoring rule, or 12 generations from a cold default isn't
  enough budget. Note both interpretations in cycle-13 plan.

**Stage 2 (fresh-anchor piecewise):**
- If test ≥ 460 → cycle-8 basin was sub-optimal; re-anchor cycle 13
  on this fresh result.
- If 440 < test < 460 → fresh-anchor lands in the same cluster as
  warm-starts; the cycle-8 basin IS the right basin. Cycle 13
  pivots to recipe (longer gens, wider rerank, larger pop) or
  challenge-rule analysis.
- If test < 430 → 12 gens of from-defaults CEM is too few to escape
  the default basin (interpretable: the cycle-8-derived anchor IS
  the local optimum nearest the default; warm-start was the only
  way to refine past the default-driven CEM ceiling).

## Outputs

- `results/latent_full_progress.log` — streaming per-gen log (stage 1)
- `results/latent_full_history.json` — per-generation best/elite/val
- `results/latent_full_test.json` — final val/test/rerank
- `results/fresh_anchor_piecewise_progress.log` — streaming per-gen
  log (stage 2)
- `results/fresh_anchor_piecewise_history.json` — per-generation
  best/elite/val
- `results/fresh_anchor_piecewise_test.json` — final val/test/rerank
- `results/chain.log` — driver-level start/finish log
- `figures/cycle12_summary.png` — combined visualization

## Headline results

| stage | family | dim | init_std | best_test | val_score | Δ_vs_456.8 |
|---|---|---:|---:|---:|---:|---:|
| 1 | latent_full | 18 | 0.25 | **388.57** | 388.77 | −68.24 |
| 2 | piecewise (fresh) | 16 | 0.30 | **418.65** | 419.34 | −38.16 |

Both stages land **below** the cycle-11 warm-start cluster (449–457).
Both falsifying directions hit the "test < 430" branch of the
falsification design — confirming the cycle-11 saturation hypothesis
and ruling out the two cleanest cycle-13 candidate moves (capacity
escalation and re-anchor).

**Verdict:** with 12 generations of CEM under this recipe, neither a
richer policy family nor a wider-init fresh-anchor can match what
cycle 6→8→9→10→11 achieved by stacking warm-start refinements on the
cycle-8 anchor. The warm-start path is doing real refinement work
that this cycle's two alternatives can't reach in 12 gens. The
saturation we observed at ~457 is therefore the local ceiling of the
cycle-8 piecewise basin under (pop=24, gen=12) recipe — not an
artifact of starving an alternative path.

The implication for cycle 13: we should **escalate the recipe**
rather than the policy family. Most-informative next moves: (a) longer
generations (24-36) with a hold-out reset to test whether warm-start
CEM keeps climbing past 457 with more compute; (b) larger pop (e.g.
48 or 64) to widen per-gen search; (c) abandon the AMM-challenge
sub-ceiling entirely and pivot to M3 (generalization study) using
the d16_s2 anchor as the M2 deliverable.

## Notes

- Total chain wall-clock: stage 1 = 36 min (CEM 30 min + rerank 5 min);
  stage 2 estimate = ~30 min.
- jax check still failing as expected; not retried this cycle.
- All inherited working-tree changes (cycle 8/9/10/11 leftovers) still
  untouched — cycle-12 edits are restricted to
  `research/experiments/2026-05-04-cycle12-latent-ladder-cem/`.
