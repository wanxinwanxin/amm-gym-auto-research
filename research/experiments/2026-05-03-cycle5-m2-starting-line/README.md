# 2026-05-03 cycle 5 — M2 starting line

## Question

Before launching M2 (target: `score_challenge > 540`), what's the
starting line we need to beat? Specifically:

1. What does a trivial fixed-fee strategy get us on the challenge
   evaluator?
2. Does the inherited best-learnable baseline (piecewise CEM,
   `experiments/piecewise_cem_1h_20260422.json`) actually reproduce
   when re-run from its saved params?

## Setup

* Evaluator: `evaluator_kind="challenge"` (synthetic GBM + Poisson).
* Test seeds: `range(2000, 2256)` (held-out, matches the inherited
  report's `test_seeds`).
* Normalizer venue: `FixedFeeStrategy(0.003, 0.003)` (30 bps, default).
* Per-seed runtime: ~0.05–22 s (varies sharply with fee — lower fees
  trigger more retail flow / arb trades and run slower).
* Total wall: ~3 h on the sandbox (single-process). The cycle ran over
  the 2-hour budget; the 1-bps and 5-bps fixed-fee runs were the
  long tail.

## Results

### Fixed-fee sweep (256 seeds, challenge evaluator, normalizer = 30 bps)

| fee | score    | edge_advantage | notes |
| --: | -------: | -------------: | ----- |
|   1 bps |   -0.516 |   -206.04 | LP loses to arb at this spread |
|   3 bps |   40.083 |   -171.25 |
|   5 bps |   77.249 |   -140.24 |
|  10 bps |  158.759 |    -75.60 |
|  30 bps |  342.826 |     +0.00 | parity with normalizer |
| 100 bps |  373.724 |   -192.97 | best fixed-fee; loses share but earns more per trade |

Source: `results/fixed_fee_sweep.json`.

The 100-bps fixed-fee scores higher than 30-bps because the wider
spread defends better against the in-sim arbitrageur even though it
sacrifices market share to the 30-bps normalizer (negative
`edge_advantage`). Headline fixed-fee floor for M2 framing: **343
(30 bps)**.

### Inherited piecewise CEM — replicate

Re-running the saved parameters from
`experiments/piecewise_cem_1h_20260422.json::best_validation` on the
held-out test seeds 2000:2256:

* `score = 414.010` — matches the inherited `best_test = 414.010`
  to 3 decimal places. Reproducibility is clean; the seed RNG and
  evaluator pipeline are deterministic in the parameters.
* `edge_advantage_mean = -69.26` — piecewise loses ~69 of edge
  to the normalizer venue's flow, but earns more per trade than fixed
  fee can.

Source: `results/piecewise_replicate.json`.

### Cycle-5 starting line

| baseline                                  | score   |
| ----------------------------------------- | ------: |
| trivial floor (fixed_fee 30 bps)          |  342.83 |
| best fixed-fee (100 bps)                  |  373.72 |
| **inherited best learnable (piecewise CEM)** |  **414.01** |
| target (M2 milestone)                     |  540.00 |
| structured-retail clairvoyant oracle\*    |  586.51 |

\* From `experiments/structured_retail_oracle_full_0_999.json` on
seed range 0..999. Different seed range, but the magnitude (~586)
sets the upper-bound reference. The oracle has access to the
**structured retail signal** before quoting; it's the ceiling a
*non-clairvoyant* policy is approximating.

**Gap to target: 540 − 414 = 126 points.**

## Implications for M2

1. The clairvoyant oracle proves the target is achievable in
   principle on this evaluator (586.5 > 540), so M2 isn't asking for
   the impossible — it's asking for ~73 % of the oracle's edge from
   a learnable policy.
2. The inherited best already uses the richest piecewise family in
   the search; the gap is unlikely to close from policy capacity
   alone. Three angles ranked by expected value:
   - Better optimization on the same family (more CEM generations,
     gradient via `tape_smooth`, hybrid).
   - Inventory-aware shaping (none of the inherited families lean
     hard on inventory; the oracle's `pnl_advantage` is much larger
     than its `edge_advantage`, suggesting inventory leak matters).
   - Higher-capacity (MLP) policies via `training/`.
3. The fixed-fee curve is informative for sanity-checking new
   policies: any policy that scores below 343 on this evaluator with
   a 30-bps normalizer is doing strictly worse than constant 30 bps
   and has a bug.

## Files

* `scripts/run_starting_line.py` — runner; takes ~3 h on a
  single sandbox process.
* `results/fixed_fee_sweep.json` — per-fee metrics.
* `results/piecewise_replicate.json` — replicate of the inherited
  best.
* `results/starting_line.json` — combined summary.
* `figures/m2_starting_line.png` — bar chart of the starting line
  vs the M2 target and oracle ceiling.
