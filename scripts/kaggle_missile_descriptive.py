"""Descriptive summary of the Kaggle missile-attack dataset. Not a model input.

Writes docs/enterprise/kaggle_missile_descriptive.md. Missing days stay missing: the summary
reports how many calendar days have no record instead of filling them with zero.
"""

from pathlib import Path

import pandas as pd

RAW = Path("data/raw/kaggle_missile/missile_attacks_daily.csv")
OUT = Path("docs/enterprise/kaggle_missile_descriptive.md")


def main() -> None:
    df = pd.read_csv(RAW)
    ts = pd.to_datetime(df["time_start"], format="mixed", errors="coerce")
    if ts.isna().any():
        raise ValueError(f"{int(ts.isna().sum())} rows have unparseable time_start")

    days = ts.dt.normalize().drop_duplicates().sort_values()
    calendar = pd.date_range(days.min(), days.max(), freq="D")
    missing_days = len(calendar.difference(days))

    monthly = (
        pd.DataFrame({"month": ts.dt.to_period("M"), "launched": df["launched"], "destroyed": df["destroyed"]})
        .groupby("month")
        .agg(records=("launched", "size"), launched=("launched", "sum"), destroyed=("destroyed", "sum"))
    )

    lines = [
        "# Kaggle missile dataset: descriptive summary",
        "",
        "Source and provenance: see `kaggle_missile_profile.md`. Licence CC BY-NC-SA 4.0 (Petro",
        "Ivaniuk). The file aggregates Telegram channel posts (see the Telegram terms caveat in",
        "`candidates_review.md`). Descriptive use only: no forecasting feature is built from this data.",
        "",
        f"- Records: {len(df):,}",
        f"- Date range: {days.min().date()} to {days.max().date()}",
        f"- Calendar days with no record: {missing_days} of {len(calendar):,} (not zero-filled)",
        "",
        "## Monthly totals",
        "",
        "| Month | Records | Launched (sum) | Destroyed (sum) |",
        "|---|---:|---:|---:|",
    ]
    for month, row in monthly.iterrows():
        lines.append(
            f"| {month} | {int(row.records)} | {row.launched:,.0f} | {row.destroyed:,.0f} |"
        )
    lines += [
        "",
        "Sums skip missing values. A month with few records reflects fewer reported events, not",
        "necessarily fewer attacks.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} ({len(monthly)} months, {missing_days} missing days)")


if __name__ == "__main__":
    main()
