#!/usr/bin/env python3
"""Per-day bar chart of router vs non-router vs all means, with sim baseline reference line."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EXP = Path(__file__).resolve().parents[1]
INFILE = EXP / "results/multi_day_breakdown.json"
OUT = EXP / "figures/per_day_means.png"


def main() -> None:
    with INFILE.open() as f:
        d = json.load(f)

    days = [row["dt"][5:] for row in d["per_day"]]
    router = [row["router"]["mean_bps_next"] for row in d["per_day"]]
    nonrouter = [row["non_router"]["mean_bps_next"] for row in d["per_day"]]
    all_ = [row["all"]["mean_bps_next"] for row in d["per_day"]]

    sim_mean = d["comparison_with_sim"]["sim_retail_mean_bps_next"]

    x = np.arange(len(days))
    w = 0.27

    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar(x - w, router, w, label="ROUTER", color="#d62728")
    ax.bar(x, nonrouter, w, label="NON-ROUTER", color="#2ca02c")
    ax.bar(x + w, all_, w, label="ALL retail", color="#7f7f7f")

    ax.axhline(sim_mean, color="#1f77b4", lw=2.5, ls="--",
               label=f"Sim retail (fee=5 bps, mean={sim_mean:.2f})")
    ax.axhline(0, color="k", lw=0.5)

    five_day_router = d["five_day_aggregate"]["router"]["weighted_mean_bps_next"]
    five_day_nonrouter = d["five_day_aggregate"]["non_router"]["weighted_mean_bps_next"]
    five_day_all = d["five_day_aggregate"]["all"]["weighted_mean_bps_next"]

    ax.text(
        0.99, 0.97,
        f"5-day weighted means\n"
        f"  Router:     +{five_day_router:.2f} bps\n"
        f"  Non-router: +{five_day_nonrouter:.2f} bps\n"
        f"  All:        +{five_day_all:.2f} bps\n"
        f"\nSim - Router gap = {sim_mean - five_day_router:+.2f} bps",
        ha="right", va="top", transform=ax.transAxes,
        fontsize=9, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.9),
    )

    ax.set_xticks(x)
    ax.set_xticklabels(days)
    ax.set_xlabel("block_date (2026-)")
    ax.set_ylabel("mean markout_next (bps)")
    ax.set_title(
        "Mean retail markout, by day and router-flag (canonical WETH/USDC v3 0.05% pool)\n"
        "Router-only on-chain flow has near-zero mean markout — the gap to sim is ~5 bps, not ~2.7."
    )
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
