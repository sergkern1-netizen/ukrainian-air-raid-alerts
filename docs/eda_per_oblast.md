# Per-oblast EDA: weekly volunteer counts

Reproduce: `python scripts/eda_per_oblast.py` (needs `data/raw/`). Window: last 52 complete weeks,
ending 2026-09-28. Source: volunteer feed, after the exact-duplicate ingest rule.

## Result

| Regime | Rule (mean alerts per week, last 52 weeks) | Oblasts |
|---|---|---|
| Dense | ≥ 5 | 19 (Kharkiv 97.8 down to Rivne 5.8) |
| Sparse | 0.5 to < 5 | 5: Khmelnytska 4.4, Chernivetska 3.0, Ternopilska 2.5, Ivano-Frankivska 2.3, Zakarpatska 1.9 |
| Silent | < 0.5 | Luhanska (0.0; no alerts after 4 April 2022) |

Sparse oblasts have 10–39% zero weeks in the last 52 weeks (Zakarpatska 38.5%, Ivano-Frankivska,
Chernivetska 19.2% each, Ternopilska 17.3%, Khmelnytska 9.6%). Dense oblasts have 0% zero weeks
except Rivne (5.8%) and Vinnytsia (3.8%) in the window, which sit at the threshold.

Dispersion (variance / mean) is 0.8 to 15.1. Kyivska (15.1) and Odeska (9.8) are the most
overdispersed dense oblasts. Lag-1 autocorrelation is 0.04 to 0.80 for dense oblasts, and the
sparse oblasts are weaker (0.10 to 0.29).

## What this means for the critique

- The sparsity concern applies to five western oblasts with about two alerts per week. It does
  not apply to the national series, which has 0% zero weeks (see `docs/eda_gate2.md`).
- For those five, weekly counts are close to the range where a zero-inflated model would be
  needed. The current negative-binomial model is not designed for that.
- The volunteer-versus-official overlap fell most in Lviv and Volyn (`docs/gate3_results.md`).
  Those oblasts have low counts, so overlap ratios there are noisy, and the drop should not be
  read as precise.

## Decision

No per-oblast model has been built, and none is needed for the approved national weekly
target. If per-oblast forecasts are wanted later, the dense oblasts can use the same backtest
harness, and the five sparse oblasts need a zero-inflated model or aggregation to a
macro-region. That would be a new gate with its own metric, not part of the current pipeline.
