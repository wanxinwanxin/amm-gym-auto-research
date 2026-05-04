"""Cycle-8 init_std sweep figure.

Two panels, derived from `init_std_<frac>_history.json` files:

1. Per init_std_frac, val score per generation. Lets us see whether wider
   init_std basin width gives more (or less) headroom than the cycle-7
   default of 0.10×range.
2. Per init_std_frac, headline bar of inherited test (410.78), cycle-7
   warm-start test (416.08), cycle-8 sweep test scores. Annotate Δ.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPDIR = ROOT / "research/experiments/2026-05-04-cycle8-init-std-sweep"
RESULTS = EXPDIR / "results"
FIGURES = EXPDIR / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # Discover all completed init_std files.
    history_files = sorted(RESULTS.glob("init_std_*_history.json"))
    test_files = sorted(RESULTS.glob("init_std_*_test.json"))
    if not history_files:
        raise RuntimeError("no init_std_*_history.json under results/")

    histories = []
    for f in history_files:
        d = json.loads(f.read_text())
        histories.append(d)
    histories.sort(key=lambda d: d["init_std_frac"])

    tests = {}
    for f in test_files:
        d = json.loads(f.read_text())
        tests[d["init_std_frac"]] = d

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5))

    # Panel 1: convergence per init_std
    ax = axes[0]
    palette = ["#3C7BB0", "#D9534F", "#5CB85C", "#9467BD", "#E67E22"]
    for i, h in enumerate(histories):
        gens = np.asarray([g["generation"] for g in h["history"]])
        val = np.asarray([g["fixed_val_score"] for g in h["history"]])
        color = palette[i % len(palette)]
        ax.plot(gens, val, marker="o", color=color, label=f"init_std={h['init_std_frac']:.2f}")
    ax.axhline(410.78, ls="--", color="grey", alpha=0.7, label="inherited (cycle-5)")
    ax.axhline(416.88, ls=":", color="#7F7F7F", alpha=0.7, label="cycle-7 (init_std=0.10)")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Val score (128 seeds)")
    ax.set_title("submission_compact init_std sensitivity\n(warm-start CEM, 6 gens each)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")

    # Panel 2: headline bar
    ax = axes[1]
    cycle7_val = 416.88
    cycle7_test = 416.08
    bars = [("cycle-7\ninit_std=0.10", cycle7_test, "#7F7F7F")]
    for h in histories:
        frac = h["init_std_frac"]
        if frac in tests:
            bars.append((f"cycle-8\ninit_std={frac:.2f}", tests[frac]["best_by_val"]["test_score"], "#5CB85C"))

    xs = np.arange(len(bars))
    heights = [b[1] for b in bars]
    colors = [b[2] for b in bars]
    ax.bar(xs, heights, color=colors)
    ax.axhline(410.78, ls="--", color="grey", alpha=0.7, label="inherited")
    for i, h in enumerate(heights):
        ax.text(i, h + 0.5, f"{h:.1f}", ha="center", fontsize=9)
    ax.set_xticks(xs)
    ax.set_xticklabels([b[0] for b in bars], fontsize=9)
    ax.set_ylabel("Test score (256 seeds)")
    ax.set_title("Init_std sweep — headline test scores")
    ax.set_ylim(405, 430)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25, axis="y")

    fig.tight_layout()
    out = FIGURES / "init_std_sweep_summary.png"
    fig.savefig(out, dpi=120)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
