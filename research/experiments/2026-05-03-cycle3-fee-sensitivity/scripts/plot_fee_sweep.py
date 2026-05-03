"""Plot retail markout vs fee from fee_sweep.json."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> int:
    base = Path("research/experiments/2026-05-03-cycle3-fee-sensitivity")
    data = json.loads((base / "results" / "fee_sweep.json").read_text())

    fees = np.array([r["fee_bps"] for r in data["by_fee"]])
    means_now = np.array([r["retail_markout_now"]["mean_bps"] for r in data["by_fee"]])
    means_next = np.array([r["retail_markout_next"]["mean_bps"] for r in data["by_fee"]])

    slope_now = data["fits"]["markout_now"]["slope"]
    int_now = data["fits"]["markout_now"]["intercept_bps"]
    slope_next = data["fits"]["markout_next"]["slope"]
    int_next = data["fits"]["markout_next"]["intercept_bps"]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=130)
    ax.plot(fees, means_now, "o-", color="C0", lw=1.6, label=f"sim markout_now  (slope={slope_now:.3f}, int={int_now:+.2f} bps)")
    ax.plot(fees, means_next, "s--", color="C1", lw=1.6, label=f"sim markout_next  (slope={slope_next:.3f}, int={int_next:+.2f} bps)")

    # 1:1 reference line
    xs = np.linspace(0, max(fees) * 1.05, 100)
    ax.plot(xs, xs, color="gray", lw=0.8, alpha=0.6, label="1:1 (slope=1, int=0)")

    # On-chain reference at fee=5
    ax.scatter([5.0], [3.06], color="crimson", marker="*", s=180, zorder=5,
               label="on-chain ref (4-27, 5 bps pool)")
    ax.annotate("on-chain mean = +3.06 bps\n(gap ≈ -2.7 bps)",
                xy=(5.0, 3.06), xytext=(6.2, 1.4),
                fontsize=9, color="crimson",
                arrowprops=dict(arrowstyle="->", color="crimson", lw=0.7))

    ax.set_xlabel("LP fee (bps, both bid + ask)")
    ax.set_ylabel("Retail markout mean (bps, LP+)")
    ax.set_title("Fee sensitivity of sim retail markout (cycle 3)\n"
                 "8 seeds × 5000 steps × 4 fee tiers")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()

    out = base / "figures" / "fee_sweep_retail_markout.png"
    fig.savefig(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
