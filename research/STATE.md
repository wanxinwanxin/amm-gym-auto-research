# State — current cycle

**Last updated**: 2026-05-04 (cycle 12 — closed)

## Active milestone

**M2 — Optimize against the simple-AMM challenge.** Cycle 12 ran two
falsifying experiments designed to differentiate three lurking
hypotheses about the cycle-11 saturation at test ≈ 457:

  (a) capacity is the bottleneck (need richer policy family)
  (b) the cycle-8 anchor is in a sub-optimal basin
  (c) the saturation is a genuine ceiling under this (pop=24, gen=12)
      recipe and we need to escalate the recipe

**Best M2 score (unchanged): 456.80** (cycle-11 d16_s2; held-out 256
seeds). Gap to M2 target: 83.20 pts.

## Cycle-12 results

| stage | family | dim | init_std | val_score | test_score | adv_test | Δ vs warm-start |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | latent_full | 18 | 0.25 | 388.77 | **388.57** | −123.65 | −68.24 |
| 2 | piecewise (fresh) | 16 | 0.30 | 419.34 | **418.65** | −36.43 | −38.16 |
| (ref) | piecewise (warm) | 16 | 0.10 | 458.54 | 456.80 | +63.32 | (anchor) |

Both cycle-12 stages land in the "test < 430" branch of their
falsification design — i.e. *neither* policy-family escalation nor
fresh-anchor wide-init beats the cycle-11 warm-start cluster under the
matched (pop=24, gen=12) compute budget.

## Hypothesis verdict (cycle 12)

> *Going-in priors: ~30% ladder beats 460; ~25% fresh-anchor beats
> 460; ~45% both land below.*

**Both predictions in the "both land below" bucket.**
- **(a) capacity-is-bottleneck — strongly falsified.** Even the
  richest 18-d ladder rung with EMAs over six market features lands
  68 pts below warm-start piecewise. The simpler family wins; richer
  state didn't pay.
- **(b) anchor-is-sub-optimal — not resolved.** Fresh-anchor's val
  trajectory was still climbing at gen 11 (+0.2 pts/gen), which
  means we haven't distinguished "wrong basin" from "same basin,
  needs more gens". A 24-36-gen fresh-anchor run is needed to close
  the loop.
- **(c) recipe-ceiling — most consistent with the data.** Both
  alternatives land below warm-start at the *same* compute, which
  is exactly what (c) predicts. The fresh-anchor's still-rising
  trajectory specifically suggests the piecewise basin is broad and
  reachable from many starts but takes more than 12 gens to refine
  to within noise of the cycle-11 ceiling.

## Cumulative M2 history (post-cycle-12)

