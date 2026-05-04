# State — current cycle

**Last updated**: 2026-05-05 (cycle 14 — closed)

## Active milestone

**M3 — Generalization study.** M2 closed by cycle 13 with
`cycle-11 d16_s2` (test=456.80) as the deliverable; cycle 14 ran the
M3 cycle-1 dual-curve eval and produced the first OOD generalization
plot.

**Best M2 score (held): 456.80** (cycle-11 d16_s2; held-out 256
seeds). M2 reopens only on a *recipe-shape* change (different
init_std / pop / hybrid CEM→PPO / different normalizer venue).

## Cycle-13 verdict (M2 closure)

Long-run warm-start CEM (gen=24) on the cycle-11 d16_s2 anchor:
  - **test = 456.803, Δ vs champion = +0.000**
  - Best-by-val came from **gen 0 (the anchor itself)** with val=458.539.
  - The 23 subsequent gens evaluated 552 candidates and found *zero*
    elites whose 128-seed val score beat the anchor.
  - Per the pre-committed cycle-13 decision rule (test < 457 →
    confirm + pivot), **recipe ceiling confirmed**, **M2 closed**.
  - All three cycle-12 hypotheses now resolved: (a) capacity
    falsified; (b) anchor-sub-optimal de facto falsified by 13 not
    finding a better basin; (c) recipe-ceiling confirmed.

## Cycle-14 result (M3 cycle-1 dual-curve)

For each chronological M2 anchor (c5..c13), score on both `challenge`
and `real_data` evaluators using the standard val seed split
(1000..1127, n=128). Normalizer = FixedFee(0.003) in both modes.

| anchor | challenge_val | real_data_val | adv_real | lift_vs_FF_real |
|--|--:|--:|--:|--:|
| FixedFee(0.003) | 342.04 | 0.584 | 0.000 | (norm) |
| c5 baseline   | 414.42 | -0.353 | -6.10 | **-0.94** |
| c6 warmstart  | 433.57 | -0.614 | -5.89 | **-1.20** |
| c8 inv-aware  | 447.66 | +0.044 | -3.90 | -0.54 |
| c9 third-pass | 450.05 | +1.784 | +0.30 | +1.20 |
| c9 EMA-inv    | 457.62 | +2.784 | +2.53 | +2.20 |
| c10A noop     | 457.67 | +2.967 | +3.09 | +2.38 |
| c11 d16_s2    | 458.54 | +2.918 | +3.05 | +2.33 |
| c13 longrun   | 458.54 | +2.918 | +3.05 | +2.33 |

The OOD trajectory partitions into three regimes:
  1. **c5 → c6 (chal 414 → 434)**: real_data score *regresses*
     **below** FixedFee. Early challenge optimization is
     **net-harmful** OOD.
  2. **c8 → c9-EMA (chal 448 → 458)**: real_data score climbs from
     ~0 to +2.8 above FixedFee. **High-leverage segment** —
     challenge optimization actually buys OOD value here.
  3. **c9-EMA → c13 (chal 458 → 458)**: real_data score saturates
     at +2.4 above FixedFee. **OOD ceiling reached at the same
     compute as the in-distribution ceiling.**

`c11 = c13` exactly on real_data too (2.918 = 2.918), confirming the
recipe ceiling holds OOD.

## Active hypothesis going into cycle 15

> **"Challenge optimization is net-harmful OOD early and saturates
> OOD before it saturates in-distribution."** Cycle 14's evidence is
> suggestive but single-seed (n=128 val). Cycle 15 needs to (a)
> replicate the early-anchor inversion on a 2nd anchor sequence, (b)
> add a held-out test seed split so headline numbers aren't
> point-estimates, (c) decompose the real_data score for the c5
> baseline into retail vs arb PnL to *localize* what the early
> optimization is breaking. If (a) and (b) hold the inversion is
> locked in; (c) gives M4 the targeting information it needs.

## Cycle-15 plan-of-record

1. **Held-out test split for the dual-curve table.** Re-run
   `eval_anchors_dualcurve.py` with seeds 2000..2255 (n=256) so
   each anchor has both val and test points on both evaluators. ~10
   min. Headline numbers in the presentation will then be test, not
   val.
