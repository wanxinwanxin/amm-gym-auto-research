"""
M3 cycle-2 — held-out test split + bootstrap CI + retail/arb decomposition.

Question. Cycle 14 produced the first M3 dual-curve plot but every
headline number was a single-seed val estimate (n=128, seeds
1000..1127). Three things were left unfinished:

  1. **Held-out test seeds.** Headline OOD numbers should be on a
     held-out split (2000..2255, n=256) so they aren't being driven
     by the same seeds CEM saw during search.
  2. **Bootstrap confidence intervals.** Without per-seed dispersion
     numbers, we cannot tell whether c5/c6's "below FixedFee" finding
     is statistically significant or within batch noise.
  3. **PnL decomposition.** The single OOD score conflates retail-fee
     PnL and arb-loss PnL. To know *what* early-anchor optimization
     is breaking on real_data, we need to split the score into those
     components for c5 vs c11.

This script also adds a 9th anchor — c10-B (rng_seed=1, dim=16) —
which was M2's "different rng seed, same recipe, same anchor" cell.
It's the closest thing we have to a 2nd-chain replicate of c11.

Method.
  For each of 9 anchors (the cycle-14 8 + c10-B), run two evaluations
  on each of two seed splits:
    val seeds 1000..1127  (n=128)  — replicate cycle-14 numbers
    test seeds 2000..2255 (n=256)  — held-out
  Both evaluators (challenge, real_data). Normalizer FixedFee(0.003).
  From each batch's per-sim simulations we compute:
    - Mean score (the headline)
    - 95% bootstrap CI on the mean (10000 resamples)
    - retail_edge_advantage_mean (LP fee revenue, sub minus norm)
    - arb_loss_advantage_mean (LP loss to arbs, sub minus norm)
    - edge_advantage = retail_edge - arb_loss (identity check)

  Compute time estimate. Cycle-14 ran 8 anchors × 2 evaluators × 128
  seeds in ~10 min. We add 9th anchor and 256-seed split, so ~30 min.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402

VAL_SEEDS = tuple(range(1000, 1128))         # 128 seeds (cycle-14 split)
TEST_SEEDS = tuple(range(2000, 2256))        # 256 seeds (held-out for cycle-15 headline)
NORMALIZER_FEE = 0.003
N_BOOTSTRAP = 10_000
RNG_SEED_BS = 0xC15

OUTDIR = (
    ROOT
    / "research/experiments/2026-05-05-cycle15-m3-test-split-decomp/results"
)
OUTDIR.mkdir(parents=True, exist_ok=True)

ANCHORS = [
    {
        "label": "c5 baseline",
        "family": "piecewise",
        "path": "research/experiments/2026-05-03-cycle5-m2-starting-line/results/piecewise_replicate.json",
        "params_key": "params",
    },
    {
        "label": "c6 warmstart",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/warmstart_cem_test.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c8 inv-aware",
        "family": "inventory_aware_piecewise",
        "path": "research/experiments/2026-05-04-cycle8-inventory-piecewise/results/inventory_warmstart_cem_test.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c9 third-pass",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_test.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c9 EMA-inv",
        "family": "ema_inventory_piecewise",
        "path": "research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results/ema_inventory_cem_test.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c10A noop",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_test.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c10B s1 (NEW)",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/seed_lottery_cem_test.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c11 d16_s2",
        "family": "piecewise",
        "path": "research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2/result.json",
        "params_key": ("best_by_val", "params"),
    },
    {
        "label": "c13 longrun",
        "family": "piecewise",
        "path": "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/longrun_d16_s0_g24/result.json",
        "params_key": ("best_by_val", "params"),
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


def _bootstrap_ci(per_seed: np.ndarray, n_bs: int, rng: np.random.Generator) -> tuple[float, float]:
    """Return 95% bootstrap CI (lo, hi) for the mean of per_seed."""
    n = per_seed.shape[0]
    idx = rng.integers(0, n, size=(n_bs, n))
    means = per_seed[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _evaluate(
    family: str,
    params_dict: dict,
    seeds: tuple[int, ...],
    evaluator_kind: str,
    rng: np.random.Generator,
) -> dict:
    spec = POLICY_SPECS[family]
    cleaned = _strip_noop(params_dict)
    params = spec.params_cls(**cleaned).normalized()
    batch = run_batch(
        lambda: spec.strategy_cls(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(
            NORMALIZER_FEE, NORMALIZER_FEE
        ),
        evaluator_kind=evaluator_kind,
    )
    # Per-sim arrays — pulls out per-seed values for bootstrap on the mean.
    per_score = np.array([s.score for s in batch.simulations], dtype=np.float64)
    per_edge_adv = np.array(
        [s.edge_advantage for s in batch.simulations], dtype=np.float64
    )
    per_retail_edge_adv = np.array(
        [s.retail_edge_advantage for s in batch.simulations], dtype=np.float64
    )
    # arb_loss is a positive number (a loss) on each side; the LP-favorable
    # quantity is (-arb_loss). The "advantage" here is how much *less* the
    # submission lost vs the normalizer (positive = sub bled less than norm).
    per_arb_loss_sub = np.array(
        [s.arb_loss_submission for s in batch.simulations], dtype=np.float64
    )
    per_arb_loss_norm = np.array(
        [s.arb_loss_normalizer for s in batch.simulations], dtype=np.float64
    )
    per_arb_adv = -(per_arb_loss_sub - per_arb_loss_norm)  # +ve = sub better

    score_lo, score_hi = _bootstrap_ci(per_score, N_BOOTSTRAP, rng)
    edge_lo, edge_hi = _bootstrap_ci(per_edge_adv, N_BOOTSTRAP, rng)
    retail_lo, retail_hi = _bootstrap_ci(per_retail_edge_adv, N_BOOTSTRAP, rng)
    arb_lo, arb_hi = _bootstrap_ci(per_arb_adv, N_BOOTSTRAP, rng)

    return {
        "n_seeds": len(seeds),
        "score_mean": float(batch.score),
        "score_ci95": [score_lo, score_hi],
        "edge_advantage_mean": float(batch.edge_advantage_mean),
        "edge_advantage_ci95": [edge_lo, edge_hi],
        "retail_edge_advantage_mean": float(per_retail_edge_adv.mean()),
        "retail_edge_advantage_ci95": [retail_lo, retail_hi],
        "arb_loss_advantage_mean": float(per_arb_adv.mean()),
        "arb_loss_advantage_ci95": [arb_lo, arb_hi],
        # Identity check: edge_advantage ≈ retail_edge_adv + arb_loss_adv
        # (arb_loss_adv defined as -(sub-norm) so + means sub better)
        "identity_residual": float(
            batch.edge_advantage_mean
            - (per_retail_edge_adv.mean() + per_arb_adv.mean())
        ),
        "score_per_seed": per_score.tolist(),
    }


def _log(stdout, msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    stdout.write(line + "\n")
    stdout.flush()


def main() -> None:
    rng = np.random.default_rng(RNG_SEED_BS)
    stdout = (OUTDIR / "dualcurve_test.stdout").open("w")
    t_start = time.time()

    # FixedFee baselines on both splits and both evaluators.
    _log(stdout, "baseline FixedFee on (val, test) × (challenge, real_data)…")
    fixedfee = {}
    for split_name, seeds in [("val", VAL_SEEDS), ("test", TEST_SEEDS)]:
        for kind in ("challenge", "real_data"):
            t0 = time.time()
            batch = run_batch(
                lambda: FixedFeeStrategy(NORMALIZER_FEE, NORMALIZER_FEE),
                seeds,
                normalizer_strategy_factory=lambda: FixedFeeStrategy(
                    NORMALIZER_FEE, NORMALIZER_FEE
                ),
                evaluator_kind=kind,
            )
            per_score = np.array(
                [s.score for s in batch.simulations], dtype=np.float64
            )
            lo, hi = _bootstrap_ci(per_score, N_BOOTSTRAP, rng)
            fixedfee[f"{split_name}_{kind}"] = {
                "score_mean": float(batch.score),
                "score_ci95": [lo, hi],
                "n_seeds": len(seeds),
            }
            _log(
                stdout,
                f"  FF {split_name:4s} {kind:9s} | score={batch.score:7.3f} "
                f"[{lo:7.3f}, {hi:7.3f}] | n={len(seeds)} | {time.time()-t0:.1f}s",
            )

    rows = []
    for anchor in ANCHORS:
        path = ROOT / anchor["path"]
        d = json.loads(path.read_text())
        params = _get(d, anchor["params_key"])

        t_anchor = time.time()
        results = {}
        for split_name, seeds in [("val", VAL_SEEDS), ("test", TEST_SEEDS)]:
            for kind in ("challenge", "real_data"):
                results[f"{split_name}_{kind}"] = _evaluate(
                    anchor["family"], params, seeds, kind, rng
                )

        elapsed = time.time() - t_anchor
        row = {
            "label": anchor["label"],
            "family": anchor["family"],
            "n_params": len(params),
            "metrics": results,
            "elapsed_s": elapsed,
        }
        rows.append(row)

        # Compact log line — focus on test/real_data + decomp.
        rd = results["test_real_data"]
        ch = results["test_challenge"]
        ff_real_test = fixedfee["test_real_data"]["score_mean"]
        lift = rd["score_mean"] - ff_real_test
        _log(
            stdout,
            f"  {anchor['label']:14s} (n={len(params):2d}) | "
            f"chal_test={ch['score_mean']:7.3f} "
            f"[{ch['score_ci95'][0]:6.2f},{ch['score_ci95'][1]:6.2f}] | "
            f"real_test={rd['score_mean']:6.3f} "
            f"[{rd['score_ci95'][0]:+6.2f},{rd['score_ci95'][1]:+6.2f}] "
            f"adv={rd['edge_advantage_mean']:+6.3f} "
            f"retail={rd['retail_edge_advantage_mean']:+6.3f} "
            f"arb={rd['arb_loss_advantage_mean']:+6.3f} "
            f"lift_FF={lift:+6.3f} | {elapsed:.1f}s",
        )

    out = {
        "val_seeds_range": [VAL_SEEDS[0], VAL_SEEDS[-1] + 1],
        "test_seeds_range": [TEST_SEEDS[0], TEST_SEEDS[-1] + 1],
        "n_val_seeds": len(VAL_SEEDS),
        "n_test_seeds": len(TEST_SEEDS),
        "normalizer_fee": NORMALIZER_FEE,
        "n_bootstrap": N_BOOTSTRAP,
        "rng_seed_bootstrap": RNG_SEED_BS,
        "fixedfee": fixedfee,
        "rows": rows,
        "total_elapsed_s": time.time() - t_start,
    }
    out_path = OUTDIR / "dualcurve_test.json"
    out_path.write_text(json.dumps(out, indent=2))
    _log(stdout, f"-> wrote {out_path} ({(time.time() - t_start)/60:.1f} min)")
    stdout.close()


if __name__ == "__main__":
    main()
