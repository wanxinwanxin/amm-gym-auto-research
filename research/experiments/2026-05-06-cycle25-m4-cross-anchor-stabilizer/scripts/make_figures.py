"""Cycle 25 figures.

Inputs (results/{anchor_key}_seed{seed}/test.json):
  cycle21_seed2_seed1     # Q1: second seed on c21-s2 long-CEM ladder
  cycle18_seed0_seed0     # Q2: cross-anchor probe on c18-s0

Outputs:
  figures/m4_c25_anchor_lift_curve.png  -- 3-anchor inverse-scaling plot
  figures/m4_c25_long_cem_val_curves.png -- CEM val trajectories
  figures/m4_c25_lift_summary.png       -- bar chart of lift over piecewise

Also emits results/cross_seed_summary.json with aggregated cross-anchor numbers
including cycle 23/24/25 long-CEM ladder runs.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-06-cycle25-m4-cross-anchor-stabilizer"
FIG_DIR = EXP_DIR / "figures"
PRES_FIG_DIR = ROOT / "research/presentation/figures"

FIG_DIR.mkdir(parents=True, exist_ok=True)
PRES_FIG_DIR.mkdir(parents=True, exist_ok=True)


def _load(p: Path) -> dict:
    with p.open() as f:
        return json.load(f)


def main() -> None:
    # Cycle-23/24 results (already on disk; reload for the summary).
    c23_s1_seed0 = _load(
        ROOT
        / "research/experiments/2026-05-06-cycle23-m4-ladder-longcem/results/cycle21_seed1_seed0/test.json"
    )
    c23_s1_seed1 = _load(
        ROOT
        / "research/experiments/2026-05-06-cycle23-m4-ladder-longcem/results/cycle21_seed1_seed1/test.json"
    )
    c24_s1_seed2 = _load(
        ROOT
        / "research/experiments/2026-05-06-cycle24-m4-ladder-longcem-followup/results/cycle21_seed1_seed2/test.json"
    )
    c24_s2_seed0 = _load(
        ROOT
        / "research/experiments/2026-05-06-cycle24-m4-ladder-longcem-followup/results/cycle21_seed2_seed0/test.json"
    )

    # Cycle-25 results.
    c25_s2_seed1 = _load(EXP_DIR / "results/cycle21_seed2_seed1/test.json")
    c25_s0_seed0 = _load(EXP_DIR / "results/cycle18_seed0_seed0/test.json")

    # Piecewise anchor lift_FF (held-out test, n=256), reused as the per-anchor
    # baseline for "lift over same-anchor piecewise."
    PIECEWISE_LIFT_FF = {
        "cycle18_seed0": 3.005713888877396,
        "cycle21_seed1": 2.899545354389765,
        "cycle21_seed2": 2.275403095096121,
    }

    # Compose the long-CEM ladder per-anchor records.
    runs = [
        {"anchor": "cycle18_seed0", "rng_seed": 0, "test": c25_s0_seed0["best_by_val"]["test_score"], "lift_FF": c25_s0_seed0["best_by_val"]["lift_FF"]},
        {"anchor": "cycle21_seed1", "rng_seed": 0, "test": c23_s1_seed0["best_by_val"]["test_score"], "lift_FF": c23_s1_seed0["best_by_val"]["lift_FF"]},
        {"anchor": "cycle21_seed1", "rng_seed": 1, "test": c23_s1_seed1["best_by_val"]["test_score"], "lift_FF": c23_s1_seed1["best_by_val"]["lift_FF"]},
        {"anchor": "cycle21_seed1", "rng_seed": 2, "test": c24_s1_seed2["best_by_val"]["test_score"], "lift_FF": c24_s1_seed2["best_by_val"]["lift_FF"]},
        {"anchor": "cycle21_seed2", "rng_seed": 0, "test": c24_s2_seed0["best_by_val"]["test_score"], "lift_FF": c24_s2_seed0["best_by_val"]["lift_FF"]},
        {"anchor": "cycle21_seed2", "rng_seed": 1, "test": c25_s2_seed1["best_by_val"]["test_score"], "lift_FF": c25_s2_seed1["best_by_val"]["lift_FF"]},
    ]

    by_anchor: dict[str, list[dict]] = {}
    for r in runs:
        r["lift_over_piecewise"] = r["lift_FF"] - PIECEWISE_LIFT_FF[r["anchor"]]
        by_anchor.setdefault(r["anchor"], []).append(r)

    summary = {}
    for anchor, rs in by_anchor.items():
        lifts = np.asarray([r["lift_over_piecewise"] for r in rs])
        summary[anchor] = {
            "piecewise_lift_FF": PIECEWISE_LIFT_FF[anchor],
            "n_seeds": int(len(rs)),
            "mean_lift_over_piecewise": float(lifts.mean()),
            "stddev_lift_over_piecewise": float(lifts.std(ddof=1)) if len(rs) > 1 else None,
            "ladder_test_scores": [r["test"] for r in rs],
            "ladder_lift_FFs": [r["lift_FF"] for r in rs],
            "lift_over_piecewise": list(lifts),
            "rng_seeds": [r["rng_seed"] for r in rs],
        }

    with (EXP_DIR / "results/cross_seed_summary.json").open("w") as f:
        json.dump({"by_anchor": summary, "all_runs": runs}, f, indent=2)

    # === Figure 1: 3-anchor inverse-scaling plot ============================
    anchor_order = ["cycle21_seed2", "cycle21_seed1", "cycle18_seed0"]
    pw_lifts = np.asarray([PIECEWISE_LIFT_FF[a] for a in anchor_order])
    means = np.asarray([summary[a]["mean_lift_over_piecewise"] for a in anchor_order])
    stds = np.asarray(
        [
            summary[a]["stddev_lift_over_piecewise"] or 0.0
            for a in anchor_order
        ]
    )
    ns = [summary[a]["n_seeds"] for a in anchor_order]

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    ax.errorbar(pw_lifts, means, yerr=stds, fmt="o-", color="C2", lw=2, capsize=5, ms=8, label="long-CEM ladder mean ±σ")
    for x, y, anchor, n in zip(pw_lifts, means, anchor_order, ns):
        label = anchor.replace("cycle", "c").replace("_", "-")
        ax.annotate(
            f"{label}\nn={n}",
            (x, y),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=9,
            color="black",
        )
    # Underlay individual seed points
    for r in runs:
        ax.scatter(PIECEWISE_LIFT_FF[r["anchor"]], r["lift_over_piecewise"], color="C0", alpha=0.5, zorder=2, s=30)
    ax.axhline(0.0, color="grey", linestyle="--", lw=0.8)
    ax.set_xlabel("piecewise anchor quality (lift_FF on test, higher = stronger basin)")
    ax.set_ylabel("long-CEM ladder lift over same-anchor piecewise")
    ax.set_title("M4 long-CEM ladder: lift over piecewise vs anchor quality\n(cycles 23+24+25, n=6 runs across 3 anchors)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "m4_c25_anchor_lift_curve.png", dpi=140)
    fig.savefig(PRES_FIG_DIR / "m4_c25_anchor_lift_curve.png", dpi=140)
    plt.close(fig)

    # === Figure 2: CEM val trajectories on the new runs =====================
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), sharey=False)
    new_runs = [
        ("cycle21_seed2 / rng=1 (Q1)", c25_s2_seed1, "C0"),
        ("cycle18_seed0 / rng=0 (Q2)", c25_s0_seed0, "C3"),
    ]
    for ax, (title, run, color) in zip(axes, new_runs):
        hist = run["history"]
        gens = [h["gen"] for h in hist]
        bests = [h["best_score"] for h in hist]
        elites = [h["elite_mean_score"] for h in hist]
        ax.plot(gens, bests, "o-", color=color, label="best of gen")
        ax.plot(gens, elites, "s--", color=color, alpha=0.6, label="elite mean")
        # Anchor val score reference
        ax.axhline(run["anchor_val_score"], color="grey", linestyle=":", lw=1.0, label=f"anchor val ({run['anchor_val_score']:+.3f})")
        ax.set_title(title)
        ax.set_xlabel("CEM generation")
        ax.set_ylabel("search score")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=8)
    fig.suptitle("M4 cycle 25 — long-CEM ladder val trajectories (10g × 24p)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "m4_c25_long_cem_val_curves.png", dpi=140)
    fig.savefig(PRES_FIG_DIR / "m4_c25_long_cem_val_curves.png", dpi=140)
    plt.close(fig)

    # === Figure 3: bar chart of cross-anchor lift over piecewise ============
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    xs = np.arange(len(anchor_order))
    ax.bar(xs, means, yerr=stds, color=["C3", "C2", "C0"], capsize=6, edgecolor="black")
    for i, (m, s, n) in enumerate(zip(means, stds, ns)):
        annotation = f"{m:+.3f}"
        if n > 1:
            annotation += f"\n±{s:.3f}\n(n={n})"
        else:
            annotation += f"\n(n={n})"
        ax.text(i, max(m + (s if s else 0) + 0.05, m + 0.05), annotation, ha="center", fontsize=9)
    ax.axhline(0.0, color="grey", linestyle="--", lw=0.8)
    ax.set_xticks(xs)
    ax.set_xticklabels(
        [
            f"{a.replace('cycle','c').replace('_','-')}\npiecewise +{PIECEWISE_LIFT_FF[a]:.2f}"
            for a in anchor_order
        ]
    )
    ax.set_ylabel("ladder lift over same-anchor piecewise")
    ax.set_title("M4 long-CEM ladder: anchor-conditional lift\n(cycles 23+24+25)")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "m4_c25_lift_summary.png", dpi=140)
    fig.savefig(PRES_FIG_DIR / "m4_c25_lift_summary.png", dpi=140)
    plt.close(fig)

    # Print quick summary for the LOG.
    print("=== Cycle 25 cross-anchor long-CEM ladder summary ===")
    for a in anchor_order:
        s = summary[a]
        print(
            f"  {a:>14s}: piecewise +{s['piecewise_lift_FF']:.3f} "
            f"| ladder lift mean {s['mean_lift_over_piecewise']:+.3f} "
            f"(std {s['stddev_lift_over_piecewise'] if s['stddev_lift_over_piecewise'] else 'n/a'}, "
            f"n={s['n_seeds']})"
        )


if __name__ == "__main__":
    main()
