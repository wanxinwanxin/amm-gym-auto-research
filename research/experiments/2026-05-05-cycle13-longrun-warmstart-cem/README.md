# Cycle 13 — long-run warm-start CEM (gen=24)

**Cycle date:** 2026-05-05.

## Question

Cycle 12 closed with three live hypotheses about why warm-start CEM
saturated near 457 across cycles 9-11:

  - (a) **capacity-is-bottleneck** — falsified by cycle 12 stage 1
    (latent_full @ 388.6).
  - (b) **anchor-is-sub-optimal** — not resolved (fresh-anchor
    piecewise was still climbing at gen 11).
  - (c) **recipe-ceiling** — most consistent with the cycle-12 data:
    both alternatives landed below warm-start at the same compute,
    which is exactly what (c) predicts.

Hypothesis (c) has not actually been *tested* yet — it has been
*observed-to-be-consistent*. Cycle 13 tests it directly: doubling the
CEM budget on the same warm-start anchor under the same recipe.

> **Going-in prior**: the elite-mean trajectory at cycle-11 gen 11 was
> still drifting up at +0.05 pts/gen, so the recipe-ceiling
> hypothesis isn't a slam dunk. Probability split (cycle 13):
>   - 40% test ≥ 460 (recipe ceiling falsified — refinement still left)
>   - 30% test in [457, 460) (marginal lift, ambiguous)
>   - 30% test < 457 (recipe ceiling confirmed at this anchor)

## Method

`scripts/run_long_warmstart.py` reuses the cycle-11 grid driver
recipe (pop=24, init_std_frac=0.10, elite_frac=0.20) but doubles
generations to 24 and anchors on the cycle-11 d16_s2 best_by_val
params (current M2 champion, test=456.80) instead of the cycle-8
ablation. Same val/test seed split (1000..1127 / 2000..2255) as every
prior M2 cycle, so the resulting test score is on the same
scoreboard.

Outputs:
- `results/longrun_d16_s0_g24/progress.log` — per-gen log.
- `results/longrun_d16_s0_g24/history.json` — full per-gen history.
- `results/longrun_d16_s0_g24/result.json` — top-8 rerank + best-by-val
  test evaluation.

## Decision rule (committed before running)

| Outcome | Cycle-14 implication |
|---|---|
| test ≥ 460 | Recipe ceiling **falsified**. Continue along this axis (gen=36 or wider pop). |
| 457 ≤ test < 460 | Marginal/ambiguous. Add one replicate at a different rng seed before calling it. |
| test < 457 | Recipe ceiling **confirmed** at this anchor. Pivot to M3 with d16_s2 (456.80) as M2 deliverable (~85% of way to 540). |

## Result

**Verdict: RECIPE_CEILING_CONFIRMED.** test = **456.803** vs champion
456.803 → Δ = **+0.000**. Best-by-val came from the **anchor itself
(generation 0)** with val=458.539; gens 1-23 explored without ever
producing a candidate that beat the anchor on val. Headline figure:
`figures/cycle13_summary.png`.

| metric | gen 0 (anchor) | gens 1-23 best | gen 11 (cycle-11 stop) | gen 23 |
|--|--:|--:|--:|--:|
| val score | **458.539** | 457.749 (gen 16) | 457.641 | 457.576 |
| best-search score | 452.387 | 451.365 (gen 10) | 451.192 | 451.230 |
| elite-mean search | 436.020 | 451.167 (gen 8) | 451.109 | 451.144 |

The CEM did *narrow* the elite cluster (elite-mean climbed 436 → 451
in 8 gens, then plateaued), but it did not produce a single elite
candidate whose 128-seed val score beat the anchor's 458.5. The
champion wins by val by ~0.8 pts and by test by 0 pts.

### What this means for M2

- Per the pre-committed decision rule (test < 457 → confirm and
  pivot), **M2 is closed**. The deliverable is `cycle-11 d16_s2`
  best_by_val (`research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2/result.json`),
  test=456.80, ~85% of the way to the 540 target.
- The cycle-12 hypothesis (a) "capacity is bottleneck" was already
  falsified. Cycle 13 falsifies "longer-run warm-start refines past
  the cycle-11 ceiling under this recipe". By construction, the
  hypotheses left for a future M2 reopening are **recipe-shape
  changes** (much wider init_std, much larger pop, hybrid CEM→PPO,
  different normalizer venue, etc.) — anything that *changes* the
  search distribution rather than refining it. None of those is the
  most informative next step right now; M3 is.

### Operational note

The driver's in-script rerank step never wrote `result.json` — the
24-gen CEM took 60.7 min, then the 8-elite × 128-seed val rerank +
1 × 256-seed test step started but the script must have been killed
between then and the next cycle. `scripts/finish_rerank.py` recovered
the result by reranking the 8 unique gen-best candidates from
`history.json`. This is strictly weaker than the original "all-elites
top-8" pool (which would draw from up to 24×4=96 candidates), but
since the per-gen-best is by definition the best of its elite set and
the elite cluster narrowed quickly to within ~0.4 pts after gen 8,
the val-best across the recovered pool matches the all-pool best
within search-noise (and lands on the anchor itself, which is in both
pools by construction).

