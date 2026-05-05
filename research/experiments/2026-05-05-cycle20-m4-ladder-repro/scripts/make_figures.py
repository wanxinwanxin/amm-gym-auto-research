"""
Cycle-20 figure builder.

Inputs (read at runtime; tolerates missing seed-2 if not yet done):
  - cycle-19 ladder result: test.json
  - cycle-20 seed-1 ladder result: test.json
  - cycle-20 seed-2 ladder result: test.json (optional)
  - cycle-18 c11+CEM long: test.json (anchor)

Outputs (figures/):
  - m4_c20_seed_dispersion.png  -- bar chart of test lift_FF across
    seeds 0/1/2 vs c11+CEM long anchor band, with the cycle-19
    "marginal" decision band overlaid.
  - m4_c20_val_curves.png       -- per-gen best/elite_mean curves on
    SEARCH seeds for seeds 0/1/2.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
CYCLE19 = ROOT / "research/experiments/2026-05-05-cycle19-m4-ablation-and-ladder/results/ladder_cem/test.json"
CYCLE20_S1 = ROOT / "research/experiments/2026-05-05-cycle20-m4-ladder-repro/results/ladder_cem_seed1/test.json"
CYCLE20_S2 = ROOT / "research/experiments/2026-05-05-cycle20-m4-ladder-repro/results/ladder_cem_seed2/test.json"
CYCLE18 = ROOT / "research/experiments/2026-05-05-cycle18-m4-prior-sweep/results/long_cem_from_c11/test.json"

OUT_FIG = ROOT / "research/experiments/2026-05-05-cycle20-m4-ladder-repro/figures"
OUT_FIG.mkdir(parents=True, exist_ok=True)
PRESENTATION_FIG = ROOT / "research/presentation/figures"
PRESENTATION_FIG.mkdir(parents=True, exist_ok=True)


def _load(p: Path) -> dict | None:
    if not p.exists():
        return None
    with p.open() as f:
        return json.load(f)


def main() -> None:
    c19 = _load(CYCLE19)
    s1 = _load(CYCLE20_S1)
    s2 = _load(CYCLE20_S2)
    c18 = _load(CYCLE18)

    rows = []
    if c19 is not None:
        rows.append(("ladder seed=0\n(cycle-19)", c19["best_by_val"]["lift_FF"], c19["best_by_val"]["test_retail_advantage"]))
    if s1 is not None:
        rows.append(("ladder seed=1\n(cycle-20)", s1["best_by_val"]["lift_FF"], s1["best_by_val"]["test_retail_advantage"]))
    if s2 is not None:
        rows.append(("ladder seed=2\n(cycle-20)", s2["best_by_val"]["lift_FF"], s2["best_by_val"]["test_retail_advantage"]))

    anchor_lift = c18["best_by_val"]["lift_FF"] if c18 is not None else None
    anchor_retail = c18["best_by_val"]["test_retail_advantage"] if c18 is not None else None

    # ----- figure 1: lift_FF dispersion bar chart -----
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    labels = [r[0] for r in rows]
    lifts = np.asarray([r[1] for r in rows])
    xs = np.arange(len(rows))
    bars = ax.bar(xs, lifts, color=["#3a8fb7", "#cf6e2a", "#3a8fb7"][: len(rows)], edgecolor="black", zorder=3)
    for b, v in zip(bars, lifts):
        ax.annotate(f"{v:+.3f}", xy=(b.get_x() + b.get_width() / 2, v),
                    xytext=(0, 4), textcoords="offset points", ha="center", fontsize=10)
    if anchor_lift is not None:
        ax.axhline(anchor_lift, color="black", linestyle="--", linewidth=1.0,
                   label=f"c11+CEM long anchor ({anchor_lift:+.3f})", zorder=2)
    # cycle-19 reproducibility band
    ax.axhspan(3.15, 3.35, color="#ffd966", alpha=0.30, label="REPRO_OK band [+3.15, +3.35]", zorder=1)
    ax.axhline(3.15, color="#b6841c", linestyle=":", linewidth=0.8, zorder=1)
    ax.axhline(3.35, color="#b6841c", linestyle=":", linewidth=0.8, zorder=1)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylabel("test lift_FF (n=256, real_data)")
    ax.set_title("Ladder family CEM — seed dispersion\n(cycle-20 reproducibility check)")
    ax.set_ylim(min(lifts.min() if len(lifts) else 0, 2.95) - 0.1, max(lifts.max() if len(lifts) else 4, 3.4) + 0.15)
    ax.grid(axis="y", linestyle=":", alpha=0.4, zorder=0)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    out1 = OUT_FIG / "m4_c20_seed_dispersion.png"
    fig.savefig(out1, dpi=140)
    fig.savefig(PRESENTATION_FIG / "m4_c20_seed_dispersion.png", dpi=140)
    plt.close(fig)
    print(f"wrote {out1}")

    # ----- figure 2: per-gen search-score curves -----
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    if c19 is not None:
        gens = [g["gen"] for g in c19["history"]]
        ax.plot(gens, [g["best_score"] for g in c19["history"]], "-o", label="seed=0 best", color="#3a8fb7")
        ax.plot(gens, [g["elite_mean_score"] for g in c19["history"]], "--^", label="seed=0 elite_mean", color="#3a8fb7", alpha=0.6)
    if s1 is not None:
        gens = [g["gen"] for g in s1["history"]]
        ax.plot(gens, [g["best_score"] for g in s1["history"]], "-o", label="seed=1 best", color="#cf6e2a")
        ax.plot(gens, [g["elite_mean_score"] for g in s1["history"]], "--^", label="seed=1 elite_mean", color="#cf6e2a", alpha=0.6)
    if s2 is not None:
        gens = [g["gen"] for g in s2["history"]]
        ax.plot(gens, [g["best_score"] for g in s2["history"]], "-o", label="seed=2 best", color="#5b8c2d")
        ax.plot(gens, [g["elite_mean_score"] for g in s2["history"]], "--^", label="seed=2 elite_mean", color="#5b8c2d", alpha=0.6)
    ax.set_xlabel("generation")
    ax.set_ylabel("score on SEARCH seeds (n=64, real_data)")
    ax.set_title("Ladder CEM search-score trajectory across rng_seeds")
    ax.grid(linestyle=":", alpha=0.4)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    out2 = OUT_FIG / "m4_c20_val_curves.png"
    fig.savefig(out2, dpi=140)
    fig.savefig(PRESENTATION_FIG / "m4_c20_val_curves.png", dpi=140)
    plt.close(fig)
    print(f"wrote {out2}")

    # ----- summary table -----
    summary = {
        "anchor_c11_long_lift_FF": anchor_lift,
        "anchor_c11_long_retail_adv": anchor_retail,
        "seeds": {
            "seed_0_cycle19": {"lift_FF": c19["best_by_val"]["lift_FF"] if c19 else None,
                                "test_score": c19["best_by_val"]["test_score"] if c19 else None,
                                "retail_adv": c19["best_by_val"]["test_retail_advantage"] if c19 else None,
                                "edge_adv": c19["best_by_val"]["test_edge_advantage"] if c19 else None},
            "seed_1_cycle20": {"lift_FF": s1["best_by_val"]["lift_FF"] if s1 else None,
                                "test_score": s1["best_by_val"]["test_score"] if s1 else None,
                                "retail_adv": s1["best_by_val"]["test_retail_advantage"] if s1 else None,
                                "edge_adv": s1["best_by_val"]["test_edge_advantage"] if s1 else None},
            "seed_2_cycle20": {"lift_FF": s2["best_by_val"]["lift_FF"] if s2 else None,
                                "test_score": s2["best_by_val"]["test_score"] if s2 else None,
                                "retail_adv": s2["best_by_val"]["test_retail_advantage"] if s2 else None,
                                "edge_adv": s2["best_by_val"]["test_edge_advantage"] if s2 else None},
        },
    }
    if all(v["lift_FF"] is not None for v in summary["seeds"].values()):
        lifts_arr = np.asarray([v["lift_FF"] for v in summary["seeds"].values()])
        summary["lift_FF_mean"] = float(lifts_arr.mean())
        summary["lift_FF_std"] = float(lifts_arr.std(ddof=1))
        summary["lift_FF_min"] = float(lifts_arr.min())
        summary["lift_FF_max"] = float(lifts_arr.max())
    with (OUT_FIG.parent / "results" / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"summary: {summary}")


if __name__ == "__main__":
    main()
