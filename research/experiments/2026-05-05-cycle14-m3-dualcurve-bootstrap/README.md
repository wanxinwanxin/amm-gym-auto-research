# Cycle 14 — M3 cycle-1 dual-curve bootstrap

**Cycle date:** 2026-05-05.

## Question

Cycle 13 closed M2: warm-start CEM saturated at test=456.80
(champion = `cycle-11 d16_s2`); doubling the gen budget produced no
lift (best-by-val came from gen 0 itself). With M2 closed, M3 asks:
**of the same chronological policy sequence we trained on the
challenge env, how do those policies score on the *realistic* env?
When does the realistic curve plateau or diverge from the challenge
curve?**

The simplest (and highest-information-density) M3 cycle-1 deliverable
is to take the M2 anchor sequence as the "training trajectory" — each
anchor is the head of the leaderboard at one cycle — and to evaluate
each on both evaluators with a matched seed split. This requires zero
new training; it just needs N×2 batched evals.

> **Going-in prior**: I expected the realistic curve to track the
> challenge curve at roughly half the slope, i.e. monotonic and
> positive. I gave maybe 25% odds that early M2 anchors would be
> *worse* on real_data than FixedFee (i.e. that challenge-only
> optimization can be net-harmful on the OOD env).

## Method

`scripts/eval_anchors_dualcurve.py` loads `best_by_val.params` from
each of cycles 5, 6, 8, 9-third, 9-EMA, 10A, 11 d16_s2, and 13
longrun. For each, it runs `run_batch(..., evaluator_kind="challenge")`
and `run_batch(..., evaluator_kind="real_data")` on the standard val
seed split (1000..1127, n=128). Normalizer is FixedFee(0.003) in both
modes (matches every prior M2 cycle). Compute: ~10 min single-process,
no parallelism (each batch is ~60s and we run 8 anchors × 2 evals).

The "trajectory" axis is *chronological* (cycle order), not
generation-step within a single training run. This is a deliberate
M3-cycle-1 choice: the M2 anchor sequence already provides 8
historical-quality snapshots ranging from score 414 to 458, which is a
much richer trajectory than any single CEM history. Cycle-15+ can
re-do this within a single CEM training run if the cycle-1 plot
suggests it would add information.

## Result

`results/dualcurve.json` and `figures/m3_dualcurve.png`.

| anchor | n_params | challenge_val | real_data_val | adv_real | lift_vs_FF_real |
|--|--:|--:|--:|--:|--:|
| FixedFee   | — | 342.04 | 0.584 | 0.000 | (norm) |
| c5 baseline   | 16 | 414.42 | -0.353 | -6.10 | **-0.94** |
| c6 warmstart  | 16 | 433.57 | -0.614 | -5.89 | **-1.20** |
| c8 inv-aware  | 19 | 447.66 | +0.044 | -3.90 | -0.54 |
| c9 third-pass | 16 | 450.05 | +1.784 | +0.30 | +1.20 |
| c9 EMA-inv    | 20 | 457.62 | +2.784 | +2.53 | +2.20 |
| c10A noop     | 20 | 457.67 | +2.967 | +3.09 | +2.38 |
| c11 d16_s2    | 16 | 458.54 | +2.918 | +3.05 | +2.33 |
| c13 longrun   | 16 | 458.54 | +2.918 | +3.05 | +2.33 |

(c11 ≡ c13 — the cycle-13 best-by-val came from the cycle-11 anchor
itself; same params yield identical scores.)

### Headline findings

1. **Early M2 anchors are *actively harmful* OOD.** The c5 starting
   line and c6 first-warm-start both score *below* FixedFee on
   real_data (-0.94, -1.20 lift). The first 19 pts of M2 challenge
   improvement (414 → 433) make the realistic edge advantage *worse*
   (-6.10 → -5.89, slightly worse if anything).
2. **The OOD curve crosses zero at c8.** The first M2 anchor that
   beats FixedFee on real_data is `c8 inv-aware` (challenge 447.7,
   real_lift +0.04 ≈ 0; the first solidly-positive anchor is
   `c9 third-pass` at challenge 450.0).
3. **The OOD curve plateaus by c9 EMA-inv.** From c9 EMA onward, the
   realistic lift hovers at +2.2 to +2.4 (~7% relative to challenge's
   FixedFee 0.58 → trained 2.9). The last 18 pts of challenge
   improvement (440 → 458) buy ~+0.7 pts of real_data lift; the next
   1 pt of challenge improvement (457.6 → 458.5) buys ~0 pts of
   real_data lift.
4. **Per-pt-of-challenge OOD efficiency is non-monotonic.**
   - c5 → c6: +19 challenge pts buys -0.26 real_data pts (anti-correlated).
   - c6 → c8: +14 challenge pts buys +0.66 real_data pts (small but positive).
   - c8 → c9-EMA: +10 challenge pts buys +2.74 real_data pts (the high-leverage segment).
   - c9-EMA → c13: +0.92 challenge pts buys +0.13 real_data pts (saturated).
5. **The recipe-ceiling carries OOD.** c11 = c13 on real_data too —
   confirming the cycle-13 conclusion that warm-start CEM has stopped
   refining anything (in or out of distribution) under this recipe.

## What it changed

- The cycle-13 framing of "M2 is a saturation problem" is reinforced
  on the OOD side: the additional CEM compute we spent in cycles
  10-13 produced essentially zero additional OOD value.
- Hypothesis 1 from M3's introduction in the task spec — *"action-space
  mismatch?"* — is at least partially confirmed by the early-anchor
  inversion. The piecewise policy class is rich enough to find the
  challenge-optimal point, but its first 1-2 CEM passes pull params
  in directions that *break* on real_data even while they
  monotonically improve challenge.
- Practical M3 implication: there is a **15-20 pt window** of
  challenge improvement (~c8 → c9-EMA) where each additional pt of
  challenge optimization actually buys real_data improvement. Beyond
  that the curves diverge.

## Open questions for cycle 15

1. Is the c8 → c9-EMA "high-leverage" segment a genuine
   capability-tier transition, or did it land on a real-data-friendly
   local optimum by luck? **Re-run the c5..c13 sequence with a 2nd
   anchor sequence** (e.g. seed-1 / seed-2 variants from cycle 11 grid)
   to check if the inversion shape replicates.
2. The c5/c6 anchors are **negative-adv on real_data** but score
   ~-0.6 only because FixedFee normalizer is also weak there. What
   are these policies *doing wrong* — quoting too tight? toxic-flow
   misclassification? Decompose the real_data PnL by retail vs arb
   to localize the failure mode.
3. Can we **train directly on real_data** (M4 prefigure) and recover
   a higher OOD lift than the +2.4 plateau? If yes, M4's hypothesis
   ("more complexity pays off when you train on the right env") gets
   strong early support; if no, +2.4 may simply be the env ceiling.

## Caveats

- "real_data val" is a single-seed-split point estimate (n=128).
  Cycle-15 should add a held-out test split (e.g. 2000..2255) before
  any number gets put in the headline plot for stakeholder
  consumption.
- All scores here use FixedFee(0.003) as the normalizer. The
  real_data evaluator's score depends on this; if we change the
  normalizer fee or strategy, the entire OOD curve shifts. Keep this
  pinned.
- The eval is read-only on the simulator code: no policy retraining,
  no objective change. The trajectory is purely "how do
  challenge-optimized policies score on a different env?" — not
  "what does training on real_data look like?"
