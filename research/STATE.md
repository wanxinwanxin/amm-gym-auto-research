# State — current cycle

**Last updated**: 2026-05-05 (cycle 20 — closed)

## Active milestone

**M4 cycle 4 (closed) → M4 cycle 5 (next).** Cycle 20 ran the cycle-19
plan-of-record reproducibility check. Result: **REPRO_FAIL**. With three
independent rng seeds (0, 1, 2) the ladder family CEM produces test
lift_FF of `+3.251 / +3.076 / +3.006` (mean +3.111, stddev ±0.126).
Cycle-19's headline +3.251 was a single-seed positive draw, not a
reproducible family lift over c11+CEM long (anchor +3.006). On seed=2
the CEM never produced a candidate that beat the warm-start on val,
and the rerank correctly returned the anchor unchanged. The "+0.245
incremental gain from family escalation" reported in cycle 19 is, with
3 seeds, revised to **+0.105 ± 0.13** — within seed noise.

## Headline numbers (held-out test, n=256)

- **Best M2 score (challenge test, n=256): 456.80** [CI 448.0, 465.7]
  — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable). Unchanged.
- **Best real_data score (single-seed cycle-19 ladder): +3.721,
  lift_FF +3.251.** Held as the single-seed champion only.
- **Best real_data lift_FF, multi-seed mean (cycle 20, n=3 ladder
  seeds): +3.111 ± 0.126.** This is the right-of-the-headline
  number going forward.
- **c11+CEM long anchor (single seed, cycle 18): +3.006 lift_FF,
  retail_adv +3.215.** Within ladder seed noise.
- **Implied M4 status:** at the cycle-18/19/20 CEM budget
  (5g × 12p, real_data, warm-started from c11), the policy-family
  lift_FF on real_data sits in **[+3.00, +3.11]** across families
  and across rng seeds. Cycle-18's "saturating near +3.0" verdict,
  which cycle 19 partially falsified at n=1, is **re-confirmed** at
  multi-seed.

## Cycle-20 verdict

1. **Cycle-19's ladder headline was a single-seed positive draw.**
   With 3 seeds: mean lift_FF +3.111, stddev ±0.126, range
   [+3.006, +3.251] (Δ=0.245). The seed dispersion is comparable
   to the apparent family-escalation effect.

2. **Single-seed CEM at this budget is high-variance.** Pop=12 × gen=5
   produces gen-4-best-on-val test scores with stddev ~0.13 across
   rng_seeds — which is comparable to the family payoff we were
   trying to measure. Going forward, any M4 family/budget claim
   needs ≥3 seeds before declaring a new headline.

3. **Cycle-19's "family pays on arb side, compute extension pays on
   retail side" generalization was overfit.** With 3 seeds the
   retail_adv across the ladder family alone ranges +3.11 / +3.83 /
   +3.22 — not a stable family attribute, but a per-seed basin
   property.

4. **The "+3.0 lift_FF ceiling" hypothesis is re-elevated.** Across
   piecewise (cycle 18, 1 seed) and ladder (cycle 20, 3 seeds), the
   mean test lift_FF on real_data stays in [+3.00, +3.11]. Whether
   this is a budget ceiling or a representational ceiling is the
   live M4 question.

## Active hypothesis going into cycle 21

> **"The +3.0 lift_FF on real_data is a *budget* ceiling, not a
> representational ceiling. Repeating cycle-18's long-CEM recipe
> (10g × 24p) on c11+CEM long across 3 rng seeds will produce a
> mean lift_FF >+3.20 with seed std ~0.10 — falsifying the
> 'population-ceiling at +3.0' reading."**
>
> If true: the gain comes from search depth on a fixed family. The
> seed-1 ladder pickup (+3.08) and the seed-0 ladder pickup (+3.25)
> are both close to what the long-CEM recipe would deliver multi-
> seeded on piecewise itself. Family is roughly neutral.
>
> If false (3-seed long-CEM on piecewise stays at +3.0 ± 0.1): the
> +3.0 is a population ceiling under this evaluator + warm-start +
> family combination. Then the next move is a structurally different
> family — smooth-head MLP, EMA-inv state — but with ≥3 seeds from
> the start.

## Cycle-21 plan-of-record

1. **Multi-seed long-CEM on c11+CEM long (same family).** Re-run
   cycle-18's recipe (10g × 24p, piecewise, warm c11) with rng_seed
   ∈ {0, 1, 2}. Decision rule on cross-seed mean lift_FF:
   - mean > +3.20 → +3.0 was a budget/anchor-search-noise ceiling,
     not a population ceiling. Family is neutral; use compute, not
     family, going forward.
   - mean in [+3.00, +3.20] → +3.0 is a population ceiling; family
     escalation is the next move (with ≥3 seeds from the start).
   - mean < +3.00 → cycle-18's single-seed +3.006 was on the high
     end; the ceiling is even tighter. Heavily revise priors.
   Cost: ~3 × ~50 min = ~150 min wall-clock. Run sequentially or
   in parallel up to sandbox budget; long-CEM is heavier than
   ladder repro so cycle 21 may need to run only seeds 0-1 and
   defer seed 2 to cycle 22.

