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

See `research/STATE.md`. As of cycle 27: M1 closed (cycle 5); **M2
closed (cycle 13)** with deliverable challenge test = **456.80**
(piecewise warm-start CEM, cycle-11 d16_s2 cell, ~85% of way to 540
target). **M3 closed (cycle 16)** with the per-trade-size mechanism
(c5↔c11 retail-edge gap is ~95% small-bucket; mechanism is a two-AMM
router collapse — c5 captures only ~13% of small-trade count vs c11's
~57%). **M4 active (cycle 11 closed)**.

**M4 frontier on real_data (held since cycle 26).** Long-CEM 4-bucket
ladder on the cycle-18-seed-0 ("c18-s0") piecewise anchor, n=3 across
cycles 25+26: mean test **+3.747**, lift_FF **+3.277 ± 0.027**, lift
over the same-anchor piecewise **+0.271 ± 0.027**. The c18-s0 cluster
is both higher and 2.5× tighter than the c21-s1 cluster (cycles 23+24,
lift_FF +3.034 ± 0.066). Single-seed best on real_data: cycle-26
rng_seed=2 on c18-s0, test **+3.777**, lift_FF **+3.307**.

**Cycle 27 result.** Tested whether a structurally richer family
(5-bucket ladder; 22-d, splitting the 4-bucket's `tiny` bucket into
`ultra_tiny + tiny`) at the same anchor and CEM budget could move the
frontier. **It cannot.** n=2 mean lift_FF **+3.093 ± 0.123**, lift
over piecewise **+0.087 ± 0.123** — both seeds below the +3.28
frontier-move threshold; n=2 mean −0.184 below the 4-bucket cluster.
Mechanism: the 22-d search space is starved at the cycle-26 CEM
budget (init_std_new=0.15) — 4-bucket elite-mean exceeds anchor by
gen 2; 5-bucket elite-mean does not until gen 4 (one seed) or never
(the other, which rerank-picks the anchor for lift = 0).

**Cycle-28 plan-of-record**: 5-bucket at lower init_std_new=0.05 on
c18-s0 multi-seed (same CEM budget; tests whether the cycle-27
underperformance is compute-bounded or family-bounded). A more
expensive alternative is 5-bucket at 15g × 24p (1.5× compute);
hold for cycle 29 if the init_std variant doesn't help. Stretch: 4th
c18-s0 long-CEM 4-bucket seed to tighten the cluster from n=3 to n=4.

The cumulative narrative is in `research/presentation/index.html`.
