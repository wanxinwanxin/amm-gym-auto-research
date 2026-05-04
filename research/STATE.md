# State — current cycle

**Last updated**: 2026-05-04 (cycle 11 — closed)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 11 ran a
3-cell warm-start CEM grid (round 1 of a multi-seed × multi-dim
sweep) on the cycle-8 anchor: (16-d, seed=2), (24-d-noop, seed=0),
(24-d-noop, seed=1). The grid bounds the empirical CEM-noise
distribution on this anchor + recipe and shows that cycle-10's
"warm-start CEM is saturating around 456-457" framing is correct.

**Best M2 score: 456.80** (held-out 256 seeds; 16-d piecewise CEM
at rng_seed=2; cycle-11 cell `d16_s2`). Up +0.06 from cycle-10's
456.74 — a within-noise improvement, not a new regime. Gap to M2
target: 83.20 pts.

## Cycle-11 results

| cell                  | dim | seed | val (best) | test (best, n=256) | Δ vs c10 best |
|-----------------------|----:|-----:|-----------:|-------------------:|--------------:|
| c11 d16-s2 (bare 16d) |  16 |    2 |    458.539 |        **456.803** |        +0.06  |
| c11 d24-s0 (8 noop)   |  24 |    0 |    457.294 |            455.656 |        −1.08  |
| c11 d24-s1 (8 noop)   |  24 |    1 |    453.740 |            452.565 |        −4.18  |

**Combined with cycle 9/10**, the 7-cell ablation distribution on
this anchor is:

| cell                | dim | seed | test (n=256) |
|---------------------|----:|-----:|-------------:|
| c9 #1 (bare)        |  16 |    0 |       448.81 |
| c9 #3 (EMA wrap)    |  20 |    0 |       456.64 |
| c10 A (noop tail)   |  20 |    0 |       456.74 |
| c10 B (seed lottery)|  16 |    1 |       452.96 |
| **c11 d16-s2**      |  16 |    2 |   **456.80** |
| c11 d24-s0          |  24 |    0 |       455.66 |
| c11 d24-s1          |  24 |    1 |       452.57 |

Empirical headline: a 16-d third seed (`d16_s2`) is the new best by
+0.06; both dim=24 cells underperform the dim=20 region. Searching
wider in dim doesn't keep helping past ~20.

## Hypothesis verdict (cycle 11)

> *Going-in hypothesis: 50% chance the grid finds ≥ 460; 30% chance
> > 462; 20% chance ≤ 458 across all 3 reps.*

**Falsified, decisively.** None of the 3 cells reached 459 on test;
the highest (d16_s2 = 456.80) is within the +0.10 noise band of
cycle-10's 456.74. The basin is saturated under this anchor +
recipe.

## Cumulative M2 history (post-cycle-11)

| pass | family | dims | seed | test score | Δ vs c9 #1 | wrapper signal |
|--|--|--|--|--|--|--|
| start (c5) | piecewise | 16 | — | ~414 | −34.8 | — |
| pass 1 (c6) | piecewise | 16 | 0 | 432.75 | −16.0 | n/a |
| pass 2 (c8) | inv-aware piecewise | 19 | 0 | 446.61 | −2.2 | −0.17 |
| pass 3 (c9 #1) | piecewise | 16 | 0 | 448.81 | (baseline) | n/a |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | 0 | 456.64 | +7.83 | +0.024 |
| pass 5 (c10 A) | piecewise + no-op tail | 20 | 0 | 456.74 | +7.93 | 0 (by construction) |
| pass 6 (c10 B) | piecewise (seed lottery) | 16 | 1 | 452.96 | +4.15 | n/a |
| pass 7 (c11 d16-s2) | piecewise (seed lottery) | 16 | 2 | **456.80** | +7.99 | n/a |
| pass 8 (c11 d24-s0) | piecewise + noop×8 | 24 | 0 | 455.66 | +6.85 | 0 |
| pass 9 (c11 d24-s1) | piecewise + noop×8 | 24 | 1 | 452.57 | +3.76 | 0 |

## Hypothesis going into cycle 12

The 16-d piecewise basin under this anchor + recipe ceilings out
near 457. Adding more (dim, seed) cells is a low-information bet at
this point — the CEM-noise std (~3 pts) is large enough that single
cells will keep landing in 449-457 essentially uniformly. The
information-rich next move is to *change the recipe or the policy
family*: longer gens, larger pop, ladder/MLP capacity, or a fresh
anchor (not warm-started from cycle-8).

## Cycle-12 plan-of-record

1. **Capacity escalation: ladder policy.** Warm-start a ladder
   level-1 rung from `d16_s2 best` (test 456.80). Same recipe
   (pop=24, gen=12) for direct comparison. Hypothesis: if ladder
   beats piecewise, capacity is the bottleneck and we move to
   ladder + MLP from there. If ladder is within noise of 456-457,
   neither dim nor capacity is the bottleneck; the *anchor* probably
   is.
2. **Fresh-anchor CEM (sanity).** A from-scratch piecewise CEM with
   a much wider init_std (e.g. 0.30) to test whether the
   cycle-8/cycle-9-derived anchor is itself sub-optimal. ~30 min.
3. **Background**: jax-via-CPU-wheel install retry; if successful,
   bring back smooth-vs-exact correlation as cycle-13 priority.

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
  `/sessions/busy-ecstatic-curie/mnt/amm-gym-auto-research`
  (sandbox name changes each cycle; always confirm with `pwd`).
- **The host `.venv/bin/python` is Mac-Homebrew-only**; use system
  `python3` (3.10.12) directly. Project deps to install once per
  fresh sandbox: `pip install --break-system-packages --no-cache-dir
  numpy gymnasium pyarrow pytest`. Skip jax until OOM is resolved.
- **Cannot `unlink` files in the sandbox results dir** — drivers
  open log files in `"w"` mode to truncate instead of deleting.
- **CPU**: 4 cores. Each CEM run uses 3 workers; ~120s/gen at
  pop=24, dim=16; ~120-130s/gen at dim=20-24. Two CEMs in parallel
  would saturate (6 worker procs on 4 cores) — run sequentially.
- **Cycle-11 wall-clock**: ~5 min orient + ~10 min script writeup +
  ~30 min × 3 cells + ~5 min figure + ~15 min STATE/LOG/presentation
  + ~5 min commit = ~110 min. Within 2-h budget.
- **`bin/checks/` policy**: every cycle runs `bash bin/run_checks.sh`
  first thing. Cycle-11 found all green except the optional jax
  check.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) still
  untouched per convention; cycle-11's only edits were under
  `research/` and the experiment scripts.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143 by the bash tool's max-timeout. Pattern that works:
  launch via `nohup ... &` once, then poll every 8-9 min by reading
  `progress.log` directly.
- **Grid driver path bug** (cycle 11): `cd "$(dirname "$0")/../.."`
  was one parent too many; corrected to `cd "$(dirname "$0")/.."`
  before relaunch. The python cell script computes `ROOT`
  independently from its own file path so it self-corrected even
  through the broken driver run; only the driver's per-cell
  stdout-redirect target was wrong.
