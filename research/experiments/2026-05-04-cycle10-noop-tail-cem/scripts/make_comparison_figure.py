"""
Build the cycle-10 hypothesis-test comparison figure.

Reads four CEM histories (cycle-9 #1, cycle-9 #3, cycle-10 A, cycle-10 B)
and renders a two-panel figure: (left) per-generation val curves;
(right) bar chart of test scores at the end.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/figures"
OUT.mkdir(parents=True, exist_ok=True)


def _load(history_path: Path):
    d = json.load(history_path.open())
    return d["history"]


def _test(test_path: Path):
    if not test_path.exists():
        return None
    d = json.load(test_path.open())
    return d["best_by_val"]["test_score"], d["best_by_val"]["val_score"]


CYCLE9_1_HIST = ROOT / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_history.json"
CYCLE9_1_TEST = ROOT / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_test.json"
CYCLE9_3_HIST = ROOT / "research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results/ema_inventory_cem_history.json"
CYCLE9_3_TEST = ROOT / "research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results/ema_inventory_cem_test.json"
CYCLE10_A_HIST = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_history.json"
CYCLE10_A_TEST = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_test.json"
CYCLE10_B_HIST = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/seed_lottery_cem_history.json"
CYCLE10_B_TEST = ROOT / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/seed_lottery_cem_test.json"


def main() -> None:
    runs = [
        ("c9 #1: 16-d, seed=0", CYCLE9_1_HIST, CYCLE9_1_TEST, "#1f77b4", "-"),
        ("c9 #3: 20-d EMA wrap, seed=0", CYCLE9_3_HIST, CYCLE9_3_TEST, "#2ca02c", "-"),
        ("c10 A: 20-d no-op tail, seed=0", CYCLE10_A_HIST, CYCLE10_A_TEST, "#d62728", "-"),
        ("c10 B: 16-d, seed=1", CYCLE10_B_HIST, CYCLE10_B_TEST, "#9467bd", "--"),
    ]

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(13, 5))

    for label, hist_p, test_p, color, ls in runs:
        if not hist_p.exists():
            continue
        hist = _load(hist_p)
        gens = [r["generation"] for r in hist]
        val = [r["fixed_val_score"] for r in hist]
        ax_l.plot(gens, val, color=color, linestyle=ls, marker="o", markersize=4, label=label)

    ax_l.axhline(y=446.61, color="grey", linestyle=":", linewidth=1, alpha=0.7,
                 label="cycle-8 anchor (446.61)")
    ax_l.set_xlabel("generation")
    ax_l.set_ylabel("val score (n=128)")
    ax_l.set_title("CEM convergence — same anchor, varying dim & seed")
    ax_l.grid(alpha=0.3)
    ax_l.legend(loc="lower right", fontsize=8)

    # Right: test bar chart
    bar_labels = []
    bar_vals = []
    bar_colors = []
    bar_text = []
    for label, _, test_p, color, _ in runs:
        t = _test(test_p)
        if t is None:
            continue
        bar_labels.append(label.replace(": ", "\n"))
        bar_vals.append(t[0])
        bar_colors.append(color)
        bar_text.append(f"{t[0]:.2f}")

    if bar_vals:
        bars = ax_r.bar(range(len(bar_vals)), bar_vals, color=bar_colors, alpha=0.85)
        ax_r.set_xticks(range(len(bar_labels)))
        ax_r.set_xticklabels(bar_labels, fontsize=8)
        for i, (bar, txt) in enumerate(zip(bars, bar_text)):
            ax_r.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                      txt, ha="center", va="bottom", fontsize=10, fontweight="bold")
        ax_r.axhline(y=446.61, color="grey", linestyle=":", linewidth=1, alpha=0.7)
        ax_r.text(-0.4, 446.61 + 0.5, "cycle-8 anchor", fontsize=8, color="grey")
        lo = min(bar_vals) - 5
        hi = max(bar_vals) + 5
        ax_r.set_ylim(lo, hi)
    ax_r.set_ylabel("test score (n=256 held-out seeds)")
    ax_r.set_title("Held-out test scores")
    ax_r.grid(alpha=0.3, axis="y")

    fig.suptitle("Cycle 10 — does CEM benefit from inert tail dimensions?", fontsize=12)
    fig.tight_layout()

    out = OUT / "cycle10_hypothesis_test.png"
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
