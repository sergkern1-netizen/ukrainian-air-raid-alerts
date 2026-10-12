# Gate 2 decisions: deliberation and binding rulings

Context: `docs/eda_gate2.md`. This records the simulated deliberation between an Optimist,
a Critic and an executive Orchestrator, and the rulings that follow from it.

## Optimist

Baselines already exist, so there is no reason to stall. The volunteer series is consistent
in resolution, and the investigation can run in parallel with the first models rather than
in front of them. Weekly aggregation removes most daily noise. The 28-day-mean baseline is
already 6.4% weekly WAPE, so the first model that beats it proves the pipeline works. Start
with a negative-binomial regression and an ARIMA(d=1) on weekly totals and iterate.

## Critic

1. **The volunteer series is one Telegram channel.** Nothing shows its coverage is stable. A
   2x rise could be real escalation, a new subscriber base, or a change in reporting. A stable
   `naive` share argues against a change in method, but does not prove constant coverage.
2. **The regional shift is not neutral.** Donetsk loses 5 points and Kharkiv gains 3.5, which
   fits front-line movement. But the region count drops from 25 to 24, and the missing region
   is not identified.
3. **Official and volunteer disagree on level.** Official oblast counts average 47.8 per day
   before December 2025, against 59.5 for volunteer. The official file is not a complete
   record of the same events, so it cannot validate the volunteer series in absolute terms.
4. **The post-break window is short.** About 290 days (41 weeks) since December 2025, too few
   for a regime model to be trusted without caveats.
5. **The NB 95% interval under-covers** at 92.3%. Tails are too thin, which understates risk on
   the days that matter most.
6. **A weekly metric hides daily risk.** Weekly WAPE can look good while single days are badly
   off.

## Orchestrator rulings

**R1. Metric (binding for Gate 3 engineering).** The point-error target is retired and replaced
with three measures, all computed on rolling-origin backtests with 52 weekly origins:

- **Primary: weekly WAPE.** The 28-day-mean baseline is **6.4%**. A candidate must beat it on
  the same backtest, with a Diebold–Mariano test at p < 0.05.
- **Secondary: daily WAPE.** Baseline **16.5%**. A candidate must not be worse than baseline
  on daily error.
- **Probabilistic: interval coverage.** The 80% and 95% prediction intervals must cover 77–83%
  and 93–97% of observations. Current baselines give 79.2% and 92.3%, so the 95% interval fails
  and must be recalibrated.

**R2. Target series (provisional, pending sign-off).** The volunteer series, aggregated to
weekly national totals at oblast level, is the Gate 3 target. The official series is a
cross-check before December 2025 only. A coverage indicator is a covariate from day one.

**R3. Volunteer investigation before modeling: yes, time-boxed to one day, not blocking.**

- The `naive` share stays within 3 points of its 2023–2025 level. Passed: 6.1%, 5.6%, 5.8%,
  then 4.7% in 2026.
- The regional mix change is consistent with front-line movement, and the 25 → 24 region drop
  is explained. Partially checked.
- Official–volunteer overlap within 5 minutes is similar before and after December 2025, within
  10 points. Not yet computed.

If the overlap check fails, the target is frozen and the source is audited before modeling.

**R4. Scope.** Weekly modeling does not support daily alerting. Daily alerting would be a
separate gate with its own metric.

## Pivot triggers

- **T1.** If no candidate beats the 6.4% weekly baseline on the 52-origin backtest, ship the
  baseline and stop model work.
- **T2.** If 95% interval coverage stays outside 93–97% for 26 consecutive weeks, switch to
  empirical quantiles of recent residuals.
- **T3.** If a structural-break test rejects a stable mean at p < 0.01 after the pre-December-2025
  period, retrain on post-break data only. If fewer than 52 weeks of post-break data exist, use
  the baseline.
- **T4.** If the R3 overlap check differs by more than 10 points across the break, pause modeling
  and audit the volunteer source.
- **T5.** If no candidate passes T1 by the end of the Gate 3 window, the baseline is the Gate 3
  deliverable.

## Gate 3 plan

1. Day 1: R3 checks, including the overlap computation and the missing-region check.
2. Days 2–3: weekly dataset and a rolling-origin backtest harness reporting baseline and
   candidate metrics side by side.
3. Days 4–6: negative-binomial regression (lagged weekly counts, 4-week mean, coverage
   indicator) and ARIMA(·,1,·) on log1p weekly totals. Compare to baseline with DM tests and
   check interval coverage.
4. Day 7: apply pivot triggers, record the decision in `docs/gate3_results.md`.

## Project owner rulings (received)

1. **Alert types.** Yellow alerts, drone threats and red alerts are to be included in the target,
   documented as a regime change in threat classification. **Not implementable from the Vadimkin
   files**, which have no alert-type field. Recorded as a limitation in `docs/gate3_results.md`.
2. **Feeds.** No UkraineAlarm or alerts.in.ua credentials. Use the existing sources. Official
   raion rows are rolled up to oblast as a cross-check.
3. **Target.** The volunteer series is the primary modeling target, with its caveats (western
   over-reporting, recent threat-level changes). This overrides trigger T4 in
   `docs/gate3_day1_findings.md`; the override is documented in `docs/gate3_results.md`.
4. **Reporting.** `docs/gate3_results.md` must document source choice, feed comparison and
   validation, reliability methods and all limitations.

**Formal approval (received):** the R1 metrics replace the RMSE < 5 criterion under CLAUDE.md, and
the trailing four-week mean baseline is accepted as the Gate 3 deliverable under trigger T1.

## Sign-off required (CLAUDE.md)

- Replacing the RMSE < 5 threshold with R1 metrics changes a success criterion. Pending the
  project owner's approval.
- R2 depends on a single volunteer channel. Other sources for the same events are being
  checked before the target is fixed.