2. **Replicate the early-anchor inversion** on cycle-11 grid
   `d16_s0` and `d16_s1` anchor chains (different rng seeds, same
   warm-start recipe). If the inversion shape replicates on both
   independent chains the finding is locked in; if it doesn't, c5/c6
   may be a one-chain fluke. ~15 min each = 30 min.
3. **Decompose c5 baseline real_data PnL** into retail vs arb
   components to localize the failure mode (toxic-flow miss-quote?
   too-tight base spread? signal-decay mistuned?). Requires either a
   small evaluator wrapper or a per-trade event log dump. ~20 min.
4. **(Background)** retire `bin/checks/10_cycle12_alternatives.py`
   if cycle 15 produces a more compact "warm-start cluster
   dominates" assertion that subsumes it. (Don't retire yet — the
   c10 finding is still load-bearing.)

## Cumulative M2 history (closed; reproduced for context)

| pass | family | dims | init | seed | test score | Δ vs c5 |
|--|--|--|--|--|--|--|
| start (c5) | piecewise | 16 | inh | — | 414.01 | (baseline) |
| pass 1 (c6) | piecewise | 16 | warm | 0 | 432.75 | +18.7 |
| pass 2 (c8) | inv-aware piecewise | 19 | warm | 0 | 446.61 | +32.6 |
| pass 3 (c9 #1) | piecewise | 16 | warm | 0 | 448.81 | +34.8 |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | warm | 0 | 456.64 | +42.6 |
| pass 5 (c10 A) | piecewise + noop | 20 | warm | 0 | 456.74 | +42.7 |
| pass 6 (c10 B) | piecewise | 16 | warm | 1 | 452.96 | +38.9 |
| pass 7 (c11 d16_s2) | piecewise | 16 | warm | 2 | **456.80** | **+42.8** |
| pass 8 (c11 d24_s0) | piecewise + noop×8 | 24 | warm | 0 | 455.66 | +41.6 |
| pass 9 (c11 d24_s1) | piecewise + noop×8 | 24 | warm | 1 | 452.57 | +38.6 |
| c12 stage 1 | latent_full | 18 | default | 0 | 388.57 | -25.4 |
| c12 stage 2 | piecewise (fresh) | 16 | default+wide | 0 | 418.65 | +4.6 |
| **c13 longrun** | **piecewise** | **16** | **warm** | **0** | **456.80** | **+42.8** |

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-13 — 3.9 GB
  RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh`.
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
  Passes through `--ignore`d list during `pytest -x -q`. Either
  install torch host-side or treat as an acknowledged-skipped suite.
- Push topology (origin git@github.com…; sandbox can't resolve DNS)
  means commits are pushed by host-side tooling, not in-sandbox.
  Cycle-1 `checks/04_no_outbound_dns.sh` already encodes this as a
  passing-when-failing predictor.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken on
  this Linux sandbox.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir numpy gymnasium pyarrow pytest matplotlib`.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate instead of deleting.
- CPU: 4 cores. CEM at pop=24 / dim=16-18 / 3 workers ≈ 125-130 s/gen.
  Two CEMs in parallel saturate (6 procs on 4 cores) — chain them.
- **Long-script gotcha (cycle-13)**: when a long-running script chain
  has a CEM phase + a postprocessing phase, **always checkpoint the
  postprocessing pool to disk before scoring**, or split into two
  scripts. Cycle-13 lost its rerank step at the cycle boundary even
  though the CEM itself was checkpointed.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Cycle 14 added `11_cycle13_recipe_ceiling.py`. 11 active
  checks; budget cap is ~12, so cycle 15 should retire one before
  adding another. Carry-forward `08_jax_optional` and `04_no_outbound_dns`
  are passing-when-failing predictors that document the sandbox
  topology, not work-to-do — keep them.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143. Pattern that
  works: launch via `nohup ... &` once, then poll `progress.log`
  every 8-9 min.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) untouched per
  convention; cycle-14's only edits were under `research/` and
  `bin/checks/11_cycle13_recipe_ceiling.py`.
