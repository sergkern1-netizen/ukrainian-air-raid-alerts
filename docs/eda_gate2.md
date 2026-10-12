# Gate 2 EDA: daily national alert counts

Reproduce with `python scripts/eda_daily.py` (needs `data/raw/` from
`scripts/inspect_vadimkin.py`). Counts are alerts per UTC day, all regions, oblast-level rows
only so both sources use the same resolution. The exact-duplicate ingest rule is applied.

## Results

| | Official (oblast rows) | Volunteer |
|---|---|---|
| Days covered | 1,636 (2022-03-15 .. 2026-09-05) | 1,690 (2022-02-25 .. 2026-10-11) |
| Mean alerts/day | 39.9 | 68.6 |
| Variance / mean | 19.1 | 14.3 |
| Zero-alert days | 5.4% | 0.0% |
| ADF on levels (p) | 0.35 (unit root not rejected) | 0.74 (unit root not rejected) |
| ADF on first difference (p) | not run | 3.7e-28 (stationary) |
| ACF lag 1 / lag 7 | 0.61 / 0.60 | 0.62 / 0.57 |
| Ljung-Box (lags 7, 14, 30) | all p < 0.001 | all p < 0.001 |
| Mean before / from Dec 2025 | 47.8 / 1.7 | 59.5 / 108.6 |

Volunteer quarterly means rise from about 40 (2022 Q4) to 145 (2026 Q4, partial).

## Findings

1. **Overdispersed counts: Poisson is ruled out.** Variance is 14 to 19 times the mean. Use a
   negative binomial or a model with explicit variance.
2. **The series is not stationary in levels, but its first difference is.** The ADF test on
   levels does not reject a unit root (p 0.74), while the first difference is stationary by a
   wide margin. The series is I(1). Trend-stationarity is borderline (p 0.09), so a fixed
   linear trend is not a safe fix.
3. **Strong autocorrelation.** Lag-1 ACF is 0.62 and decays slowly. Ljung-Box rejects
   independence at every tested horizon. CLAUDE.md allows ARIMA/Prophet when autocorrelation
   is present, so ARIMA with d=1 is a candidate, alongside a negative-binomial model.
4. **The official oblast series breaks in December 2025.** After that date, the official
   feed reports mostly raion-level alerts (see `docs/data_inspection_gate1.md`). The
   oblast-only official series falls from 48 to 1.7 per day. It cannot be used as a
   continuous target across that date.
5. **The volunteer series roughly doubles over the period.** The mean rises from about 60 per
   day in 2025 to about 109 from December 2025 on. This could be real escalation, a change in
   reporting, or a change in the channel's coverage. It needs checking before modeling.

## Baselines and the CLAUDE.md success criterion

Last 365 days of volunteer data, one-step-ahead forecasts:

| Forecast | RMSE | MAE |
|---|---|---|
| Naive (yesterday) | 26.5 | 19.7 |
| 7-day mean | 23.9 | 17.9 |
| 28-day mean | 23.3 | 17.3 |

Mean daily count in that window: 104.5. Poisson noise alone gives an RMSE floor of √104.5 ≈ 10.2,
and the real series is overdispersed, so the floor is higher.

**The CLAUDE.md target (RMSE < 5 alerts/day) is below the noise floor for daily national
counts.** No model can meet it at this granularity. This is a decision for you, because
CLAUDE.md says success thresholds are yours to set.

## Decisions needed

1. **Success metric.** Options:
   - Keep daily national RMSE but accept it will not meet 5, and report the baseline ratio.
   - Change the target granularity, for example weekly totals or per-oblast counts, and
     re-derive the threshold from the baseline.
   - Replace point-error thresholds with probabilistic checks, such as coverage of
     negative-binomial prediction intervals.
2. **Target series.** Still open from Gate 1: official (broken at Dec 2025 at oblast level),
   volunteer (consistent, but its rise needs explaining), or a combined series.
3. **Volunteer level change.** Investigate whether the late-2025 rise is real or reporting
   before using it as the target.

## Not done yet

- ARIMA and negative-binomial candidates are not fitted. Gate 3 needs them with rolling-origin
  backtests against the baselines above.
- Per-oblast EDA is not done.
