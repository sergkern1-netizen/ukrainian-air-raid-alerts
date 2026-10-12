"""
Rolling-origin backtest for weekly alert totals (Gate 3, docs/gate2_decisions.md R1).

Each origin refits on data strictly before the forecast week, so no future values leak in.
Forecasts are one week ahead. Metrics: weekly WAPE (primary), daily WAPE (secondary),
interval coverage at 80% and 95%, and a Diebold–Mariano test against the baseline.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA

logger = logging.getLogger(__name__)

ORIGINS = 52
LEVELS = (0.80, 0.95)


@dataclass
class Forecast:
    """One model's one-week-ahead forecasts over the backtest origins."""

    name: str
    mean: List[float] = field(default_factory=list)
    intervals: Dict[float, List[tuple]] = field(default_factory=dict)


def _nb_intervals(mu: float, alpha: float, level: float) -> tuple:
    """Central NB2 prediction interval for mean mu and dispersion alpha (var = mu + alpha mu^2)."""
    n = 1.0 / alpha
    p = n / (n + mu)
    lo, hi = stats.nbinom.ppf([(1 - level) / 2, (1 + level) / 2], n, p)
    return float(lo), float(hi)


def baseline_trailing_mean(y: pd.Series, t: int, window: int = 4) -> float:
    """Mean of the `window` weeks before week t."""
    return float(y.iloc[t - window : t].mean())


def nb_forecast(y: pd.Series, regime: pd.Series, t: int) -> tuple:
    """
    Negative-binomial regression on lag-1, 4-week mean and regime, fitted on weeks < t.

    Regressors are scaled by the training mean so the optimiser sees values near 1.

    Returns:
        (predicted mean, dispersion alpha, converged flag).
    """
    frame = pd.DataFrame({"y": y, "regime": regime})
    frame["lag1"] = y.shift(1)
    frame["mean4"] = y.shift(1).rolling(4).mean()
    frame = frame.dropna().iloc[: t - 4]
    scale = max(float(frame["y"].mean()), 1.0)

    # The regime column is constant until December 2025; including it then makes X singular
    cols = ["lag1", "mean4"] + (["regime"] if frame["regime"].nunique() > 1 else [])
    X = sm.add_constant(
        frame[cols].assign(lag1=frame["lag1"] / scale, mean4=frame["mean4"] / scale),
        has_constant="add",
    )
    with np.errstate(all="ignore"):
        fit = sm.NegativeBinomial(frame["y"], X).fit(disp=0, maxiter=500, method="bfgs")

    x_next = {
        "const": 1.0,
        "lag1": y.iloc[t - 1] / scale,
        "mean4": y.iloc[t - 4 : t].mean() / scale,
    }
    if "regime" in cols:
        x_next["regime"] = regime.iloc[t]
    mu = float(fit.predict(pd.DataFrame([x_next])[X.columns])[0])
    alpha = float(fit.params["alpha"])
    converged = bool(fit.mle_retvals.get("converged", False))
    return mu, alpha, converged


def arima_forecast(y: pd.Series, t: int) -> tuple:
    """ARIMA(1,1,0) on log1p weekly totals, fitted on weeks < t. Returns log-scale mean and fit."""
    log_y = np.log1p(y.iloc[:t].astype(float).values)
    fit = ARIMA(log_y, order=(1, 1, 0)).fit()
    fc = fit.get_forecast(steps=1)
    mean_log = float(fc.predicted_mean[0])
    intervals = {}
    for level in LEVELS:
        ci = fc.conf_int(alpha=1 - level)[0]
        intervals[level] = (max(float(np.expm1(ci[0])), 0.0), float(np.expm1(ci[1])))
    return float(np.expm1(mean_log)), intervals


