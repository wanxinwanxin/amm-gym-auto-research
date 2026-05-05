"""
Cycle-21 figures + cross-seed summary.

Inputs:
  results/seed1/{history.json, test.json, progress.log}
  results/seed2/{history.json, test.json, progress.log}
  cycle-18 long-CEM results (seed=0 reference) at
    research/experiments/2026-05-05-cycle18-m4-prior-sweep/results/long_cem_from_c11/

Outputs (figures/):
  m4_c21_long_cem_val_curves.png    — per-gen val score, 3 seeds overlaid
  m4_c21_long_cem_seed_dispersion.png — bar chart of test lift_FF, 3 seeds
                                          (long-CEM piecewise) + ladder reference

Outputs (results/):
  cross_seed_summary.json           — mean / std / range across 3 seeds
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-05-cycle21-m4-longcem-multiseed"
C18 = (
    ROOT
    / "research/experiments/2026-05-05-cycle18-m4-prior-sweep/results/long_cem_from_c11"
)
LADDER = (
    ROOT
    / "research/experiments/2026-05-05-cycle20-m4-ladder-repro/results"
)

FIG_DIR = EXP_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
RES_DIR = EXP_DIR / "results"
RES_DIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # --- Load 3 long-CEM seed runs ---
    seed_runs = [
        {"seed": 0, "label": "seed 0 (cycle 18)", "history": C18 / "history.json", "test": C18 / "test.json"},
        {"seed": 1, "label": "seed 1 (cycle 21)", "history": EXP_DIR / "results/seed1/history.json", "test": EXP_DIR / "results/seed1/test.json"},
        {"seed": 2, "label": "seed 2 (cycle 21)", "history": EXP_DIR / "results/seed2/history.json", "test": EXP_DIR / "results/seed2/test.json"},
    ]
    for run in seed_runs:
        run["history_data"] = _load(run["history"])
        run["test_data"] = _load(run["test"])

    # --- Load ladder seeds for reference (from cycle-20 summary.json) ---
    ladder_summary_p = LADDER / "summary.json"
    ladder_runs = []
    if ladder_summary_p.exists():
        ladder_summary = _load(ladder_summary_p)
        for key, val in ladder_summary["seeds"].items():
            sid = int(key.split("_")[1])
            ladder_runs.append({
                "seed": sid,
                "test_data": {"best_by_val": {"lift_FF": val["lift_FF"]}},
            })
        ladder_runs.sort(key=lambda r: r["seed"])

    # --- Anchor (FF baseline) ---
    ff_score = seed_runs[0]["test_data"]["best_by_val"]["ff_test_score"]

    # --- val_curves figure ---
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for run, color in zip(seed_runs, colors):
        hist = run["history_data"]["history"]
        gens = [h["generation"] for h in hist]
        vals = [h["fixed_val_score"] for h in hist]
        ax.plot(gens, vals, marker="o", linewidth=2, color=color, label=run["label"])
    # anchor val (c11 = same for all)
    ax.axhline(
        seed_runs[0]["history_data"]["c11_val_score"],
        color="black",
        linestyle="--",
        linewidth=1.0,
        label="c11 anchor val",
    )
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("best-search val score (n=128)")
    ax.set_title("M4 cycle-21 — long-CEM val trajectory (10g x 24p, piecewise, 3 seeds)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "m4_c21_long_cem_val_curves.png", dpi=110)
    plt.close(fig)

    # --- seed_dispersion figure ---
    fig, ax = plt.subplots(figsize=(9, 5))
    long_cem_lifts = [r["test_data"]["best_by_val"]["lift_FF"] for r in seed_runs]
    long_cem_labels = [f"seed {r['seed']}" for r in seed_runs]
    long_mean = float(np.mean(long_cem_lifts))
    long_std = float(np.std(long_cem_lifts, ddof=0))
    ladder_lifts = [r["test_data"]["best_by_val"]["lift_FF"] for r in ladder_runs]
    ladder_mean = float(np.mean(ladder_lifts)) if ladder_lifts else float("nan")
    ladder_std = float(np.std(ladder_lifts, ddof=0)) if ladder_lifts else float("nan")
    ladder_labels = [f"ladder s{r['seed']}" for r in ladder_runs]

    xs = np.arange(len(long_cem_lifts) + len(ladder_lifts))
    bar_labels = long_cem_labels + ladder_labels
    bar_vals = long_cem_lifts + ladder_lifts
    bar_colors = [colors[i] for i in range(len(long_cem_lifts))] + ["#7f7f7f"] * len(ladder_lifts)

    ax.bar(xs, bar_vals, color=bar_colors)
    for i, v in enumerate(bar_vals):
        ax.text(i, v + 0.04, f"{v:+.3f}", ha="center", fontsize=9)
    if ladder_lifts:
        ax.axhline(ladder_mean, color="#7f7f7f", linestyle=":", linewidth=1.0, label=f"ladder mean (n=3) = {ladder_mean:+.3f}")
    ax.axhline(long_mean, color="#1f77b4", linestyle=":", linewidth=1.0, label=f"long-CEM piecewise mean (n=3) = {long_mean:+.3f}")
    ax.axhline(3.20, color="red", linestyle="--", linewidth=0.8, alpha=0.5, label="decision threshold +3.20")
    ax.axhline(3.00, color="green", linestyle="--", linewidth=0.8, alpha=0.5, label="decision threshold +3.00")
    ax.set_xticks(xs)
    ax.set_xticklabels(bar_labels, rotation=20)
    ax.set_ylabel("test lift_FF (n=256)")
    ax.set_title("M4 cycle-21 — long-CEM piecewise (3 seeds) vs cycle-20 ladder (3 seeds)")
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "m4_c21_long_cem_seed_dispersion.png", dpi=110)
    plt.close(fig)

    # --- summary json ---
    summary = {
        "long_cem_piecewise": {
            "seeds": [r["seed"] for r in seed_runs],
            "test_scores": [r["test_data"]["best_by_val"]["test_score"] for r in seed_runs],
            "lift_FF": long_cem_lifts,
            "retail_adv": [r["test_data"]["best_by_val"]["test_retail_advantage"] for r in seed_runs],
            "edge_adv": [r["test_data"]["best_by_val"]["test_edge_advantage"] for r in seed_runs],
            "mean_lift_FF": long_mean,
            "std_lift_FF": long_std,
            "min_lift_FF": float(np.min(long_cem_lifts)),
            "max_lift_FF": float(np.max(long_cem_lifts)),
            "ff_test_score": ff_score,
        },
        "ladder_reference": {
            "seeds": [r["seed"] for r in ladder_runs],
            "lift_FF": ladder_lifts,
            "mean_lift_FF": ladder_mean,
            "std_lift_FF": ladder_std,
        },
        "decision_band": {
            "ceiling_is_budget_above": 3.20,
            "ceiling_is_population_below": 3.00,
            "long_cem_mean_lift_FF": long_mean,
            "verdict": (
                "ceiling_was_budget" if long_mean > 3.20
                else ("ceiling_is_population" if long_mean >= 3.00 else "ceiling_even_tighter")
            ),
        },
    }
    (RES_DIR / "cross_seed_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
