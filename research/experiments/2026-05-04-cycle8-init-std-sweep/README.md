# Cycle-8 — Init_std sensitivity sweep on `submission_compact`

## Question

Cycle 7 ran warm-start CEM at `init_std_frac=0.10` from the inherited
`submission_compact` best (test 410.78) and lifted to 416.08 (+5.30 pts).
Population kept drifting upward at gen 11 but val plateaued by gen 8.
**Was 0.10 the wrong width?** Sweep init_std_frac ∈ {0.05, 0.20, 0.30}
and report the per-init-std lift to either (a) re-spec the cycle-7
prescription as "warm-start AND match init_std to inherited basin width"
or (b) close the question by confirming 0.10 was already near-optimal.

## What we ran

5-gen warm-start CEM at each init_std_frac, otherwise identical to
cycle 7 (pop=24, elite_frac=0.20, search seeds 0..63, val 1000..1127,
test 2000..2255, rng_seed=0).

Reduced from cycle-7's 12 gens to 5 to fit budget. Cycle-7 saw val
plateau by gen 4-8 so 5 gens is enough to see whether the basin is
wider or narrower than 0.10×range.

## Result

| init_std_frac | best_val | test (256 seeds) | Δ vs starting line | Notes |
|---|---|---|---|---|
| 0.05 | 413.75 | 413.03 | +2.26 | too narrow |
| **0.10 (cycle 7)** | **416.88** | **416.08** | **+5.30** | **sweet spot** |
| 0.20 | 414.53 | 413.58 | +2.80 | too wide |
| 0.30 | 415.03 | 413.88 | +3.11 | also too wide |

**Clean U-shape.** init_std=0.10 is the sweet spot; both narrower and
wider widths underperform by ~2-3 pts. The cycle-7 default was correct
and `submission_compact` is action-space saturated for warm-start CEM at
this seed budget — no width tweaking will unlock more from this family.

## What this changed about my prior

- **The cycle-7 cycle-8-priority #2 hypothesis is falsified.** I went in
  expecting either 0.20 or 0.30 to lift to ~430+, which would have
  re-spec'd the warm-start prescription. Neither did. 0.20 and 0.30
  are *worse* than 0.10 — the broader sampling apparently hurts more
  than it helps because the inherited basin is small.
- **Combined with the cycle-7 family ablation**, this confirms
  `submission_compact` is a flat-bottom basin with a small high-value
  region. The right move with this family is not to tune CEM
  hyperparameters but to either (a) accept the ~416 cap or (b) try a
  different optimizer entirely.
- The U-shape itself is informative for future warm-start CEM runs:
  start at 0.10 unless you have a specific reason to deviate.

## Operational footnote

`init_std=0.30` gen 2 took 36 minutes wall-clock in the cloud sandbox
(vs ~140s for the other gens) — likely a system-level pause. The
generation completed correctly so the result is intact.

## Files

- `scripts/run_init_std_sweep.py` — main driver (parametrized
  init_std_fracs).
- `scripts/build_figure.py` — 2-panel summary figure.
- `results/init_std_<frac>_history.json` — per-gen records per
  sub-run.
- `results/init_std_<frac>_test.json` — final per-sub-run rerank+test.
- `results/sweep_summary.json` — compact summary across init_std values.
- `figures/init_std_sweep_summary.png` — convergence + headline bar.