def run_backtest(weekly: pd.DataFrame, origins: int = ORIGINS) -> Dict[str, Forecast]:
    """
    Run all models over the last `origins` weeks.

    Args:
        weekly: Output of weekly_totals(): columns `alerts`, `regime`.

    Returns:
        Dict of model name -> Forecast, plus the actuals under key 'actual'.
    """
    y = weekly["alerts"].astype(float)
    regime = weekly["regime"].astype(int)
    n = len(y)
    first = n - origins
    origin_range = range(first, n)

    base = Forecast("baseline_trailing4")
    nb = Forecast("negative_binomial")
    arima = Forecast("arima_110_log1p")
    nb.intervals = {level: [] for level in LEVELS}
    arima.intervals = {level: [] for level in LEVELS}

    nb_nonconverged = 0
    for t in origin_range:
        base.mean.append(baseline_trailing_mean(y, t))

        mu, alpha, converged = nb_forecast(y, regime, t)
        nb_nonconverged += 0 if converged else 1
        nb.mean.append(mu)
        for level in LEVELS:
            nb.intervals[level].append(_nb_intervals(mu, alpha, level))

        mean_a, intervals_a = arima_forecast(y, t)
        arima.mean.append(mean_a)
        for level in LEVELS:
            arima.intervals[level].append(intervals_a[level])

    actual = y.iloc[first:].values
    logger.info(f"backtest: {origins} origins, {n} weeks of history")
    return {
        "actual": actual,
        "weeks": weekly.index[first:],
        "nb_nonconverged": nb_nonconverged,
        "baseline": base,
        "nb": nb,
        "arima": arima,
    }


def wape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Weighted absolute percentage error: sum |e| / sum |actual|."""
    return float(np.abs(actual - forecast).sum() / np.abs(actual).sum())


def coverage(actual: np.ndarray, intervals: List[tuple]) -> float:
    """Share of actuals inside their prediction interval."""
    hits = [lo <= a <= hi for a, (lo, hi) in zip(actual, intervals)]
    return float(np.mean(hits))


def diebold_mariano(actual: np.ndarray, model: np.ndarray, baseline: np.ndarray) -> tuple:
    """
    Two-sided DM test on absolute loss, one-step-ahead (no HAC correction needed).

    Returns:
        (statistic, p-value). Positive statistic means the model has the lower loss.
    """
    d = np.abs(actual - baseline) - np.abs(actual - model)
    if np.all(d == 0):
        return 0.0, 1.0
    se = d.std(ddof=1) / np.sqrt(len(d))
    if se == 0:
        # Constant non-zero loss difference: one forecast is better in every period
        return float(np.sign(d.mean()) * np.inf), 0.0
    stat = float(d.mean() / se)
    p = float(2 * (1 - stats.norm.cdf(abs(stat))))
    return stat, p


def daily_wape(mean: np.ndarray, weeks: pd.DatetimeIndex, daily: pd.Series) -> float:
    """
    Daily WAPE with each weekly forecast spread evenly over its seven days.

    This is the least favourable assumption for weekly models: any day-of-week shape the
    models could learn is ignored. Compare candidates and the baseline on the same basis.
    """
    actual_days, pred_days = [], []
    for week_start, weekly_pred in zip(weeks, mean):
        days = pd.date_range(week_start, periods=7, freq="D", tz="UTC")
        actual_days.append(daily.reindex(days, fill_value=0).values)
        pred_days.append(np.full(7, weekly_pred / 7.0))
    return wape(np.concatenate(actual_days), np.concatenate(pred_days))


def summarize(
    results: Dict[str, Forecast], weeks: pd.DatetimeIndex, daily: Optional[pd.Series] = None
) -> Dict[str, dict]:
    """Compute the R1 metrics for every model against the baseline."""
    actual = results["actual"]
    base_mean = np.array(results["baseline"].mean)
    summary = {}
    for key in ("baseline", "nb", "arima"):
        fc = results[key]
        mean = np.array(fc.mean)
        entry = {
            "weekly_wape": round(wape(actual, mean), 4),
            "weekly_mae": round(float(np.abs(actual - mean).mean()), 2),
        }
        if daily is not None:
            entry["daily_wape"] = round(daily_wape(mean, weeks, daily), 4)
        if key != "baseline":
            stat, p = diebold_mariano(actual, mean, base_mean)
            entry["dm_vs_baseline"] = {"stat": round(stat, 3), "p": round(p, 4)}
            entry["coverage"] = {
                f"{int(level * 100)}%": round(coverage(actual, fc.intervals[level]), 3)
                for level in LEVELS
            }
        summary[key] = entry
    return summary
