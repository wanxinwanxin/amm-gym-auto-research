# Cycle-9 #3 — EMA-inventory piecewise warm-start CEM (M2)

## Question

Cycle 8 falsified the *instantaneous* inventory-skew hypothesis — the
3 inv-skew params zeroed out without touching the score (Δ = -0.17).
But cycles 6-8 only tried one formulation. Maybe ChallengeTape one-
sided flow is too intermittent for instantaneous skew to do anything;
a slow EMA over reserve deviation might pick up *sustained* directional
pressure where the instantaneous version can't.

This is the "one more cheap shot at inventory before declaring the
dimension dead" experiment from cycle 8's planned next-steps.

## Setup

- **Policy family**: `ema_inventory_piecewise` (new, 20 dims). Adds
  4 params on top of the 16 piecewise core: `inventory_ema_decay`,
  `inventory_skew_to_bid`, `inventory_skew_to_ask`,
  `inventory_skew_dead_zone`.
- **State**: tracks `imbalance_ema` updated on every trade as
  `decay * prior_ema + (1 - decay) * raw_imbalance`. Soft-hinge dead
  zone applied to the EMA, not the raw.
- **Anchor**: cycle-8 ablation params + `inventory_ema_decay = 0.5`
  + skews zeroed. By construction the anchor score equals the bare
  piecewise score (parity check confirmed in `tests/test_ema_inventory_piecewise.py`).
- **Recipe**: pop=24, gen=12, init_std_frac=0.10, elite=0.20.
  search 0..63, val 1000..1127, test 2000..2255 (matches cycles 6-8).
- **Driver**: `scripts/run_ema_inventory_cem.py`.

## Hypothesis

Prior: ~30% chance EMA inventory contributes ≥ +2 pts on test relative
to a no-skew baseline. The cycle-8 ablation was strong evidence the
dimension is dead in the instantaneous form, and EMA is just a smoothed
variant of the same signal — the bigger question is whether ChallengeTape
generates enough sustained directional flow at any horizon for inventory
skew to be informative. If Δ ≥ +2 on test (with the search converging on
non-zero skew weights), the dimension is alive and worth a follow-up;
if Δ ≤ +0.5 *or* the search converges on zero-skew, the dimension is
genuinely dead and we should turn to richer policy classes (MLP, ladder).

## Result

(populated once the run completes; see `results/ema_inventory_cem_test.json`)

## Files

- `scripts/run_ema_inventory_cem.py` — driver
- `results/ema_inventory_cem_history.json` — per-gen history (best,
  elite-mean, val, EMA-decay/skews running mean)
- `results/ema_inventory_cem_test.json` — final reranked best + test
- `results/ema_inventory_cem_progress.log` — human-readable log
