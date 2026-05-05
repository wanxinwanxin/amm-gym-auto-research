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

See `research/STATE.md`. As of cycle 25: M1 closed (cycle 5); **M2
closed (cycle 13)** with deliverable challenge test = **456.80**
(piecewise warm-start CEM, cycle-11 d16_s2 cell, ~85% of way to 540
target). **M3 closed (cycle 16)** with the per-trade-size mechanism
(c5↔c11 retail-edge gap is ~95% small-bucket; mechanism is a two-AMM
router collapse — c5 captures only ~13% of small-trade count vs c11's
~57%). **M4 active (cycle 9 closed)**.

**M4 long-CEM ladder update (cycle 25).** Cycle 25 ran the cycle-24
plan-of-record: (Q1) second rng_seed of long-CEM ladder on the c21-s2
(basin-collapsed) anchor; (Q2) single-seed long-CEM ladder probe on the
cycle-18-seed-0 anchor (the strongest piecewise basin, lift_FF +3.006).
**Result on Q1: c21-s2 second seed COLLAPSED.** CEM trajectory bottomed
out at elite-mean +1.21, all non-anchor val scores ≥1.4 below the anchor,
rerank picked the anchor itself, lift over piecewise = **+0.000**. The
c21-s2 n=2 mean is now **+0.273 ± 0.387** (error bar contains zero);
the cycle-24 single-seed +0.547 was a positive tail draw, not a stable
stabilizer signature. **Result on Q2:** c18-s0 anchor lifted **+0.250**
over piecewise (test **+3.727**, lift_FF +3.256, retail_adv +3.541) —
*higher* than the c21-s1 n=3 mean lift (+0.134), so the proposed
inverse-scaling line ("ladder lift drops as piecewise quality climbs")
is rejected. The 3-anchor curve (c21-s2 +0.27, c21-s1 +0.13, c18-s0
+0.25) is non-monotone. **The cycle-25 c18-s0 single-seed test +3.727
is the highest single-seed real_data score on record** (n=1, supporting
evidence). Aggregating all 6 long-CEM ladder seeds across 3 anchors:
mean lift over piecewise +0.200 ± 0.192 — small, positive on average,
but high-variance per seed. Long-CEM is bimodal: 5/6 in "search-find"
(non-anchor val beats anchor by ≥+0.10), 1/6 in "search-collapse"
(non-anchor val trails anchor by ≥+0.50). Empty dead zone in between.

**Cycle-26 plan-of-record**: (i) two more rng_seeds on c18-s0 long-CEM
ladder to upgrade the c18-s0 anchor from n=1 to n=3 — the cleanest
single experiment for moving the M4 frontier to a new anchor cluster;
(ii) stretch: structurally richer family at long-CEM on c21-s1,
multi-seed (cycle-24's plan-of-record direction).

The cumulative narrative is in `research/presentation/index.html`.
