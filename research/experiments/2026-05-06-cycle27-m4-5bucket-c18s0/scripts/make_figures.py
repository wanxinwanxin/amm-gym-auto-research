"""
Cycle-27 figures + cross-seed summary.

Produces:
- m4_c27_anchor_lift_curve.png — bar/error chart comparing 4-bucket
  cluster (cycle 26) vs 5-bucket cluster (cycle 27) on c18-s0 anchor.
- m4_c27_long_cem_val_curves.png — 5-bucket CEM trajectories per seed.
- m4_c27_lift_summary.png — per-seed lift over piecewise (cycle 26
  4-bucket vs cycle 27 5-bucket).
- results/cross_seed_summary.json — n>=2 mean/stddev/test scores.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, stdev

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-06-cycle27-m4-5bucket-c18s0"
RESULTS = EXP_DIR / "results"
FIGURES = EXP_DIR / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# Cycle 26 (4-bucket) c18-s0 cluster numbers for comparison.
CYCLE26 = {
    "anchor": "cycle18_seed0",
    "policy_family": "ladder_4bucket",
    "piecewise_lift_FF": 3.005713888877396,
    "rng_seeds": [0, 1, 2],
    "test_scores": [3.7265037577716833, 3.737884411604931, 3.7773175878377154],
    "lift_FFs": [3.2561983858883536, 3.267579039721601, 3.3070122159543858],
    "lift_over_piecewise": [0.25048449701095743, 0.2618651508442049, 0.30129832707698956],
}


def _load_run(rng_seed: int) -> dict | None:
    p = RESULTS / f"cycle18_seed0_seed{rng_seed}" / "test.json"
    if not p.exists():
        return None
    with p.open() as f:
        return json.load(f)


def main() -> None:
    runs: list[tuple[int, dict]] = []
    for s in (0, 1, 2, 3):
        r = _load_run(s)
        if r is not None:
            runs.append((s, r))
    if not runs:
        print("no cycle-27 results yet; skipping figures")
        return
    print(f"loaded {len(runs)} cycle-27 runs: seeds {[s for s, _ in runs]}")

    # Cross-seed summary.
    test_scores = [r["best_by_val"]["test_score"] for _, r in runs]
    lift_FFs = [r["best_by_val"]["lift_FF"] for _, r in runs]
    pw_lift = CYCLE26["piecewise_lift_FF"]
    lift_over_pw = [lf - pw_lift for lf in lift_FFs]

    summary = {
        "policy_family": "ladder_5bucket",
        "anchor": "cycle18_seed0",
        "piecewise_lift_FF": pw_lift,
        "n_seeds": len(runs),
        "rng_seeds": [s for s, _ in runs],
        "test_scores": test_scores,
        "lift_FFs": lift_FFs,
        "lift_over_piecewise": lift_over_pw,
        "mean_test_score": float(np.mean(test_scores)) if test_scores else None,
        "mean_lift_FF": float(np.mean(lift_FFs)) if lift_FFs else None,
        "stddev_lift_FF": float(np.std(lift_FFs, ddof=1)) if len(lift_FFs) > 1 else None,
        "mean_lift_over_piecewise": float(np.mean(lift_over_pw)) if lift_over_pw else None,
        "stddev_lift_over_piecewise": float(np.std(lift_over_pw, ddof=1))
        if len(lift_over_pw) > 1
        else None,
        "compare_cycle26_4bucket": {
            "n_seeds": len(CYCLE26["rng_seeds"]),
            "mean_lift_FF": float(np.mean(CYCLE26["lift_FFs"])),
            "stddev_lift_FF": float(np.std(CYCLE26["lift_FFs"], ddof=1)),
            "mean_lift_over_piecewise": float(np.mean(CYCLE26["lift_over_piecewise"])),
            "stddev_lift_over_piecewise": float(np.std(CYCLE26["lift_over_piecewise"], ddof=1)),
        },
    }
    with (RESULTS / "cross_seed_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {RESULTS / 'cross_seed_summary.json'}")

    # Figures.
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skipping figures")
        return

    # Figure 1: lift_FF cluster comparison.
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    families = ["piecewise\n(cycle 18+21)", "4-bucket\n(cycle 25+26)", "5-bucket\n(cycle 27)"]
    if summary["mean_lift_FF"] is not None:
        means = [pw_lift, summary["compare_cycle26_4bucket"]["mean_lift_FF"], summary["mean_lift_FF"]]
        # piecewise n_seed=1 (cycle 18 anchor) — no error bar
        errs = [
            0.0,
            summary["compare_cycle26_4bucket"]["stddev_lift_FF"] or 0.0,
            summary["stddev_lift_FF"] or 0.0,
        ]
    else:
        means = [pw_lift, summary["compare_cycle26_4bucket"]["mean_lift_FF"], 0.0]
        errs = [0.0, 0.0, 0.0]
    bars = ax.bar(families, means, yerr=errs, capsize=6, color=["#888", "#3b75af", "#ef8a62"])
    ax.axhline(3.31, color="red", linestyle="--", alpha=0.6, label="frontier threshold +3.31")
    ax.set_ylabel("lift_FF (test, n=256)")
    ax.set_title(f"M4 c18-s0 anchor: family vs lift_FF (cycle 27 5-bucket n={len(runs)})")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(2.8, max(3.5, max(means) + 0.1))
    for b, m in zip(bars, means):
        ax.text(b.get_x() + b.get_width() / 2, m + 0.01, f"{m:.3f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES / "m4_c27_anchor_lift_curve.png", dpi=130)
    plt.close(fig)
    print(f"wrote {FIGURES / 'm4_c27_anchor_lift_curve.png'}")

    # Figure 2: CEM trajectories (best score per gen) per seed.
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    for s, r in runs:
        gens = [h["gen"] for h in r["history"]]
        bests = [h["best_score"] for h in r["history"]]
        elites = [h["elite_mean_score"] for h in r["history"]]
        ax.plot(gens, bests, marker="o", label=f"seed{s} best")
        ax.plot(gens, elites, marker=".", linestyle="--", alpha=0.6, label=f"seed{s} elite mean")
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("real_data score (n=64 search seeds)")
    ax.set_title("M4 cycle-27 5-bucket ladder long-CEM trajectory (c18-s0)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "m4_c27_long_cem_val_curves.png", dpi=130)
    plt.close(fig)
    print(f"wrote {FIGURES / 'm4_c27_long_cem_val_curves.png'}")

    # Figure 3: per-seed lift over piecewise.
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    cycle26_seeds = CYCLE26["rng_seeds"]
    cycle26_lifts = CYCLE26["lift_over_piecewise"]
    cycle27_seeds = [s for s, _ in runs]
    cycle27_lifts = lift_over_pw
    x26 = np.arange(len(cycle26_seeds))
    x27 = np.arange(len(cycle27_seeds)) + 0.4
    ax.bar(x26, cycle26_lifts, width=0.35, label="4-bucket (cycle 25+26)", color="#3b75af")
    ax.bar(x27, cycle27_lifts, width=0.35, label="5-bucket (cycle 27)", color="#ef8a62")
    if summary["mean_lift_over_piecewise"] is not None:
        ax.axhline(summary["mean_lift_over_piecewise"], color="#ef8a62", linestyle=":", alpha=0.6, label=f"5-bucket mean {summary['mean_lift_over_piecewise']:+.3f}")
    ax.axhline(
        summary["compare_cycle26_4bucket"]["mean_lift_over_piecewise"],
        color="#3b75af",
        linestyle=":",
        alpha=0.6,
        label=f"4-bucket mean {summary['compare_cycle26_4bucket']['mean_lift_over_piecewise']:+.3f}",
    )
    ax.set_xlabel("rng_seed")
    ax.set_ylabel("lift over piecewise (test)")
    ax.set_title("M4 cycle-27 per-seed lift over piecewise on c18-s0")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "m4_c27_lift_summary.png", dpi=130)
    plt.close(fig)
    print(f"wrote {FIGURES / 'm4_c27_lift_summary.png'}")

    # Print summary to stdout.
    print("\n=== cycle-27 5-bucket ladder cross-seed summary ===")
    print(f"  n_seeds: {summary['n_seeds']}")
    print(f"  test scores: {[f'{x:.4f}' for x in test_scores]}")
    print(f"  lift_FFs:    {[f'{x:.4f}' for x in lift_FFs]}")
    print(f"  lift over piecewise: {[f'{x:+.4f}' for x in lift_over_pw]}")
    if summary["mean_lift_FF"]:
        sd = summary["stddev_lift_FF"] if summary["stddev_lift_FF"] is not None else float("nan")
        print(f"  mean lift_FF: {summary['mean_lift_FF']:+.4f}, stddev {sd:.4f}")
    if summary["mean_lift_over_piecewise"]:
        sd = summary["stddev_lift_over_piecewise"] if summary["stddev_lift_over_piecewise"] is not None else float("nan")
        print(f"  mean lift over piecewise: {summary['mean_lift_over_piecewise']:+.4f}, stddev {sd:.4f}")
    cmp = summary["compare_cycle26_4bucket"]
    print(f"  cycle-26 4-bucket comparison: mean lift_FF {cmp['mean_lift_FF']:+.4f}, stddev {cmp['stddev_lift_FF']:.4f}")
    print(f"  cycle-26 4-bucket comparison: mean lift over piecewise {cmp['mean_lift_over_piecewise']:+.4f}, stddev {cmp['stddev_lift_over_piecewise']:.4f}")


if __name__ == "__main__":
    main()
