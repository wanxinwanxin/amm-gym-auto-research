"""Build M1 comparison: simulator markout distribution vs on-chain reference.

Reads:
  results/sim_markouts.parquet    (per-trade simulator markouts)
  results/bq_quantiles_2026-04-27.json (200-bin BQ quantile dump)
  results/bq_daily_summary.json   (per-day on-chain summary stats)

Writes:
  results/comparison_table.json   (side-by-side percentile table)
  figures/markout_cdf_overlay.png (CDF of sim retail vs BQ on-chain)
  figures/markout_hist_overlay.png (histogram overlay)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def load_bq_quantiles(path: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    rows = json.loads(path.read_text())
    pcts = np.asarray([r["pct"] / 100.0 for r in rows], dtype=float)  # 0..1
    qs_next = np.asarray([r["markout_next_bps"] for r in rows], dtype=float)
    head = rows[0]
    meta = {
        "n": int(head["n"]),
        "mean_bps_next": float(head["mean_bps_next"]),
        "std_bps_next": float(head["std_bps_next"]),
        "mean_bps_15s": float(head["mean_bps_15s"]),
        "std_bps_15s": float(head["std_bps_15s"]),
        "total_usd": float(head["total_usd"]),
    }
    return pcts, qs_next, meta


def percentile_table(values_bps: np.ndarray) -> dict:
    out = {"n": int(len(values_bps))}
    if len(values_bps) == 0:
        return out
    out["mean_bps"] = float(values_bps.mean())
    out["std_bps"] = float(values_bps.std(ddof=1))
    for p in [1, 5, 25, 50, 75, 95, 99]:
        out[f"p{p}_bps"] = float(np.percentile(values_bps, p))
    return out


def main() -> None:
    df = pd.read_parquet(RESULTS / "sim_markouts.parquet")
    retail = df[df["source"] == "retail"]
    sim_next_bps = (retail["markout_next_log"].dropna() * 1e4).to_numpy()
    sim_now_bps = (retail["markout_now_log"].dropna() * 1e4).to_numpy()

    pcts, qs_bq_next, bq_meta = load_bq_quantiles(RESULTS / "bq_quantiles_2026-04-27.json")

    # Side-by-side comparison
    table = {
        "ground_truth": {
            "source": "uniswap-labs.research.markout_prod",
            "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 (WETH/USDC v3 0.05%)",
            "block_date": "2026-04-27",
            "filter": "ABS(markout_next) < 0.05 to drop benchmark-glitch outliers",
            **bq_meta,
            "p1_bps":  float(np.interp(0.01, pcts, qs_bq_next)),
            "p5_bps":  float(np.interp(0.05, pcts, qs_bq_next)),
            "p25_bps": float(np.interp(0.25, pcts, qs_bq_next)),
            "p50_bps": float(np.interp(0.50, pcts, qs_bq_next)),
            "p75_bps": float(np.interp(0.75, pcts, qs_bq_next)),
            "p95_bps": float(np.interp(0.95, pcts, qs_bq_next)),
            "p99_bps": float(np.interp(0.99, pcts, qs_bq_next)),
        },
        "simulator_retail_markout_now": percentile_table(sim_now_bps),
        "simulator_retail_markout_next": percentile_table(sim_next_bps),
    }
    (RESULTS / "comparison_table.json").write_text(json.dumps(table, indent=2))
    print("wrote comparison_table.json")

    # CDF overlay (focus on the inner 95% of mass for shape readability)
    sim_sorted = np.sort(sim_next_bps)
    sim_pcts = np.linspace(0, 1, len(sim_sorted))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    ax.plot(qs_bq_next, pcts, "-", color="#1f3a93", lw=2.0,
            label=f"On-chain (n={bq_meta['n']:,}, mean={bq_meta['mean_bps_next']:+.2f} bps)")
    ax.plot(sim_sorted, sim_pcts, "--", color="#e74c3c", lw=2.0,
            label=f"Simulator retail (n={len(sim_sorted):,}, mean={sim_next_bps.mean():+.2f} bps)")
    ax.axvline(0, color="#888", lw=0.6, ls=":")
    ax.set_xlim(-30, 30)
    ax.set_ylim(0, 1)
    ax.set_xlabel("markout_next (bps; LP perspective)")
    ax.set_ylabel("CDF")
    ax.set_title("CDF: simulator retail vs on-chain reference\n(WETH/USDC v3 0.05%, 2026-04-27)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)

    # Reconstruct an approximate on-chain sample by piecewise-uniform-from-CDF
    # (treats the quantile grid as histogram edges) just for the histogram.
    bq_sample = np.interp(np.random.default_rng(0).random(50_000), pcts, qs_bq_next)
    sim_sample = sim_next_bps

    ax = axes[1]
    bins = np.linspace(-30, 30, 121)
    ax.hist(bq_sample, bins=bins, density=True, alpha=0.45, color="#1f3a93",
            label=f"On-chain (resampled n={len(bq_sample):,})")
    ax.hist(sim_sample, bins=bins, density=True, alpha=0.45, color="#e74c3c",
            label=f"Simulator retail (n={len(sim_sample):,})")
    ax.axvline(0, color="#888", lw=0.6, ls=":")
    ax.set_xlim(-30, 30)
    ax.set_xlabel("markout_next (bps; LP perspective)")
    ax.set_ylabel("density")
    ax.set_title("Histogram: simulator retail vs on-chain reference")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES / "markout_cdf_overlay.png", dpi=140, bbox_inches="tight")
    print("wrote markout_cdf_overlay.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
