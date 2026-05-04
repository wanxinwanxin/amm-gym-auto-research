"""
Cycle-12 figure: per-gen best-search/val for the two CEMs (latent_full
and fresh-anchor piecewise) plotted alongside the prior warm-start
cluster's saturation band.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
FIGURES = HERE.parent / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def _load(name: str) -> dict | None:
    path = RESULTS / name
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> None:
    ladder = _load("latent_full_history.json")
    fresh = _load("fresh_anchor_piecewise_history.json")
    ladder_test = _load("latent_full_test.json")
    fresh_test = _load("fresh_anchor_piecewise_test.json")

    if ladder is None or fresh is None:
        print("Missing one or both history JSONs; skipping figure", file=sys.stderr)
        return

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.0), constrained_layout=True)

    # Panel A: per-gen progression for the two cells.
    axA = axes[0]
    PIECEWISE_BAR = 456.803  # cycle 11 d16_s2
    PIECEWISE_PRIOR = 414.010  # cycle 5 starting line
    TARGET = 540.0

    for hist, label, color in (
        (ladder, "latent_full (18d, init_std=0.25)", "#1f77b4"),
        (fresh, "piecewise fresh (16d, init_std=0.30)", "#d62728"),
    ):
        gens = [g["generation"] for g in hist["history"]]
        best = [g["best_search_score"] for g in hist["history"]]
        val = [g["fixed_val_score"] for g in hist["history"]]
        elite = [g["elite_mean_search_score"] for g in hist["history"]]
        axA.plot(gens, best, "o-", color=color, label=f"{label}: best_search", lw=1.5)
        axA.plot(gens, val, "s--", color=color, label=f"{label}: fixed_val", lw=1.0, alpha=0.7)
        axA.plot(gens, elite, ":", color=color, alpha=0.5)

    axA.axhline(PIECEWISE_BAR, color="k", linestyle="-", lw=0.8, alpha=0.6, label=f"warm-start bar 456.8")
    axA.axhline(PIECEWISE_PRIOR, color="grey", linestyle=":", lw=0.8, alpha=0.6, label=f"cycle-5 starting 414")
    axA.set_xlabel("generation")
    axA.set_ylabel("score")
    axA.set_title("Cycle 12 — per-gen best/val/elite-mean")
    axA.legend(loc="lower right", fontsize=8)
    axA.grid(alpha=0.3)

    # Panel B: M2 progression bar chart over cycles.
    axB = axes[1]
    cells = [
        ("c5 inherited", PIECEWISE_PRIOR, "#cccccc"),
        ("c6 piecewise warm", 432.75, "#a8d5a8"),
        ("c8 inv-piecewise", 446.61, "#90c890"),
        ("c9 #1 piecewise", 448.81, "#78bb78"),
        ("c9 #3 EMA-inv", 456.64, "#60ae60"),
        ("c10 A noop-tail", 456.74, "#48a148"),
        ("c10 B seed1", 452.96, "#48a148"),
        ("c11 d16_s2", 456.80, "#309430"),
        ("c11 d24_s0", 455.66, "#309430"),
        ("c11 d24_s1", 452.57, "#309430"),
    ]
    if ladder_test:
        score = ladder_test["best_by_val"]["test_score"]
        cells.append(("c12 latent_full", score, "#1f77b4"))
    if fresh_test:
        score = fresh_test["best_by_val"]["test_score"]
        cells.append(("c12 piecewise fresh", score, "#d62728"))

    labels = [c[0] for c in cells]
    scores = [c[1] for c in cells]
    colors = [c[2] for c in cells]
    bars = axB.bar(range(len(cells)), scores, color=colors)
    axB.set_xticks(range(len(cells)))
    axB.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axB.set_ylabel("test score (held-out 256 seeds)")
    axB.set_title("M2 cumulative history (cycle 5 → 12)")
    axB.axhline(PIECEWISE_BAR, color="k", linestyle="--", lw=0.6, alpha=0.6)
    axB.axhline(TARGET, color="r", linestyle="--", lw=0.6, alpha=0.6, label="target 540")
    axB.set_ylim(380, 560)
    axB.grid(axis="y", alpha=0.3)
    for b, s in zip(bars, scores):
        axB.text(b.get_x() + b.get_width() / 2, s + 1, f"{s:.1f}", ha="center", fontsize=7)

    out = FIGURES / "cycle12_summary.png"
    fig.savefig(out, dpi=110)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
