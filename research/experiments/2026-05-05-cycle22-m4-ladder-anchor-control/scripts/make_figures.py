"""Make cycle-22 figures for cross-anchor ladder vs piecewise comparison."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-05-cycle22-m4-ladder-anchor-control"
FIGDIR = EXP_DIR / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)


def _load(run: str) -> dict:
    return json.load((EXP_DIR / "results" / run / "test.json").open())


def main() -> None:
    runs = {
        "cycle21_seed1_seed0": _load("cycle21_seed1_seed0"),
        "cycle21_seed1_seed1": _load("cycle21_seed1_seed1"),
    }
    # Optionally include the stretch run if it's done.
    stretch = EXP_DIR / "results/cycle21_seed2_seed0/test.json"
    if stretch.exists():
        runs["cycle21_seed2_seed0"] = json.load(stretch.open())

    # ---------- Fig 1: anchor lift bar ----------
    # Cross-anchor lift: ladder best_by_val test_score - piecewise anchor test
    piecewise_anchor_test = {
        "cycle18_seed0": 3.476,    # cycle-18 long CEM
        "cycle21_seed1": 3.370,    # cycle-21 long CEM
        "cycle21_seed2": 2.746,    # cycle-21 long CEM (basin-collapsed)
    }
    piecewise_anchor_lift_FF = {
        "cycle18_seed0": 3.006,
        "cycle21_seed1": 2.900,
        "cycle21_seed2": 2.275,
    }

    # Cycle-19 ladder (single-seed) was warm-started from cycle18_seed0:
    # test 3.721, lift_FF +3.251 → cross-anchor lift +0.245.
    # Cycle-22 seeds 0,1 from cycle21_seed1: lift = 0.000, 0.000.
    rows = []
    rows.append(("cycle18_seed0", "ladder seed=0 (cycle 19)", 3.721, 3.251))
    if (EXP_DIR / "results/cycle21_seed1_seed0/test.json").exists():
        d = runs["cycle21_seed1_seed0"]
        rows.append(("cycle21_seed1", "ladder seed=0 (cycle 22)",
                     d["best_by_val"]["test_score"], d["best_by_val"]["lift_FF"]))
    if (EXP_DIR / "results/cycle21_seed1_seed1/test.json").exists():
        d = runs["cycle21_seed1_seed1"]
        rows.append(("cycle21_seed1", "ladder seed=1 (cycle 22)",
                     d["best_by_val"]["test_score"], d["best_by_val"]["lift_FF"]))
    if "cycle21_seed2_seed0" in runs:
        d = runs["cycle21_seed2_seed0"]
        rows.append(("cycle21_seed2", "ladder seed=0 (cycle 22)",
                     d["best_by_val"]["test_score"], d["best_by_val"]["lift_FF"]))

    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    labels = []
    deltas = []
    colors = []
    anchor_color = {"cycle18_seed0": "#1f77b4", "cycle21_seed1": "#ff7f0e", "cycle21_seed2": "#2ca02c"}
    for anchor, lab, _ts, lift in rows:
        labels.append(f"{anchor}\n{lab}")
        deltas.append(lift - piecewise_anchor_lift_FF[anchor])
        colors.append(anchor_color[anchor])
    bars = ax.bar(range(len(labels)), deltas, color=colors, alpha=0.8)
    ax.axhline(0.0, color="black", linewidth=0.7)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("ladder test lift_FF − piecewise anchor test lift_FF")
    ax.set_title(
        "Ladder family lift over the same-anchor piecewise (cycle-22 cross-anchor control)\n"
        "Negative or zero on the cycle-21 anchors → cycle-19's +0.245 is anchor-driven, not a family effect"
    )
    for i, (d, b) in enumerate(zip(deltas, bars)):
        ax.text(b.get_x() + b.get_width() / 2, d + (0.005 if d >= 0 else -0.02),
                f"{d:+.3f}", ha="center", va="bottom" if d >= 0 else "top", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGDIR / "m4_c22_cross_anchor_ladder_lift.png", dpi=140)
    plt.close(fig)

    # ---------- Fig 2: CEM val curves vs anchor for seeds 0,1 ----------
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    palette = {"cycle21_seed1_seed0": "#ff7f0e", "cycle21_seed1_seed1": "#d62728"}
    for run, d in runs.items():
        if not run.startswith("cycle21_seed1"):
            continue
        history = d["history"]
        gens = [h["gen"] for h in history]
        # The 'best_score' is search-set (n=64); to overlay val, use the anchor val + final rerank vals
        ax.plot(gens, [h["best_score"] for h in history], "o-",
                color=palette[run], label=f"{run} best (search n=64)")
        ax.plot(gens, [h["elite_mean_score"] for h in history], "s--",
                color=palette[run], alpha=0.6, label=f"{run} elite mean (search n=64)")
    ax.axhline(runs["cycle21_seed1_seed0"]["anchor_val_score"], color="black",
               linestyle=":", label="anchor val (n=128) = 3.651")
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("score (n=64 search seeds for best/elite_mean; n=128 val for anchor)")
    ax.set_title("Cycle-22 ladder CEM trajectories on cycle-21-seed-1 piecewise anchor")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGDIR / "m4_c22_seed1_anchor_val_curves.png", dpi=140)
    plt.close(fig)

    # ---------- Cross-seed summary JSON ----------
    summary = {
        "anchors": {
            "cycle21_seed1": {
                "piecewise_anchor": {
                    "test_score": piecewise_anchor_test["cycle21_seed1"],
                    "lift_FF": piecewise_anchor_lift_FF["cycle21_seed1"],
                },
                "ladder_runs": [
                    {"rng_seed": 0, "best_by_val_source":
                     runs["cycle21_seed1_seed0"]["best_by_val"]["source"],
                     "test_score": runs["cycle21_seed1_seed0"]["best_by_val"]["test_score"],
                     "lift_FF": runs["cycle21_seed1_seed0"]["best_by_val"]["lift_FF"]},
                    {"rng_seed": 1, "best_by_val_source":
                     runs["cycle21_seed1_seed1"]["best_by_val"]["source"],
                     "test_score": runs["cycle21_seed1_seed1"]["best_by_val"]["test_score"],
                     "lift_FF": runs["cycle21_seed1_seed1"]["best_by_val"]["lift_FF"]},
                ],
                "ladder_lift_over_piecewise_seed1": [
                    runs["cycle21_seed1_seed0"]["best_by_val"]["lift_FF"]
                    - piecewise_anchor_lift_FF["cycle21_seed1"],
                    runs["cycle21_seed1_seed1"]["best_by_val"]["lift_FF"]
                    - piecewise_anchor_lift_FF["cycle21_seed1"],
                ],
            },
        },
        "cycle19_reference": {
            "anchor": "cycle18_seed0",
            "ladder_test": 3.721,
            "ladder_lift_FF": 3.251,
            "piecewise_anchor_lift_FF": piecewise_anchor_lift_FF["cycle18_seed0"],
            "lift_over_piecewise": 3.251 - piecewise_anchor_lift_FF["cycle18_seed0"],
        },
    }
    if "cycle21_seed2_seed0" in runs:
        d = runs["cycle21_seed2_seed0"]
        summary["anchors"]["cycle21_seed2"] = {
            "piecewise_anchor": {
                "test_score": piecewise_anchor_test["cycle21_seed2"],
                "lift_FF": piecewise_anchor_lift_FF["cycle21_seed2"],
            },
            "ladder_runs": [
                {"rng_seed": 0,
                 "best_by_val_source": d["best_by_val"]["source"],
                 "test_score": d["best_by_val"]["test_score"],
                 "lift_FF": d["best_by_val"]["lift_FF"]},
            ],
            "ladder_lift_over_piecewise_seed2": [
                d["best_by_val"]["lift_FF"] - piecewise_anchor_lift_FF["cycle21_seed2"],
            ],
        }

    with (EXP_DIR / "results/cross_anchor_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
