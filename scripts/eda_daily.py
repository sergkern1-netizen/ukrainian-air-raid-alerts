"""
Gate 2 EDA on daily alert counts (CLAUDE.md: sparsity, ADF, ACF/PACF, model rationale).

    python scripts/eda_daily.py

Runs on the Vadimkin files in data/raw/ (see scripts/inspect_vadimkin.py) with the
exact-duplicate ingest rule applied. Counts are alerts per UTC day, national total,
oblast-level rows only so the resolution is the same for both sources.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf, adfuller, pacf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ingestion.alert_dedupe import drop_exact_duplicates  # noqa: E402

RAW = ROOT / "data" / "raw"
LAGS = 30
SPLIT = pd.Timestamp("2025-12-01", tz="UTC")


def daily_counts(df: pd.DataFrame, name: str) -> pd.Series:
    """Alerts per UTC day across all regions, with zero-filled gaps."""
    days = df.started_at.dt.floor("D")
    counts = days.value_counts().sort_index()
    full = pd.date_range(counts.index.min(), counts.index.max(), freq="D", tz="UTC")
    return counts.reindex(full, fill_value=0).rename(name)


def describe(series: pd.Series, label: str) -> None:
    """Print sparsity, dispersion, stationarity and autocorrelation diagnostics."""
    x = series.astype(float)
    print(f"\n== {label}: {len(x):,} days, {x.index[0].date()} .. {x.index[-1].date()}")
    print(
        f"mean={x.mean():.2f}  var={x.var():.2f}  var/mean={x.var() / x.mean():.2f}  "
        f"zero-days={(x == 0).mean():.1%}  max={int(x.max())}"
    )

    adf_stat, adf_p, *_ = adfuller(x, autolag="AIC")
    print(
        f"ADF (full): stat={adf_stat:.2f} p={adf_p:.4f}  "
        f"-> {'stationary' if adf_p < 0.05 else 'unit root not rejected'}"
    )

    acf_vals = acf(x, nlags=LAGS, fft=True)
    pacf_vals = pacf(x, nlags=LAGS, method="ywm")
    band = 1.96 / np.sqrt(len(x))
    sig_acf = [k for k in range(1, LAGS + 1) if abs(acf_vals[k]) > band]
    sig_pacf = [k for k in range(1, LAGS + 1) if abs(pacf_vals[k]) > band]
    print(
        f"ACF lag1={acf_vals[1]:.3f} lag7={acf_vals[7]:.3f}  significant lags (1..{LAGS}): "
        f"{sig_acf[:12]}{'...' if len(sig_acf) > 12 else ''}"
    )
    print(
        f"PACF lag1={pacf_vals[1]:.3f} lag7={pacf_vals[7]:.3f}  significant lags: "
        f"{sig_pacf[:12]}{'...' if len(sig_pacf) > 12 else ''}"
    )

    lb = acorr_ljungbox(x, lags=[7, 14, 30], return_df=True)
    print("Ljung-Box p-values (lags 7/14/30):", lb.lb_pvalue.round(4).tolist())

    for period, part in [
        ("before Dec 2025", x[x.index < SPLIT]),
        ("from Dec 2025", x[x.index >= SPLIT]),
    ]:
        if len(part):
            print(f"  {period}: mean={part.mean():.2f} zero-days={(part == 0).mean():.1%}")


def baselines(series: pd.Series, window: int = 365) -> None:
    """1-step-ahead RMSE/MAE of simple forecasts over the last `window` days."""
    x = series.astype(float)
    actual = x.iloc[-window:]
    forecasts = {
        "naive (yesterday)": x.shift(1),
        "7-day mean": x.shift(1).rolling(7).mean(),
        "28-day mean": x.shift(1).rolling(28).mean(),
    }
    print(f"\n== baselines, last {window} days, 1-step-ahead")
    for name, pred in forecasts.items():
        error = actual - pred.iloc[-window:]
        print(f"  {name:<18} RMSE={np.sqrt((error ** 2).mean()):.2f}  MAE={error.abs().mean():.2f}")
    print(f"  mean={actual.mean():.1f}  poisson floor sqrt(mean)={np.sqrt(actual.mean()):.1f}")


def main() -> int:
    official_raw = pd.read_csv(
        RAW / "official_data_en.csv", parse_dates=["started_at", "finished_at"]
    )
    volunteer = pd.read_csv(
        RAW / "volunteer_data_en.csv", parse_dates=["started_at", "finished_at"]
    )

    official, dropped = drop_exact_duplicates(official_raw, "official")
    official_oblast = official[official.level == "oblast"]
    volunteer_clean, _ = drop_exact_duplicates(volunteer, "volunteer")

    describe(daily_counts(official_oblast, "official_oblast"), "official, oblast-level rows")
    describe(daily_counts(volunteer_clean, "volunteer"), "volunteer (oblast only)")
    baselines(daily_counts(volunteer_clean, "volunteer"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
