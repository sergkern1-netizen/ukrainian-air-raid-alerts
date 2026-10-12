# Gate 3 results: weekly alert forecasting

Reproduce: `python scripts/gate3_backtest.py` (needs `data/raw/` from
`scripts/inspect_vadimkin.py`). Output: `output/gate3_backtest.json`.
Rulings: `docs/gate2_decisions.md`. Day 1 checks: `docs/gate3_day1_findings.md`.

## Decision

**Trigger T1 fired: no candidate beats the trailing four-week baseline.** Under T1 and T5 the
baseline is the Gate 3 deliverable, and model work stops here.

**Approved by the project owner:** the R1 metrics replace the RMSE < 5 criterion under CLAUDE.md,
and the trailing four-week mean is accepted as the Gate 3 deliverable under T1.

| Model | Weekly WAPE | Daily WAPE | DM vs baseline (p) | 80% coverage | 95% coverage |
|---|---|---|---|---|---|
| **Baseline: trailing 4-week mean** | **8.52%** | **16.58%** | — | n/a | n/a |
| Negative binomial (lag-1, 4-week mean, regime) | 12.40% | 19.65% | worse (p = 0.027) | 88.5% | 94.2% |
| ARIMA(1,1,0) on log1p weekly | 8.55% | 16.96% | no difference (p = 0.97) | 94.2% | 100% |

Target bands from docs/gate2_decisions.md R1: coverage 77–83% (80%) and 93–97% (95%). Neither
ARIMA interval is inside its band. The NB 80% interval is too wide, and its 95% interval is
inside the band.

Diagnostic (not a pre-specified candidate): NB without the regime term gives 11.96% weekly WAPE,
still worse than baseline (p = 0.050). The regime term is not what makes the NB model worse.

## Sensitivity: shorter backtest windows

Run with `python scripts/gate3_backtest.py --origins N`. Same models, same data, same metrics. The
windows are nested (the last 13 origins lie inside the last 26, which lie inside the last 52), so
they are not independent confirmations.

| Origins | Baseline weekly WAPE | Baseline daily WAPE | NB weekly WAPE (DM p) | ARIMA weekly WAPE (DM p) | NB coverage 80/95 | ARIMA coverage 80/95 |
|---|---|---|---|---|---|---|
| 52 | 8.52% | 16.58% | 12.40% (0.027, worse) | 8.55% (0.97) | 88.5 / 94.2 | 94.2 / 100 |
| 26 | 7.77% | 15.45% | 14.13% (0.026, worse) | 8.58% (0.46) | 84.6 / 92.3 | 92.3 / 100 |
| 13 | 7.46% | 12.55% | 14.90% (0.118, worse) | 8.01% (0.74) | 84.6 / 92.3 | 92.3 / 100 |

Reading: the ranking is stable. The baseline has the lowest weekly and daily WAPE in every window.
The negative-binomial model is worse in all three windows, and significantly so at 52 and 26
origins. ARIMA is never significantly different from the baseline, and its point WAPE is slightly
higher in every window. Neither model beats the baseline in any window, so T1 holds.

Limits of the sensitivity check: 13 origins give very little power, and the p-values at that
size should not be read as evidence of no difference. Interval coverage misses its R1 bands in
every window. The ARIMA 95% interval covers 100% of actuals, which means it is too wide.

## Corrections to earlier figures

- **The 6.4% weekly baseline in docs/gate2_decisions.md is withdrawn.** It used the rolling mean
  computed at the end of each week, which already contains that week's counts, so it was
  leaky. The corrected trailing four-week baseline is **8.52%**. The R1 targets should be read
  against this figure.
- **The 26.5 / 23.3 RMSE figures in docs/eda_gate2.md are daily-scale and are unaffected.**
- **An earlier post-break correlation of 0.28 (raised in the working analysis, not in a saved
  file)** counted multi-level rows as separate alerts. Counted per (oblast, start time), the post-break
  correlation is 0.85 (table below).

## Target and sources

**Target:** volunteer feed, oblast-level rows, Monday-start weeks, partial first and last weeks
dropped. 240 weeks from 2022-02-28 to 2026-09-28, after the exact-duplicate ingest rule.
Backtest: 52 one-week-ahead origins, refit on all earlier weeks at each origin.

**Why these sources:**

- **Volunteer (`volunteer_data_en.csv`) is the primary target.** It is the only feed that
  continues after 2026-09-07. It is oblast-level throughout, so its resolution does not change.
  The repository's root LICENSE is MIT (checked 2026-10-12). Whether that licence covers the data
  files was not confirmed: `datasets/README.md` returned HTTP 503 when checked. It was accepted as
  the target by the project owner, with its caveats.
- **Official (`official_data_en.csv`) is the cross-check.** It is the official record, but it
  ends on 2026-09-07 (the official Telegram feed ended the same day) and changes to raion level
  in December 2025.
