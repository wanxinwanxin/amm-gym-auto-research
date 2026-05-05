"""
M3 cycle 2 figure — held-out test split with bootstrap CIs.

Two panels, mirroring cycle 14's layout but on the *test* split with
95% bootstrap CI bands:
  Left:  challenge score by anchor (in-distribution).
  Right: real_data score by anchor (OOD), with the FixedFee(0.003)
         baseline as a reference horizontal line.
A third panel (bottom) decomposes the OOD edge_advantage into retail
fee-edge and arb-loss components for c5 vs c11.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "research/experiments/2026-05-05-cycle15-m3-test-split-decomp"
RESULTS = json.loads((EXP / "results/dualcurve_test.json").read_text())


def _err(lo_hi: list[float], mean: float) -> tuple[float, float]:
    """Return (asymmetric err lo, err hi) from a 95% CI band."""
    return (mean - lo_hi[0], lo_hi[1] - mean)


def main() -> None:
    rows = RESULTS["rows"]
    labels = [r["label"] for r in rows]
    n = len(rows)
    x = np.arange(n)

    chal_means = [r["metrics"]["test_challenge"]["score_mean"] for r in rows]
    chal_ci = [r["metrics"]["test_challenge"]["score_ci95"] for r in rows]
    real_means = [r["metrics"]["test_real_data"]["score_mean"] for r in rows]
    real_ci = [r["metrics"]["test_real_data"]["score_ci95"] for r in rows]

    chal_err_lo = [m - c[0] for m, c in zip(chal_means, chal_ci)]
    chal_err_hi = [c[1] - m for m, c in zip(chal_means, chal_ci)]
    real_err_lo = [m - c[0] for m, c in zip(real_means, real_ci)]
    real_err_hi = [c[1] - m for m, c in zip(real_means, real_ci)]

    ff_chal = RESULTS["fixedfee"]["test_challenge"]["score_mean"]
    ff_real = RESULTS["fixedfee"]["test_real_data"]["score_mean"]
    ff_real_ci = RESULTS["fixedfee"]["test_real_data"]["score_ci95"]

    # -- top: challenge + real curves
    fig = plt.figure(figsize=(13, 9))
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 1, 2)

    ax1.errorbar(
        x, chal_means, yerr=[chal_err_lo, chal_err_hi],
        fmt="o-", color="#1f4e8c", capsize=4, lw=1.5, markersize=5,
        label="challenge test"
    )
    ax1.axhline(ff_chal, color="#888", lw=1, linestyle="--", label=f"FixedFee = {ff_chal:.1f}")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax1.set_ylabel("challenge test score (n=256)")
    ax1.set_title("In-distribution: challenge score by anchor")
    ax1.grid(True, alpha=0.25)
    ax1.legend(loc="lower right", fontsize=8)

    # color-coded points by OOD sign
    colors = ["#c0392b" if m < ff_real else "#2e7d32" for m in real_means]
    ax2.errorbar(
        x, real_means, yerr=[real_err_lo, real_err_hi],
        fmt="o-", color="#444", capsize=4, lw=1.0, markersize=5, alpha=0.6
    )
    ax2.scatter(x, real_means, c=colors, s=60, zorder=5)
    ax2.axhline(ff_real, color="#888", lw=1, linestyle="--",
                label=f"FixedFee = {ff_real:.3f}")
    ax2.fill_between(
        [-0.5, n - 0.5], ff_real_ci[0], ff_real_ci[1],
        color="#aaa", alpha=0.18, label="FF 95% CI",
    )
    ax2.axhspan(min(real_means) - 0.5, ff_real, color="#fde2e2", alpha=0.25,
                label="below FF (harmful)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax2.set_ylabel("real_data test score (n=256)")
    ax2.set_title("OOD: real_data score by anchor (95% bootstrap CI)")
    ax2.grid(True, alpha=0.25)
    ax2.legend(loc="lower right", fontsize=8)
    ax2.set_xlim(-0.5, n - 0.5)

    # -- bottom: decomposition
    retail = [r["metrics"]["test_real_data"]["retail_edge_advantage_mean"] for r in rows]
    arb = [r["metrics"]["test_real_data"]["arb_loss_advantage_mean"] for r in rows]
    edge = [r["metrics"]["test_real_data"]["edge_advantage_mean"] for r in rows]

    width = 0.28
    ax3.bar(x - width, retail, width, label="retail edge_adv", color="#1f6f3a", alpha=0.85)
    ax3.bar(x, arb, width, label="arb_loss_adv (–Δarb_loss)", color="#c0392b", alpha=0.85)
    ax3.bar(x + width, edge, width, label="net edge_adv", color="#1f4e8c", alpha=0.85)
    ax3.axhline(0, color="black", lw=0.6)
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax3.set_ylabel("real_data edge_advantage components (test, n=256)")
    ax3.set_title(
        "OOD PnL decomposition: retail fee-edge vs. arb-loss vs. net "
        "(positive = submission better than FixedFee normalizer)"
    )
    ax3.grid(True, alpha=0.25, axis="y")
    ax3.legend(loc="lower right", fontsize=9)

    fig.suptitle(
        "M3 cycle 2 — chronological M2 anchors, held-out test split (n=256, 95% bootstrap CI)",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path = EXP / "figures/m3_test_split.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    print(f"-> wrote {out_path}")


if __name__ == "__main__":
    main()
