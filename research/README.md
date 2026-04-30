# Research Log — `amm-gym-auto-research`

This directory is the working memory of the autonomous research agent that
operates on this repo on a 2-hour cron. The user is rarely present during
runs; treat this README as the first thing a stranger should read.

## What this project is

We have a step-by-step AMM market-making simulator (`amm_gym/`,
`arena_eval/exact_simple_amm/`, `arena_eval/diff_simple_amm/`) and a stack of
candidate fee-setting policies (`arena_policies/`) plus search/training
machinery (`arena_search/`, `training/`). The simulator can run in two
flavors:

- **Challenge mode** — a synthetic GBM price + Poisson/lognormal retail
  flow. Used for the `arena_eval` scoring rule (`score_challenge`,
  default 1000 seeds).
- **Realistic mode** — same engine but with a **regime-switching** price
  return process fitted from Binance ETHUSDT order-book data, and an
  **empirical retail price-impact** distribution fitted from on-chain
  Uniswap v3 router swaps. The empirical artifacts live under
  `analysis/weth_usdc_90d/`.

The four research milestones (see `AUTORESEARCH_PROMPT.md`) are:

1. **M1** — validate the realistic simulator's markout against on-chain
   reality (`uniswap-labs.research.markout_prod`).
2. **M2** — train a policy on the differentiable simple-AMM challenge
   target. Goal: score > 540.
3. **M3** — generalization study: same policy, train on simple, eval on
   realistic, plot both curves.
4. **M4** — directly optimize against realistic; sweep policy complexity
   and find the realistic-score / complexity Pareto.

## Where things live

| Path | Purpose |
| --- | --- |
| `research/STATE.md` | Current milestone, current sub-task, next action, blockers. **Read this first each cycle.** |
| `research/LOG.md` | Append-only chronological cycle log (one entry per run). |
| `research/notes/` | Durable reference notes (data sources, scoring rule, parameter glossaries). |
| `research/experiments/<YYYY-MM-DD-HHMM-slug>/` | One directory per experiment. Each has its own `README.md`. |
| `research/presentation/` | The cumulative narrative artifact a stranger reads end-to-end. Updated whenever a milestone-relevant figure lands. |

## Lay of the land (cycle 1 survey)

**`amm_gym/`** — Gymnasium-compatible env wrapping the simulator. Default
6-D ladder action; the trainer-facing contract is in
`docs/env_training_contract.md`. The simulator (`amm_gym/sim/engine.py`)
handles a submission venue + a benchmark/normalizer venue, with retail
routing and an arb actor pulling each venue toward fair price every step.
Currently uses `GBMPriceProcess`; `RegimeSwitchingReturnProcess` is the
realistic price plug-in slated to be wired in (see
`analysis/weth_usdc_90d/REGIME_EXTRACTION.md` §5).

**`arena_eval/exact_simple_amm/`** — the *faithful* simple-AMM evaluator
used for both the `challenge` and `real_data` scoring kinds (selected
through `ExactSimpleAMMConfig.evaluator_kind`). 10,000 12-second steps per
episode (≈33 hours wall-clock). Score = mean `edge_submission` across
seeds (default 1000 seeds in `score_challenge`).

**`arena_eval/diff_simple_amm/`** — the *differentiable* re-write of the
same simulator. Two tape generators
(`build_challenge_tape`, `build_realistic_tape`) materialize the
exogenous randomness once so the rest of the rollout is deterministic and
differentiable. `tape_smooth.py` (1300+ LOC) implements the smoothed
relaxation used for gradient-based search via PyTorch-style autodiff.
There is a parity test stack to keep diff and exact in lockstep
(`tests/test_diff_simple_amm_*`).

**`arena_eval/core/types.py`** — shared `SimulationResult` /
`BatchResult` dataclasses with markout helpers
(`retail_markout_bps_submission`, `arb_markout_bps_submission`).

**`arena_policies/`** — parameter-light policy families:
`piecewise_controller`, `latent_ladder`, `belief_state_controller`,
`reactive_controller`, `inventory_toxicity`, `submission_safe`,
`retail_recapture`. These plug into `arena_search/`.

**`arena_search/`** — random/CMA-style search loops
(`simple_amm_search.py`, `diff_simple_amm_search.py`). Driver scripts in
`scripts/run_simple_amm_search.py`, `scripts/run_exact_search.py`, etc.

**`training/`** — RL/learner stack (CEM in `algorithms/cem.py`, PPO in
`algorithms/ppo.py`, baseline runner in `run_baseline.py`,
`run_first_pass.py`, `run_ppo.py`). Policy families: `linear`,
`heuristic`, `mlp`. Eval helpers in `eval/`.

## Current milestone

See `research/STATE.md`. As of cycle 1: bootstrapping; M1 plan sketched.
