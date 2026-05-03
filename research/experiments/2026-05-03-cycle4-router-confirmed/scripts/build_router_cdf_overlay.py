#!/usr/bin/env python3
"""Build the router-vs-non-router CDF overlay figure (cycle 4).

Layers four CDFs of `markout_next` (in bps) on the canonical WETH/USDC v3 0.05% pool:
  - Sim retail (cycle-2 baseline, fee=5 bps, seeds 0..31)
  - On-chain ALL retail (4-27)
  - On-chain ROUTER-only (4-27)
  - On-chain NON-ROUTER (4-27)

The headline takeaway: the simulator's retail flow was fitted from router-only on-chain
swaps, so the apples-to-apples reference is the ROUTER curve — not the all-flow curve.
The gap is ~5 bps (much bigger than the ~2.7 bps reported in cycle 2).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[3] / ".."  # research/experiments/<id>/scripts -> repo root
REPO = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
OUT = EXP / "figures" / "router_cdf_overlay.png"

SIM_PARQUET = REPO / "research/experiments/2026-04-30-2240-m1-baseline-markout/results/sim_markouts.parquet"
QUANT_JSON = EXP / "results/router_quantiles_2026-04-27.json"
ALL_QUANT_JSON = REPO / "research/experiments/2026-04-30-2240-m1-baseline-markout/results/bq_quantiles_2026-04-27.json"


def cdf_from_quantiles(qs: list[float]) -> tuple[np.ndarray, np.ndarray]:
    qs = np.asarray(qs, dtype=float) * 1e4  # raw -> bps
    n = len(qs)
    # APPROX_QUANTILES with k buckets returns k+1 evenly spaced values from min to max.
    # The fraction at index i is i/k.
    p = np.linspace(0.0, 1.0, n)
    return qs, p


def cdf_from_samples(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.sort(x.astype(float))
    p = np.arange(1, len(x) + 1) / len(x)
    return x, p


def main() -> None:
    # Load sim retail (markout_next, retail-side only)
    table = pq.read_table(SIM_PARQUET)
    df = table.to_pandas()
    sim_retail = df[df["source"] == "retail"]["markout_next_log"].to_numpy() * 1e4
    sim_retail = sim_retail[np.abs(sim_retail) < 500]  # match the BQ |markout_next|<5% filter

    # Load BQ quantiles
    with QUANT_JSON.open() as f:
        bq = json.load(f)
    router_q, router_p = cdf_from_quantiles(bq["router"]["q_next"])
    nonrouter_q, nonrouter_p = cdf_from_quantiles(bq["non_router"]["q_next"])
    n_router = bq["router"]["n"]
    n_nonrouter = bq["non_router"]["n"]

    with ALL_QUANT_JSON.open() as f:
        bq_all = json.load(f)
    # Cycle-2 saved a list of 201 dicts with 'pct' (0..100) and 'markout_next_bps' precomputed.
    all_q = np.array([row["markout_next_bps"] for row in bq_all], dtype=float)
    all_p = np.array([row["pct"] / 100.0 for row in bq_all], dtype=float)
    n_all = bq_all[0]["n"]

    sim_x, sim_p = cdf_from_samples(sim_retail)
    sim_n = len(sim_retail)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, xlim_kind in zip(axes, ["body", "wide"]):
        ax.plot(sim_x, sim_p, label=f"Sim retail (fee=5bps, n={sim_n:,})", color="#1f77b4", lw=2)
        ax.plot(all_q, all_p, label=f"On-chain ALL (n={n_all:,})", color="#7f7f7f", lw=1.8, ls="--")
        ax.plot(router_q, router_p, label=f"On-chain ROUTER (n={n_router:,})", color="#d62728", lw=2)
        ax.plot(nonrouter_q, nonrouter_p, label=f"On-chain NON-ROUTER (n={n_nonrouter:,})", color="#2ca02c", lw=2)

        ax.axvline(0.0, color="k", lw=0.5, alpha=0.4)
        ax.set_xlabel("markout_next (bps)")
        ax.set_ylabel("CDF")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="lower right", fontsize=9)
        if xlim_kind == "body":
            ax.set_xlim(-15, 25)
            ax.set_title("Body of the distribution (-15 to +25 bps)")
        else:
            ax.set_xlim(-50, 80)
            ax.set_title("Wider view (-50 to +80 bps)")

    fig.suptitle(
        "Cycle 4: Router-filtered on-chain markout falsifies the cycle-3 MEV-shift hypothesis\n"
        "Sim mean=+5.79 bps · ALL=+3.06 bps · ROUTER=+0.67 bps · NON-ROUTER=+3.98 bps · canonical pool, 4-27",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
