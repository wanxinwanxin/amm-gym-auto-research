# State — current cycle

**Last updated**: 2026-05-05 (cycle 17 — closed)

## Active milestone

**M4 cycle 1 (closed) → M4 cycle 2 (next).**
Cycle 17 ran the cycle-16 plan-of-record: (1) mirror experiment —
direct CEM-on-real_data warm-started from c11 instead of c5, and
(2) per-bucket decomposition of the cycle-16 M4 baseline. Both
produced sharp findings; the load-bearing one is that the
warm-start prior dominates short-budget CEM on real_data, which
re-frames M4 as a prior-sweep before a complexity-sweep.

## Headline numbers (held; reproduced cycle 17)

- **Best M2 score (challenge test, n=256): 456.80**
  [CI 448.0, 465.7] — c11 d16_s2 (cycle-11 grid CEM, M2 deliverable).
- **Best real_data lift_FF (test, n=256): +2.772**
  for c11 + CEM (cycle-17 mirror, 5-gen × 12-pop CEM warm-started
  from c11_d16_s2). Up from c11 anchor's +2.10 (M2 deliverable)
  and the c5+CEM M4 baseline's +0.74.
- **Same compute, c5-start vs c11-start gap: 2.03 lift_FF.** Same
  evaluator (real_data), same population (12), same gens (5),
  same seeds — only the warm-start changed.

## Cycle-17 verdict

1. **Decision rule from cycle 16 fires the "warm-start prior
   dominates" branch.** c11+CEM lift_FF = +2.77 > +2.20 threshold.
   The piecewise family on real_data has demonstrable headroom;
   the bottleneck is finding the right starting basin.

2. **c11+CEM stays in c11's retail basin; c5+CEM amplifies the
   routing collapse.** Per-bucket retail_edge_advantage on n=128
   val seeds:

       anchor               | small  | medium | large  | overall
       c5 baseline          | -9.51  | +0.04  | -0.66  | -10.14
       c5 + CEM (c16 M4)    | -10.33 | +0.06  | -3.06  | -13.33
       c11_d16_s2           | +1.17  | -0.02  | -0.08  | +1.07
       c11 + CEM (this c)   | +1.45  | +0.07  | -0.83  | +0.70

   c11+CEM keeps small-bucket retail edge POSITIVE and *slightly
   higher* than the c11 anchor itself. Routing share on the small
   bucket: c5 13.3%, c5+CEM 5.8% (worse), c11 56.8%, c11+CEM
   60.4% (preserved/improved).

3. **Cycle-17 prior — "M4 baseline retail drop is small-bucket
   dominated" — is partially falsified.** Of the M4-vs-c5
   retail-advantage drop of -3.20:
   - small: -0.82 (~26%)
   - medium: +0.02 (~-1%)
   - large: -2.40 (~75%)
   The dominant CEM-induced retail degradation is large-bucket.
   The small bucket got slightly worse, not dramatically. Don't
   reuse "small-bucket dominates the GAP" priors when reasoning
   about "CEM-induced DEGRADATION" — different mechanisms.

## Active hypothesis going into cycle 18

> **"The piecewise family on real_data has more headroom than
> +2.77 lift_FF. Either (a) longer-budget CEM from c11
> monotonically climbs past +3.0 within ~10 gens, or (b) the basin
> matters so much that the right experiment is to seed CEM from
> many anchors and see which basins generalize best."**
>
> If true (a): a 10-gen × 24-pop CEM from c11 lifts to >= +3.2 by
> gen ~6-7 and we close M4 cycle 2 with a clean piecewise-family
> ceiling estimate.
>
> If true (b) but not (a): some non-c11 anchor (default, c8) lifts
> past +3.0 with the same 5-gen × 12-pop budget, and the
> family-vs-prior question becomes the M4 cycle 3 framing.
>
> If neither: c11+CEM saturates near +2.77 in 10 gens AND no other
> anchor reaches +3.0 → c11 is the piecewise-family real_data
> ceiling and M4 cycle 3 has to escalate to richer families
> (ladder, MLP) or retail-aware loss.

## Cycle-18 plan-of-record

