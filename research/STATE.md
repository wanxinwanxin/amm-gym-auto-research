# State — current cycle

**Last updated**: 2026-05-04 (cycle 10 — closed)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 10 ran a
clean test of the cycle-9 wrapper-as-noise hypothesis. Two CEMs from
the same anchor and recipe disambiguated three competing explanations
of cycle-9's +7.83 lift.

**Best M2 score: 456.74** (held-out 256 seeds; 20-d piecewise + 4 inert
no-op tail dims, rng_seed=0; test score). Up trivially from cycle-9's
456.64 (within search noise). Gap to M2 target: 83.26 pts.

## Cycle-10 results (final)

1. **Experiment A — 20-d no-op-tail piecewise CEM, rng_seed=0**.
   Eval function strips the 4 trailing dims before instantiating
   `PiecewiseControllerParams`, so they cannot affect the score in
   any way. Test score = **456.74**, val 457.67. Reproduces cycle-9
   #3 (456.64) to within +0.10 pts.
2. **Experiment B — 16-d 4th-pass piecewise CEM, rng_seed=1**. Same
   anchor and recipe as cycle-9 #1 (which used seed=0); only the
   sampling RNG seed changes. Test score = **452.96**, val 453.82.
   Beats cycle-9 #1 (448.81) by +4.15 but trails the 20-d runs by
   ~3.8.
3. **Comparison figure**:
   `research/experiments/2026-05-04-cycle10-noop-tail-cem/figures/cycle10_hypothesis_test.png`.

## Hypothesis verdict

Of the three candidate explanations for the cycle-9-#3-vs-#1 +7.83 lift:

| hypothesis | verdict | evidence |
|--|--|--|
| (A) Inert tail dims help CEM | **confirmed**, but mechanism is rng-stream-offset, not "more search directions" | A reproduces #3 to +0.10 with mathematically-zero tail interaction |
| (B) RNG-seed lottery | **real, smaller** (~+4.2 of the +7.83) | B at seed=1 hits 452.96 (+4.15 vs c9 #1) |
| (C) EMA × piecewise joint signal | **falsified** | A's flat-zero EMA wrapper matches #3 |

**Decomposition**: cycle-9 #3's +7.83 lift = ~+4.2 from rng-seed
sequence luck + ~+3.8 from dim-20-specific sequence luck (extra 4
normals per candidate per generation shifts the RNG state offset).

## Cumulative M2 history (post-cycle-10)

| pass | family | dims | seed | test score | Δ vs c9 #1 | wrapper signal |
|--|--|--|--|--|--|--|
| start (c5) | piecewise | 16 | — | ~414 | −34.8 | — |
| pass 1 (c6) | piecewise | 16 | 0 | 432.75 | −16.0 | n/a |
| pass 2 (c8) | inv-aware piecewise | 19 | 0 | 446.61 | −2.2 | −0.17 |
| pass 3 (c9 #1) | piecewise | 16 | 0 | 448.81 | (baseline) | n/a |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | 0 | 456.64 | +7.83 | +0.024 |
| pass 5 (c10 A) | piecewise + no-op tail | 20 | 0 | **456.74** | +7.93 | 0 (by construction) |
| pass 6 (c10 B) | piecewise (seed lottery) | 16 | 1 | 452.96 | +4.15 | n/a |

## Hypothesis going into cycle 11

The 16-d piecewise basin's true ceiling is at least 456.74 and likely
higher; we've sampled only 4 (dim, seed) cells out of a wide grid.
The CEM-noise distribution is wide enough that single-CEM headlines
need their seed disclosed.

Best next step: a small multi-seed × multi-dim CEM grid on the same
anchor. Three seeds × three dim levels (16, 24, 32 with no-op tails)
= 9 runs at ~30 min = ~4.5 hours, spread across 2-3 cycles. The
distribution of best-test scores will tell us:
- the basin's actual ceiling (best of grid)
- the CEM-search-noise spread (std across reps)
- whether dim-count systematically helps beyond seed lottery

Prior on best-of-grid: ~50% chance of finding ≥ 460, ~30% chance of
finding > 462, ~20% chance the grid stays ≤ 458.

## Cycle-11 plan-of-record

1. **Multi-seed × multi-dim CEM grid (round 1)**. 3 runs:
   (16-d, seed=2), (24-d-noop, seed=0), (24-d-noop, seed=1). Picks
   that maximize info per run: a third 16-d seed plus two
   higher-dim variants. ~90 min CPU.
2. **If round 1 lifts test ≥ 459**: another round at the winning
   (dim, seed) with longer gens (gen=18) to test whether the basin
   has more depth than 12 gens reveals.
3. **If round 1 stays ≤ 458 across all 3 reps**: pivot to ladder/MLP
   capacity escalation, warm-starting the level-1 rung from the
   current 456.74.
4. **Background**: jax-via-CPU-wheel install retry; if successful,
   bring back smooth-vs-exact correlation as a cycle-12 priority.

## Blockers for user

- **jax install OOMs on this sandbox.** 3.9 GB total RAM, no swap.
  `pip install jax[cpu]` and `pip install jax jaxlib` both die with
  exit 143 (SIGTERM, OOM). Either the sandbox needs more RAM/swap,
  or we need a host-side install path. Documented as a passing-when-
  failing check (`bin/checks/08_jax_optional.sh`). Push topology
  unchanged: sandbox commits to local `main`; host launchd agent
  ships to `origin` every 15 min.

## Operational notes

- **Repo path on this sandbox**:
  `/sessions/jolly-confident-mccarthy/mnt/amm-gym-auto-research`
  (sandbox name changes each cycle; always confirm with `pwd`).
- **The host `.venv/bin/python` is Mac-Homebrew-only**; use system
  `python3` (3.10.12) directly. Project deps to install once per
  fresh sandbox: `pip install --break-system-packages --no-cache-dir
  numpy gymnasium pyarrow pytest`. Skip jax until OOM is resolved.
- **Cannot `unlink` files in the sandbox results dir** — drivers
  open log files in `"w"` mode to truncate instead of deleting.
- **CPU**: 4 cores. Each CEM run uses 3 workers; ~120s/gen at
  pop=24, dim=16; ~125s/gen at dim=20. Two CEMs in parallel would
  saturate (6 worker procs on 4 cores) — run sequentially.
- **Cycle-10 wall-clock**: ~5 min orient + ~10 min script writeup
  + ~30 min experiment A + ~30 min experiment B + ~5 min figure
  + ~10 min presentation/STATE/LOG. Within 2-hour budget.
- **`bin/checks/` policy** (per AUTORESEARCH_PROMPT.md): every cycle
  runs `bash bin/run_checks.sh` first thing. Cycle-10 found all
  green except the optional jax check.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still untouched
  per convention; cycle-10's only edits were under `research/` and
  experiment scripts.
- **CEM-determinism subtlety I learned this cycle**: with
  `np.random.default_rng(seed).normal(mean, std)`, two runs at
  identical seed but different `len(mean)` produce *identical* first
  N standard normals where N = min(len) — the larger run just consumes
  more. So dim=20 vs dim=16 at seed=0 effectively skips ahead in the
  rng stream by 4 normals per candidate per generation. This is why
  cycle-9 #3 (and cycle-10 A) diverge from cycle-9 #1 starting at
  gen 1 even though all three start from the same anchor.
