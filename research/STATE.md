# State — current cycle

**Last updated**: 2026-05-03 (cycle 4)

## Active milestone

**M1 — Validate realistic simulator against on-chain markout.** Cycle 4
unblocked the router-filtered pull and falsified the cycle-3 hypothesis.
M1 has a much sharper conclusion now; ready to declare done in cycle 5
after one short cleanup, then start M2.

## Current sub-task

Cycle 4 finished:
- BQ MCP back online. Found the obvious efficiency win: `markout_prod`
  has `transaction_to_address` directly — no need for the
  `dex_trades` JOIN that cycle-3 SQL templated. Direct
  `LOWER(transaction_to_address) IN UNNEST(router_list)` brings each
  canonical-pool day under the 1 GB ceiling.
- Pulled per-day router/non-router/all means for 5 days
  (`research/experiments/2026-05-03-cycle4-router-confirmed/results/multi_day_breakdown.json`).
- Pulled 100-bucket APPROX_QUANTILES for the canonical day (4-27),
  router and non-router (`results/router_quantiles_2026-04-27.json`).
- Built two figures: CDF overlay
  (`figures/router_cdf_overlay.png`) and per-day means
  (`figures/per_day_means.png`).
- Updated `presentation/index.html` with the cycle-4 section.
- The cycle-3 SQL template at
  `research/experiments/2026-05-01-cycle3-router-replicate-stitch/scripts/router_filtered_quantiles.sql`
  is now superseded; cycle 5 should retire / mark it obsolete.

**Headline finding**: routers carry MORE adverse selection on-chain, not
less. 5-day weighted router mean = +0.82 bps (vs sim +5.79 bps); the
gap is ~5 bps, not ~2.7 bps as cycle 2 reported. The simulator's retail
impact distribution captures price-impact magnitude but is missing
informedness (correlation between trade direction and short-term
Binance drift) on aggregator flow.

## Hypothesis going into cycle 5

The M1 calibration story is now clean enough to publish: shape match,
~5 bps mean over-credit on router flow, cause = missing informedness.
We *could* prototype a calibration extension (add a learned
direction × tape correlation to retail draws), but it's not on the
critical path for the M2-M4 milestones. Recommendation: declare M1
done after one cleanup cycle (retire the obsolete cycle-3 SQL,
update `research/notes/data_sources.md` with the
`transaction_to_address` lesson), and start M2 in cycle 6.

## Next action (cycle 5)

1. **Cleanup pass** (~10% of cycle):
   - Retire the obsolete cycle-3 SQL template (move to a `_obsolete/`
     subdir or rewrite as the new direct-filter form).
   - Update `research/notes/data_sources.md` with the
     `transaction_to_address` lesson and the cycle-4 budget pattern.
2. **Start M2 setup** (~80% of cycle):
   - Read `arena_search/simple_amm_search.py` and the `arena_policies/`
     directory in detail. List the policy families and the existing
     baselines' challenge scores.
   - Find the AMM-challenge scoring rule (per the milestones, the
     target is >540) — should be in `arena_eval/exact_simple_amm/`
     or `scripts/run_exact_search.py`. Document it in
     `research/notes/scoring_rule.md`.
   - Run one baseline policy through the search to record an inherited
     score. This is cycle-5's "starting line" for M2.
3. **Optional cycle 5+ side-track**: prototype the sim's retail
   informedness extension. Measure whether adding a small
   `direction × forward-Binance-return` correlation closes the
   router-mean gap. If so, ship it as an M1 calibration PR — if not,
   abandon and document the residual.

## Blockers for user

None. Push topology unchanged: sandbox commits to local main; host
launchd agent ships to origin every 15 min.

## Operational notes

- Repo path on this machine: `/sessions/clever-ecstatic-tesla/mnt/amm-gym-auto-research`
  (changed from cycle 2's `bold-eloquent-babbage`; always confirm with
  `pwd` and `git remote -v`).
- BQ-MCP was responsive this cycle (cycle 3 had it down all cycle).
  Tool state is volatile across cycles; never plan on it being up
  unless you've just tested it.
- `pyarrow` was installed into `.venv` again this cycle — the install
  doesn't survive across mounts. If we keep needing it in figure-build
  scripts, add to `requirements.txt` for consistency.
- Cycle 4 left the inherited working-tree changes from earlier cycles
  (`arena_eval/`, `arena_policies/`, etc., plus untracked
  `oracle.py`, `retail_recapture.py`, calibration scripts) untouched,
  per the cycle-1 / cycle-2 / cycle-3 convention.
