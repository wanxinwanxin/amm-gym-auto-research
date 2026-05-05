"""Cycle-17 figures.

(1) Gen-by-gen val-score trajectory: c5+CEM (cycle 16) vs c11+CEM
    (cycle 17). Shared y-axis = real_data val score; horizontal lines
    at FixedFee val and at the c5/c11 anchor val scores. Horizontal
    line at the lift_FF=+2.20 decision-rule threshold (in val units).

(2) Per-bucket retail_edge_advantage across 4 anchors (c5, c5+CEM /
    M4 baseline, c11, c11+CEM). Grouped bar chart, error bars from
    bootstrap 95% CIs. This is the headline cycle-17 figure: it
    falsifies the cycle-17 prior (small-bucket dominates the M4
    baseline drop) and adds the basin-staying evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUTDIR = ROOT / "research/experiments/2026-05-05-cycle17-m4-c11-mirror"

# Data sources.
C16_M4_HISTORY = json.loads((
    ROOT
    / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results/m4_baseline/history.json"
).read_text())
C17_HISTORY = json.loads((
    OUTDIR / "results/m4_c11_mirror/history.json"
).read_text())
C17_TEST = json.loads((
    OUTDIR / "results/m4_c11_mirror/test.json"
).read_text())
C16_TEST = json.loads((
    ROOT
    / "research/experiments/2026-05-05-cycle16-trade-size-decomp/results/m4_baseline/test.json"
).read_text())

DECOMP_M4 = json.loads((
    OUTDIR / "results/size_decomp_m4_baseline.json"
).read_text())
DECOMP_C11_MIRROR = json.loads((
    OUTDIR / "results/size_decomp_c11_mirror.json"
).read_text())


def _val_curve(history_doc) -> tuple[list[int], list[float]]:
    gens = [h["generation"] for h in history_doc["history"]]
    vals = [h["fixed_val_score"] for h in history_doc["history"]]
    return gens, vals


def fig1_gen_curves() -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    g16, v16 = _val_curve(C16_M4_HISTORY)
    g17, v17 = _val_curve(C17_HISTORY)
    c5_val_score = C16_M4_HISTORY["c5_val_score"]
    c11_val_score = C17_HISTORY["c11_val_score"]
    # FixedFee val on real_data — recover from c5_val: in cycle 16
    # FixedFee was the normalizer. We don't have FixedFee val
    # directly here but we have FixedFee test. Use FixedFee test as a
    # close proxy (validation distribution similar).
    ff_test = C17_TEST["best_by_val"]["ff_test_score"]

    ax.plot(g16, v16, "o-", color="#cc4444", label="c5 + CEM (cycle 16, M4 baseline)")
    ax.plot(g17, v17, "s-", color="#3366cc", label="c11 + CEM (cycle 17, mirror)")
    ax.axhline(c5_val_score, color="#cc4444", linestyle="--", alpha=0.6, label=f"c5 anchor val = {c5_val_score:.2f}")
    ax.axhline(c11_val_score, color="#3366cc", linestyle="--", alpha=0.6, label=f"c11 anchor val = {c11_val_score:.2f}")
    ax.axhline(ff_test, color="gray", linestyle=":", alpha=0.6, label=f"FixedFee test = {ff_test:.2f}")
    ax.set_xlabel("CEM generation")
    ax.set_ylabel("Val score (real_data, n=128)")
    ax.set_title("c5+CEM vs c11+CEM on real_data — basin matters more than CEM")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = OUTDIR / "figures/gen_val_curves.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"-> {out}")


def fig2_bucket_decomp() -> None:
    """4-anchor grouped bar chart with bootstrap 95% CIs as error bars."""
    # Pull anchors. Cycle-16's combined doc has c5, m4, c11. Cycle-17
    # decomp_c11_mirror has the mirror.
    anchors_by_label = {a["label"]: a for a in DECOMP_M4["anchors"]}
    c11_mirror = DECOMP_C11_MIRROR

    order = [
        ("c5_baseline", "c5 anchor", "#cc4444"),
        ("m4_baseline", "c5 + CEM (cycle 16)", "#aa2222"),
        ("c11_d16_s2", "c11 anchor", "#3366cc"),
        ("c11_mirror", "c11 + CEM (cycle 17)", "#1a4499"),
    ]
    buckets = ["small", "medium", "large"]

    by_anchor = {}
    by_anchor["c5_baseline"] = anchors_by_label["c5_baseline"]
    by_anchor["m4_baseline"] = anchors_by_label["m4_baseline"]
    by_anchor["c11_d16_s2"] = anchors_by_label["c11_d16_s2"]
    by_anchor["c11_mirror"] = c11_mirror

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    n_anchors = len(order)
    width = 0.18
    x = np.arange(len(buckets))

    for i, (key, label, color) in enumerate(order):
        a = by_anchor[key]
        means = [a["per_bucket"][b]["retail_edge_advantage_mean"] for b in buckets]
        cis = [a["per_bucket"][b]["retail_edge_advantage_ci95"] for b in buckets]
        lo = [m - c[0] for m, c in zip(means, cis)]
        hi = [c[1] - m for m, c in zip(means, cis)]
        ax.bar(
            x + (i - (n_anchors - 1) / 2) * width,
            means,
            width=width,
            color=color,
            yerr=[lo, hi],
            capsize=3,
            label=label,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(buckets)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylabel("retail_edge_advantage (sub minus norm), n=128 val seeds")
    ax.set_xlabel("Trade size bucket (size_ratio cuts at 0.003 / 0.012)")
    ax.set_title("Per-bucket retail_edge_advantage: basin determines retail behavior; CEM stays in basin")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    out = OUTDIR / "figures/retail_edge_by_bucket.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"-> {out}")


def fig3_lift_summary() -> None:
    """4-anchor lift_FF summary bar (test, n=256)."""
    # c5 anchor lift_FF: per cycle-15 we had c5 test_lift_FF = -1.22.
    # Pull from cycle-15 if possible; else use STATE.md numbers. We
    # have the M4 baseline test.json which tells us c5 wasn't measured
    # there but cycle-15 had it. Hard-code from STATE.md.
    lift_data = [
        ("c5 anchor", -1.22, "#cc4444"),
        ("c5 + CEM (cycle 16)", C16_TEST["best_by_val"]["lift_FF"], "#aa2222"),
        ("c11 anchor", 2.10, "#3366cc"),
        ("c11 + CEM (cycle 17)", C17_TEST["best_by_val"]["lift_FF"], "#1a4499"),
    ]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    labels = [r[0] for r in lift_data]
    values = [r[1] for r in lift_data]
    colors = [r[2] for r in lift_data]
    bars = ax.bar(labels, values, color=colors)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.axhline(2.20, color="green", linewidth=0.8, linestyle="--",
               label="cycle-17 decision threshold (+2.20 lift_FF)")
    ax.set_ylabel("test lift_FF on real_data (n=256)")
    ax.set_title("Lift over FixedFee: warm-start prior dominates short-budget CEM")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.1 if v > 0 else -0.3),
                f"{v:+.2f}", ha="center", fontsize=10, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    out = OUTDIR / "figures/lift_summary.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"-> {out}")


if __name__ == "__main__":
    fig1_gen_curves()
    fig2_bucket_decomp()
    fig3_lift_summary()
