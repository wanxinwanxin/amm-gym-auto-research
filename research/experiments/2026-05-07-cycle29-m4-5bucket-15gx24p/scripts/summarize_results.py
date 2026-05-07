"""
Cycle-29 cross-seed summary — minimal version.

Produces:
- results/cross_seed_summary.json — per-seed best-by-val test scores,
  cluster mean/stddev, comparison vs cycle 28 cluster (10g) and
  cycle 26 4-bucket cluster (10g), decision-rule verdict.
- figures/m4_c29_compute_compare.png — bar chart comparing cycle-26
  4-bucket (10g, n=3), cycle-28 5-bucket-tight (10g, n=2), cycle-29
  5-bucket-tight (15g, n=2).
- figures/m4_c29_long_cem_val_curves.png — CEM trajectories per
  seed at 15g for cycle 29 with cycle-28 10g trajectories overlaid
  (gens 0-9 should match exactly).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "research/experiments/2026-05-07-cycle29-m4-5bucket-15gx24p"
C28_DIR = ROOT / "research/experiments/2026-05-06-cycle28-m4-5bucket-tightstd"
RESULTS = EXP_DIR / "results"
FIGURES = EXP_DIR / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# Frontier reference numbers (held since cycle 26 / cycle 28).
PIECEWISE_LIFT_FF = 3.005713888877396  # cycle-18 c18-s0 piecewise

CYCLE26_4BUCKET_LIFT_FF = [3.2561983858883536, 3.267579039721601, 3.3070122159543858]
CYCLE28_5BUCKET_TIGHT_LIFT_FF = []  # filled from disk below

# Decision thresholds.
FRONTIER_THRESHOLD = 3.28
CEILING_THRESHOLD = 3.20


def _load_test(seed_dir: Path) -> dict:
    p = seed_dir / "test.json"
    if not p.exists():
        return {"status": "incomplete", "path": str(p)}
    return json.loads(p.read_text())


def _load_history(seed_dir: Path) -> list[dict]:
    p = seed_dir / "history.json"
    if not p.exists():
        return []
    return json.loads(p.read_text())


def main() -> None:
    seed_dirs = sorted(RESULTS.glob("cycle18_seed0_seed*"))
    seeds = []
    incomplete = []
    for sd in seed_dirs:
        rng_seed = int(sd.name.split("seed")[-1])
        test = _load_test(sd)
        history = _load_history(sd)
        if test.get("status") == "incomplete":
            incomplete.append({"rng_seed": rng_seed, "history_gens": len(history)})
            seeds.append(
                {
                    "rng_seed": rng_seed,
                    "status": "incomplete",
                    "history_gens": len(history),
                    "last_elite_mean": history[-1]["elite_mean_score"] if history else None,
                }
            )
            continue
        bbv = test["best_by_val"]
        seeds.append(
            {
                "rng_seed": rng_seed,
                "status": "complete",
                "history_gens": len(history),
                "anchor_val_score": test["anchor_val_score"],
                "best_by_val": {
                    "val_score": bbv["val_score"],
                    "test_score": bbv["test_score"],
                    "test_retail_advantage": bbv.get("test_retail_advantage"),
                    "lift_FF": bbv["lift_FF"],
                    "ff_test_score": bbv["ff_test_score"],
                    "source": bbv.get("source"),
                },
                "lift_over_piecewise": bbv["lift_FF"] - PIECEWISE_LIFT_FF,
            }
        )

    complete = [s for s in seeds if s["status"] == "complete"]
    if complete:
        lift_FFs = np.asarray([s["best_by_val"]["lift_FF"] for s in complete])
        test_scores = np.asarray([s["best_by_val"]["test_score"] for s in complete])
        retail_advs = np.asarray(
            [s["best_by_val"]["test_retail_advantage"] for s in complete if s["best_by_val"].get("test_retail_advantage") is not None]
        )
        lift_pw = np.asarray([s["lift_over_piecewise"] for s in complete])
        cluster = {
            "n_seeds_complete": int(len(complete)),
            "lift_FF_mean": float(lift_FFs.mean()),
            "lift_FF_std": float(lift_FFs.std(ddof=0)) if len(complete) > 1 else 0.0,
            "lift_FF_min": float(lift_FFs.min()),
            "lift_FF_max": float(lift_FFs.max()),
            "test_score_mean": float(test_scores.mean()),
            "lift_over_piecewise_mean": float(lift_pw.mean()),
            "lift_over_piecewise_std": float(lift_pw.std(ddof=0)) if len(complete) > 1 else 0.0,
            "test_retail_advantage_mean": (
                float(retail_advs.mean()) if len(retail_advs) > 0 else None
            ),
        }
    else:
        cluster = {"n_seeds_complete": 0}

    # Compare vs cycle 26 (4-bucket cluster) and cycle 28 (5-bucket-tight 10g).
    c26_mean = float(np.mean(CYCLE26_4BUCKET_LIFT_FF))
    c26_std = float(np.std(CYCLE26_4BUCKET_LIFT_FF, ddof=0))

    # Pull cycle 28 cluster live from disk.
    c28_lifts = []
    for sd in sorted((C28_DIR / "results").glob("cycle18_seed0_seed*")):
        test = _load_test(sd)
        if test.get("status") != "incomplete":
            c28_lifts.append(test["best_by_val"]["lift_FF"])
    c28_mean = float(np.mean(c28_lifts)) if c28_lifts else None
    c28_std = float(np.std(c28_lifts, ddof=0)) if len(c28_lifts) > 1 else 0.0

    # Decision rule.
    verdict = "PENDING"
    rationale = ""
    if cluster.get("n_seeds_complete", 0) >= 2:
        worst = cluster["lift_FF_min"]
        mean = cluster["lift_FF_mean"]
        if worst < CEILING_THRESHOLD:
            verdict = "CEILING_CONFIRMED"
            rationale = (
                f"worst seed lift_FF {worst:.3f} < {CEILING_THRESHOLD}; "
                "4-bucket family is the c18-s0 ceiling at long-CEM"
            )
        elif worst >= CEILING_THRESHOLD and mean > FRONTIER_THRESHOLD:
            verdict = "FRONTIER_LIFTED"
            rationale = (
                f"worst {worst:.3f} >= {CEILING_THRESHOLD} and mean {mean:.3f} "
                f"> {FRONTIER_THRESHOLD}; 5-bucket-tight at 15g lifts the M4 frontier"
            )
        else:
            verdict = "MODEST_GAIN"
            rationale = (
                f"worst {worst:.3f} >= {CEILING_THRESHOLD} but mean {mean:.3f} "
                f"<= {FRONTIER_THRESHOLD}; modest compute gain, family ceiling open"
            )

    summary = {
        "experiment": "2026-05-07-cycle29-m4-5bucket-15gx24p",
        "anchor": "cycle18_seed0",
        "family": "ladder_5bucket",
        "init_std_frac_new": 0.05,
        "init_std_frac_inherited": 0.05,
        "generations": 15,
        "population": 24,
        "evaluator_kind": "real_data",
        "piecewise_lift_FF": PIECEWISE_LIFT_FF,
        "seeds": seeds,
        "incomplete": incomplete,
        "cluster_cycle29_5bucket_tight_15g": cluster,
        "cluster_cycle28_5bucket_tight_10g": {
            "n_seeds": len(c28_lifts),
            "lift_FF_mean": c28_mean,
            "lift_FF_std": c28_std,
            "lift_FFs": c28_lifts,
        },
        "cluster_cycle26_4bucket_10g": {
            "n_seeds": 3,
            "lift_FF_mean": c26_mean,
            "lift_FF_std": c26_std,
            "lift_FFs": CYCLE26_4BUCKET_LIFT_FF,
        },
        "delta_vs_c28_10g": (
            cluster["lift_FF_mean"] - c28_mean
            if cluster.get("lift_FF_mean") is not None and c28_mean is not None
            else None
        ),
        "delta_vs_c26_4bucket": (
            cluster["lift_FF_mean"] - c26_mean
            if cluster.get("lift_FF_mean") is not None
            else None
        ),
        "decision_thresholds": {
            "frontier_lift": FRONTIER_THRESHOLD,
            "ceiling_floor": CEILING_THRESHOLD,
        },
        "verdict": verdict,
        "verdict_rationale": rationale,
    }

    out_path = RESULTS / "cross_seed_summary.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out_path}")
    print(f"verdict={verdict}")
    if cluster.get("n_seeds_complete"):
        print(
            f"cycle29 cluster (n={cluster['n_seeds_complete']}): "
            f"lift_FF={cluster['lift_FF_mean']:+.3f} ± {cluster['lift_FF_std']:.3f} "
            f"(range {cluster['lift_FF_min']:+.3f}, {cluster['lift_FF_max']:+.3f})"
        )
        print(
            f"  vs cycle 28 (10g, n={len(c28_lifts)}): "
            f"Δ={summary['delta_vs_c28_10g']:+.3f} | "
            f"vs cycle 26 (4-bucket, n=3): Δ={summary['delta_vs_c26_4bucket']:+.3f}"
        )
    if incomplete:
        print(f"incomplete seeds: {incomplete}")


def make_compare_figure() -> None:
    """Bar chart: cycle-26 4-bucket / cycle-28 5b-tight 10g / cycle-29 5b-tight 15g."""
    import matplotlib.pyplot as plt

    summary = json.loads((RESULTS / "cross_seed_summary.json").read_text())
    cluster = summary["cluster_cycle29_5bucket_tight_15g"]
    if cluster.get("n_seeds_complete", 0) == 0:
        print("no complete seeds; skipping figure")
        return

    labels = [
        "4-bucket\n10g (c26, n=3)",
        "5-bucket-tight\n10g (c28, n=2)",
        f"5-bucket-tight\n15g (c29, n={cluster['n_seeds_complete']})",
    ]
    means = [
        summary["cluster_cycle26_4bucket_10g"]["lift_FF_mean"],
        summary["cluster_cycle28_5bucket_tight_10g"]["lift_FF_mean"],
        cluster["lift_FF_mean"],
    ]
    stds = [
        summary["cluster_cycle26_4bucket_10g"]["lift_FF_std"],
        summary["cluster_cycle28_5bucket_tight_10g"]["lift_FF_std"],
        cluster["lift_FF_std"],
    ]
    colors = ["#2b6cb0", "#d97706", "#7c3aed"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(labels))
    bars = ax.bar(x, means, yerr=stds, color=colors, edgecolor="#1a202c", capsize=8)
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + 0.005, f"{m:+.3f} ± {s:.3f}", ha="center", fontsize=9)

    ax.axhline(
        summary["cluster_cycle26_4bucket_10g"]["lift_FF_mean"],
        color="#2b6cb0",
        linestyle="--",
        alpha=0.5,
        label="4-bucket cluster mean",
    )
    ax.axhline(
        summary["piecewise_lift_FF"],
        color="#666",
        linestyle=":",
        alpha=0.5,
        label="c18-s0 piecewise (anchor)",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("test lift_FF (real_data, n=256)")
    ax.set_title(
        "Cycle 29 — does extending CEM compute (10g→15g) close\n"
        "the 5-bucket-tight vs 4-bucket gap on c18-s0?"
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(2.95, 3.40)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIGURES / "m4_c29_compute_compare.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"wrote {out}")


def make_val_curve_figure() -> None:
    """Compare cycle 28 (10g) and cycle 29 (15g) elite_mean trajectories."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    palette = {0: "#7c3aed", 1: "#d97706"}
    palette_c28 = {0: "#7c3aed", 1: "#d97706"}

    # Cycle 29 (15g)
    for sd in sorted(RESULTS.glob("cycle18_seed0_seed*")):
        rng_seed = int(sd.name.split("seed")[-1])
        history = _load_history(sd)
        if not history:
            continue
        gens = [h["gen"] for h in history]
        elite = [h["elite_mean_score"] for h in history]
        ax.plot(
            gens,
            elite,
            color=palette.get(rng_seed, "#444"),
            marker="o",
            linewidth=2,
            label=f"c29 15g seed={rng_seed}",
        )

    # Cycle 28 (10g) overlay
    for sd in sorted((C28_DIR / "results").glob("cycle18_seed0_seed*")):
        rng_seed = int(sd.name.split("seed")[-1])
        history = _load_history(sd)
        if not history:
            continue
        gens = [h["gen"] for h in history]
        elite = [h["elite_mean_score"] for h in history]
        ax.plot(
            gens,
            elite,
            color=palette_c28.get(rng_seed, "#888"),
            marker="x",
            linewidth=1.2,
            linestyle="--",
            alpha=0.55,
            label=f"c28 10g seed={rng_seed} (overlay)",
        )

    # Anchor / 4-bucket cluster reference lines
    ax.axhline(2.901, color="#666", linestyle=":", alpha=0.5, label="anchor val (search)")

    ax.set_xlabel("generation")
    ax.set_ylabel("elite-mean search val (real_data, 64 seeds)")
    ax.set_title(
        "Cycle 29 vs cycle 28 — 5-bucket-tight ladder elite-mean\n"
        "trajectories on c18-s0 (gens 0-9 reproduce; 10-14 extend)"
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIGURES / "m4_c29_long_cem_val_curves.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
    if "--figures" in sys.argv:
        make_compare_figure()
        make_val_curve_figure()
