"""Render bar charts for cycle-16 per-trade-size decomposition."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXPDIR = ROOT / "research/experiments/2026-05-05-cycle16-trade-size-decomp"
RESULTS = EXPDIR / "results/size_decomp.json"
FIGDIR = EXPDIR / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    d = json.loads(RESULTS.read_text())
    buckets = ("small", "medium", "large")
    anchor_labels = [a["label"] for a in d["anchors"]]
    advs = {a["label"]: [a["per_bucket"][b]["retail_edge_advantage_mean"] for b in buckets] for a in d["anchors"]}
    err_lo = {a["label"]: [a["per_bucket"][b]["retail_edge_advantage_mean"] - a["per_bucket"][b]["retail_edge_advantage_ci95"][0] for b in buckets] for a in d["anchors"]}
    err_hi = {a["label"]: [a["per_bucket"][b]["retail_edge_advantage_ci95"][1] - a["per_bucket"][b]["retail_edge_advantage_mean"] for b in buckets] for a in d["anchors"]}

    cnt_sub = {a["label"]: [a["per_bucket"][b]["count_sub_mean"] for b in buckets] for a in d["anchors"]}
    cnt_norm = {a["label"]: [a["per_bucket"][b]["count_norm_mean"] for b in buckets] for a in d["anchors"]}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Panel 1: retail edge advantage by bucket
    ax = axes[0]
    n_b = len(buckets)
    width = 0.35
    x = np.arange(n_b)
    colors = {"c5_baseline": "#d62728", "c11_d16_s2": "#1f77b4"}
    for i, lab in enumerate(anchor_labels):
        vals = advs[lab]
        yerr = np.array([err_lo[lab], err_hi[lab]])
        ax.bar(x + (i - 0.5) * width, vals, width, label=lab, color=colors.get(lab, f"C{i}"), yerr=yerr, capsize=4, ecolor="black", alpha=0.85)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(buckets)
    ax.set_xlabel("Trade-size bucket (size_ratio = amount_y / reserve_y_post)")
    ax.set_ylabel("Retail edge advantage (sub − norm)\non real_data eval, n=128 seeds")
    ax.set_title("Cycle 16 — retail edge advantage by trade-size bucket\nc5 vs c11 ; cuts at 0.003 (small/medium) and 0.012 (medium/large)")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    # Panel 2: routing — trade count per bucket
    ax = axes[1]
    width = 0.18
    x_pos = np.arange(n_b)
    for i, lab in enumerate(anchor_labels):
        sub_vals = cnt_sub[lab]
        norm_vals = cnt_norm[lab]
        offs = -width if i == 0 else width
        # Place sub and norm side by side per anchor; differentiate by hatch
        ax.bar(x_pos + offs - 0.5 * width, sub_vals, width, color=colors.get(lab, f"C{i}"), alpha=0.9, label=f"{lab} → sub")
        ax.bar(x_pos + offs + 0.5 * width, norm_vals, width, color=colors.get(lab, f"C{i}"), alpha=0.4, hatch="///", label=f"{lab} → norm")
    ax.set_yscale("log")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(buckets)
    ax.set_xlabel("Trade-size bucket")
    ax.set_ylabel("Mean retail trade count per episode (log)")
    ax.set_title("Trade-count routing — solid=submission, hatched=normalizer")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4, which="both")

    fig.suptitle("c5 retail-edge OOD failure is concentrated in the small-trade bucket", fontsize=12, y=1.02)
    fig.tight_layout()
    out = FIGDIR / "retail_edge_by_bucket.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"-> wrote {out}")


if __name__ == "__main__":
    main()
