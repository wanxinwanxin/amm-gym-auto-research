# State — current cycle

**Last updated**: 2026-05-05 (cycle 19 — closed)

## Active milestone

**M4 cycle 3 (closed) → M4 cycle 4 (next).** Cycle 19 ran the cycle-18
plan-of-record: (1) param-importance "step-back-to-anchor" ablation on
the 16 piecewise params of c11+CEM long, and (2) a policy-family
escalation to a 4-bucket "ladder" controller (19 dims) warm-started
from c11+CEM long. The ablation localized 81% of the per-param edge
to two parameters (`base_fee` Δ +1.946, `reversal_small` Δ +0.755).
The ladder lifted real_data test from +3.476 to **+3.721** (lift_FF
**+3.251**) in 5g × 12p — clean signal in the cycle-18 [+3.20, +3.50]
"marginal" band, partially falsifying cycle-18's "saturating near +3.0"
verdict.

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80**
  [CI 448.0, 465.7] — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable).
  Unchanged.
- **Best real_data score (cycle 19): +3.721** —
  ladder-4-bucket + CEM warm-started from c11+CEM long.
- **Best real_data lift_FF (cycle 19): +3.251.** Up from cycle-18
  c11+CEM long's +3.006 (+0.245).
- **Test retail_advantage (held): +3.113** for ladder; cycle-18
  c11+CEM long was +3.215. The +0.25 score lift comes from the arb
  side, not retail.
- **Param importance (cycle 19 ablation, val n=128).** base_fee
  carries Δ +1.946, reversal_small Δ +0.755, continuation_to_same_side
  Δ +0.314, continuation_to_cross_side Δ +0.301, large_trade_threshold
  Δ +0.133, all others Δ < 0.07. Sum-of-Δ = +3.31, vs full anchor reset
  Δ = +0.967 (parameters interact non-additively).

## Cycle-19 verdict

1. **Cycle-18's "saturating near +3.0" is partially falsified** —
   ladder family adds +0.245 lift_FF on top of c11+CEM long at
   1× compute. The piecewise ceiling ~+3.0 was a representational
   limit, not a CEM-recipe limit.

2. **Family vs compute, near the frontier.** Cycle 18: 4× more compute
   on piecewise from c11_short → +0.234 lift_FF.
   Cycle 19: 1× compute, swap to 4-bucket ladder family
   from c11+CEM long → +0.245 lift_FF. Roughly co-equal levers near
   the current frontier — not the 10:1 compute-dominated ratio that
   cycle 18 reported within a fixed family.

3. **Family escalation pays on the arb side; compute extension pays
   on the retail side.** Cycle 18 long-budget CEM moved DEEPER into
   c11's retail-positive basin (small-bucket retail_adv val
   +1.45 → +3.31). Cycle 19 ladder kept retail-adv flat (test +3.215
   → +3.113); the score lift came entirely from edge_advantage / arb
   loss reduction. Different optimization regime, different lever.

4. **Two params carry 81% of the per-param edge** but the per-param
   ablation drops do NOT sum to the full anchor reset (3.31 vs
   0.967) — parameters interact non-additively. A single cyclical
   metric (top-2 via step-back ablation) is a useful lower bound on
   "where to add capacity," not a complete accounting.

## Active hypothesis going into cycle 20

