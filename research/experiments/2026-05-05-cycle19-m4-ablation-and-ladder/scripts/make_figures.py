"""Cycle-19 figures: param-importance ablation bar chart and ladder val curve."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "research/experiments/2026-05-05-cycle19-m4-ablation-and-ladder"
FIG = EXP / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def make_ablation_figure() -> None:
    p = EXP / "results/ablation/results.json"
    if not p.exists():
        print(f"ablation results missing: {p}")
        return
    d = json.load(p.open())
    rows = d["ranked"]
    base = d["baseline"]
    anchor = d["anchor_baseline"]
    base_score = base["score"]
    anchor_score = anchor["score"]

    # Sort ascending by drop for horizontal bar (largest at top)
    rows_sorted = sorted(rows, key=lambda r: r["score_drop"])
    names = [r["param"] for r in rows_sorted]
    drops = [r["score_drop"] for r in rows_sorted]
    colors = ["#cc3333" if d > 0.1 else ("#888888" if d > -0.05 else "#3366aa") for d in drops]

    fig, ax = plt.subplots(figsize=(10, 6.5))
    y = np.arange(len(names))
    ax.barh(y, drops, color=colors, edgecolor="black", alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Δ val score (baseline − reset_to_anchor)")
    ax.set_title(
        f"Param-importance ablation: c11+CEM long → reset param i to c11 anchor\n"
        f"baseline (c11+CEM long) val={base_score:.3f}; "
        f"full anchor val={anchor_score:.3f} (Δ {base_score-anchor_score:+.3f})"
    )
    ax.axvline(0.0, color="black", linewidth=0.7)
    ax.axvline(base_score - anchor_score, color="green", linestyle=":", alpha=0.6,
               label=f"full reset Δ={base_score-anchor_score:.3f}")
    for i, (drop, row) in enumerate(zip(drops, rows_sorted)):
        ax.text(drop + (0.02 if drop >= 0 else -0.02), i,
                f"{drop:+.3f}", va="center",
                ha="left" if drop >= 0 else "right", fontsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.legend(loc="lower right")
    plt.tight_layout()
    out = FIG / "m4_c19_param_importance.png"
    plt.savefig(out, dpi=110)
    plt.close()
    print(f"wrote {out}")


def make_ladder_val_figure() -> None:
    p = EXP / "results/ladder_cem/test.json"
    if not p.exists():
        print(f"ladder test.json missing: {p}")
        return
    d = json.load(p.open())
    history = d.get("history", [])
    if not history:
        print("ladder history empty")
        return
    gens = [h["gen"] for h in history]
    best = [h["best_score"] for h in history]
    elite_mean = [h["elite_mean_score"] for h in history]
    all_mean = [h["mean_score"] for h in history]
    anchor_val = d.get("anchor_val_score", 3.885)
    best_by_val = d.get("best_by_val", {})
    best_test = best_by_val.get("test_score")
    best_lift_FF = best_by_val.get("lift_FF")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(gens, best, "o-", label="gen best (search seeds, n=64)", color="#cc3333", linewidth=2)
    ax.plot(gens, elite_mean, "s-", label="elite mean (top 2)", color="#cc6600", linewidth=1.5)
    ax.plot(gens, all_mean, ".--", label="all-pop mean (n=12)", color="#888888", alpha=0.7)
    ax.axhline(anchor_val, color="green", linestyle=":", alpha=0.6,
               label=f"anchor val (c11+CEM long extended) = {anchor_val:.3f}")
    if best_test is not None:
        ax.axhline(best_test, color="purple", linestyle="--", alpha=0.5,
                   label=f"best-by-val test (n=256) = {best_test:.3f} (lift_FF {best_lift_FF:+.3f})")
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("score")
    ax.set_title("Ladder-family (k=4) CEM warm-started from c11+CEM long")
    ax.grid(linestyle="--", alpha=0.4)
    ax.legend(loc="best", fontsize=9)
    plt.tight_layout()
    out = FIG / "m4_c19_ladder_val_curve.png"
    plt.savefig(out, dpi=110)
    plt.close()
    print(f"wrote {out}")


def main() -> None:
    make_ablation_figure()
    make_ladder_val_figure()


if __name__ == "__main__":
    main()