| pass | family | dims | init | seed | test score | Δ vs c5 | wrapper |
|--|--|--|--|--|--|--|--|
| start (c5) | piecewise | 16 | inh | — | 414.01 | (baseline) | — |
| pass 1 (c6) | piecewise | 16 | warm | 0 | 432.75 | +18.7 | n/a |
| pass 2 (c8) | inv-aware piecewise | 19 | warm | 0 | 446.61 | +32.6 | −0.17 |
| pass 3 (c9 #1) | piecewise | 16 | warm | 0 | 448.81 | +34.8 | n/a |
| pass 4 (c9 #3) | EMA-inv piecewise | 20 | warm | 0 | 456.64 | +42.6 | +0.024 |
| pass 5 (c10 A) | piecewise + noop | 20 | warm | 0 | 456.74 | +42.7 | 0 |
| pass 6 (c10 B) | piecewise | 16 | warm | 1 | 452.96 | +38.9 | n/a |
| pass 7 (c11 d16_s2) | piecewise | 16 | warm | 2 | **456.80** | **+42.8** | n/a |
| pass 8 (c11 d24_s0) | piecewise + noop×8 | 24 | warm | 0 | 455.66 | +41.6 | 0 |
| pass 9 (c11 d24_s1) | piecewise + noop×8 | 24 | warm | 1 | 452.57 | +38.6 | 0 |
| **c12 stage 1** | **latent_full** | **18** | **default** | **0** | **388.57** | **−25.4** | **n/a** |
| **c12 stage 2** | **piecewise (fresh)** | **16** | **default+wide** | **0** | **418.65** | **+4.6** | **n/a** |

Reading: warm-start cluster (c5 → c11) climbs ~43 pts above the
inherited starting line; cycle-12's two cold-start alternatives sit
**below** that warm-start cluster by 38-68 pts. The warm-start
refinement path is doing real work; richer family / wider init alone
can't replicate it in 12 gens.

## Hypothesis going into cycle 13

> *The cycle-11 "warm-start saturates near 457" finding is real, but
> "saturated at this compute" is the better framing. Doubling the
> CEM budget (gen=24) on the d16_s2 anchor, with the same family,
> has a 50%+ chance of lifting test ≥ 460 because the elite-mean
> trajectory at cycle-11 gen 11 was still ∆ +0.05 pts/gen. If recipe
> escalation doesn't lift past 457, we have decisively shown a
> recipe ceiling and should pivot to M3 with d16_s2 as the M2
> deliverable.*

## Cycle-13 plan-of-record

1. **Long-run warm-start CEM on d16_s2.** Same anchor (cycle-11
   d16_s2 best params), same family (piecewise 16-d), pop=24,
   **gen=24** (double cycle-11), init_std_frac=0.10. Tests
   hypothesis (c) directly. ~60 min wall-clock, fits in one cycle.
2. **(If time)** Long-run fresh-anchor piecewise. init_std=0.30,
   pop=24, gen=24 from defaults. Resolves cycle-12's ambiguity
   about whether the cycle-8 anchor is in the right basin.
3. **(Background)** Add a `bin/checks/10_cycle12_alternatives.py`
   check that re-runs both cycle-12 best params on a small seed
   set and asserts they reproduce within tolerance. Encodes the
   cycle-12 finding ("ladder family + fresh-anchor both below
   warm-start") as a runnable assertion that would flip if scoring
   or simulator semantics changed.

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycle 11 — 3.9 GB
  RAM, no swap, `pip install jax[cpu]` dies with exit 143. Either
  more sandbox RAM or a host-side install path needed before we
  can run smooth-vs-exact correlation work. Documented as the
  passing-when-failing check `bin/checks/08_jax_optional.sh`.
- Push topology (`origin` is git@github.com…; sandbox can't
  resolve DNS) means commits are pushed by host-side tooling, not
  in-sandbox. Cycle-1 `checks/04_no_outbound_dns.sh` already
  encodes this as a passing-when-failing predictor.

## Operational notes (carry-forward)

- Repo path: `/sessions/<sandbox-name>/mnt/amm-gym-auto-research`
  (sandbox name changes each cycle; always confirm with `pwd`).
- Use `python3` (system, 3.10.12); the host `.venv/bin/python` is
  Mac-Homebrew-only and broken on this Linux sandbox. Project deps
  needed once per fresh sandbox: `pip install
  --break-system-packages --no-cache-dir numpy gymnasium pyarrow
  pytest matplotlib`. Skip jax until OOM resolved.
- Cannot `unlink` files in the sandbox results dir — drivers open
  log files in `"w"` mode to truncate instead of deleting.
- CPU: 4 cores. Each CEM run uses 3 workers; ~115-130s/gen at
  pop=24, dim=16-18. Two CEMs in parallel would saturate (6 worker
  procs on 4 cores) — run sequentially via a chain driver like
  cycle-12's `scripts/run_chain.sh`.
- **Cycle-12 wall-clock:** ~5 min orient + ~10 min script writeup +
  ~36 min stage 1 + ~35 min stage 2 + ~5 min figure + ~15 min
  STATE/LOG/presentation + ~5 min commit ≈ 110 min. Within 2h
  budget; cycle-13's gen=24 single-stage CEM should fit
  comfortably (~60 min CEM, plenty of slack).
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Cycle-12 found dep-missing on first run (fresh
  sandbox), green after install. No new checks added.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143 if other
  cycles run into the 10-min cap. Pattern that works: launch via
  `nohup ... &` once, then poll `progress.log` every 8-9 min.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) untouched
  per convention; cycle-12's only edits were under `research/`.
