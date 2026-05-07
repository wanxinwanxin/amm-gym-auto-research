# Cycle 29 — M4 / 5-bucket ladder long-CEM at 15g × 24p compute

**Date.** 2026-05-07.

**Milestone / sub-task.** M4 — does the 5-bucket-tight family
catch up to the 4-bucket cluster on the c18-s0 anchor at higher
CEM compute?

## Question

Cycle 28 ran 5-bucket-tight ladder long-CEM on c18-s0 at 10g × 24p
compute and produced cluster mean lift_FF +3.253 ± 0.009 (n=2),
−0.024 below the cycle-26 4-bucket cluster mean +3.277 ± 0.027.
The gap is within ~0.9σ of the 4-bucket cluster — statistically
indistinguishable on n=2 vs n=3 — but the cycle-28 elite-mean
trajectory was still slowly rising at gen 9 (gen 7→8→9 deltas of
+0.010, +0.008 on seed 0). Compute-limited, not converged.

Going-in hypothesis:

> "At init_std_new=0.05, the 5-bucket family is variance-matched
> to the 4-bucket family on c18-s0 long-CEM. The remaining
> −0.024 cluster-mean gap is compute-bounded: at 15g × 24p budget
> (1.5× compute), the 5-bucket-tight cluster will close the gap
> or exceed the 4-bucket cluster on c18-s0."

## Method

Identical to cycle-28 driver except `GENERATIONS = 15` (was 10).
- Warm-start: c18-s0 piecewise anchor → 22-d 5-bucket via the
  identity-equivalent split-small-bucket map (`continuation_small`,
  `reversal_small` shared across `ultra_tiny_*`, `tiny_*`, `small_*`;
  thresholds split at 0.25× and 0.5× of small_threshold).
- CEM: pop=24, gen=15, elite_frac=0.2, anchor included in the
  first generation.
- Init std: `init_std_frac_new = init_std_frac_inh = 0.05` (fraction
  of each dim's full bound range).
- Normalizer: FixedFee(0.003, 0.003).
- Evaluator: real_data; 64 search seeds, 128 val (seeds 1000–1127),
  256 test (seeds 2000–2255).
- Rerank: anchor + top-6 unique elites by search val score; pick by
  val score (real_data 128).
- Anchor: `cycle18_seed0`. Two RNG seeds in parallel: 0 and 1.

## Decision rule

Cycle-26 4-bucket cluster mean +3.277 ± 0.027 is the M4 frontier.
For n=2 5-bucket-tight at 15g × 24p:

- **Lift frontier:** Both seeds > +3.20 AND cluster mean lift_FF
  > +3.28 → 15g compute lifts the 5-bucket cluster onto/past
  the 4-bucket frontier; cycle 30 confirms with n=3 and the M4
  frontier moves to the 5-bucket family.
- **Reject compute hypothesis:** At least one seed < +3.20 → the
  4-bucket family is the c18-s0 ceiling at long-CEM; the M4
  headline locks at +3.277 ± 0.027.
- **Modest gain, ambiguous:** Both seeds in [+3.20, +3.28], cluster
  mean in (+3.253, +3.28) → modest compute gain but family ceiling
  still open; stretch with n=3 in cycle 30.

## Layout

- `scripts/run_ladder5_15gx24p.py` — main driver. Forks one CEM
  trajectory per `RNG_SEED` env var, persists `progress.log`,
  `history.json`, `test.json` under `results/{anchor_key}_seed{N}/`.
- `scripts/ladder5_strategy.py` — the 22-d 5-bucket controller
  (copy of the cycle-27/28 file; identical normalizer behaviour,
  pre-split thresholds via `normalized()`).
- `results/{anchor_key}_seed{N}/` — per-seed outputs.
- `results/seed{N}_stdout.log` — captured stdout/stderr from the
  background launch.

## Reproduce

```bash
cd "$(git rev-parse --show-toplevel)"

ANCHOR_KEY=cycle18_seed0 RNG_SEED=0 MAX_WORKERS=2 \
  python3 research/experiments/2026-05-07-cycle29-m4-5bucket-15gx24p/scripts/run_ladder5_15gx24p.py

ANCHOR_KEY=cycle18_seed0 RNG_SEED=1 MAX_WORKERS=2 \
  python3 research/experiments/2026-05-07-cycle29-m4-5bucket-15gx24p/scripts/run_ladder5_15gx24p.py
```

## Cycle-budget note

10g × 24p in cycle 28 took ~6000s (100min) per seed, two seeds
in parallel. 15g × 24p ≈ 1.5× = ~9000s ≈ 150 min — likely over
the 2-hour cycle budget. The runner persists `history.json` after
every generation and is therefore resumable in spirit (cycle 30
can re-extract reranks from a partial trajectory if the run is
killed mid-rerank). Test+rerank only takes ~5 min and only runs
at the very end.

## Status

Run launched 2026-05-07. Results pending.
