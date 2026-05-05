"""Make cycle-23 figures: long-CEM ladder vs short-CEM ladder vs piecewise.

The headline question is whether the ladder family payoff manifests at
the long-CEM budget (10g x 24p, matching cycle-18 piecewise compute),
since cycle 22 falsified it at the short-CEM budget (5g x 12p).

Figures:
  1. m4_c23_long_vs_short_ladder_lift.png — bar chart comparing
     short-CEM ladder lift over piecewise (cycle 22) vs long-CEM ladder
     lift over piecewise (cycle 23), all on the cycle-21-seed-1 anchor.
  2. m4_c23_longcem_val_curves.png — CEM search-best per generation
     for both rng seeds, with the anchor val line overlaid.
  3. cross_seed_summary.json — machine-readable summary.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-06-cycle23-m4-ladder-longcem"
C22_DIR = ROOT / "research/experiments/2026-05-05-cycle22-m4-ladder-anchor-control"
FIGDIR = EXP_DIR / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path) -> dict:
    return json.load(path.open())


def main() -> None:
    runs = {}
    for run in ("cycle21_seed1_seed0", "cycle21_seed1_seed1"):
        p = EXP_DIR / "results" / run / "test.json"
        if p.exists():
            runs[run] = _load(p)

    # --- Reference numbers (locked from prior cycles) ---
    # piecewise on the cycle-21-seed-1 anchor: test 3.370 / lift_FF +2.900
    piecewise_anchor_lift_FF = 2.900
    # cycle-22 short-CEM ladder on the same anchor: lift = +0.000 / +0.000
    c22_short_ladder_lift_FF = [
        2.900,  # cycle21_seed1_seed0 (rerank picked anchor)
        2.900,  # cycle21_seed1_seed1 (rerank picked anchor)
    ]
    # cycle-19 short-CEM ladder on cycle-18-seed-0 anchor: lift = +0.245
    c19_short_ladder_lift_FF = 3.251
    c18s0_piecewise_anchor_lift_FF = 3.006

    # --- Fig 1: lift bar chart ---
    rows: list[tuple[str, str, float, float]] = []
    rows.append(("cycle18-s0\n(short-CEM)",
                 "cycle 19 ladder (single-seed)",
                 c19_short_ladder_lift_FF,
                 c19_short_ladder_lift_FF - c18s0_piecewise_anchor_lift_FF))
    for i, lift in enumerate(c22_short_ladder_lift_FF):
        rows.append((f"cycle21-s1\n(short-CEM)",
                     f"cycle 22 ladder seed={i}",
                     lift,
                     lift - piecewise_anchor_lift_FF))
    for run, d in runs.items():
        seed = run.split("_seed")[-1]
        rows.append((f"cycle21-s1\n(LONG-CEM)",
                     f"cycle 23 ladder seed={seed}",
                     d["best_by_val"]["lift_FF"],
                     d["best_by_val"]["lift_FF"] - piecewise_anchor_lift_FF))

    labels = [f"{r[0]}\n{r[1]}" for r in rows]
    deltas = [r[3] for r in rows]
    colors = ["#1f77b4", "#ff7f0e", "#ff7f0e", "#d62728", "#d62728"][: len(rows)]

    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    bars = ax.bar(range(len(labels)), deltas, color=colors, alpha=0.85)
    ax.axhline(0.0, color="black", linewidth=0.7)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=8)
    ax.set_ylabel("ladder test lift_FF − piecewise anchor lift_FF (same anchor)")
    title = (
        "Ladder family lift over the same-anchor piecewise (cycle-23 long-CEM extension)\n"
        "Decision rule: long-CEM lift > +0.20 → family is real at long budget"
    )
    ax.set_title(title)
    for d, b in zip(deltas, bars):
        y = d + (0.005 if d >= 0 else -0.02)
        ax.text(b.get_x() + b.get_width() / 2, y,
                f"{d:+.3f}", ha="center", va="bottom" if d >= 0 else "top", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGDIR / "m4_c23_long_vs_short_ladder_lift.png", dpi=140)
    plt.close(fig)

    # --- Fig 2: CEM val curves ---
    fig, ax = plt.subplots(figsize=(9.0, 5.5))
    palette = {"cycle21_seed1_seed0": "#d62728", "cycle21_seed1_seed1": "#9467bd"}
    for run, d in runs.items():
        history = d["history"]
        gens = [h["gen"] for h in history]
        ax.plot(gens, [h["best_score"] for h in history], "o-",
                color=palette[run], label=f"{run} best (search n=64)")
        ax.plot(gens, [h["elite_mean_score"] for h in history], "s--",
                color=palette[run], alpha=0.6, label=f"{run} elite mean (search n=64)")
    if runs:
        ax.axhline(next(iter(runs.values()))["anchor_val_score"], color="black",
                   linestyle=":", label=f"anchor val (n=128) = {next(iter(runs.values()))['anchor_val_score']:.3f}")
    # Overlay cycle-22 short-CEM trajectories for comparison
    for run in ("cycle21_seed1_seed0", "cycle21_seed1_seed1"):
        p = C22_DIR / "results" / run / "test.json"
        if not p.exists():
            continue
        d22 = _load(p)
        history = d22["history"]
        gens = [h["gen"] for h in history]
        c22_color = "#ff7f0e" if "seed0" in run else "#bcbd22"
        ax.plot(gens, [h["best_score"] for h in history], "x-",
                color=c22_color, alpha=0.55, linewidth=1.0,
                label=f"cycle-22 short {run} best")
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("score (search n=64 for best/elite; val n=128 for anchor)")
    ax.set_title("Cycle-23 long-CEM ladder trajectories vs cycle-22 short-CEM (same anchor)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR / "m4_c23_longcem_val_curves.png", dpi=140)
    plt.close(fig)

    # --- Cross-seed summary ---
    summary = {
        "anchor": "cycle21_seed1 piecewise (long-CEM, cycle-21-seed-1 best_by_val)",
        "anchor_test_score": 3.370,
        "anchor_lift_FF": piecewise_anchor_lift_FF,
        "cycle23_runs": [
            {
                "rng_seed": int(run.split("_seed")[-1]),
                "best_by_val_source": d["best_by_val"]["source"],
                "test_score": d["best_by_val"]["test_score"],
                "val_score": d["best_by_val"]["val_score"],
                "lift_FF": d["best_by_val"]["lift_FF"],
                "lift_over_piecewise_anchor": d["best_by_val"]["lift_FF"] - piecewise_anchor_lift_FF,
                "retail_advantage_test": d["best_by_val"]["test_retail_advantage"],
            }
            for run, d in runs.items()
        ],
        "context": {
            "cycle22_short_ladder_lift_over_piecewise": c22_short_ladder_lift_FF,
            "cycle19_short_ladder_lift_FF_on_cycle18s0": c19_short_ladder_lift_FF,
            "cycle19_lift_over_cycle18s0_piecewise": c19_short_ladder_lift_FF - c18s0_piecewise_anchor_lift_FF,
        },
    }
    with (EXP_DIR / "results/cross_seed_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
