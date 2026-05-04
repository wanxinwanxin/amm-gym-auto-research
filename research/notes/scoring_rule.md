# AMM Challenge Scoring Rule

The M2 milestone targets `score > 540` on the AMM-challenge scoring rule.
This note documents exactly what that score is and where it comes from
in the codebase, so M2 evaluations are unambiguous.

## Definition

The scoring function is
`arena_eval.exact_simple_amm.simulator.score_challenge`:

```python
def score_challenge(
    submission_strategy_factory,
    *,
    n_simulations: int = 1000,
    evaluator_kind: str = "challenge",
    submission_liquidity_fraction: float | None = None,
) -> float:
    batch = run_batch(
        submission_strategy_factory,
        range(n_simulations),
        evaluator_kind=evaluator_kind,
        submission_liquidity_fraction=submission_liquidity_fraction,
    )
    return batch.score
```

The returned score is the **mean of `edge_submission` across
`n_simulations=1000` seeds** with a default `range(1000)` seed list.

### `edge_submission` — what it actually accumulates

Defined per simulation in
`arena_eval/exact_simple_amm/simulator.py::Simulation` (lines ~543, 660–745):

1. `edge_submission` starts at `0.0`.
2. Every step, the arbitrageur runs against the **submission** venue. If
   it executes, the arb's profit is **subtracted** from
   `edge_submission` (LP losing to arb).
3. Every step, the retail trader generates orders and the router routes
   them to the venue with the better effective price. Trades that land
   on the submission venue add a `trade_edge` to `edge_submission`,
   defined as

   ```python
   trade_edge = (
       trade.amount_x * fair_price - trade.amount_y
       if trade.amm_buys_x  # retail sold X to LP at the LP's bid
       else trade.amount_y - trade.amount_x * fair_price
   )
   ```

   That is, the difference between the LP's fill notional and the
   fair-price-priced inventory the LP ended up holding (in token-Y
   units). Positive = LP earned its quoted spread on top of fair value.
4. Per-simulation `score = edge_submission` (set in `result()`,
   line ~799).
5. Batch score = `mean(sim.score for sim in simulations)` (line ~867).

The score is in **token-Y units** (USDC for the canonical pool). The
default `step_seconds = 12.0` and `n_steps = 10_000` mean each episode
covers ~33.3 hours of simulated wall-clock time.

### Adversary venue ("normalizer")

`run_batch` always pairs the submission strategy against a normalizer
strategy (default in `scripts/run_exact_search.py`:
`FixedFeeStrategy(0.003, 0.003)` at 30 bps). The submission and
normalizer venues compete for retail flow via `OrderRouter`, which
sends each order to whichever venue gives the trader a better price.

`edge_advantage = edge_submission − edge_normalizer` is reported as a
diagnostic but is **not** the scored quantity. The scored quantity is
`edge_submission` alone — i.e. the goal is to maximize LP edge on
**this** venue without (directly) penalizing what the other venue does.
A policy that simply quotes a less-bad spread than 30 bps can pull
retail flow and score positively.

### Evaluator backends

`evaluator_kind` selects the dynamics:

* `"challenge"` (default, used for M2) — synthetic GBM price (`gbm_mu`,
  `gbm_sigma` configured in `ExactSimpleAMMConfig`) with Poisson
  retail arrivals (lognormal sizes).
* `"real_data"` — regime-switching log-return process fitted from
  Binance ETHUSDT (see `data_sources.md` §2) with empirical retail
  price-impact distribution (§3). Used for M1 / M3 / M4.

The challenge target threshold (>540) refers specifically to
`evaluator_kind="challenge"`.

## Reference scores — inherited baselines

These are best-test scores on `evaluator_kind="challenge"` from
`experiments/*_cem_1h_*.json` runs that landed before M2 began. Test
seed range `2000:2256` (256 seeds), search seeds `0:64`, validation
seeds `1000:1128`. CEM with 8–14 generations × 22–24 population.

| policy family       | best_test | source file |
| ------------------- | --------: | ----------- |
| `piecewise`         |   414.010 | `piecewise_cem_1h_20260422.json` |
| `submission_compact`|   410.776 | `submission_compact_cem_1h_20260423_rebatch1.json` |
| `exact_search`      |   404.908 | `exact_search_cem_1h_20260421.json` (default reactive) |
| `latent_full`       |   389.611 | `latent_full_cem_1h_20260423_rebatch1.json` |
| `submission_regime` |   387.407 | `submission_regime_cem_1h_20260423_rebatch1.json` |
| `inventory_toxicity`|   379.868 | `inventory_toxicity_cem_1h_20260422.json` |
| `submission_basis`  |   380.262 | `submission_basis_cem_1h_20260423_rebatch1.json` |
| `belief_state`      |   377.117 | `belief_state_cem_1h_20260422.json` |

For comparison, the trivial baselines (also from
`experiments/structured_retail_oracle_full_0_999.json`):

| controller | score | what it is |
| ---------- | ----: | ---------- |
| `fixed_fee` (30 bps) | 343.45 | trivial constant-fee, n=1000 |
| `structured_retail_oracle` | 586.51 | clairvoyant: sees the retail order before quoting |

So the **>540 target sits between the best inherited learnable policy
(414) and the clairvoyant oracle (586.5)**. It is *achievable in
principle* (the oracle clears it) but no learnable policy in the repo
has crossed it yet — closing that ~130-point gap is what M2 has to do.

### Implication for M2 strategy

- Cycle 5 starting line: best inherited learnable score ≈ **414**, gap
  to target ≈ **126**.
- The richer policy families (`piecewise`, `submission_compact`) sit
  near the top, so escalating capacity isn't obviously the missing
  ingredient. The oracle's gap to `piecewise` (172 pts) suggests the
  controllers are mostly leaving on the table the *signal* the oracle
  uses — i.e. retail arrival foreknowledge / better mid prediction.
- Three plausible attack angles, in rough order of expected value:
  1. **Better optimization** on existing `piecewise` /
     `submission_compact` (CEM with more generations, gradient via
     `tape_smooth`, hybrid CEM-then-gradient). Cheap to try.
  2. **Inventory-aware** action shaping — none of the inherited
     policies look strongly inventory-driven and the oracle's
     `pnl_advantage` is much larger than its `edge_advantage`,
     suggesting inventory matters.
  3. **Higher-capacity** policy (MLP via `training/`) once we've
     established that simpler policies plateau. Spend compute here last.

## Configuration constants

From `arena_eval/exact_simple_amm/config.py` (canonical
`ExactSimpleAMMConfig` at construction time):

* `n_steps = 10_000`, `step_seconds = 12.0` → 33.3 simulated hours
  per seed.
* `submission_initial_x = 100.0`, `submission_initial_y = 200_000.0`
  (init mid = $2,000).
* `normalizer_initial_x`, `normalizer_initial_y` similarly; default
  fee 30 bps each side.
* `submission_liquidity_fraction` lets the submission pool start
  smaller than the normalizer for capacity-sensitive sweeps; default
  1.0 (parity).

## Reproducibility checklist

When reporting an M2 score:

1. Use `score_challenge(strategy_factory, n_simulations=1000)` — never
   change `n_simulations` for the headline number.
2. `evaluator_kind="challenge"`, default seeds `range(1000)`. Use
   held-out seeds (e.g. `range(2000, 2256)` mirroring the inherited
   reports' test set) when the eval feeds into M3/M4 conclusions.
3. Pair against `FixedFeeStrategy(0.003, 0.003)` as the normalizer
   unless the comparison being made requires otherwise.
4. Quote the score in token-Y (USDC) units to 1 decimal place.