2. **Conditional on (1):** if mean > +3.20, retire the family-
   escalation thread (`smooth-head MLP`, `finer ladder`) and pivot
   to "what does long-CEM compute on c11+CEM long actually unlock?"
   If mean ≤ +3.20, design the smooth-head MLP experiment with ≥3
   seeds.

3. *(stretch)* Encode the "n=1 family-escalation claim is unreliable"
   rule as a `bin/checks/` falsifying test: re-run a single-seed
   ladder CEM and compare to the multi-seed mean +3.111 ± 0.126;
   the check fails if a single-seed re-run lands more than 2σ above
   the mean (which would imply this whole STATE is wrong about the
   distribution).

## M4 cumulative history (revised)

| pass | family | warm-start | budget | seeds | test lift_FF | retail_adv (test) |
|--|--|--|--|--:|--:|--:|
| anchor (c5) | piecewise | inh | — | n/a | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | 1 | +2.10 | +1.08 (val) |
| **c5 + CEM** (cycle 16) | piecewise | c5 | 5g×12p, real_data | 1 | +0.74 | -10.14 |
| **c11 + CEM short** (cycle 17) | piecewise | c11_d16_s2 | 5g×12p, real_data | 1 | +2.77 | +0.66 |
| default + CEM (cycle 18) | piecewise | default | 5g×12p, real_data | 1 | +1.05 | -15.28 |
| c6 + CEM (cycle 18) | piecewise | c6_warmstart | 5g×12p, real_data | 1 | +1.89 | -0.00 |
| c8_16d + CEM (cycle 18) | piecewise | c8 inv-aware best (16d proj) | 5g×12p, real_data | 1 | +2.35 | +0.36 |
| **c11 + CEM long** (cycle 18) | piecewise | c11_d16_s2 | 10g×24p, real_data | 1 | +3.006 | +3.215 |
| **ladder seed=0** (cycle 19) | ladder-4bucket | c11_long extended | 5g×12p, real_data | 1 | +3.251 | +3.113 |
| **ladder seed=1** (cycle 20) | ladder-4bucket | c11_long extended | 5g×12p, real_data | 1 | +3.076 | +3.834 |
| **ladder seed=2** (cycle 20) | ladder-4bucket | c11_long extended | 5g×12p, real_data | 1 | +3.006 | +3.215 |
| **ladder mean ±σ** (n=3) | ladder-4bucket | c11_long extended | 5g×12p, real_data | 3 | **+3.111 ± 0.126** | +3.39 ± 0.39 |

## M2 cumulative history (closed; reproduced for context)

Unchanged — see cycle-18 STATE for the table.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-20 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh` (vendored wheels make it
  importable on this fresh sandbox after the cycle's setup step).
- **pyarrow install OOMs on this sandbox** when bundled with other
  deps; install it alone or in the small bundle (`gymnasium pyarrow
  pytest`) the cycle-20 setup step uses.
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
- **Push topology** (origin git@github.com…; sandbox can't resolve
  DNS) means commits are pushed by host-side tooling, not in-sandbox.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`.
  Always confirm with `pwd`; sandbox name changes each cycle.
- Use `python3` (system, 3.10.12); `.venv/bin/python` is broken.
- Project deps for fresh sandbox: `pip install --break-system-packages
  --no-cache-dir gymnasium pyarrow pytest matplotlib` — the bundle
  works at cycle-20's RAM headroom; if it OOMs, fall back to one
  package at a time.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate.
- CPU: 4 cores. CEM at pop=12 / dim=19 / 3 workers ≈ 70-85 s/gen on
  real_data with 64 search seeds; pop=24 ≈ ~125 s/gen.
- **Bash-tool polling subtlety**: long single `sleep` commands
  >~360s may be killed with exit 143 by the sandbox. Pattern that
  works: launch CEM via `nohup ... &` once, then poll the
  experiment's `progress.log` periodically with shorter `sleep`s.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 12 active checks. No additions/retirements
  this cycle.
- **Seed reproducibility rule (cycle-20).** Going forward, any M4
  family/budget claim at the cycle-19/20 CEM budget needs ≥3
  rng_seeds before being entered as a headline. Single-seed gen-4-
  best-on-val test scores have stddev ~0.13 across rng_seeds —
  comparable to typical claimed effect sizes.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `scripts/`, `tests/`, etc.) untouched per
  convention; cycle-20's edits restricted to `research/`.