1. **Longer-budget CEM from c11.** 10-gen × 24-pop on real_data,
   warm-started from c11_d16_s2. Same evaluator, same seeds, same
   normalizer. Watch for plateau in best_search and val. Decision
   rule:
   - if test lift_FF > +3.20 → real_data ceiling > +3.20; M4 cycle
     2 = "is +3.20 the actual ceiling or do we keep climbing?"
   - if test lift_FF in [+2.80, +3.20] → c11+CEM saturating
     near +3.0; ceiling probably nearby.
   - if test lift_FF < +2.80 (i.e. < this cycle's 5-gen result)
     → CEM noise or the longer run found a different elite that
     overfit val; investigate.
   - Wall-clock estimate: ~30-40 min CEM + ~10 min rerank/test ≈
     50 min. Use the nohup + poll-every-8-min pattern from cycle 16.

2. **Prior sweep at fixed compute.** 5-gen × 12-pop CEM (this
   cycle's exact budget) from each of {default-piecewise, c6
   (cycle-6 warm-start), c8 (inv-aware), c11_d16_s2 — already done
   as the cycle-17 mirror, included for axis continuity}. Plot
   final lift_FF vs starting-line lift_FF. Single-figure answer
   to "how does basin determine convergence?"
   - Wall-clock: ~50 min (3 new runs × ~12 min each + figure).

3. *(stretch, only if 1 + 2 finish in <90 min)* Retail-aware CEM
   from c5: redefine search score = edge_advantage + 0.2 ×
   retail_edge_advantage. Same 5-gen × 12-pop budget. Tests
   whether a small retail penalty bridges from c5 to the c11
   basin.

## M4 cumulative history

| pass | family | warm-start | budget | test lift_FF | retail_adv |
|--|--|--|--|--:|--:|
| anchor (c5) | piecewise | inh | — | -1.22 | -10.14 |
| anchor (c11_d16_s2) | piecewise | warm c5 (M2) | challenge CEM | +2.10 | +1.08 (val) |
| **c5 + CEM** | piecewise | c5 | 5g×12p, real_data | **+0.74** | -13.10 |
| **c11 + CEM** | piecewise | c11_d16_s2 | 5g×12p, real_data | **+2.77** | +0.66 |

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
| c16 M4 baseline | piecewise | 16 | c5 warm + real_data CEM | 0 | (not measured) | +1.21 (+0.74) |
| **c17 M4 mirror** | piecewise | 16 | c11 warm + real_data CEM | 0 | (not measured) | **+3.24 (+2.77)** |

## Blockers for user

- **jax install OOMs on this sandbox.** Same as cycles 11-16 — 3.9
  GB RAM, no swap, `pip install jax[cpu]` dies with exit 143.
  Documented as the passing-when-failing check
  `bin/checks/08_jax_optional.sh` (vendored wheels make it
  importable on this fresh sandbox after the cycle's setup step).
- **pyarrow install OOMs on this sandbox** (added cycle 17). Not
  needed for current cycle's experiments; flagged for any future
  driver that wants Parquet round-trips. Workaround: use JSON or
  feather via `pandas.to_feather` (pandas dep is preinstalled).
- **torch not installed on this sandbox** — `tests/test_training.py`
  collection fails with `ModuleNotFoundError: No module named 'torch'`.
  Either install torch host-side or treat as an
  acknowledged-skipped suite.
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
  --no-cache-dir gymnasium pytest matplotlib`. (numpy is preinstalled;
  pyarrow OOMs and is optional for the experiments.) jax via
  `bin/setup_jax_from_vendored.sh`.
- Cannot `unlink` files in the sandbox results dir; drivers should
  open log files in `"w"` mode to truncate instead of deleting.
  Cycle-16+17 reminder: when authoring a new long-running driver,
  do NOT copy `LOGFILE.unlink(missing_ok=True)` from cycle-6 etc.
  Use `LOGFILE.open("w").close()` instead. (Encoded as the
  passing-when-failing check 05.)
- CPU: 4 cores. CEM at pop=12 / dim=16 / 3 workers ≈ 70-80 s/gen on
  real_data; pop=24 ≈ ~125 s/gen extrapolating from cycle 6. Real_data
  eval slightly slower per candidate (10000 episode steps reading
  from empirical distribution) than challenge eval.
- **Bash-tool polling subtlety**: `sleep N` with N > 600 is killed
  with exit 143; even N ≈ 540 sometimes returns 143. Pattern that
  works: launch via `nohup ... &` once, then poll the experiment's
  `progress.log` every 8-9 min.
- **Sandbox can stall mid-run**: cycle 17 saw a ~26-min stall on
  gen 3 of an otherwise ~70 s/gen CEM. Always set up
  incrementally-saved checkpoints (`history.json` written every
  gen) so a stall (or restart) doesn't lose the search trajectory.
- **Rerank pool injection trick (added cycle 17)**: when running
  CEM from a known-good warm-start anchor on real_data, inject the
  anchor itself into the rerank pool BEFORE adding elites by
  search score. Guarantees `best_by_val` cannot regress past the
  anchor — important when CEM gen-by-gen val noise (~0.1-0.4 score
  units on n=128) could otherwise let a candidate with a lucky
  val draw be picked over the anchor.
- **`bin/checks/` policy**: `bash bin/run_checks.sh` first thing
  every cycle. Currently 12 active checks (no addition or
  retirement cycle 17). Carry-forward `08_jax_optional` and
  `04_no_outbound_dns` are passing-when-failing predictors
  documenting the sandbox topology, not work-to-do — keep them.
- **Inherited working-tree changes** (across `arena_eval/`,
  `arena_policies/`, `arena_search/`, `tests/`, etc.) untouched per
  convention; cycle-17's only edits were under `research/`.
