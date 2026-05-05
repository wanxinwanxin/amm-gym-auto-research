"""Cycle-18 figures.

Three PNGs (matplotlib, no external deps):
  1. fig_val_curve_long_cem.png — gen-by-gen val score for the
     10g x 24p CEM from c11. Overlaid: cycle-17 5g x 12p curve.
  2. fig_prior_sweep.png — final test lift_FF vs anchor (default,
     c5, c6, c8_16d, c11; c5 / c11 reused from cycles 16 / 17).
     Includes anchor starting val score for context.
  3. fig_basin_vs_compute.png — 2D scatter of starting_val_lift_FF
     (x) vs final_test_lift_FF (y) across all anchors. Tests basin-
     dominance hypothesis visually.

Inputs read at import time; missing inputs skip the figure with a
warning rather than crashing — supports partial runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-05-cycle18-m4-prior-sweep"
FIG_DIR = EXP_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

LONG_HISTORY = EXP_DIR / "results/long_cem_from_c11/history.json"
LONG_TEST = EXP_DIR / "results/long_cem_from_c11/test.json"
PRIOR_SUMMARY = EXP_DIR / "results/prior_sweep_summary.json"

C17_HISTORY = (
    ROOT
    / "research/experiments/2026-05-05-cycle17-m4-c11-mirror/results/m4_c11_mirror/history.json"
)
C17_TEST = (
    ROOT
    / "research/experiments/2026-05-05-cycle17-m4-c11-mirror/results/m4_c11_mirror/test.json"
)
C16_TEST = (
    ROOT
    / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results/m4_baseline/test.json"
)


def _load(p: Path) -> dict | None:
    if not p.exists():
        print(f"warn: missing {p}", file=sys.stderr)
        return None
    return json.loads(p.read_text())


def fig_val_curve() -> None:
    long_h = _load(LONG_HISTORY)
    c17_h = _load(C17_HISTORY)
    if long_h is None and c17_h is None:
        print("skip fig_val_curve (no history)", file=sys.stderr)
        return
    fig, ax = plt.subplots(figsize=(7.0, 4.6))

    if long_h is not None:
        gens = [r["generation"] for r in long_h["history"]]
        vals = [r["fixed_val_score"] for r in long_h["history"]]
        anchor_v = long_h["c11_val_score"]
        ax.plot(gens, vals, "-o", color="C0", label="cycle-18 long (10g × 24p)", lw=2)
        ax.axhline(anchor_v, color="C0", ls=":", alpha=0.6,
                   label=f"c11 anchor val = {anchor_v:.2f}")

    if c17_h is not None:
        gens17 = [r["generation"] for r in c17_h["history"]]
        vals17 = [r["fixed_val_score"] for r in c17_h["history"]]
        ax.plot(gens17, vals17, "-s", color="C1",
                label="cycle-17 short (5g × 12p)", lw=2)

    ax.set_xlabel("generation")
    ax.set_ylabel(f"best-of-gen val score (real_data, n=128)")
    ax.set_title("M4 cycle-18: c11+CEM val trajectory, long vs short budget")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "fig_val_curve_long_cem.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  -> {out}")


def _anchor_data() -> list[dict]:
    """Pull all anchor (start, finish) data points from cycles 16-18."""
    rows: list[dict] = []

    # c5 from cycle 16.
    c16 = _load(C16_TEST)
    if c16 is not None:
        rows.append({
            "anchor_id": "c5",
            "anchor_val_score": c16.get("c5_val_score"),
            "test_score": c16["best_by_val"]["test_score"],
            "lift_FF": c16["best_by_val"]["lift_FF"],
            "test_retail_advantage": c16["best_by_val"].get("test_retail_advantage"),
            "source": "cycle 16 short (5g × 12p)",
        })

    # c11 (short) from cycle 17.
    c17 = _load(C17_TEST)
    if c17 is not None:
        rows.append({
            "anchor_id": "c11_short",
            "anchor_val_score": c17.get("c11_val_score"),
            "test_score": c17["best_by_val"]["test_score"],
            "lift_FF": c17["best_by_val"]["lift_FF"],
            "test_retail_advantage": c17["best_by_val"].get("test_retail_advantage"),
            "source": "cycle 17 short (5g × 12p)",
        })

    # c11 (long) from cycle 18.
    c18 = _load(LONG_TEST)
    if c18 is not None:
        rows.append({
            "anchor_id": "c11_long",
            "anchor_val_score": c18.get("c11_val_score"),
            "test_score": c18["best_by_val"]["test_score"],
            "lift_FF": c18["best_by_val"]["lift_FF"],
            "test_retail_advantage": c18["best_by_val"].get("test_retail_advantage"),
            "source": "cycle 18 long (10g × 24p)",
        })

    # Other anchors from cycle-18 prior sweep summary.
    summary = _load(PRIOR_SUMMARY)
    if summary is not None:
        for row in summary["anchors"]:
            rows.append({
                "anchor_id": row["anchor_id"],
                "anchor_val_score": row["anchor_val_score"],
                "test_score": row["best_by_val"]["test_score"],
                "lift_FF": row["best_by_val"]["lift_FF"],
                "test_retail_advantage": row["best_by_val"].get("test_retail_advantage"),
                "source": "cycle 18 short (5g × 12p)",
            })

    return rows


def fig_prior_sweep() -> None:
    rows = _anchor_data()
    if not rows:
        print("skip fig_prior_sweep (no rows)", file=sys.stderr)
        return
    rows.sort(key=lambda r: r["lift_FF"])
    labels = [r["anchor_id"] for r in rows]
    lifts = [r["lift_FF"] for r in rows]
    starts = [r["anchor_val_score"] for r in rows]

    fig, ax1 = plt.subplots(figsize=(8.0, 4.8))
    ax2 = ax1.twinx()
    x = np.arange(len(rows))
    bars = ax1.bar(x - 0.18, lifts, width=0.36, color="C0", alpha=0.85,
                   label="final test lift_FF")
    ax2.bar(x + 0.18, starts, width=0.36, color="C1", alpha=0.55,
            label="anchor val score")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right")
    ax1.set_ylabel("final test lift_FF (real_data, n=256)")
    ax2.set_ylabel("anchor val score (real_data, n=128)")
    ax1.axhline(0.0, color="k", lw=0.8, alpha=0.4)
    ax1.set_title("Cycle 18 — prior sweep: anchor → CEM lift")

    for bar, lift in zip(bars, lifts):
        ax1.annotate(f"{lift:+.2f}", xy=(bar.get_x() + bar.get_width() / 2, lift),
                     xytext=(0, 3 if lift >= 0 else -12), textcoords="offset points",
                     ha="center", fontsize=8)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper left")
    ax1.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "fig_prior_sweep.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  -> {out}")


def fig_basin_vs_compute() -> None:
    rows = _anchor_data()
    if len(rows) < 2:
        print("skip fig_basin_vs_compute (need ≥2 rows)", file=sys.stderr)
        return
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    starts = np.array([r["anchor_val_score"] for r in rows])
    lifts = np.array([r["lift_FF"] for r in rows])
    labels = [r["anchor_id"] for r in rows]

    # Color by source budget (short vs long).
    is_long = np.array(["long" in r["source"] for r in rows])

    ax.scatter(starts[~is_long], lifts[~is_long], s=80, c="C0", marker="o",
               label="short (5g × 12p)", zorder=3)
    ax.scatter(starts[is_long], lifts[is_long], s=110, c="C3", marker="*",
               label="long (10g × 24p)", zorder=4)
    for x, y, lbl in zip(starts, lifts, labels):
        ax.annotate(lbl, xy=(x, y), xytext=(4, 4), textcoords="offset points",
                    fontsize=8)

    ax.axhline(0.0, color="k", lw=0.7, alpha=0.4)
    ax.set_xlabel("anchor val score (start, real_data, n=128)")
    ax.set_ylabel("final test lift_FF (real_data, n=256)")
    ax.set_title("Cycle 18 — does basin dominate? final lift_FF vs anchor val")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / "fig_basin_vs_compute.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  -> {out}")


def main() -> None:
    fig_val_curve()
    fig_prior_sweep()
    fig_basin_vs_compute()


if __name__ == "__main__":
    main()
