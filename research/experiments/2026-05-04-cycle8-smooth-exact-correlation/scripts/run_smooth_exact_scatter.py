"""
Cycle-8 M2 — smooth-vs-exact correlation study around cycle-6 piecewise best.

Cycle-6 gradient probe (`probe_gradient_v2.py`) showed the smooth surrogate
returns ~−2895 at the CEM-best point while the exact score is ~+433. At
LR=1e-3 the smooth gradient destroys the policy in 2 steps; at LR=1e-5 the
surrogate gradient is statistical noise. The cycle-7 plan deferred the
diagnostic; cycle 8 runs it.

Method
------

1. Sample N=64 random parameter vectors in a 0.10×range neighborhood of the
   cycle-6 piecewise best (same Gaussian width as warm-start CEM).
2. For each, score on:
     - exact: `run_batch` over `exact_seeds = 0..31` (32 seeds, the
       gradient-probe-train budget)
     - smooth: `smooth_piecewise_batch_result` over the same 32 seeds
       worth of `build_challenge_tape` rollouts
3. Plot exact-vs-smooth scatter, compute Pearson and Spearman correlations.
4. Save (a) raw json with per-sample (params, exact, smooth) and (b) figure.

If correlation is high (≥0.7), the surrogate is salvageable — the basin
shape is right but offset/scaled wrong (we'd want to try gradient again
with proper LR and possibly a constant subtraction). If correlation is
near zero or negative, the surrogate is unusable and gradient on
piecewise-from-CEM-best is officially dead.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_eval.exact_simple_amm import (  # noqa: E402
    ExactSimpleAMMConfig,
    FixedFeeStrategy,
    run_batch,
)
from arena_eval.diff_simple_amm import (  # noqa: E402
    SmoothRelaxationConfig,
    build_challenge_tape,
    challenge_env_vector,
    piecewise_param_vector,
    smooth_piecewise_batch_result,
)
from arena_policies import (  # noqa: E402
    PiecewiseControllerParams,
    PiecewiseControllerStrategy,
)
from arena_search.simple_amm_search import (  # noqa: E402
    PIECEWISE_CONTROLLER_PARAM_RANGES,
)


OUTDIR = ROOT / "research/experiments/2026-05-04-cycle8-smooth-exact-correlation/results"
OUTDIR.mkdir(parents=True, exist_ok=True)

CYCLE6_TEST_JSON = (
    ROOT
    / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/warmstart_cem_test.json"
)

PIECEWISE_NAMES = list(PIECEWISE_CONTROLLER_PARAM_RANGES.keys())
N_SAMPLES = 64
SEED_COUNT = 32  # 0..31, matches gradient-probe train budget
NEIGHBORHOOD_FRAC = 0.10  # same width as warm-start CEM


def _bounds():
    lows = np.asarray(
        [PIECEWISE_CONTROLLER_PARAM_RANGES[n][0] for n in PIECEWISE_NAMES], dtype=float
    )
    highs = np.asarray(
        [PIECEWISE_CONTROLLER_PARAM_RANGES[n][1] for n in PIECEWISE_NAMES], dtype=float
    )
    return lows, highs


def _cycle6_best_vector():
    d = json.loads(CYCLE6_TEST_JSON.read_text())
    p = d["best_by_val"]["params"]
    return np.asarray([p[n] for n in PIECEWISE_NAMES], dtype=float)


def _exact_score(params_dict: dict, seeds: tuple[int, ...]) -> float:
    params = PiecewiseControllerParams(**params_dict).normalized()
    batch = run_batch(
        lambda: PiecewiseControllerStrategy(params),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    return float(batch.score)


def _smooth_score(params_dict: dict, tapes, env_vec) -> float:
    params = PiecewiseControllerParams(**params_dict).normalized()
    pv = piecewise_param_vector(params)
    res = smooth_piecewise_batch_result(
        pv,
        config=ExactSimpleAMMConfig(),
        tapes=tapes,
        env_vector=env_vec,
        relaxation=SmoothRelaxationConfig(),
    )
    return float(res.score)


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(x, y)[0, 1])


def main() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Cycle-8 smooth-vs-exact correlation")
    rng = np.random.default_rng(0)
    lows, highs = _bounds()
    center = _cycle6_best_vector()
    std = NEIGHBORHOOD_FRAC * (highs - lows)
    print(f"  center: cycle-6 piecewise best (16 params)")
    print(f"  N samples: {N_SAMPLES} (Gaussian, σ={NEIGHBORHOOD_FRAC}×range)")
    print(f"  seeds: 0..{SEED_COUNT - 1} ({SEED_COUNT} per sample)")

    # Pre-build challenge tapes once (deterministic in seed) so each
    # smooth eval just plays back the same tape with different params.
    config = ExactSimpleAMMConfig()
    seeds = tuple(range(SEED_COUNT))
    print(f"[{time.strftime('%H:%M:%S')}] Building {len(seeds)} challenge tapes…")
    t0 = time.time()
    tapes = tuple(build_challenge_tape(config=config, seed=s) for s in seeds)
    env_vec = challenge_env_vector(config)
    print(f"  -> {time.time() - t0:.1f}s")

    # Center exact + smooth for sanity.
    center_dict = dict(zip(PIECEWISE_NAMES, center.tolist()))
    print(f"[{time.strftime('%H:%M:%S')}] Center exact score…")
    t0 = time.time()
    center_exact = _exact_score(center_dict, seeds)
    print(f"  -> exact={center_exact:.3f} ({time.time() - t0:.1f}s)")

    print(f"[{time.strftime('%H:%M:%S')}] Center smooth score…")
    t0 = time.time()
    center_smooth = _smooth_score(center_dict, tapes, env_vec)
    print(f"  -> smooth={center_smooth:.3f} ({time.time() - t0:.1f}s)")

    # Sample neighborhood.
    samples: list[dict] = []
    samples.append({
        "id": -1,
        "params": center_dict,
        "exact_score": center_exact,
        "smooth_score": center_smooth,
        "is_center": True,
    })

    for i in range(N_SAMPLES):
        v = rng.normal(center, std)
        v = np.clip(v, lows, highs)
        params_dict = dict(zip(PIECEWISE_NAMES, v.tolist()))

        t_e0 = time.time()
        exact = _exact_score(params_dict, seeds)
        t_s0 = time.time()
        smooth = _smooth_score(params_dict, tapes, env_vec)
        t_done = time.time()

        samples.append({
            "id": i,
            "params": params_dict,
            "exact_score": exact,
            "smooth_score": smooth,
            "is_center": False,
        })

        if i < 5 or i == N_SAMPLES - 1 or i % 10 == 9:
            print(
                f"  sample {i:3d}: exact={exact:7.3f} smooth={smooth:10.3f}  "
                f"({t_s0 - t_e0:.1f}s exact + {t_done - t_s0:.1f}s smooth)"
            )

    exacts = np.asarray([s["exact_score"] for s in samples if not s["is_center"]])
    smooths = np.asarray([s["smooth_score"] for s in samples if not s["is_center"]])
    pearson = _pearson(exacts, smooths)
    spearman = _spearman(exacts, smooths)
    print(
        f"\nN={len(exacts)} | Pearson={pearson:+.3f} | Spearman={spearman:+.3f}\n"
        f"  exact range: [{exacts.min():.3f}, {exacts.max():.3f}] mean={exacts.mean():.3f}\n"
        f"  smooth range: [{smooths.min():.3f}, {smooths.max():.3f}] mean={smooths.mean():.3f}"
    )

    out = {
        "n_samples": int(len(exacts)),
        "neighborhood_frac": NEIGHBORHOOD_FRAC,
        "seed_count": SEED_COUNT,
        "center_exact_score": center_exact,
        "center_smooth_score": center_smooth,
        "pearson": pearson,
        "spearman": spearman,
        "exact_range": [float(exacts.min()), float(exacts.max())],
        "smooth_range": [float(smooths.min()), float(smooths.max())],
        "samples": samples,
    }
    (OUTDIR / "smooth_exact_scatter.json").write_text(json.dumps(out, indent=2))
    print(f"  -> wrote {OUTDIR / 'smooth_exact_scatter.json'}")

    # Lightweight scatter figure (matplotlib).
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6.5, 5.5))
        ax.scatter(exacts, smooths, s=18, alpha=0.7, edgecolors="none", color="#3C7BB0")
        ax.scatter([center_exact], [center_smooth], marker="*", s=180, color="#D9534F",
                   label="cycle-6 piecewise best (center)")
        ax.set_xlabel("Exact challenge score (32 seeds)")
        ax.set_ylabel("Smooth surrogate score")
        ax.set_title(
            f"Cycle-8 smooth-vs-exact correlation (N={len(exacts)})\n"
            f"Pearson={pearson:+.3f}, Spearman={spearman:+.3f}",
            fontsize=11,
        )
        ax.grid(alpha=0.25)
        ax.legend(loc="best", fontsize=9)
        fig.tight_layout()
        fig_path = ROOT / (
            "research/experiments/2026-05-04-cycle8-smooth-exact-correlation/figures/"
            "smooth_vs_exact_scatter.png"
        )
        fig_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(fig_path, dpi=120)
        print(f"  -> wrote {fig_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"  (matplotlib figure skipped: {exc!r})")


if __name__ == "__main__":
    main()