- **Not used as data:** GitHub projects that build on the same files (not independent),
  UkraineAlarm and alerts.in.ua (no credentials available, per the project owner's ruling).

## How the feeds were compared and validated

1. **Ingest rule.** Exact duplicates removed from the official file (113,845 rows, every one a
   pair). No duplicates in the volunteer file.
2. **Naive end times.** 5.0% of volunteer rows have an inferred end time. The share is stable by
   year (2023–2025: 5.6–6.1%; 2026: 4.7%), so the reporting method did not change at the break.
   End times do not affect weekly counts.
3. **Regional mix.** Shifts across the break fit front-line movement (Donetsk −5.2 points,
   Kharkiv +3.5). Luhanska oblast disappears after 2022-04-04, which matches the README's note
   about a permanent siren not in the data.
4. **Event-level overlap.** Volunteer alerts matched to any official alert in the same oblast
   within 5 minutes: 69.0% before December 2025, 52.7% after, over the period when both feeds
   overlap (to 2026-09-07). The 16-point drop is widespread (21 of 24 oblasts with at least 50
   alerts in both periods) and largest in the west (Lviv 74% → 10%, Volyn 68% → 11%).
   *Correction (2026-10-12):* the original figures, 44.8% after and a 24-point drop, counted
   volunteer alerts after the official feed ended (2026-09-07) as unmatched, which biased the
   post-break rate low. Western figures in the original (Lviv 74% → 8%, Volyn 68% → 9%) also
   included those months. Source: `scripts/feed_integrity.py`, `docs/analysis/feed_integrity.md`.
5. **Weekly agreement (counted per distinct oblast and start time):**

   | Period | Weeks | Correlation | Volunteer ÷ official |
   |---|---|---|---|
   | Before Dec 2025 | 193 | 0.72 | 0.84 |
   | From Dec 2025 | 40 | 0.85 | 0.50 |
   | All | 233 | 0.90 | 0.71 |

   The post-break ratio of 0.50 is not a level validation. From December 2025 the official
   roll-up counts raion events, and one oblast alert can now be several raion events. The
   correlation is the more informative figure, and it is higher after the break.

**Interpretation.** Both feeds track the same events in time. Their levels differ in a way that
grows in the west. Without an independent source of ground truth, the data cannot say which
feed is more accurate. This is why the target carries a documented western over-reporting caveat.

## Reliability methods

- Rolling-origin backtest: 52 one-week-ahead origins; each model refit using only earlier weeks.
- The regime indicator (1 from 2025-12-01) is known in advance, so using it inside a model is not
  leakage. The break date itself was chosen after inspecting the full series, so the choice of
  date is a judgement made with hindsight, not a leakage-free out-of-sample choice.
- Primary metric WAPE on weekly totals; secondary daily WAPE with each weekly forecast spread
  evenly over seven days (the least favourable assumption for weekly models).
- Diebold–Mariano test on absolute loss against the baseline (one-step horizon, so no HAC
  correction). A constant loss difference is returned as an infinite statistic, not as zero.
- Negative-binomial fits converged on all 52 origins (`nb_fits_not_converged = 0`), after
  scaling the regressors.
- Prediction intervals checked against actuals (coverage), not assumed.

## Data verification (owner's request)

- **Stall check.** The owner reported that collection stalled and left the last year incomplete.
  The files do not show this. The volunteer feed has no gap of three or more days in its full
  history, and every calendar month from September 2025 to October 2026 is present (October is
  partial by design). The incomplete period is the official feed, which ends on 2026-09-07. That
  matches the end of the official Telegram feed, not a stall in volunteer collection.
- **Cross-verification source.** A search of GitHub for Karpathy repositories on air-raid alerts,
  Ukraine or alert data found none. His public repositories are machine-learning and educational
  projects. No Karpathy-attributed alert dataset exists, so none is used. If a specific repository
  or URL was intended, it has not been provided.

## Known limitations

1. **Alert types cannot be separated.** The Vadimkin files contain no alert-type field, so yellow
   alerts, red alerts and drone threats cannot be included or excluded as separate categories.
   The project owner's ruling to include them is recorded, but these files cannot implement it.
   The statement that these categories raise recent counts is not verified from the data. It
   would need a dated source that records types. The break in the series cannot be attributed to
   a threat-classification change.
2. **One volunteer channel.** The feed is manually posted by about 30 volunteers, so coverage
   depends on staffing. The channel publishes alert types beyond those in the dataset.
3. **No ground truth.** Neither feed can be verified against an independent record. The western
   over-reporting is documented, not corrected.
4. **Short post-break window.** 40 weeks since December 2025. Regime-specific claims rest on
   little data.
5. **Weak statistical power.** 52 origins. The NB–baseline gap (p = 0.027) is the only
   significant difference, and it favours the baseline.
6. **Weekly granularity.** Weekly totals do not support daily alerting. The daily metric uses a
   flat weekly-to-daily split.
7. **Inferred end times** (5%) affect durations only.
8. **Single-channel dependency.** The target's accuracy depends on one volunteer channel and its
   sources, which include the Air Force channel. The two feeds are therefore not independent.
9. **R1 approval.** The project owner asked for the Gate 3 pipeline to proceed, which this treats
   as approval of the R1 metrics. This is stated here so it can be overruled.

## Next steps (for the project owner)

- If Gate 3 is to continue, an independent ground-truth source is needed to resolve the western
  over-reporting. Options are UkraineAlarm or alerts.in.ua, both of which need credentials, or a
  dated sample of events verified by hand.
- A dated alert-type source would be needed before the yellow/red/drone-threat ruling can be
  applied.
- Until then, the baseline is the deliverable. Its forecasts are reproducible from the script.
