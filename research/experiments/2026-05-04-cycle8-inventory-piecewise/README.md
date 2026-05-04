# Cycle-8 — Inventory-aware piecewise warm-start CEM

## Question

Cycle 7 falsified the cycle-6 hypothesis that warm-start CEM lift is
family-agnostic — `submission_basis` got essentially zero lift while
`piecewise` got +18.7. The cycle-7 conclusion was that piecewise's
explicit large/medium/small × continuation/reversal action-space
structure carries the family. Cycle-8 priority #1: **does the
piecewise family have more headroom if we extend it with explicit
inventory awareness?**

## Hypothesis going in

~60/40 the inventory dimension matters. Prior: the cycle-6
piecewise best had val_edge_advantage = -19.3 (i.e. losing flow share
to the 30-bps normalizer). Adding fee skew that pulls inventory
back to neutral should at minimum claw back some adverse-selection
losses and could plausibly lift +5 to +15 pts if it works.

If the lift is ≥ +5 on test, the family is not action-space-saturated
and cycle 9 should keep escalating piecewise structure (e.g. add
multi-level reversal memory, or fair-value gap). If the lift is < +2,
piecewise's structural advantage tops out at ~432 and we should
pivot to a denser policy class.

## What we ran

1. New strategy `arena_policies/inventory_aware_piecewise.py` —
   16-param piecewise + 3 new params:
   - `inventory_skew_to_bid` ∈ [-0.05, 0.05]
   - `inventory_skew_to_ask` ∈ [-0.05, 0.05]
   - `inventory_skew_dead_zone` ∈ [0.0, 0.5]
   At zero, the strategy is behaviourally identical to
   `PiecewiseControllerStrategy` — verified by two unit tests
   (batch-score parity, dead-zone suppression) and by the in-driver
   anchor-score check (gen-0 best 427.521 == cycle-6 piecewise
   reference).
2. `tests/test_inventory_aware_piecewise.py` — 3 tests passing.
3. Driver
   `scripts/run_inventory_warmstart_cem.py` — 12-gen CEM, pop=24,
   elite_n=4, init_std_frac=0.10, search seeds 0..63, val 1000..1127,
   test 2000..2255. Mirrors the cycle-7 warm-start CEM driver.
4. The driver was reaped between sandboxes after gen 11 finished but
   before the test eval. Recovery script
   `scripts/recover_rerank_and_test.py` re-runs the rerank+test from
   the persisted history (top-1 per gen, deduped).

## Result

| Metric | Cycle-6 piecewise (M2 best) | Cycle-8 inventory-aware | Δ |
|---|---|---|---|
| val_score (128 seeds) | 433.57 | 447.66 | +14.09 |
| **test_score (256 seeds)** | **432.75** | **446.44** | **+13.69** |
| val_edge_advantage | -17.19 | +21.69 | flipped sign |
| test_edge_advantage | -19.30 | +26.16 | flipped sign |
| Gap to M2 target (540) | 107.25 | 93.56 | -13.69 |

**Hypothesis confirmed (the strong version).** The lift exceeded the
optimistic prior, and the edge_advantage flip from −19 to +26 is the
qualitative shift: the strategy went from losing flow share to the
normalizer to actively winning it.

## Ablation — the inventory dimension contributes nothing

`scripts/run_ablation.py` re-evaluates the cycle-8 best with the 3
inv-skew params zeroed out (keeping the refined 16-d piecewise section
identical) and runs the same params under the bare
`PiecewiseControllerStrategy` as a parity check.

| Variant | Test score (256 seeds) | edge_advantage |
|---|---|---|
| Cycle-8 inv-aware best (inv params ON) | 446.441 | +26.157 |
| Same params, inv params zeroed | **446.613** | +26.298 |
| Same 16 dims via PiecewiseStrategy (parity check) | 446.613 | +26.298 |

**The 3 inventory-skew params contribute Δ = -0.17 (slightly negative,
within noise).** The full +13.69 pt lift over cycle-6 piecewise is
attributable to additional CEM refinement on the **16 inherited
piecewise dims**, not to the new inventory dimension.

This *falsifies* the going-in hypothesis. Cycle 8's "inventory-aware"
framing turned out to be misleading — what really happened is that 12
more CEM gens at init_std=0.10 starting from cycle-6 best lifted
piecewise alone from 432.7 to 446.6 (+13.9 pts). The 3 extra dimensions
in the search space did not hurt convergence noticeably (gen-over-gen
progress was monotonic and similar in shape to cycle-6) but they did
not help either.

## What this changed about my prior

- **Inventory awareness in this exact form (symmetric fee skew on
  EMA-free reserve imbalance) is not the bottleneck for piecewise.**
  Either the ChallengeTape distribution doesn't generate enough
  sustained one-sided flow for inventory shaping to matter, or this
  specific implementation (single soft-hinge + 2 linear coefficients) is
  too coarse to express the right policy. Cycle 9 could try a smarter
  inventory feature (e.g. EMA over reserve deviation, or
  reserve-conditional spread) before declaring inventory dead.
- **Cycle 6 was much more under-converged than its own log claimed.**
  Cycle-6's val plateaued around 433 by gen 11; cycle-8's "second pass"
  CEM (also 12 gens, also init_std=0.10, but warm-started from cycle-6
  best) lifted +14 pts from there. Two-pass CEM is itself a free win on
  piecewise — at least one more pass is worth trying.
- **Best M2 score updated**: 446.61 (cycle-8 piecewise-only ablation),
  vs cycle-6's 432.75. Gap to M2 target (540): **93.39 pts**.

## Cycle-9 implications

1. **Run cycle-8b: a third pass of warm-start CEM on bare piecewise**,
   anchored at the cycle-8 ablation params. If the marginal lift is
   small (< +2), the family is now genuinely converged. If it's
   another +5+, we have 2-3 cheap passes left in this approach.
2. **Try a smarter inventory feature.** The current formulation acts
   on instantaneous reserve deviation; an EMA version may be less
   noisy and capture trend more reliably.
3. **Keep cycle-6 and cycle-8 as comparable baselines** for any
   structural change to the policy class, since we now know two
   passes of CEM are doing real work.

## What this changed about my prior

- Inventory-awareness adds real signal even at small magnitudes.
  Likely working through reduced adverse selection during sustained
  one-sided flow.
- The piecewise family is **not** structurally saturated at 432. The
  fact that the warm-start at zero-inventory recovers cycle-6
  exactly, then 12 gens of refinement add +14 pts, suggests cycle 6
  was meaningfully under-converged.
- The cycle-7 prior "submission_basis flat-bottom basin" suggested
  the inherited CEM was only sometimes under-converged. With
  inventory-aware piecewise we have direct evidence that 12 more
  gens of CEM at init_std=0.10 still finds non-trivial gradient even
  when the inherited optimizer was already 22 gens deep.

## Files

- `scripts/run_inventory_warmstart_cem.py` — main driver.
- `scripts/recover_rerank_and_test.py` — recovers test eval from
  history if the driver was killed mid-rerank.
- `scripts/build_figure.py` — 3-panel summary figure.
- `results/inventory_warmstart_cem_history.json` — per-gen records.
- `results/inventory_warmstart_cem_test.json` — final rerank + test.
- `figures/inventory_aware_summary.png` — convergence + inv-skew
  dynamics + headline bar.

## Seed split

- search seeds: 0..63 (64)
- val seeds: 1000..1127 (128)
- test seeds: 2000..2255 (256)

Same as cycle 7 — held-out test seeds were not seen during search or
val.
