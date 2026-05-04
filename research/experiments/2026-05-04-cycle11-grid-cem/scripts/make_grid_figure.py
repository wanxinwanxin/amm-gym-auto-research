"""
Cycle-11 grid figure: combine cycle-10 (4 cells) with cycle-11 round 1
(3 cells) into a single (dim, rng_seed) → score scatter and a CEM-noise
spread summary.

Inputs (relative to repo root):
  research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_test.json   # c9 #1 (16-d, seed=0)
  research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results/ema_inventory_cem_test.json  # c9 #3 (20-d EMA, seed=0)
  research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_test.json   # c10 A (20-d noop, seed=0)
  research/experiments/2026-05-04-cycle10-noop-tail-cem/results/seed_lottery_cem_test.json # c10 B (16-d, seed=1)
  research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2/result.json
  research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d24_s0/result.json
  research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d24_s1/result.json

Output: research/experiments/2026-05-04-cycle11-grid-cem/figures/grid_summary.png
        research/experiments/2026-05-04-cycle11-grid-cem/results/grid_summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]


def _load(path: Path) -> dict | None:
    if not path.exists():
        print(f"[skip] missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return None
    with path.open() as f:
        return json.load(f)


def main() -> None:
    cells: list[dict] = []

    # cycle-9 #1: 16-d piecewise, seed=0
    c9_first = _load(
        ROOT
        / "research/experiments/2026-05-04-cycle9-third-pass-piecewise-cem/results/third_pass_cem_test.json"
    )
    if c9_first is not None:
        cells.append(
            {
                "label": "c9-#1",
                "dim_total": 16,
                "core_dim": 16,
                "tail_dim": 0,
                "rng_seed": 0,
                "wrapper": "bare",
                "test_score": c9_first["best_by_val"]["test_score"],
                "val_score": c9_first["best_by_val"]["val_score"],
            }
        )

    # cycle-9 #3: EMA wrapper (20-d but ablation says EMA=+0.024)
    c9_third = _load(
        ROOT
        / "research/experiments/2026-05-04-cycle9-ema-inventory-piecewise/results/ema_inventory_cem_test.json"
    )
    if c9_third is not None:
        cells.append(
            {
                "label": "c9-#3",
                "dim_total": 20,
                "core_dim": 16,
                "tail_dim": 4,
                "rng_seed": 0,
                "wrapper": "EMA-inv (ablated to ~zero signal)",
                "test_score": c9_third["best_by_val"]["test_score"],
                "val_score": c9_third["best_by_val"]["val_score"],
            }
        )

    # cycle-10 A: 20-d noop, seed=0
    c10_a = _load(
        ROOT
        / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/noop_tail_cem_test.json"
    )
    if c10_a is not None:
        cells.append(
            {
                "label": "c10-A",
                "dim_total": 20,
                "core_dim": 16,
                "tail_dim": 4,
                "rng_seed": 0,
                "wrapper": "noop tail",
                "test_score": c10_a["best_by_val"]["test_score"],
                "val_score": c10_a["best_by_val"]["val_score"],
            }
        )

    # cycle-10 B: 16-d, seed=1
    c10_b = _load(
        ROOT
        / "research/experiments/2026-05-04-cycle10-noop-tail-cem/results/seed_lottery_cem_test.json"
    )
    if c10_b is not None:
        cells.append(
            {
                "label": "c10-B",
                "dim_total": 16,
                "core_dim": 16,
                "tail_dim": 0,
                "rng_seed": 1,
                "wrapper": "bare",
                "test_score": c10_b["best_by_val"]["test_score"],
                "val_score": c10_b["best_by_val"]["val_score"],
            }
        )

    # cycle-11 round 1
    cycle11_results = (
        ROOT / "research/experiments/2026-05-04-cycle11-grid-cem/results"
    )
    for label, dim_total, seed in (("c11-d16-s2", 16, 2), ("c11-d24-s0", 24, 0), ("c11-d24-s1", 24, 1)):
        d = _load(cycle11_results / f"cell_d{dim_total}_s{seed}" / "result.json")
        if d is None:
            continue
        cells.append(
            {
                "label": label,
                "dim_total": dim_total,
                "core_dim": 16,
                "tail_dim": dim_total - 16,
                "rng_seed": seed,
                "wrapper": "noop tail" if dim_total > 16 else "bare",
                "test_score": d["best_by_val"]["test_score"],
                "val_score": d["best_by_val"]["val_score"],
            }
        )

    if not cells:
        print("No cells loaded; aborting.", file=sys.stderr)
        sys.exit(1)

    # ---------- figure ----------
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    # left panel: test score vs (dim_total, rng_seed)
    ax = axes[0]
    seeds = sorted({c["rng_seed"] for c in cells})
    dims = sorted({c["dim_total"] for c in cells})
    seed_color = {s: c for s, c in zip(seeds, plt.cm.tab10.colors[: len(seeds)])}
    for c in cells:
        x = c["dim_total"] + 0.18 * c["rng_seed"]
        y = c["test_score"]
        ax.scatter(
            x,
            y,
            s=110,
            color=seed_color[c["rng_seed"]],
            edgecolor="black",
            linewidth=0.6,
            label=f"seed {c['rng_seed']}",
            zorder=3,
        )
        ax.annotate(c["label"], (x, y), xytext=(6, -3), textcoords="offset points", fontsize=8)
    ax.axhline(446.61, color="grey", lw=1, ls=":", label="cycle-8 anchor 446.61")
    ax.axhline(540, color="C3", lw=1, ls="--", label="M2 target 540")
    ax.set_xticks(dims)
    ax.set_xlabel("CEM dimension (16 piecewise core + inert noop tail)")
    ax.set_ylabel("Test score (256 held-out seeds)")
    ax.set_title("Cycle-11 grid: warm-start CEM scores by (dim, rng_seed)")
    handles, labels = ax.get_legend_handles_labels()
    seen = set()
    uniq = []
    for h, l in zip(handles, labels):
        if l in seen:
            continue
        seen.add(l)
        uniq.append((h, l))
    ax.legend(*zip(*uniq), loc="lower right", fontsize=8)
    ax.grid(alpha=0.25)

    # right panel: spread / distribution
    ax = axes[1]
    test_scores = [c["test_score"] for c in cells]
    ax.boxplot(
        [test_scores],
        widths=0.5,
        vert=True,
        showmeans=True,
        meanline=True,
        labels=["all cells"],
    )
    for i, c in enumerate(cells):
        x = 1 + 0.10 * (i - len(cells) / 2)
        ax.scatter(x, c["test_score"], color=seed_color[c["rng_seed"]], s=70, edgecolor="black", linewidth=0.5, zorder=3)
        ax.annotate(c["label"], (x, c["test_score"]), xytext=(6, 0), textcoords="offset points", fontsize=8)
    ax.axhline(446.61, color="grey", lw=1, ls=":")
    arr = np.asarray(test_scores)
    ax.set_title(
        f"CEM-noise spread (n={len(arr)}): "
        f"min {arr.min():.2f} | mean {arr.mean():.2f} | max {arr.max():.2f} | std {arr.std(ddof=1):.2f}"
    )
    ax.set_ylabel("Test score")
    ax.grid(alpha=0.25)

    fig.suptitle(
        "Cycle-11 — multi-seed × multi-dim warm-start CEM grid (anchor: cycle-8 ablation best, recipe: pop=24, gen=12, init_std=0.10)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_png = (
        ROOT
        / "research/experiments/2026-05-04-cycle11-grid-cem/figures/grid_summary.png"
    )
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

    out_json = (
        ROOT
        / "research/experiments/2026-05-04-cycle11-grid-cem/results/grid_summary.json"
    )
    out_json.write_text(
        json.dumps(
            {
                "cells": cells,
                "summary": {
                    "n": len(cells),
                    "min": float(arr.min()),
                    "mean": float(arr.mean()),
                    "median": float(np.median(arr)),
                    "max": float(arr.max()),
                    "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
                    "argmax_label": cells[int(np.argmax(arr))]["label"],
                },
            },
            indent=2,
        )
    )
    print(f"wrote {out_png.relative_to(ROOT)}")
    print(f"wrote {out_json.relative_to(ROOT)}")
    print(json.dumps({"argmax": cells[int(np.argmax(arr))], "summary": {"min": float(arr.min()), "max": float(arr.max()), "mean": float(arr.mean())}}, indent=2))


if __name__ == "__main__":
    main()
