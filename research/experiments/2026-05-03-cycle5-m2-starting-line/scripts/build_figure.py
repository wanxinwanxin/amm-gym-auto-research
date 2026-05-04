"""Build the M2 starting-line figure."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parent.parent
RESULTS = EXP / "results"
FIGURES = EXP / "figures"


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    sweep = json.loads((RESULTS / "fixed_fee_sweep.json").read_text())
    piecewise = json.loads((RESULTS / "piecewise_replicate.json").read_text())

    # Bar chart: trivial floor / best fixed / piecewise / target / oracle
    bars = [
        ("fixed 30bps\n(trivial)", 342.826, "#888888"),
        ("fixed 100bps\n(best fixed)", 373.724, "#888888"),
        ("piecewise CEM\n(inherited best)", piecewise["score"], "#1f77b4"),
        ("M2 target", 540.0, "#d62728"),
        ("clairvoyant\noracle", 586.51, "#2ca02c"),
    ]
    labels = [b[0] for b in bars]
    values = [b[1] for b in bars]
    colors = [b[2] for b in bars]

    fig, (ax_main, ax_sweep) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(11, 4.6),
        gridspec_kw={"width_ratios": [1.4, 1.0]},
    )

    bar_positions = list(range(len(bars)))
    rects = ax_main.bar(bar_positions, values, color=colors, edgecolor="black")
    ax_main.set_xticks(bar_positions)
    ax_main.set_xticklabels(labels, fontsize=9)
    ax_main.set_ylabel("score_challenge (mean edge_submission, USDC)")
    ax_main.set_title("M2 starting line vs. target (256 held-out test seeds)")
    ax_main.axhline(540.0, color="#d62728", linestyle=":", linewidth=1, alpha=0.6)
    ax_main.set_ylim(0, max(values) * 1.15)
    for rect, val in zip(rects, values):
        ax_main.text(
            rect.get_x() + rect.get_width() / 2.0,
            val + 8,
            f"{val:.1f}",
            ha="center",
            fontsize=9,
        )

    fees_bps = [row["fee_bps"] for row in sweep["rows"]]
    scores = [row["score"] for row in sweep["rows"]]
    ax_sweep.plot(fees_bps, scores, marker="o", color="#888888")
    ax_sweep.set_xscale("log")
    ax_sweep.set_xlabel("fixed bid=ask fee (bps)")
    ax_sweep.set_ylabel("score_challenge")
    ax_sweep.set_title("Fixed-fee score curve")
    ax_sweep.axhline(piecewise["score"], color="#1f77b4", linestyle="--", linewidth=1, alpha=0.6, label=f"piecewise ({piecewise['score']:.1f})")
    ax_sweep.axhline(540.0, color="#d62728", linestyle=":", linewidth=1, alpha=0.6, label="M2 target (540)")
    ax_sweep.legend(loc="lower right", fontsize=8)
    ax_sweep.grid(True, which="both", alpha=0.3)

    fig.tight_layout()
    out = FIGURES / "m2_starting_line.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
