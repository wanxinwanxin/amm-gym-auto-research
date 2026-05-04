"""
Cycle-9 #1 — Plot the three-pass M2 piecewise convergence curve.

Stitches cycle-6, cycle-8, cycle-9 per-generation `fixed_val_score` into
one chart so the reader can see whether successive warm-start passes
keep paying off or have plateaued.

Outputs:
  research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/figures/three_pass_convergence.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
OUTDIR = ROOT / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

CYCLE6_HISTORY = (
    ROOT
    / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/warmstart_cem_history.json"
)
CYCLE8_HISTORY = (
    ROOT
    / "research/experiments/2026-05-04-cycle8-inventory-piecewise/results/inventory_warmstart_cem_history.json"
)
CYCLE9_HISTORY = (
    ROOT
    / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_history.json"
)
CYCLE6_TEST = (
    ROOT
    / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/warmstart_cem_test.json"
)
CYCLE8_ABLATION = (
    ROOT
    / "research/experiments/2026-05-04-cycle8-inventory-piecewise/results/inventory_ablation.json"
)
CYCLE9_TEST = (
    ROOT
    / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_test.json"
)


def _val_curve(history_path: Path) -> list[float]:
    if not history_path.exists():
        return []
    with history_path.open() as f:
        d = json.load(f)
    return [g["fixed_val_score"] for g in d["history"]]


def main() -> None:
    c6 = _val_curve(CYCLE6_HISTORY)
    c8 = _val_curve(CYCLE8_HISTORY)
    c9 = _val_curve(CYCLE9_HISTORY)

    fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=150)

    # Three passes laid out one after the other on the x-axis so the
    # reader sees cumulative wall-clock-equivalent progress.
    x6 = list(range(len(c6)))
    x8 = list(range(len(c6), len(c6) + len(c8)))
    x9 = list(range(len(c6) + len(c8), len(c6) + len(c8) + len(c9)))
    if c6:
        ax.plot(x6, c6, "o-", color="#2b3a55", label=f"cycle 6 (pass 1, {len(c6)} gens)")
    if c8:
        ax.plot(x8, c8, "o-", color="#0f8b78", label=f"cycle 8 (pass 2, {len(c8)} gens)")
    if c9:
        ax.plot(x9, c9, "o-", color="#c0392b", label=f"cycle 9 (pass 3, {len(c9)} gens)")

    # Test-set checkpoints (256 seeds) as horizontal annotations.
    if CYCLE6_TEST.exists():
        d = json.loads(CYCLE6_TEST.read_text())
        ax.axhline(d["best_by_val"]["test_score"], linestyle="--",
                   color="#2b3a55", linewidth=0.7, alpha=0.6,
                   label=f"cycle-6 test {d['best_by_val']['test_score']:.1f}")
    if CYCLE8_ABLATION.exists():
        d = json.loads(CYCLE8_ABLATION.read_text())
        ax.axhline(d["cycle8_inv_aware_zeroed"]["score"], linestyle="--",
                   color="#0f8b78", linewidth=0.7, alpha=0.6,
                   label=f"cycle-8 ablation test {d['cycle8_inv_aware_zeroed']['score']:.1f}")
    if CYCLE9_TEST.exists():
        d = json.loads(CYCLE9_TEST.read_text())
        ax.axhline(d["best_by_val"]["test_score"], linestyle="--",
                   color="#c0392b", linewidth=0.7, alpha=0.6,
                   label=f"cycle-9 test {d['best_by_val']['test_score']:.1f}")
    ax.axhline(540.0, linestyle=":", color="black", linewidth=0.8,
               label="M2 target = 540")

    ax.set_xlabel("CEM generation (cumulative across passes)")
    ax.set_ylabel("val score (128 seeds)")
    ax.set_title("Three-pass warm-start CEM on bare piecewise (M2)")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85)
    fig.tight_layout()
    out = OUTDIR / "three_pass_convergence.png"
    fig.savefig(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
