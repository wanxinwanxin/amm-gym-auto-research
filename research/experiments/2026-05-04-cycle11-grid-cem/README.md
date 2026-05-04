# Cycle 11 — multi-seed × multi-dim warm-start CEM grid (round 1)

**Date.** 2026-05-04.
**Active milestone.** M2 — beat 540 on the simple-AMM challenge.
**Inherited best.** 456.74 test (cycle-10 A: 20-d noop tail, rng_seed=0).

## Why this experiment

Cycle 10 falsified the "wrapper-as-noise" framing: cycle-9 #3's +7.83 lift
over cycle-9 #1 was an RNG-stream artifact (different `dim_total` ⇒
different normals consumed per CEM candidate ⇒ different sampled
directions in the 16-d piecewise basin), not a property of any wrapper
geometry. That left an open question with a tight 2h cycle budget:

> What is the basin's actual ceiling on this anchor + this CEM recipe,
> once we account for the (rng_seed, dim_total) lottery?

Cycle 10 sampled only 4 cells of the (dim_total, rng_seed) grid
({16, 20} × {0, 1}, plus an EMA-wrapper variant at (20, 0) that the
ablation showed was equivalent to (20-noop, 0)). Three are dim=20 or
dim=16/seed=0,1; the dim_total=24 axis is unsampled and only 1 of 2
non-zero seeds at dim_total=16 has been measured.

## Cells run this cycle

| label        | dim_total | core | tail | rng_seed | wrapper        |
|--------------|----------:|-----:|-----:|---------:|----------------|
| c11-d16-s2   |        16 |   16 |    0 |        2 | bare           |
| c11-d24-s0   |        24 |   16 |    8 |        0 | noop tail (×8) |
| c11-d24-s1   |        24 |   16 |    8 |        1 | noop tail (×8) |

Each cell runs the same warm-start CEM recipe used since cycle 6:
- pop = 24, generations = 12, elite_frac = 0.20, init_std_frac = 0.10
- normalizer venue: fixed-fee 30 bps
- search seeds = 0..63, val seeds = 1000..1127, test seeds = 2000..2255
- anchor = cycle-8 ablation best (16 piecewise dims), inert noop tail
  initialized to zero with bounds [-1, +1] and the same init_std_frac
  scaling so the CEM samples the tail with the same proportional
  variance as the core dims.

Eval semantics: the noop_* dims are stripped before the params dict is
fed to `PiecewiseControllerParams`, so they cannot in principle change
the score — they only shift the RNG stream offset (4 extra normals per
candidate per generation per noop dim).

## What we expect to learn

- **Best-of-grid for the basin.** With cycle-10's 4 cells we have
  {448.81, 452.96, 456.64, 456.74}; adding 3 more should give a
  tighter empirical ceiling estimate.
- **CEM-noise std.** Across 7 (dim, seed) cells of the same basin we
  can compute the empirical std of the warm-start CEM's headline
  test score. That number is the threshold for what counts as a
  "real" lift in any subsequent single-CEM headline.
- **Decision rule for cycle 12.**
  - If best-of-grid ≥ 459 (~3 above current best): warm-start a
    longer-gen run from the winning (dim, seed) to test depth.
  - If best-of-grid stays ≤ 458 across all 3 reps: pivot to ladder /
    MLP capacity escalation.
  - If the std is large enough that single-CEM headlines are
    indistinguishable from noise across this grid, mark "warm-start
    CEM at this anchor is saturated" and pivot regardless of the max.

## Files

- `scripts/run_grid_cell.py` — generic CEM cell runner. `--dim-total D
  --rng-seed S` writes to `results/cell_dD_sS/{progress.log,history.json,
  result.json}`.
- `scripts/run_grid.sh` — sequential driver that runs all 3 cells.
  Each cell is a separate subprocess so a cell death doesn't kill
  the grid.
- `scripts/make_grid_figure.py` — combines cycle-9 #1, cycle-9 #3,
  cycle-10 A, cycle-10 B, and the 3 cycle-11 round-1 cells into
  `figures/grid_summary.png` and `results/grid_summary.json`.

## How to reproduce

From the repo root, with `numpy gymnasium pyarrow` installed:

```bash
# All three cells sequentially (~90 min):
bash research/experiments/2026-05-04-cycle11-grid-cem/scripts/run_grid.sh

# Or one at a time:
python3 research/experiments/2026-05-04-cycle11-grid-cem/scripts/run_grid_cell.py --dim-total 16 --rng-seed 2
python3 research/experiments/2026-05-04-cycle11-grid-cem/scripts/run_grid_cell.py --dim-total 24 --rng-seed 0
python3 research/experiments/2026-05-04-cycle11-grid-cem/scripts/run_grid_cell.py --dim-total 24 --rng-seed 1

# Build the cross-cycle figure once cells are done:
python3 research/experiments/2026-05-04-cycle11-grid-cem/scripts/make_grid_figure.py
```

## Result

| cell        | dim | seed | val (best) | test (n=256) | Δ vs c10 best (456.74) |
|-------------|----:|-----:|-----------:|-------------:|-----------------------:|
| c11-d16-s2  |  16 |    2 |    458.539 |   **456.80** |                  +0.06 |
| c11-d24-s0  |  24 |    0 |    457.294 |       455.66 |                  −1.08 |
| c11-d24-s1  |  24 |    1 |    453.740 |       452.57 |                  −4.18 |

**Headline.** c11-d16-s2 is the new best M2 score on this anchor at
**456.80 test**, up +0.06 from cycle-10 A. Within the +0.10 noise
band — the basin is saturated. See
`results/grid_summary.json` for the 7-cell cross-cycle distribution
and `figures/grid_summary.png` for the visual.

**Conclusion.** The going-in hypothesis (50% chance of ≥ 459) is
falsified. The 7-cell distribution on this anchor has min 448.81,
max 456.80, mean 454.31, std ~3.1. Cycle 12 should pivot to capacity
escalation (ladder/MLP) or fresh-anchor CEM rather than continue
sweeping (dim, seed) cells.