> **"The ladder's +0.245 lift_FF is genuine but seed-noise-sensitive
> at this small budget; a finer ladder (k=5 or k=8) won't lift much
> further (the small bucket already absorbs >99% of trade COUNT and
> splitting it once captured most of the resolution gain), but a
> learned smooth pricing head — replacing the bucketed continuation /
> reversal piecewise with a 2-layer MLP on (size_ratio, side, time
> since last trade) — could unlock the +0.5 step-change cycle 18
> conjectured if the small-bucket pricing surface is genuinely
> non-piecewise."**
>
> If true: a smooth-head policy warm-started from ladder lifts test
> lift_FF >+3.50 within comparable budget; finer ladders (k=5) plateau
> at +3.30 ± 0.05.
>
> If false (smooth head doesn't help either): the small-bucket
> pricing surface is genuinely saturated under any
> piecewise-style family. The next move is to revisit the price /
> volatility process — maybe the simulator's distribution of
> small-trade size_ratios is itself the constraint, not the
> policy family.

## Cycle-20 plan-of-record

1. **Reproducibility check FIRST: re-run ladder CEM with rng_seed=1.**
   Cheap (~12 min wall-clock at the cycle-19 budget). Does the
   +3.25 lift_FF reproduce within ±0.1, or is it a single-seed pickup?
   Decision rule:
   - If seed-1 lift_FF in [+3.15, +3.35] → cycle-19 result is
     reproducible. Move to (2).
   - If seed-1 lift_FF < +3.15 (e.g. closer to c11_long's +3.01) →
     cycle-19's +3.25 was lucky. Re-evaluate the family-escalation
     case before larger experiments.
   - If seed-1 lift_FF > +3.35 → ladder is even better than the
     cycle-19 single-seed estimate; go straight to (2) with the
     better seed as the new anchor.

2. **Smooth-head policy escalation.** Replace the bucketed
   continuation/reversal scheme with a small MLP (e.g. 2 hidden
   units of width 8, GELU, last-layer bounded sigmoid × max_response)
   on (size_ratio, log_dt, side_indicator) → (continuation_response,
   reversal_response). Initialize from the ladder by fitting the MLP
   to match the ladder's per-bucket responses (a few hundred steps
   of MSE supervised pretraining), then run CEM warm-started from
   the fitted MLP weights flattened into a parameter vector.
   Decision rule: > +3.55 lift_FF → smooth head pays; [+3.30, +3.55]
   → marginal; < +3.30 → MLP family doesn't help here either.

3. *(stretch)* If both (1) and (2) confirm a real but bounded family
   payoff, run a finer ladder (k=8) as a sensitivity check.

## M4 cumulative history

| pass | family | warm-start | budget | test lift_FF | retail_adv (test) |
|--|--|--|--|--:|--:|
| anchor (c5) | piecewise | inh | — | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | +2.10 | +1.08 (val) |
| **c5 + CEM** (cycle 16) | piecewise | c5 | 5g×12p, real_data | +0.74 | -10.14 |
| **c11 + CEM short** (cycle 17) | piecewise | c11_d16_s2 | 5g×12p, real_data | +2.77 | +0.66 |
| default + CEM (cycle 18) | piecewise | default | 5g×12p, real_data | +1.05 | -15.28 |
| c6 + CEM (cycle 18) | piecewise | c6_warmstart | 5g×12p, real_data | +1.89 | -0.00 |
| c8_16d + CEM (cycle 18) | piecewise | c8 inv-aware best (16-d projection) | 5g×12p, real_data | +2.35 | +0.36 |
| **c11 + CEM long** (cycle 18) | piecewise | c11_d16_s2 | 10g×24p, real_data | +3.01 | +3.21 |
| **ladder + CEM** (cycle 19) | ladder-4bucket | c11_long extended | 5g×12p, real_data | **+3.25** | +3.11 |

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-18 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh` (vendored wheels make it
  importable on this fresh sandbox after the cycle's setup step).
- **pyarrow install OOMs on this sandbox** when bundled with other
  deps; install it alone (cycle 18). Not needed for cycle-19 work.
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pytest matplotlib` — install one package at
  a time. Bundling causes OOMs.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate.
- CPU: 4 cores. CEM at pop=12 / dim=19 / 3 workers ≈ 70-80 s/gen on
  real_data with 64 search seeds; pop=24 ≈ ~125 s/gen.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143. Pattern that
  works: launch via `nohup ... &` once, then poll the experiment's
  `progress.log` periodically.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 12 active checks. No additions/retirements
  this cycle.
- **Cycle-19 self-contained ladder strategy file** lives under
  `research/experiments/2026-05-05-cycle19-m4-ablation-and-ladder/scripts/ladder_strategy.py`.
  It is intentionally NOT placed under `arena_policies/` — to avoid
  touching shared modules during a research cycle. If cycle 20+
  promotes ladder to a first-class family (e.g. for the smooth-head
  fitting), move it to `arena_policies/ladder_controller.py` and
  add an export.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-19's edits restricted to `research/`.
