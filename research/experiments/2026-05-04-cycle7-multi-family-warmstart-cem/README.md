# Cycle 7 — multi-family warm-start CEM (M2)

## Question

Cycle 6 ran a warm-start CEM (24 candidates × 12 generations × 64 search
seeds, init_std = 0.10 × range, mean = inherited best) on the
`piecewise` policy and lifted the held-out test score 414.0 → 432.7
(+18.7 pts). Was that lift specific to the piecewise action space, or
were *all* of the inherited 14×22 CEM runs across policy families
under-converged — in which case a warm-start CEM on every family
should yield a similar lift?

This cycle answers that for the next two highest inherited families:
`submission_compact` (inherited test 410.78) and `submission_basis`
(inherited test 380.26).

## Method

Generic warm-start CEM driver: `scripts/run_warmstart_cem.py
--family <piecewise|submission_compact|submission_basis>`. Pulls the
inherited best-by-validation params from
`experiments/<family>_cem_1h_20260423_rebatch1.json` (or the cycle-5
piecewise pin) and runs CEM with:

- population: 24 (one fixed at the anchor mean per generation)
- generations: 12
- elite fraction: 0.2 (elite_n = 4)
- init_std: 0.10 × (high − low) per dimension
- search seeds: range(0, 64)
- per-gen validation seeds: range(1000, 1128)
- final held-out test seeds: range(2000, 2256)
- ProcessPoolExecutor: 3 workers (3 of 4 cores)
- normalizer: FixedFee(0.003, 0.003), evaluator_kind: "challenge"

Final reporting: rerank top-8 unique elites on the fixed val set, take
the val-best, score it on held-out test seeds. Same protocol as
cycle 6.

## Variants

- `submission_compact` (rng_seed=0) — primary test of the
  family-agnostic hypothesis.
- `submission_basis` (rng_seed=0) — second test, larger param dim
  (32) so the per-gen exploration is shallower per dimension.
- (Stretch) `piecewise` (rng_seed=1) — sanity-check that cycle-6's
  +18.7 pt lift isn't a single-rng-seed artifact.

## Outputs

- `results/warmstart_cem_<family>_progress.log` — streaming per-gen
  log.
- `results/warmstart_cem_<family>_history.json` — per-generation
  best/elite scores, val score, post-update mean/std.
- `results/warmstart_cem_<family>_test.json` — final val/test
  scores, top-8 rerank ladder, deltas vs the inherited starting
  line.

## Falsification

The cycle-7 hypothesis is *family-agnostic warm-start CEM uplift*. We
compare each family's `delta_vs_starting_line` to cycle 6's
piecewise +18.7. Concretely:

- If both `submission_compact` and `submission_basis` lift by
  ≈+15-22 pts, the hypothesis holds: the inherited 14-gen CEM was
  systematically under-converged across families and warm-start
  refinement is the cheap optimization win.
- If one family lifts much more (>+30) and the other much less
  (<+5), the lift depends on the action space's geometry, not just
  optimizer convergence — and we should commit to the
  bigger-lifting family for cycle 8.
- If neither family lifts more than ~5 pts, piecewise's lift was
  *family-specific* and we should ask why piecewise's challenge
  surface is uniquely amenable to warm-start CEM.

## Notes

- The host `.venv` is Mac-only; on the Linux sandbox install
  `gymnasium`, `pyarrow`, `jax[cpu]` into system python via
  `pip install --break-system-packages`.
- `git pull` to github.com is blocked from inside the sandbox;
  the host launchd agent ships local commits to `origin/main`.
- Sandbox cannot `unlink` files in the results dir; the script
  truncates progress logs by opening them in write mode rather
  than calling `Path.unlink`.
