"""
Build the cycle-7 family-comparison figure.

Inputs (any subset that exists; missing families are skipped):
    results/warmstart_cem_piecewise_history.json          (cycle 6's run)
    results/warmstart_cem_submission_compact_history.json (cycle 7)
    results/warmstart_cem_submission_basis_history.json   (cycle 7)
    research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results/
        warmstart_cem_history.json   (cycle 6 piecewise — fall-back if
        the cycle-7 piecewise rerun isn't present)

Outputs:
    figures/family_comparison.png  — per-family CEM convergence
        (gen vs best-search, elite-mean, fixed-val).
    figures/family_lift_bar.png    — per-family inherited vs
        cycle-7 test score, with the +540 target line.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "research/experiments/2026-05-04-cycle7-multi-family-warmstart-cem"
RES = EXP / "results"
FIG = EXP / "figures"
FIG.mkdir(parents=True, exist_ok=True)

CYCLE6_RES = ROOT / "research/experiments/2026-05-04-cycle6-m2-warmstart-cem/results"

FAMILY_COLORS = {
    "piecewise": "#1f77b4",
    "submission_compact": "#d62728",
    "submission_basis": "#2ca02c",
}

FAMILY_TITLE = {
    "piecewise": "piecewise (cycle 6)",
    "submission_compact": "submission_compact",
    "submission_basis": "submission_basis",
}

INHERITED_TEST = {
    "piecewise": 414.010,
    "submission_compact": 410.776,
    "submission_basis": 380.262,
}


def _load_history(family: str):
    candidates = [RES / f"warmstart_cem_{family}_history.json"]
    if family == "piecewise":
        candidates.append(CYCLE6_RES / "warmstart_cem_history.json")
    for p in candidates:
        if p.exists():
            with p.open() as f:
                d = json.load(f)
            return d, p
    return None, None


def _load_test(family: str):
    candidates = [RES / f"warmstart_cem_{family}_test.json"]
    if family == "piecewise":
        candidates.append(CYCLE6_RES / "warmstart_cem_test.json")
    for p in candidates:
        if p.exists():
            with p.open() as f:
                d = json.load(f)
            return d
    return None


def build_convergence():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=False)
    families = ["piecewise", "submission_compact", "submission_basis"]
    for ax, family in zip(axes, families):
        d, _ = _load_history(family)
        if d is None:
            ax.set_title(f"{FAMILY_TITLE[family]} (n/a)")
            ax.axis("off")
            continue
        gens = [r["generation"] for r in d["history"]]
        best = [r["best_search_score"] for r in d["history"]]
        elite_mean = [r["elite_mean_search_score"] for r in d["history"]]
        val = [r["fixed_val_score"] for r in d["history"]]
        c = FAMILY_COLORS[family]
        ax.plot(gens, best, "-o", color=c, label="best-of-search", lw=1.2, markersize=4)
        ax.plot(
            gens, elite_mean, "--s", color=c, label="elite mean", alpha=0.7,
            lw=1.0, markersize=3,
        )
        ax.plot(gens, val, ":^", color="black", label="fixed-val (best)", lw=1.0, markersize=3)
        ax.axhline(INHERITED_TEST[family], color="gray", linestyle="-", lw=0.8, alpha=0.7,
                   label=f"inherited test ({INHERITED_TEST[family]:.1f})")
        ax.set_title(FAMILY_TITLE[family])
        ax.set_xlabel("generation")
        ax.set_ylabel("score")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="lower right")
    fig.suptitle("Cycle 7 — warm-start CEM convergence by policy family", y=1.02, fontsize=12)
    fig.tight_layout()
    out = FIG / "family_comparison.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def build_lift_bar():
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    families = ["piecewise", "submission_compact", "submission_basis"]
    inherited = [INHERITED_TEST[f] for f in families]
    new_scores = []
    deltas = []
    for f in families:
        t = _load_test(f)
        if t is None:
            new_scores.append(None)
            deltas.append(None)
        else:
            ts = t["best_by_val"]["test_score"]
            new_scores.append(ts)
            deltas.append(ts - INHERITED_TEST[f])

    x = list(range(len(families)))
    width = 0.35
    inh_bars = ax.bar([xi - width / 2 for xi in x], inherited, width=width,
                       color="#cccccc", label="inherited best-test")
    cycle7 = [s if s is not None else 0 for s in new_scores]
    cy_bars = ax.bar([xi + width / 2 for xi in x], cycle7, width=width,
                     color=[FAMILY_COLORS[f] for f in families],
                     label="warm-start CEM (cycle 6/7)")
    ax.axhline(540, color="red", linestyle="--", lw=1.2, label="M2 target (540)")
    for xi, ts, delta in zip(x, new_scores, deltas):
        if ts is None:
            ax.text(xi + width / 2, 5, "running…", rotation=90,
                    color="gray", ha="center", va="bottom")
            continue
        ax.text(xi + width / 2, ts + 5, f"{ts:.1f}\n({delta:+.1f})",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([FAMILY_TITLE[f] for f in families], fontsize=9)
    ax.set_ylabel("held-out test score")
    ax.set_title("Cycle 7 — inherited vs warm-start CEM by policy family")
    ax.set_ylim(0, 600)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIG / "family_lift_bar.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    build_convergence()
    build_lift_bar()
