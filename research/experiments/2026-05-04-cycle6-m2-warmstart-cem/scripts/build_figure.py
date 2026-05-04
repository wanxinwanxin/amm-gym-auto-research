"""
Build the cycle-6 M2 warm-start CEM figure.

Reads `results/warmstart_cem_history.json` and `warmstart_cem_test.json`
and writes `figures/m2_warmstart_cem.png` — a 2-panel chart:

  Left:  CEM convergence — per-generation best_search, elite_mean,
         fixed_val, plus reference lines for the inherited starting
         line (414) and the M2 target (540).

  Right: Headline bar — starting line, warm-start best (test), gap to
         oracle (586.5), and target (540).

Run:
    python3 research/experiments/2026-05-04-cycle6-m2-warmstart-cem/scripts/build_figure.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem"
RESULTS = EXP / "results"
FIGS = EXP / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

STARTING_LINE = 414.010   # cycle 5
ORACLE = 586.51           # structured-retail clairvoyant (M1 closeout)
TARGET = 540.0
FIXED30 = 342.83          # cycle-5 fixed-30bps reference


def main() -> None:
    history = json.loads((RESULTS / "warmstart_cem_history.json").read_text())["history"]
    test = json.loads((RESULTS / "warmstart_cem_test.json").read_text())

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: per-generation curves.
    gens = [h["generation"] for h in history]
    best = [h["best_search_score"] for h in history]
    elite = [h["elite_mean_search_score"] for h in history]
    val = [h["fixed_val_score"] for h in history]
    median = [h["median_search_score"] for h in history]

    ax_left.plot(gens, best, "o-", label="best_search (64 seeds)", color="#1f77b4")
    ax_left.plot(gens, elite, "s-", label="elite_mean (4 elites)", color="#ff7f0e")
    ax_left.plot(gens, median, "^-", label="median_search", color="#bcbd22", alpha=0.5)
    ax_left.plot(gens, val, "D-", label="fixed_val (128 seeds)", color="#2ca02c")

    ax_left.axhline(STARTING_LINE, color="gray", linestyle="--", alpha=0.7,
                    label=f"M2 starting line ({STARTING_LINE:.0f})")
    ax_left.axhline(TARGET, color="red", linestyle="--", alpha=0.7,
                    label=f"M2 target ({TARGET:.0f})")
    ax_left.axhline(ORACLE, color="purple", linestyle=":", alpha=0.5,
                    label=f"clairvoyant oracle ({ORACLE:.0f})")

    ax_left.set_xlabel("CEM generation")
    ax_left.set_ylabel("score (mean edge_submission)")
    ax_left.set_title(
        "Warm-start CEM on piecewise — convergence\n"
        f"init_std_frac={json.loads((RESULTS / 'warmstart_cem_history.json').read_text())['init_std_frac']}"
    )
    ax_left.legend(fontsize=8, loc="lower right")
    ax_left.grid(True, alpha=0.3)

    # Right: headline bar.
    bars_x = ["fixed\n30bps", "M2\nstarting line\n(piecewise CEM)",
              "warm-start\nCEM (test)", "M2 target", "clairvoyant\noracle"]
    test_score = test["best_by_val"]["test_score"]
    bars_y = [FIXED30, STARTING_LINE, test_score, TARGET, ORACLE]
    bar_colors = ["#cccccc", "#888888", "#1f77b4", "#d62728", "#9467bd"]

    bars = ax_right.bar(bars_x, bars_y, color=bar_colors, edgecolor="black")
    for bar, value in zip(bars, bars_y, strict=True):
        ax_right.text(bar.get_x() + bar.get_width() / 2, value + 5,
                      f"{value:.1f}", ha="center", va="bottom", fontsize=9)

    delta = test_score - STARTING_LINE
    ax_right.set_ylabel("score")
    ax_right.set_title(
        f"Headline — warm-start CEM lifts M2 starting line by "
        f"{delta:+.1f} pts ({delta/STARTING_LINE*100:+.1f}%)"
    )
    ax_right.set_ylim(0, max(bars_y) * 1.15)
    ax_right.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    out_path = FIGS / "m2_warmstart_cem.png"
    fig.savefig(out_path, dpi=140)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
