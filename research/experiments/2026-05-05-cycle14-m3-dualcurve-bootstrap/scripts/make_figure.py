"""
M3 cycle-1 figure — challenge vs real_data trajectory across the
chronological M2 anchor sequence.

Two-panel:
  Left  — challenge val_score by anchor (the "in-distribution" curve
          we already optimized). Includes the FixedFee baseline.
  Right — real_data val_score by anchor (the "OOD" curve). Includes
          the FixedFee baseline. The early M2 anchors land *below*
          FixedFee, which is the most arresting fact and gets a
          shaded "harmful" region.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "research/experiments/2026-05-05-cycle14-m3-dualcurve-bootstrap/results/dualcurve.json"
OUTDIR = ROOT / "research/experiments/2026-05-05-cycle14-m3-dualcurve-bootstrap/figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

d = json.loads(RESULTS.read_text())
rows = d["rows"]
labels = [r["label"] for r in rows]
chal = [r["challenge_val_score"] for r in rows]
real = [r["real_data_val_score"] for r in rows]
ff_chal = d["fixedfee_challenge_val_score"]
ff_real = d["fixedfee_real_data_val_score"]

x = np.arange(len(labels))

fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.6))

# Left: challenge curve.
axL.plot(x, chal, "-o", color="#04c", lw=2, label="trained policy (challenge val)")
axL.axhline(ff_chal, color="#888", ls="--", lw=1.2, label=f"FixedFee(0.003)  ({ff_chal:.1f})")
axL.set_xticks(x)
axL.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
axL.set_ylabel("score (val seeds 1000-1127)")
axL.set_title("Challenge eval (in-distribution) — what M2 optimized for")
axL.legend(loc="lower right", fontsize=9)
axL.grid(alpha=0.3)
for xi, yi in zip(x, chal):
    axL.annotate(f"{yi:.0f}", (xi, yi), textcoords="offset points", xytext=(0, 7),
                 ha="center", fontsize=8, color="#04c")

# Right: real_data curve.
axR.plot(x, real, "-o", color="#0a7", lw=2, label="trained policy (real_data val)")
axR.axhline(ff_real, color="#888", ls="--", lw=1.2, label=f"FixedFee(0.003)  ({ff_real:.2f})")

# Shade the "actively harmful" region (below FixedFee).
ymin, ymax = min(min(real), ff_real) - 0.5, max(max(real), ff_real) + 0.7
axR.fill_between(
    [x[0] - 0.5, x[-1] + 0.5],
    ymin,
    ff_real,
    color="#c40",
    alpha=0.07,
)
axR.text(
    x[0] - 0.4,
    (ymin + ff_real) / 2,
    "trained policy worse than FixedFee\n(harmful OOD)",
    fontsize=8,
    color="#a30",
    ha="left",
    va="center",
)
axR.set_ylim(ymin, ymax)
axR.set_xlim(x[0] - 0.5, x[-1] + 0.5)
axR.set_xticks(x)
axR.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
axR.set_ylabel("score (val seeds 1000-1127)")
axR.set_title("Real-data eval (OOD) — generalization curve")
axR.legend(loc="lower right", fontsize=9)
axR.grid(alpha=0.3)
for xi, yi in zip(x, real):
    axR.annotate(f"{yi:+.2f}", (xi, yi), textcoords="offset points", xytext=(0, 7),
                 ha="center", fontsize=8, color="#0a7")

fig.suptitle(
    "M3 cycle-1 — chronological M2 anchors evaluated on challenge (left) and real-data (right)",
    fontsize=11,
)
fig.tight_layout()
out = OUTDIR / "m3_dualcurve.png"
fig.savefig(out, dpi=140)
print(f"wrote {out}")
