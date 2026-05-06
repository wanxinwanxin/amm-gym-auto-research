"""
Cycle-28 figures + cross-seed summary.

Compares the cycle-28 5-bucket-with-tightened-init_std runs (n>=2)
against the cycle-27 5-bucket runs (init_std_new=0.15, the cycle-28
contrast) and the cycle-26 4-bucket frontier (init_std_new=0.15).

Produces:
- m4_c28_anchor_lift_bar.png — 4-bucket cluster (c25+c26) vs
  5-bucket cluster wide (c27, std_new=0.15) vs 5-bucket cluster
  tight (c28, std_new=0.05).
- m4_c28_long_cem_val_curves.png — 5-bucket CEM trajectories
  per seed at tightened std (and overlaid cycle-27 trajectories).
- m4_c28_lift_per_seed.png — per-seed lift over piecewise.
- results/cross_seed_summary.json — n>=2 mean/stddev/test scores
  + decision-rule verdict.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-06-cycle28-m4-5bucket-tightstd"
RESULTS = EXP_DIR / "results"
FIGURES = EXP_DIR / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# Cycle 26 (4-bucket) c18-s0 cluster numbers — frontier reference.
CYCLE26 = {
    "anchor": "cycle18_seed0",
    "policy_family": "ladder_4bucket",
    "piecewise_lift_FF": 3.005713888877396,
    "rng_seeds": [0, 1, 2],
    "test_scores": [3.7265037577716833, 3.737884411604931, 3.7773175878377154],
    "lift_FFs": [3.2561983858883536, 3.267579039721601, 3.3070122159543858],
    "lift_over_piecewise": [
        0.25048449701095743,
        0.2618651508442049,
        0.30129832707698956,
    ],
}

# Cycle 27 (5-bucket, init_std_new=0.15) c18-s0 cluster — direct contrast.
CYCLE27 = {
    "anchor": "cycle18_seed0",
    "policy_family": "ladder_5bucket",
    "init_std_frac_new": 0.15,
    "piecewise_lift_FF": 3.005713888877396,
    "rng_seeds": [0, 1],
    "test_scores": [3.6505590633786635, 3.476019260760726],
    "lift_FFs": [3.180253691495334, 3.005713888877396],
    "lift_over_piecewise": [0.17453980261793767, 0.0],
}

# Decision thresholds (from driver docstring).
FRONTIER_THRESHOLD = 3.28  # cycle-26 cluster mean (within rounding)
PIECEWISE_FLOOR = 3.06  # piecewise on c18-s0 + small tolerance


def _load_run(rng_seed: int) -> dict | None:
    p = RESULTS / f"cycle18_seed0_seed{rng_seed}" / "test.json"
    if not p.exists():
        return None
    with p.open() as f:
        return json.load(f)


def _load_cycle27_run(rng_seed: int) -> dict | None:
    p = (
        ROOT
        / f"research/experiments/2026-05-06-cycle27-m4-5bucket-c18s0/results/cycle18_seed0_seed{rng_seed}/test.json"
    )
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
        print("no cycle-28 results yet; skipping figures")
        return
    print(f"loaded {len(runs)} cycle-28 runs: seeds {[s for s, _ in runs]}")

    test_scores = [r["best_by_val"]["test_score"] for _, r in runs]
    lift_FFs = [r["best_by_val"]["lift_FF"] for _, r in runs]
    pw_lift = CYCLE26["piecewise_lift_FF"]
    lift_over_pw = [lf - pw_lift for lf in lift_FFs]

    summary = {
        "policy_family": "ladder_5bucket",
        "anchor": "cycle18_seed0",
        "init_std_frac_new": 0.05,
        "init_std_frac_inh": 0.05,
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
            "stddev_lift_over_piecewise": float(
                np.std(CYCLE26["lift_over_piecewise"], ddof=1)
            ),
        },
        "compare_cycle27_5bucket_wide": {
            "n_seeds": len(CYCLE27["rng_seeds"]),
            "mean_lift_FF": float(np.mean(CYCLE27["lift_FFs"])),
            "stddev_lift_FF": float(np.std(CYCLE27["lift_FFs"], ddof=1)),
            "mean_lift_over_piecewise": float(np.mean(CYCLE27["lift_over_piecewise"])),
            "stddev_lift_over_piecewise": float(
                np.std(CYCLE27["lift_over_piecewise"], ddof=1)
            ),
        },
    }

    # Decision-rule verdict.
    mean_lift = summary["mean_lift_FF"]
    min_lift = min(lift_FFs) if lift_FFs else float("nan")
    max_lift = max(lift_FFs) if lift_FFs else float("nan")
    if min_lift > FRONTIER_THRESHOLD and mean_lift >= FRONTIER_THRESHOLD:
        verdict = "FRONTIER_LIFTED"
    elif min_lift < PIECEWISE_FLOOR:
        verdict = "TIGHTENING_HURT"
    elif mean_lift < FRONTIER_THRESHOLD:
        verdict = "PARTIAL_OR_NO_LIFT"
    else:
        verdict = "AMBIGUOUS"
    summary["verdict"] = verdict
    summary["decision_thresholds"] = {
        "frontier": FRONTIER_THRESHOLD,
        "piecewise_floor": PIECEWISE_FLOOR,
    }

    with (RESULTS / "cross_seed_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {RESULTS / 'cross_seed_summary.json'}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skipping figures")
        return

    # Figure 1: 3-cluster bar.
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    families = [
        "piecewise\n(cycle 18)",
        "4-bucket\nstd_new=0.15\n(c25+c26 n=3)",
        f"5-bucket\nstd_new=0.15\n(c27 n={len(CYCLE27['rng_seeds'])})",
        f"5-bucket\nstd_new=0.05\n(c28 n={len(runs)})",
    ]
    means = [
        pw_lift,
        summary["compare_cycle26_4bucket"]["mean_lift_FF"],
        summary["compare_cycle27_5bucket_wide"]["mean_lift_FF"],
        mean_lift if mean_lift is not None else 0.0,
    ]
    errs = [
        0.0,
        summary["compare_cycle26_4bucket"]["stddev_lift_FF"] or 0.0,
        summary["compare_cycle27_5bucket_wide"]["stddev_lift_FF"] or 0.0,
        summary["stddev_lift_FF"] or 0.0,
    ]
    bars = ax.bar(
        families,
        means,
        yerr=errs,
        capsize=6,
        color=["#888", "#3b75af", "#ef8a62", "#7f3b9c"],
    )
    ax.axhline(
        FRONTIER_THRESHOLD,
        color="red",
        linestyle="--",
        alpha=0.6,
        label=f"frontier threshold {FRONTIER_THRESHOLD:.2f}",
    )
    ax.axhline(
        PIECEWISE_FLOOR,
        color="grey",
        linestyle=":",
        alpha=0.5,
        label=f"piecewise floor {PIECEWISE_FLOOR:.2f}",
    )
    ax.set_ylabel("lift_FF (test, n=256)")
    ax.set_title(
        f"M4 c18-s0 anchor: family × std_new (cycle 28 n={len(runs)}, verdict={verdict})"
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(2.6, max(3.5, max(means) + 0.15))
    for b, m in zip(bars, means):
        ax.text(
            b.get_x() + b.get_width() / 2,
            m + 0.012,
            f"{m:.3f}",
            ha="center",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(FIGURES / "m4_c28_anchor_lift_bar.png", dpi=130)
    plt.close(fig)
    print(f"wrote {FIGURES / 'm4_c28_anchor_lift_bar.png'}")

    # Figure 2: CEM trajectories (cycle-28 vs cycle-27 best-per-gen).
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for s, r in runs:
        gens = [h["gen"] for h in r["history"]]
        bests = [h["best_score"] for h in r["history"]]
        elites = [h["elite_mean_score"] for h in r["history"]]
        ax.plot(
            gens,
            bests,
            marker="o",
            color="#7f3b9c",
            label=f"c28 std=0.05 seed{s} best",
        )
        ax.plot(
            gens,
            elites,
            marker=".",
            linestyle="--",
            color="#7f3b9c",
            alpha=0.55,
            label=f"c28 std=0.05 seed{s} elite mean",
        )
    for s in (0, 1):
        rc = _load_cycle27_run(s)
        if rc is None:
            continue
        gens = [h["gen"] for h in rc["history"]]
        bests = [h["best_score"] for h in rc["history"]]
        elites = [h["elite_mean_score"] for h in rc["history"]]
        ax.plot(
            gens,
            bests,
            marker="x",
            linestyle="-",
            color="#ef8a62",
            alpha=0.7,
            label=f"c27 std=0.15 seed{s} best",
        )
        ax.plot(
            gens,
            elites,
            marker=".",
            linestyle=":",
            color="#ef8a62",
            alpha=0.5,
            label=f"c27 std=0.15 seed{s} elite mean",
        )
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("real_data score (n=64 search seeds)")
    ax.set_title(
        "M4 cycle-28 5-bucket ladder long-CEM (std_new=0.05 vs cycle-27 std_new=0.15)"
    )
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "m4_c28_long_cem_val_curves.png", dpi=130)
    plt.close(fig)
    print(f"wrote {FIGURES / 'm4_c28_long_cem_val_curves.png'}")

    # Figure 3: per-seed lift over piecewise — c26 4b vs c27 5b vs c28 5b-tight.
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    c26_seeds = CYCLE26["rng_seeds"]
    c26_lifts = CYCLE26["lift_over_piecewise"]
    c27_seeds = CYCLE27["rng_seeds"]
    c27_lifts = CYCLE27["lift_over_piecewise"]
    c28_seeds = [s for s, _ in runs]
    c28_lifts = lift_over_pw
    width = 0.25
    x_base = np.arange(max(len(c26_seeds), len(c27_seeds), len(c28_seeds)))
    x26 = x_base[: len(c26_seeds)] - width
    x27 = x_base[: len(c27_seeds)]
    x28 = x_base[: len(c28_seeds)] + width
    ax.bar(x26, c26_lifts, width=width, label="4-bucket (c25+c26)", color="#3b75af")
    ax.bar(x27, c27_lifts, width=width, label="5-bucket std=0.15 (c27)", color="#ef8a62")
    ax.bar(x28, c28_lifts, width=width, label="5-bucket std=0.05 (c28)", color="#7f3b9c")
    ax.axhline(
        summary["compare_cycle26_4bucket"]["mean_lift_over_piecewise"],
        color="#3b75af",
        linestyle=":",
        alpha=0.6,
        label=f"4-bucket mean {summary['compare_cycle26_4bucket']['mean_lift_over_piecewise']:+.3f}",
    )
    if summary["mean_lift_over_piecewise"] is not None:
        ax.axhline(
            summary["mean_lift_over_piecewise"],
            color="#7f3b9c",
            linestyle=":",
            alpha=0.6,
            label=f"5-bucket tight mean {summary['mean_lift_over_piecewise']:+.3f}",
        )
    ax.set_xlabel("rng_seed (positional)")
    ax.set_ylabel("lift over piecewise (test)")
    ax.set_title("M4 cycle-28 per-seed lift over piecewise on c18-s0")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_xticks(x_base)
    ax.set_xticklabels([str(int(x)) for x in x_base])
    fig.tight_layout()
    fig.savefig(FIGURES / "m4_c28_lift_per_seed.png", dpi=130)
    plt.close(fig)
    print(f"wrote {FIGURES / 'm4_c28_lift_per_seed.png'}")

    print("\n=== cycle-28 5-bucket-tightstd ladder cross-seed summary ===")
    print(f"  n_seeds: {summary['n_seeds']}")
    print(f"  test scores: {[f'{x:.4f}' for x in test_scores]}")
    print(f"  lift_FFs:    {[f'{x:.4f}' for x in lift_FFs]}")
    print(f"  lift over piecewise: {[f'{x:+.4f}' for x in lift_over_pw]}")
    if summary["mean_lift_FF"] is not None:
        sd = summary["stddev_lift_FF"] if summary["stddev_lift_FF"] is not None else float("nan")
        print(f"  mean lift_FF: {summary['mean_lift_FF']:+.4f}, stddev {sd:.4f}")
    if summary["mean_lift_over_piecewise"] is not None:
        sd = (
            summary["stddev_lift_over_piecewise"]
            if summary["stddev_lift_over_piecewise"] is not None
            else float("nan")
        )
        print(f"  mean lift over piecewise: {summary['mean_lift_over_piecewise']:+.4f}, stddev {sd:.4f}")
    cmp26 = summary["compare_cycle26_4bucket"]
    cmp27 = summary["compare_cycle27_5bucket_wide"]
    print(
        f"  cycle-26 4-bucket: mean lift_FF {cmp26['mean_lift_FF']:+.4f}, stddev {cmp26['stddev_lift_FF']:.4f}"
    )
    print(
        f"  cycle-27 5-bucket (std=0.15): mean lift_FF {cmp27['mean_lift_FF']:+.4f}, stddev {cmp27['stddev_lift_FF']:.4f}"
    )
    print(f"  verdict: {verdict}")


if __name__ == "__main__":
    main()
