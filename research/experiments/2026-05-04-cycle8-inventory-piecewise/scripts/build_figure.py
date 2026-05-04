"""Cycle-8 inventory-aware piecewise figures.

Three panels, all derived from `inventory_warmstart_cem_history.json`:

1. Convergence: best_search and val per generation, with cycle-6 piecewise
   plateau drawn as a horizontal reference.
2. Inv-skew dynamics: elite-mean of (inv_skew_to_bid, inv_skew_to_ask,
   inv_skew_dead_zone) over generations. Detects whether CEM ever
   meaningfully moved the new dimensions away from zero.
3. Headline bar: piecewise inherited (414.0), cycle-6 piecewise warm-start
   (432.7), cycle-8 inventory-aware piecewise warm-start (this run's
   test_score). Shows whether the new family adds anything on test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPDIR = ROOT / "research/experiments/2026-05-04-cycle8-inventory-piecewise"
RESULTS = EXPDIR / "results"
FIGURES = EXPDIR / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    history = json.loads((RESULTS / "inventory_warmstart_cem_history.json").read_text())["history"]
    test = json.loads((RESULTS / "inventory_warmstart_cem_test.json").read_text())

    gens = np.asarray([g["generation"] for g in history])
    best_search = np.asarray([g["best_search_score"] for g in history])
    val = np.asarray([g["fixed_val_score"] for g in history])
    inv_bid = np.asarray([g["inv_skew_to_bid_mean"] for g in history])
    inv_ask = np.asarray([g["inv_skew_to_ask_mean"] for g in history])
    inv_dz = np.asarray([g["inv_skew_dead_zone_mean"] for g in history])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # Panel 1: convergence
    ax = axes[0]
    ax.plot(gens, best_search, marker="o", color="#3C7BB0", label="best_search (64 seeds)")
    ax.plot(gens, val, marker="s", color="#D9534F", label="val (128 seeds)")
    ax.axhline(427.52, ls="--", color="grey", alpha=0.7, label="cycle-6 piecewise search ref")
    ax.axhline(433.57, ls=":", color="#7F7F7F", alpha=0.7, label="cycle-6 piecewise val ref")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Score")
    ax.set_title("Inventory-aware piecewise warm-start CEM")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")

    # Panel 2: inv-skew elite means over gens
    ax = axes[1]
    ax.plot(gens, inv_bid, marker="o", color="#3C7BB0", label="inv_skew_to_bid (mean)")
    ax.plot(gens, inv_ask, marker="s", color="#D9534F", label="inv_skew_to_ask (mean)")
    ax.plot(gens, inv_dz, marker="^", color="#5CB85C", label="inv_skew_dead_zone (mean)")
    ax.axhline(0.0, ls="--", color="grey", alpha=0.6)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Elite-population mean")
    ax.set_title("Inventory-skew dynamics")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="best")

    # Panel 3: headline bar
    ax = axes[2]
    bars = [
        ("piecewise\ninherited", 414.01, "#7F7F7F"),
        ("piecewise\ncycle-6 warm-start", 432.75, "#3C7BB0"),
        (
            "inventory-aware\ncycle-8 warm-start",
            test["best_by_val"]["test_score"],
            "#5CB85C",
        ),
    ]
    xs = np.arange(len(bars))
    heights = [b[1] for b in bars]
    colors = [b[2] for b in bars]
    ax.bar(xs, heights, color=colors)
    ax.axhline(540, ls="--", color="#D9534F", alpha=0.7, label="M2 target = 540")
    for i, h in enumerate(heights):
        ax.text(i, h + 4, f"{h:.1f}", ha="center", fontsize=9)
    ax.set_xticks(xs)
    ax.set_xticklabels([b[0] for b in bars], fontsize=9)
    ax.set_ylabel("Test score (256 seeds)")
    ax.set_title("M2 progress")
    ax.set_ylim(380, 560)
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.25, axis="y")

    fig.tight_layout()
    out = FIGURES / "inventory_aware_summary.png"
    fig.savefig(out, dpi=120)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
