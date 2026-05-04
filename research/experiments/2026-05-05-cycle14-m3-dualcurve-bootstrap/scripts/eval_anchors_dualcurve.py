"""
M3 cycle-1 — dual-curve eval of the M2 anchor sequence.

Question. M2 produced a chronological sequence of policies that
climbed from ~414 (cycle 5 starting line) to 456.8 (cycle 11
champion / cycle 13 ceiling) on the *challenge* simulator. M3 asks:
what did each of those policies *also* score on the *realistic*
simulator (`evaluator_kind="real_data"`)?

This is the simplest possible M3 cycle-1 deliverable — it reuses the
existing chronological anchor sequence as the "training trajectory"
and just scores each anchor on the held-out OOD env. The plot then
answers the M3 question directly: when does the realistic curve
plateau vs. the challenge curve?

Method.
- Load best_by_val params from each cycle-5..cycle-13 anchor.
- For each, run two evaluations under matched seed sets:
    challenge eval: evaluator_kind="challenge", seeds 1000..1127
    real_data eval: evaluator_kind="real_data", seeds 1000..1127
- Use FixedFee(0.003) as the normalizer in both modes (matches every
  prior M2 cycle).
- Score: the per-batch challenge score (challenge mode) or the
  per-batch real_data score (real_data mode). Log adv too.

Outputs:
  results/dualcurve.json   — full table per anchor.
  results/dualcurve.stdout — per-anchor live log.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

VAL_SEEDS = tuple(range(1000, 1128))  # 128 seeds; same split as every M2 cycle.
NORMALIZER_FEE = 0.003

OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle14-m3-dualcurve-bootstrap/results"
)
OUTDIR.mkdir(parents=True, exist_ok=True)

# Chronological anchor sequence — labels match research/STATE.md table.
# Each entry: (label, family_for_policy_specs, path, getter_fn). The
# getter takes the loaded JSON and returns (params_dict, challenge_test_score).
ANCHORS = [
    {
        "label": "c5 baseline",
        "family": "piecewise",
        "path": "research/experiments/2026-05-03-cycle5-m2-starting-line/results/piecewise_replicate.json",
        "params_key": "params",
        "score_key": "score",
    },
    {
        "label": "c6 warmstart",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/warmstart_cem_test.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
    {
        "label": "c8 inv-aware",
        "family": "inventory_aware_piecewise",
        "path": "research/experiments/2026-05-04-cycle8-inventory-piecewise/results/inventory_warmstart_cem_test.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
    {
        "label": "c9 third-pass",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_test.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
    {
        "label": "c9 EMA-inv",
        "family": "ema_inventory_piecewise",
        "path": "research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results/ema_inventory_cem_test.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
    {
        "label": "c10A noop",
        "family": "piecewise",  # noop_ params get stripped before instantiation
        "path": "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_test.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
    {
        "label": "c11 d16_s2",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2/result.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
    {
        "label": "c13 longrun",
        "family": "piecewise",
        "path": "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/longrun_d16_s0_g24/result.json",
        "params_key": ("best_by_val", "params"),
        "score_key": ("best_by_val", "test_score"),
    },
]


def _get(d: dict, key):
    if isinstance(key, tuple):
        for k in key:
            d = d[k]
        return d
    return d[key]


def _strip_noop(params: dict) -> dict:
    return {k: v for k, v in params.items() if not k.startswith("noop_")}


def _evaluate(family: str, params_dict: dict, seeds, evaluator_kind: str) -> dict:
    spec = POLICY_SPECS[family]
    cleaned = _strip_noop(params_dict)
    # Some param classes only accept fields they declare; trust the family.
    params = spec.params_cls(**cleaned).normalized()
    batch = run_batch(
        lambda: spec.strategy_cls(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(
            NORMALIZER_FEE, NORMALIZER_FEE
        ),
        evaluator_kind=evaluator_kind,
    )
    return {
        "score": float(batch.score),
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "n_seeds": len(seeds),
    }


def _log(stdout, msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    stdout.write(line + "\n")
    stdout.flush()


def main() -> None:
    stdout = (OUTDIR / "dualcurve.stdout").open("w")

    # FixedFee baselines on both evaluators (reference for the plot).
    _log(stdout, f"baseline FixedFee({NORMALIZER_FEE}) on val seeds (challenge & real_data)…")
    t0 = time.time()
    base_chal = run_batch(
        lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        VAL_SEEDS,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(
            NORMALIZER_FEE, NORMALIZER_FEE
        ),
        evaluator_kind="challenge",
    )
    base_chal_score = float(base_chal.score)
    base_real = run_batch(
        lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
        VAL_SEEDS,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(
            NORMALIZER_FEE, NORMALIZER_FEE
        ),
        evaluator_kind="real_data",
    )
    base_real_score = float(base_real.score)
    _log(
        stdout,
        f"  FixedFee | challenge_val={base_chal_score:7.3f} | "
        f"real_data_val={base_real_score:7.3f}  ({time.time()-t0:.1f}s)",
    )

    rows: list[dict] = []
    for anchor in ANCHORS:
        path = ROOT / anchor["path"]
        d = json.loads(path.read_text())
        params = _get(d, anchor["params_key"])
        prior_test = _get(d, anchor["score_key"])

        t_anchor = time.time()
        chal = _evaluate(anchor["family"], params, VAL_SEEDS, "challenge")
        real = _evaluate(anchor["family"], params, VAL_SEEDS, "real_data")
        elapsed = time.time() - t_anchor

        row = {
            "label": anchor["label"],
            "family": anchor["family"],
            "n_params": len(params),
            "prior_test_score_challenge": float(prior_test),
            "challenge_val_score": chal["score"],
            "challenge_val_adv": chal["edge_advantage_mean"],
            "real_data_val_score": real["score"],
            "real_data_val_adv": real["edge_advantage_mean"],
            "real_data_lift_vs_fixedfee": real["score"] - base_real_score,
            "elapsed_s": elapsed,
        }
        rows.append(row)
        _log(
            stdout,
            f"  {anchor['label']:14s} ({anchor['family']:24s}, n={len(params):2d}) | "
            f"chal_val={chal['score']:7.3f} (prior_test={prior_test:.2f}) | "
            f"real_val={real['score']:6.3f} adv={real['edge_advantage_mean']:+6.3f} | "
            f"real_lift_vs_FF={real['score']-base_real_score:+6.3f} | {elapsed:.1f}s",
        )

    out = {
        "val_seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
        "n_val_seeds": len(VAL_SEEDS),
        "normalizer_fee": NORMALIZER_FEE,
        "fixedfee_challenge_val_score": base_chal_score,
        "fixedfee_real_data_val_score": base_real_score,
        "rows": rows,
    }
    (OUTDIR / "dualcurve.json").write_text(json.dumps(out, indent=2))
    _log(stdout, f"  -> wrote {OUTDIR / 'dualcurve.json'}")
    stdout.close()


if __name__ == "__main__":
    main()
