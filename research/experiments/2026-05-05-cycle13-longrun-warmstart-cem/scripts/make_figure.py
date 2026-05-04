"""
Cycle-13 figure: per-gen CEM trajectory of the long-run (gen=24)
warm-start, overlaid on cycle-11 d16_s2 (gen=12) so you can see
visually whether gens 12-23 add anything beyond the cycle-11 ceiling.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]

C13 = ROOT / "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/results/longrun_d16_s0_g24"
C11 = ROOT / "research/experiments/2026-05-04-cycle11-grid-cem/results/cell_d16_s2"
OUTDIR = ROOT / "research/experiments/2026-05-05-cycle13-longrun-warmstart-cem/figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

c13_history = json.loads((C13 / "history.json").read_text())["history"]
c13_result = json.loads((C13 / "result.json").read_text())
c11_history = json.loads((C11 / "history.json").read_text())["history"]
c11_result = json.loads((C11 / "result.json").read_text())

c13_gens = [h["generation"] for h in c13_history]
c13_best = [h["best_search_score"] for h in c13_history]
c13_elite = [h["elite_mean_search_score"] for h in c13_history]
c13_val = [h["fixed_val_score"] for h in c13_history]

c11_gens = [h["generation"] for h in c11_history]
c11_best = [h["best_search_score"] for h in c11_history]
c11_elite = [h["elite_mean_search_score"] for h in c11_history]
c11_val = [h["fixed_val_score"] for h in c11_history]

c13_test = c13_result["best_by_val"]["test_score"]
c11_test = c11_result["best_by_val"]["test_score"]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.6))

# Left: overlay cycle-11 (gen 0-11) and cycle-13 (gen 0-23)
axL.plot(c13_gens, c13_val, "-o", label="cycle-13 val (gen=24)", color="#0a7", lw=2)
axL.plot(c11_gens, c11_val, "--s", label="cycle-11 d16_s2 val (gen=12)", color="#666", lw=1.4)
axL.axhline(c11_test, ls=":", color="#666", lw=1, label=f"c11 d16_s2 test ({c11_test:.2f})")
axL.axhline(c13_test, ls=":", color="#0a7", lw=1, label=f"c13 longrun test ({c13_test:.2f})")
axL.axhline(460.0, ls="-.", color="#c40", lw=1, alpha=0.7, label="recipe-ceiling threshold (460)")
axL.set_xlabel("CEM generation")
axL.set_ylabel("score (val seeds 1000-1127)")
axL.set_title("Per-gen val score: gen=24 warm-start vs cycle-11 (gen=12)")
axL.legend(loc="lower right", fontsize=8)
axL.grid(alpha=0.3)

# Right: best vs elite-mean within cycle 13 — does it keep climbing past gen 12?
axR.plot(c13_gens, c13_best, "-o", label="best", color="#04c", lw=2)
axR.plot(c13_gens, c13_elite, "--", label="elite mean", color="#04c", lw=1, alpha=0.6)
axR.axvline(11.5, ls=":", color="#666", alpha=0.5, label="cycle-11 stop point (gen=12)")
axR.set_xlabel("CEM generation")
axR.set_ylabel("score (search seeds 0-63)")
axR.set_title("Cycle-13 search-seed trajectory (gen 0-23)")
axR.legend(loc="lower right", fontsize=8)
axR.grid(alpha=0.3)

fig.suptitle(
    f"Cycle 13 — warm-start CEM gen=24 from c11 d16_s2 anchor "
    f"| Δ vs champion: {c13_test - c11_test:+.2f} pts",
    fontsize=11,
)
fig.tight_layout()
out = OUTDIR / "cycle13_summary.png"
fig.savefig(out, dpi=140)
print(f"wrote {out}")

# Also a short text summary
verdict = (
    "RECIPE_CEILING_CONFIRMED" if c13_test < 457
    else "MARGINAL_LIFT" if c13_test < 460
    else "RECIPE_CEILING_FALSIFIED"
)
print(
    f"cycle-13 longrun: test={c13_test:.3f} (champion {c11_test:.3f}, "
    f"Δ {c13_test - c11_test:+.3f}) | verdict: {verdict}"
)
