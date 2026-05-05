# State — current cycle

**Last updated**: 2026-05-05 (cycle 15 — closed)

## Active milestone

**M3 — Generalization study.** M2 closed by cycle 13 with `cycle-11
d16_s2` (challenge test=456.80) as the deliverable. Cycle 14 produced
the first M3 dual-curve plot on val seeds. Cycle 15 (this cycle)
locked the M3 cycle-1 finding by adding a held-out test split,
bootstrap CIs, a 9th anchor (c10B at rng_seed=1), and a retail/arb
PnL decomposition that localizes the early-anchor failure mode.

**Best M2 score (held; reproduced cycle 15): 456.80**
[CI 448.0, 465.7] (cycle-11 d16_s2; held-out 256 seeds, challenge).
**M3 OOD headline: real_data test = +2.574** [+1.98, +3.16] for the
same anchor; lift over FixedFee(0.003) = **+2.10**.

## Cycle-15 verdict (M3 cycle 2)

1. **Early-anchor inversion is statistically significant on
   test.** c5 real_test = -0.744 [-1.27, -0.23] (CI fully below
   FixedFee at 0.470 [-0.08, 1.01]); c6 real_test = -0.933 [-1.47,
   -0.40]. The cycle-14 val finding reproduces robustly on n=256
   unseen seeds.
2. **PnL decomposition localizes failure to retail.** Retail
   edge_advantage swings -9.99 (c5) → +1.06 (c11) — an 11-unit
   monotonic-ish trend. Arb loss_advantage stays in +1.7 to +3.7
   across the whole trajectory and *slightly worsens* with
   challenge optimization. Early M2 is breaking on retail-flow
   pricing, not on arb.
3. **c11 = c13 identity holds OOD on test.** real_test 2.574 =
   2.574, lift 2.104 = 2.104. Third independent recipe-ceiling
   identity check.
4. **c10B (rng_seed=1) replicates the OOD plateau, lower.** real_test
   +1.66 (lift +1.19) vs c10A/c11 ≈ +2.6 (lift +2.10). OOD plateau
   spread across rng seeds ~0.9 lift points, comparable to the
   in-distribution challenge spread.

## Active hypothesis going into cycle 16

> **"The early-anchor harm is concentrated in *specific* trade-size
> buckets / market regimes; if we can identify those, M4 has its
> first concrete inductive-bias target."** Cycle 15's
> retail-vs-arb decomposition tells us *which side* of the PnL is
> broken (retail) but not *which sub-segment of retail*. A
> trade-size decomposition (small/medium/large) and/or a
> regime-conditional decomposition (high-vol vs low-vol regimes)
> would tell us whether the early policy mis-prices a specific
> tail of the distribution or is uniformly off across all retail.
> Output of cycle 16 should be either a more granular PnL table
> or a confirmed M4-launch experiment if cycle 16 reveals the
> failure is uniform.

## Cycle-16 plan-of-record

1. **Extend the dualcurve eval with per-trade-size decomposition.**
   The simulator records `is_buy` and `amount_x`/`amount_y` per
   trade; bucket retail trades by size (small/medium/large per the
   piecewise thresholds at 0.003 and 0.01) and report retail-edge
   per bucket for c5 vs c11. Requires a small evaluator wrapper or
   a TradeInfo-level dump for each batch. ~30 min implement + ~30
   min run.
2. **Pre-launch M4 baseline.** Direct CEM optimization on
   `evaluator_kind="real_data"` with the c5 piecewise default
   anchor and a small budget (pop=12, gen=5) to (a) verify the
   real_data evaluator is CEM-friendly (gradients/scores are not
   too noisy), (b) get a baseline-budget OOD score for M4. ~30
   min.
3. **Retire `bin/checks/10_cycle12_alternatives.py`** if cycle 16
   does not depend on cycle-12 conclusions remaining lit. Currently
   load-bearing; do not retire yet.

## M2 cumulative history (closed; reproduced for context)

| pass | family | dims | init | seed | challenge test | real_data test (lift_FF) |
|--|--|--|--|--|--:|--:|
| start (c5) | piecewise | 16 | inh | — | 414.01 | -0.74 (-1.22) |
| pass 1 (c6) | piecewise | 16 | warm | 0 | 432.75 | -0.93 (-1.40) |
| pass 2 (c8) | inv-aware piecewise | 19 | warm | 0 | 446.44 | -0.28 (-0.75) |
| pass 3 (c9 #1) | piecewise | 16 | warm | 0 | 448.81 | +1.40 (+0.93) |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | warm | 0 | 456.64 | +2.36 (+1.89) |
| pass 5 (c10 A) | piecewise + noop | 20 | warm | 0 | 456.74 | +2.55 (+2.08) |
| pass 6 (c10 B) | piecewise | 16 | warm | 1 | 452.96 | +1.66 (+1.19) |
| pass 7 (c11 d16_s2) | piecewise | 16 | warm | 2 | **456.80** | **+2.57 (+2.10)** |
| pass 8 (c11 d24_s0) | piecewise + noop×8 | 24 | warm | 0 | 455.66 | (not in dualcurve) |
| pass 9 (c11 d24_s1) | piecewise + noop×8 | 24 | warm | 1 | 452.57 | (not in dualcurve) |
| c12 stage 1 | latent_full | 18 | default | 0 | 388.57 | (not OOD-evaluated) |
| c12 stage 2 | piecewise (fresh) | 16 | default+wide | 0 | 418.65 | (not OOD-evaluated) |
| c13 longrun | piecewise | 16 | warm | 0 | 456.80 | +2.57 (+2.10) — same as c11 |

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-14 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh` (vendored wheels make it
  importable on this fresh sandbox after the cycle's setup step).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
  Passes through `--ignore`d list during `pytest -x -q`. Either
  install torch host-side or treat as an acknowledged-skipped suite.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.
  Cycle-1 `checks/04_no_outbound_dns.sh` already encodes this as a
  passing-when-failing predictor.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken on
  this Linux sandbox.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib`. (numpy is
  preinstalled.) jax via `bin/setup_jax_from_vendored.sh`.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate instead of deleting.
- CPU: 4 cores. CEM at pop=24 / dim=16-18 / 3 workers ≈ 125-130 s/gen.
  Two CEMs in parallel saturate (6 procs on 4 cores) — chain them.
- **Long-script gotcha (cycle-13)**: when a long-running script chain
  has a CEM phase + a postprocessing phase, **always checkpoint the
  postprocessing pool to disk before scoring**, or split into two
  scripts.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143. Pattern that
  works: launch via `nohup ... &` once, then poll `progress.log`
  every 8-9 min. Cycle 15 used this pattern for a 37-min eval.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 11 active checks (no addition or retirement
  cycle 15). Carry-forward `08_jax_optional` and `04_no_outbound_dns`
  are passing-when-failing predictors documenting the sandbox
  topology, not work-to-do — keep them.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) untouched per
  convention; cycle-15's only edits were under `research/`.
