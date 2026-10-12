"""Tests for the Gate 3 weekly target and backtest metrics."""

import numpy as np
import pandas as pd

from src.forecasting.backtest import diebold_mariano, wape
from src.forecasting.weekly import REGIME_START, weekly_totals


def _alerts(starts: list) -> pd.DataFrame:
    return pd.DataFrame({"started_at": pd.to_datetime(starts, utc=True)})


def test_partial_first_and_last_weeks_are_dropped() -> None:
    # First record on Wed 2024-01-03, last on Wed 2024-01-24 (the week of 2024-01-22 is partial)
    df = _alerts(
        [
            "2024-01-03 10:00",
            "2024-01-08 10:00",
            "2024-01-09 10:00",
            "2024-01-15 09:00",
            "2024-01-16 09:00",
            "2024-01-24 08:00",
        ]
    )

    weekly = weekly_totals(df)

    assert weekly.index.min() == pd.Timestamp("2024-01-08", tz="UTC")
    assert weekly.index.max() == pd.Timestamp("2024-01-15", tz="UTC")
    assert weekly.alerts.tolist() == [2, 2]


def test_weeks_start_on_monday_and_counts_match() -> None:
    df = _alerts(["2024-01-08 00:00", "2024-01-14 23:00", "2024-01-15 01:00", "2024-01-22 12:00"])

    weekly = weekly_totals(df)

    assert all(ts.weekday() == 0 for ts in weekly.index)
    assert weekly.alerts.sum() == 3


def test_regime_flag_switches_in_december_2025() -> None:
    df = _alerts(["2025-11-24 10:00", "2025-12-01 10:00", "2025-12-08 10:00", "2025-12-15 10:00"])

    weekly = weekly_totals(df)

    assert weekly.loc[weekly.index < REGIME_START, "regime"].eq(0).all()
    assert weekly.loc[weekly.index >= REGIME_START, "regime"].eq(1).all()


def test_wape_is_sum_abs_error_over_sum_actual() -> None:
    actual = np.array([10.0, 20.0])
    forecast = np.array([12.0, 15.0])
    assert wape(actual, forecast) == (2 + 5) / 30


def test_diebold_mariano_positive_when_model_is_better() -> None:
    actual = np.array([10.0, 12.0, 11.0, 13.0, 10.0, 12.0])
    baseline = actual + np.array([3.0, -3.0, 3.0, -3.0, 3.0, -3.0])
    model = actual + 0.5
    stat, p = diebold_mariano(actual, model, baseline)
    assert stat > 0
    assert p < 0.05


def test_diebold_mariano_zero_for_identical_forecasts() -> None:
    actual = np.array([1.0, 2.0, 3.0])
    f = np.array([1.5, 2.5, 2.0])
    stat, p = diebold_mariano(actual, f, f)
    assert stat == 0.0
    assert p == 1.0
