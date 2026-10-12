"""
Weekly national alert totals for Gate 3 backtests.

Target: volunteer feed, oblast-level rows, counted per Monday-start week (UTC). Partial
first and last weeks are dropped so every week has the same number of days.

Alert types (yellow, red, drone threat) are not present in the Vadimkin files, so the
target counts whatever those files record. See docs/gate3_results.md.
"""

import pandas as pd

# Official feed switched to mostly raion-level alerts in December 2025 (Vadimkin README).
# Used as a known-in-advance regime indicator, so it is not leakage.
REGIME_START = pd.Timestamp("2025-12-01", tz="UTC")


def weekly_totals(alerts: pd.DataFrame) -> pd.DataFrame:
    """
    Count alerts per complete Monday-start week.

    Args:
        alerts: Deduplicated alert rows with a UTC `started_at` column.

    Returns:
        DataFrame indexed by week start (UTC) with columns:
        `alerts` (weekly count) and `regime` (1 from December 2025 on, else 0).
    """
    starts = alerts["started_at"]
    first_day = starts.min().normalize()
    last_record_day = starts.max().normalize()

    week_start = starts.dt.tz_convert("UTC").dt.normalize()
    week_start = week_start - pd.to_timedelta(week_start.dt.weekday, unit="D")
    counts = week_start.value_counts().sort_index()

    weeks = pd.date_range(counts.index.min(), counts.index.max(), freq="7D", tz="UTC")
    weekly = counts.reindex(weeks, fill_value=0).rename("alerts").to_frame()

    # Keep only weeks that start on or after the first day and end before the last record's day
    complete = (weekly.index >= first_day) & (
        weekly.index + pd.Timedelta(days=7) <= last_record_day
    )
    weekly = weekly[complete]
    weekly["regime"] = (weekly.index >= REGIME_START).astype(int)
    return weekly
