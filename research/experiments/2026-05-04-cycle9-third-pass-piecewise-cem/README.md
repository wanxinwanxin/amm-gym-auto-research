# Cycle-9 #1 — Third-pass warm-start CEM on bare piecewise (M2)

## Question

Was cycle 8's lift the asymptote, or just another waypoint? Cycle 6
took bare piecewise from a cycle-5 starting line of 414 to 432.7 with
a single 12-gen warm-start CEM pass. Cycle 8's "inventory-aware" CEM
(falsified by the inv-skew ablation) was effectively a *second* pass
of warm-start CEM on bare piecewise that lifted 432.7 → 446.6. A
third pass tells us whether successive warm-start passes keep paying
off, or two passes is enough.

## Setup

Identical recipe to cycles 6 and 8:

- **Policy family**: `piecewise` (16 dims).
- **Anchor**: cycle-8 ablation params (the 16 piecewise dims of the
  cycle-8 inv-aware best, with the 3 inv-skew params zeroed out).
  Search-seed score at anchor: 441.53. Test-seed (256 seeds) score:
  446.61.
- **Population**: 24, **generations**: 12, **elite frac**: 0.20,
  **init_std_frac**: 0.10.
- **Search seeds**: 0..63 (64 seeds). **Val seeds**: 1000..1127
  (128 seeds). **Test seeds**: 2000..2255 (256 seeds).
- **Driver**: `scripts/run_third_pass_cem.py`. Anchor parity check at
  startup confirms the 16-dim piecewise instantiation matches the
  cycle-8 ablation score exactly on the search seeds.

## Hypothesis

Prior: ~50/50 a third pass adds another +3-7 pts on test before
piecewise's 16-dim basin is truly converged. If Δ test ≥ +3, two
passes was a waypoint and there's still juice left. If Δ test ≤ +1,
cycle 8 was the basin floor and we need a richer policy class.

## Result

(populated by `scripts/build_figure.py` once the run completes; see
`results/third_pass_cem_test.json` for the headline number)

## Files

- `scripts/run_third_pass_cem.py` — driver
- `scripts/build_figure.py` — three-pass convergence chart
- `results/third_pass_cem_history.json` — per-generation history (best,
  elite mean, val, mean/std)
- `results/third_pass_cem_test.json` — final reranked best + test score
- `results/third_pass_cem_progress.log` — human-readable log
- `figures/three_pass_convergence.png` — cycles 6 + 8 + 9 val curves
  laid end-to-end
