"""Make cycle-24 figures and cross-seed/cross-anchor summary.

Cycle 23 produced n=2 long-CEM ladder runs on cycle-21-seed-1 piecewise
(mean lift over piecewise +0.132 +/- 0.066). Cycle 24 adds:
  * a third RNG seed on the same anchor (rng_seed=2) — tightens the
    n=2 mean estimate.
  * a cross-anchor probe on cycle-21-seed-2 (basin-collapsed) piecewise
    (rng_seed=0) — tests "ladder as stabilizer at long-CEM".

Figures:
  1. m4_c24_lift_summary.png — bar chart of ladder test-lift vs the
     same-anchor piecewise across c19/c22/c23/c24 runs, grouped by
     (anchor, budget).
  2. m4_c24_long_cem_val_curves.png — CEM search-best trajectories
     for the three c21-s1 long-CEM seeds (c23 s0/s1, c24 s2) plus
     the c24 cross-anchor c21-s2 trajectory, with anchor val lines
     overlaid.
  3. cross_seed_summary.json — machine-readable n=3 mean for c21-s1
     long-CEM ladder + cross-anchor lift for c21-s2.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-06-cycle24-m4-ladder-longcem-followup"
C23_DIR = ROOT / "research/experiments/2026-05-06-cycle23-m4-ladder-longcem"
C22_DIR = ROOT / "research/experiments/2026-05-05-cycle22-m4-ladder-anchor-control"
FIGDIR = EXP_DIR / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path) -> dict:
    return json.load(path.open())


def main() -> None:
    # --- Cycle-24 runs ---
    c24_runs: dict[str, dict] = {}
    for run in ("cycle21_seed1_seed2", "cycle21_seed2_seed0"):
        p = EXP_DIR / "results" / run / "test.json"
        if p.exists():
            c24_runs[run] = _load(p)

    # --- Cycle-23 runs (already on c21-s1 anchor) ---
    c23_runs: dict[str, dict] = {}
    for run in ("cycle21_seed1_seed0", "cycle21_seed1_seed1"):
        p = C23_DIR / "results" / run / "test.json"
        if p.exists():
            c23_runs[run] = _load(p)

    # --- Reference numbers (locked from prior cycles) ---
    # piecewise on cycle-21-seed-1: test 3.370 / lift_FF +2.900
    c21s1_piecewise_lift_FF = 2.900
    c21s1_piecewise_test = 3.370
    # piecewise on cycle-21-seed-2: test 2.745 / lift_FF +2.275 (basin-collapsed)
    c21s2_piecewise_lift_FF = 2.275
    c21s2_piecewise_test = 2.745
    # cycle-22 short-CEM ladder on c21-s1: lift_FF +2.900 (rerank picked anchor, n=2)
    # cycle-22 stretch ladder on c21-s2: lift_FF +2.275 (rerank picked anchor)
    c22_short_lift = {
        ("c21s1", 0): 2.900,
        ("c21s1", 1): 2.900,
        ("c21s2", 0): 2.275,
    }

    # --- Combined long-CEM ladder summary on c21-s1 (c23 s0/s1 + c24 s2) ---
    c21s1_long: list[tuple[int, float, float, str]] = []  # (seed, lift_FF, retail, source)
    for run, d in c23_runs.items():
        seed = int(run.rsplit("_seed", 1)[-1])
        c21s1_long.append((seed,
                           float(d["best_by_val"]["lift_FF"]),
                           float(d["best_by_val"]["test_retail_advantage"]),
                           "cycle23"))
    if "cycle21_seed1_seed2" in c24_runs:
        d = c24_runs["cycle21_seed1_seed2"]
        c21s1_long.append((2,
                           float(d["best_by_val"]["lift_FF"]),
                           float(d["best_by_val"]["test_retail_advantage"]),
                           "cycle24"))
    c21s1_long.sort(key=lambda t: t[0])

    c21s1_long_lifts = [t[1] for t in c21s1_long]
    c21s1_long_lift_over_piecewise = [l - c21s1_piecewise_lift_FF for l in c21s1_long_lifts]

    if c21s1_long:
        n = len(c21s1_long_lifts)
        mean_lift_FF = float(np.mean(c21s1_long_lifts))
        std_lift_FF = float(np.std(c21s1_long_lifts, ddof=1)) if n > 1 else 0.0
        mean_lift_over = float(np.mean(c21s1_long_lift_over_piecewise))
        std_lift_over = float(np.std(c21s1_long_lift_over_piecewise, ddof=1)) if n > 1 else 0.0
    else:
        n, mean_lift_FF, std_lift_FF, mean_lift_over, std_lift_over = 0, 0.0, 0.0, 0.0, 0.0

    # --- Cross-anchor probe (c21-s2 long-CEM ladder, c24 only) ---
    c21s2_long_lift_FF: float | None = None
    c21s2_long_lift_over_piecewise: float | None = None
    c21s2_long_retail: float | None = None
    if "cycle21_seed2_seed0" in c24_runs:
        d = c24_runs["cycle21_seed2_seed0"]
        c21s2_long_lift_FF = float(d["best_by_val"]["lift_FF"])
        c21s2_long_lift_over_piecewise = c21s2_long_lift_FF - c21s2_piecewise_lift_FF
        c21s2_long_retail = float(d["best_by_val"]["test_retail_advantage"])

    # --- Fig 1: lift bar chart, grouped by (anchor, budget) ---
    rows: list[tuple[str, float]] = []
    rows.append(("c21-s1 short (c22 s0)", c22_short_lift[("c21s1", 0)] - c21s1_piecewise_lift_FF))
    rows.append(("c21-s1 short (c22 s1)", c22_short_lift[("c21s1", 1)] - c21s1_piecewise_lift_FF))
    for seed, lift, _r, src in c21s1_long:
        rows.append((f"c21-s1 LONG ({src} s{seed})", lift - c21s1_piecewise_lift_FF))
    rows.append(("c21-s2 short (c22 s0)", c22_short_lift[("c21s2", 0)] - c21s2_piecewise_lift_FF))
    if c21s2_long_lift_over_piecewise is not None:
        rows.append(("c21-s2 LONG (c24 s0)", c21s2_long_lift_over_piecewise))

    labels = [r[0] for r in rows]
    deltas = [r[1] for r in rows]
    colors = []
    for lbl in labels:
        if "c21-s1 short" in lbl:
            colors.append("#ff7f0e")
        elif "c21-s1 LONG" in lbl:
            colors.append("#d62728")
        elif "c21-s2 short" in lbl:
            colors.append("#aec7e8")
        else:
            colors.append("#1f77b4")

    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    bars = ax.bar(range(len(labels)), deltas, color=colors, alpha=0.9)
    ax.axhline(0.0, color="black", linewidth=0.7)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("ladder test lift_FF − piecewise anchor lift_FF (same anchor)")
    title = (
        "M4 cycle 24 — ladder lift over same-anchor piecewise, by (anchor, budget)\n"
        "c23 s0/s1 + c24 s2 form n=3 c21-s1 long-CEM sample;  c24 c21-s2 is the cross-anchor probe"
    )
    ax.set_title(title)
    for d_, b in zip(deltas, bars):
        y = d_ + (0.005 if d_ >= 0 else -0.02)
        ax.text(b.get_x() + b.get_width() / 2, y,
                f"{d_:+.3f}", ha="center",
                va="bottom" if d_ >= 0 else "top", fontsize=10)
    if c21s1_long:
        # overlay mean line for c21-s1 LONG group
        long_xs = [i for i, lbl in enumerate(labels) if "c21-s1 LONG" in lbl]
        if long_xs:
            ymean = mean_lift_over
            ax.plot([min(long_xs) - 0.4, max(long_xs) + 0.4], [ymean, ymean],
                    color="black", linestyle=":", linewidth=1.2,
                    label=f"c21-s1 LONG mean (n={n}) = {ymean:+.3f} ± {std_lift_over:.3f}")
            ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGDIR / "m4_c24_lift_summary.png", dpi=140)
    plt.close(fig)

    # --- Fig 2: long-CEM val curves ---
    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    color_map = {
        "cycle21_seed1_seed0_c23": "#d62728",
        "cycle21_seed1_seed1_c23": "#9467bd",
        "cycle21_seed1_seed2_c24": "#e377c2",
        "cycle21_seed2_seed0_c24": "#1f77b4",
    }
    runs_for_plot: list[tuple[str, dict, str]] = []
    for run, d in c23_runs.items():
        runs_for_plot.append((run + "_c23", d, "c23"))
    for run, d in c24_runs.items():
        runs_for_plot.append((run + "_c24", d, "c24"))

    for run_label, d, _src in runs_for_plot:
        history = d["history"]
        gens = [h["gen"] for h in history]
        c = color_map.get(run_label, "#7f7f7f")
        ax.plot(gens, [h["best_score"] for h in history], "o-",
                color=c, label=f"{run_label} best (search n=64)")
        ax.plot(gens, [h["elite_mean_score"] for h in history], "s--",
                color=c, alpha=0.5, linewidth=0.9)

    # Anchor val lines per anchor
    if c23_runs:
        anchor_val_s1 = next(iter(c23_runs.values()))["anchor_val_score"]
        ax.axhline(anchor_val_s1, color="black", linestyle=":", linewidth=1.0,
                   label=f"c21-s1 anchor val (n=128) = {anchor_val_s1:.3f}")
    if "cycle21_seed2_seed0" in c24_runs:
        anchor_val_s2 = c24_runs["cycle21_seed2_seed0"]["anchor_val_score"]
        ax.axhline(anchor_val_s2, color="#1f77b4", linestyle=":", linewidth=1.0,
                   label=f"c21-s2 anchor val (n=128) = {anchor_val_s2:.3f}")

    ax.set_xlabel("CEM generation")
    ax.set_ylabel("score (search n=64 for trajectory; val n=128 for anchor)")
    ax.set_title("Cycle 24 — long-CEM ladder trajectories (c23 + c24, two anchors)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR / "m4_c24_long_cem_val_curves.png", dpi=140)
    plt.close(fig)

    # --- Cross-seed/cross-anchor JSON summary ---
    summary = {
        "anchors": {
            "c21s1": {
                "piecewise_test": c21s1_piecewise_test,
                "piecewise_lift_FF": c21s1_piecewise_lift_FF,
                "long_cem_ladder_runs": [
                    {
                        "src": src,
                        "rng_seed": seed,
                        "lift_FF": lift,
                        "lift_over_piecewise": lift - c21s1_piecewise_lift_FF,
                        "retail_advantage_test": retail,
                    }
                    for seed, lift, retail, src in c21s1_long
                ],
                "n_seeds": n,
                "long_cem_ladder_mean_lift_FF": mean_lift_FF,
                "long_cem_ladder_std_lift_FF": std_lift_FF,
                "long_cem_ladder_mean_lift_over_piecewise": mean_lift_over,
                "long_cem_ladder_std_lift_over_piecewise": std_lift_over,
                "short_cem_ladder_lift_FF": [c22_short_lift[("c21s1", 0)],
                                             c22_short_lift[("c21s1", 1)]],
            },
            "c21s2": {
                "piecewise_test": c21s2_piecewise_test,
                "piecewise_lift_FF": c21s2_piecewise_lift_FF,
                "long_cem_ladder_lift_FF": c21s2_long_lift_FF,
                "long_cem_ladder_lift_over_piecewise": c21s2_long_lift_over_piecewise,
                "long_cem_ladder_retail_advantage_test": c21s2_long_retail,
                "short_cem_ladder_lift_FF": [c22_short_lift[("c21s2", 0)]],
            },
        },
        "decision_rule": {
            "c21s1_n3_target_band_lift_FF": [2.95, 3.10],
            "c21s2_long_cem_target_lift_over_piecewise": "+0.05 (stabilizer hypothesis)",
        },
    }
    with (EXP_DIR / "results/cross_seed_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
