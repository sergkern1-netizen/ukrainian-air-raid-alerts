"""Chapter 9: daily and weekly national alert-time coverage (volunteer feed).

Descriptive only. "Covered" means at least one alert was active somewhere in the country at that
minute. This is a national measure of recorded alert time. It is NOT a measure of disruption to
any person, school, business or route, and it says nothing about warning time or cause.

Method:
  - Source: volunteer feed only (data/raw/volunteer_data_en.csv via src.ingestion.vadimkin).
  - Records with finished_at <= started_at are dropped.
  - All oblast intervals are merged into national episodes ([start, end), touching intervals merge).
  - Episodes are clipped at Europe/Kyiv midnight (days) and Monday midnight (weeks).
  - Covered minutes = union length within the period. Episodes = merged pieces within the period,
    so an episode crossing midnight counts once on each day it touches.
  - Periods with no covered minutes are "no records" and are never filled with zeros.
  - The first and last calendar days with records are partial (the feed starts and ends inside
    them), as are the weeks containing them. Partial periods are reported but excluded from
    the distributions.

Window: 2022-02-25 to 2026-10-11 (volunteer feed, as loaded).

Writes:
  output/analysis/chapter09_numbers.json
  output/analysis/chapter09_daily.csv
  docs/chapters/figures/ch09_covered_share_by_weekday.png
  docs/chapters/figures/ch09_daily_share_distribution.png
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
OUT_DIR = Path("output/analysis")
FIG_DIR = Path("docs/chapters/figures")
JSON_OUT = OUT_DIR / "chapter09_numbers.json"
DAILY_CSV = OUT_DIR / "chapter09_daily.csv"
FIG_WEEKDAY = FIG_DIR / "ch09_covered_share_by_weekday.png"
FIG_HIST = FIG_DIR / "ch09_daily_share_distribution.png"

LOCAL = "Europe/Kyiv"
MINUTES_PER_DAY = 1440
MINUTES_PER_WEEK = 10080
NS_PER_MIN = 60 * 1_000_000_000
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BAR = "#4a6fa5"
PLAIN = "#555555"


def merge_intervals(df: pd.DataFrame):
    """Union of all [start, end) intervals as merged national episodes (int64 ns, UTC)."""
    s = df["started_at"].dt.tz_convert("UTC").values.astype("datetime64[ns]").view("int64")
    e = df["finished_at"].dt.tz_convert("UTC").values.astype("datetime64[ns]").view("int64")
    order = np.argsort(s, kind="stable")
    s, e = s[order], e[order]
    cummax_e = np.maximum.accumulate(e)
    new_group = np.ones(len(s), dtype=bool)
    new_group[1:] = s[1:] > cummax_e[:-1]
    starts = np.flatnonzero(new_group)
    ends_idx = np.r_[starts[1:] - 1, len(s) - 1]
    return s[starts], cummax_e[ends_idx]


def clip_to_periods(ms: np.ndarray, me: np.ndarray, bounds: np.ndarray, n_periods: int):
    """Split merged episodes at period boundaries; return covered ns and piece counts per period."""
    i0 = np.searchsorted(bounds, ms, side="right") - 1
    i1 = np.searchsorted(bounds, me, side="left") - 1
    counts = i1 - i0 + 1
    total = int(counts.sum())
    rep = np.repeat(np.arange(len(ms)), counts)
    offsets = np.r_[0, np.cumsum(counts)[:-1]]
    k = i0[rep] + (np.arange(total) - offsets[rep])
    st = np.maximum(ms[rep], bounds[k])
    en = np.minimum(me[rep], bounds[k + 1])
    keep = en > st
    k, length = k[keep], (en - st)[keep]
    covered = np.zeros(n_periods, dtype=np.int64)
    np.add.at(covered, k, length)
    episodes = np.zeros(n_periods, dtype=np.int64)
    np.add.at(episodes, k, 1)
    return covered, episodes


def kyiv_midnight_ns(dates) -> np.ndarray:
    """UTC nanosecond timestamps of Kyiv local midnight for each naive date."""
    return np.array(
        [pd.Timestamp(d).tz_localize(LOCAL).tz_convert("UTC").value for d in dates], dtype=np.int64
    )


def build_tables(df: pd.DataFrame) -> dict:
    """Daily and weekly coverage tables for one set of positive-duration records."""
    ms, me = merge_intervals(df)
    first_day = pd.Timestamp(ms.min(), tz="UTC").tz_convert(LOCAL).normalize().tz_localize(None)
    last_day = pd.Timestamp(me.max() - 1, tz="UTC").tz_convert(LOCAL).normalize().tz_localize(None)

    days = pd.date_range(first_day, last_day, freq="D")
    day_bounds = np.r_[kyiv_midnight_ns(days), kyiv_midnight_ns([last_day + pd.Timedelta(days=1)])]
    d_cov, d_ep = clip_to_periods(ms, me, day_bounds, len(days))

    daily = pd.DataFrame(
        {
            "date": days.date,
            "weekday": [WEEKDAYS[d.weekday()] for d in days],
            "year": days.year,
            "month": days.month,
            "covered_minutes": np.where(d_cov > 0, d_cov / NS_PER_MIN, np.nan),
            "merged_episodes": np.where(d_ep > 0, d_ep, np.nan),
        }
    )
    daily["has_records"] = d_cov > 0
    daily["covered_share"] = daily["covered_minutes"] / MINUTES_PER_DAY

    data_first = first_day if d_cov[0] > 0 else days[d_cov > 0][0]
    data_last = days[d_cov > 0][-1]
    daily["partial"] = daily["date"].isin([data_first.date(), data_last.date()]) & daily["has_records"]

    mondays = pd.date_range(first_day - pd.Timedelta(days=first_day.weekday()), last_day, freq="W-MON")
    week_bounds = np.r_[
        kyiv_midnight_ns(mondays), kyiv_midnight_ns([mondays[-1] + pd.Timedelta(days=7)])
    ]
    w_cov, w_ep = clip_to_periods(ms, me, week_bounds, len(mondays))
    weekly = pd.DataFrame(
        {
            "week_start": mondays.date,
            "week_end": (mondays + pd.Timedelta(days=6)).date,
            "covered_minutes": w_cov / NS_PER_MIN,
            "merged_episodes": w_ep,
        }
    )
    weekly["has_records"] = w_cov > 0
    weekly["covered_share"] = weekly["covered_minutes"] / MINUTES_PER_WEEK
    weekly["partial"] = [
        (ws <= data_first <= ws + pd.Timedelta(days=6)) or (ws <= data_last <= ws + pd.Timedelta(days=6))
        for ws in mondays
    ]
    weekly.loc[~weekly["has_records"], ["covered_minutes", "covered_share", "merged_episodes"]] = np.nan

    return {
        "daily": daily,
        "weekly": weekly,
        "data_first": data_first,
        "data_last": data_last,
        "calendar_days": len(days),
        "max_daily_minutes": float(np.nanmax(daily["covered_minutes"])),
        "max_weekly_minutes": float(np.nanmax(weekly["covered_minutes"])),
    }


def summarize(tables: dict) -> dict:
    """Compute every number in the chapter from the coverage tables."""
    daily, weekly = tables["daily"], tables["weekly"]
    have = daily[daily["has_records"]]
    full = have[~have["partial"]]
    share = full["covered_share"]

    wk_have = weekly[weekly["has_records"]]
    wk = wk_have[~wk_have["partial"]]

    weekday = {w: round(float(full.loc[full["weekday"] == w, "covered_share"].median()), 4) for w in WEEKDAYS}
    monthly = {
        MONTHS[m - 1]: round(float(full.loc[full["month"] == m, "covered_share"].median()), 4)
        for m in range(1, 13)
        if (full["month"] == m).any()
    }
    yearly = {
        int(y): round(float(full.loc[full["year"] == y, "covered_share"].median()), 4)
        for y in sorted(full["year"].unique())
    }
    top = wk.nlargest(5, "covered_share")
    top5 = [
        {
            "week_start": str(r.week_start),
            "week_end": str(r.week_end),
            "covered_minutes": round(float(r.covered_minutes), 1),
            "covered_share": round(float(r.covered_share), 4),
            "merged_episodes": int(r.merged_episodes),
        }
        for r in top.itertuples()
    ]
    ep = full["merged_episodes"].astype(float)
    return {
        "daily_share_distribution": {
            "n_days": int(len(full)),
            "median": round(float(share.median()), 4),
            "p90": round(float(share.quantile(0.90)), 4),
            "p10": round(float(share.quantile(0.10)), 4),
            "share_days_gt_25pct": round(float((share > 0.25).mean()), 4),
            "share_days_gt_50pct": round(float((share > 0.50).mean()), 4),
            "share_days_gt_75pct": round(float((share > 0.75).mean()), 4),
        },
        "weekday_median_share": weekday,
        "monthly_median_share_pooled": monthly,
        "yearly_median_share": yearly,
        "weekly": {
            "n_weeks": int(len(wk)),
            "median_share": round(float(wk["covered_share"].median()), 4),
            "p90_share": round(float(wk["covered_share"].quantile(0.90)), 4),
            "median_merged_episodes": float(wk["merged_episodes"].median()),
            "top5_by_covered_share": top5,
        },
        "episodes_per_day": {
            "median": float(ep.median()),
            "p90": float(ep.quantile(0.90)),
        },
        "check_daily_minutes_le_1440": {
            "violations": int((daily["covered_minutes"] > MINUTES_PER_DAY).sum()),
            "max_covered_minutes": round(float(tables["max_daily_minutes"]), 4),
        },
        "check_weekly_minutes_le_10080": {
            "violations": int((weekly["covered_minutes"] > MINUTES_PER_WEEK).sum()),
            "max_covered_minutes": round(float(tables["max_weekly_minutes"]), 4),
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    _, volunteer = vadimkin.load_both(RAW_DIR)
    n_raw = len(volunteer)
    positive = volunteer["finished_at"] > volunteer["started_at"]
    n_nonpositive = int((~positive).sum())
    vol = volunteer.loc[positive].copy()
    print(f"volunteer rows {n_raw:,}; dropped non-positive duration {n_nonpositive:,}; used {len(vol):,}")

    tables = build_tables(vol)
    numbers = summarize(tables)
    daily, weekly = tables["daily"], tables["weekly"]

    no_rec_days = daily.loc[~daily["has_records"], "date"]
    numbers["meta"] = {
        "source": "Vadimkin volunteer_data_en.csv (oblast-level, UTC-aware)",
        "first_record_date_kyiv": str(tables["data_first"].date()),
        "last_record_date_kyiv": str(tables["data_last"].date()),
        "calendar_days_in_range": int(tables["calendar_days"]),
        "days_with_records": int(daily["has_records"].sum()),
        "days_without_records": int(len(no_rec_days)),
        "partial_days_excluded": [str(d) for d in daily.loc[daily["partial"], "date"]],
        "weeks_with_records": int(weekly["has_records"].sum()),
        "rows_total": int(n_raw),
        "rows_nonpositive_duration_dropped": n_nonpositive,
        "rows_used": int(len(vol)),
        "rows_naive_end_inferred": int(vol["naive"].sum()),
        "note_naive": "naive=True rows have end = start + 30 min (inferred); kept in main result",
        "note_days": "a day is covered if any alert overlaps it; episodes crossing midnight count on both days",
    }

    naive_free = vol.loc[~vol["naive"]]
    sens = summarize(build_tables(naive_free))
    numbers["sensitivity_excl_naive"] = {
        "rows_used": int(len(naive_free)),
        "daily_share_distribution": sens["daily_share_distribution"],
        "weekly_median_share": sens["weekly"]["median_share"],
        "episodes_per_day": sens["episodes_per_day"],
    }

    with JSON_OUT.open("w", encoding="utf-8") as fh:
        json.dump(numbers, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    out = daily.copy()
    out["covered_share"] = out["covered_share"].round(4)
    out["covered_minutes"] = out["covered_minutes"].round(2)
    out[["date", "weekday", "year", "month", "has_records", "partial", "covered_minutes",
         "covered_share", "merged_episodes"]].to_csv(DAILY_CSV, index=False)

    # Figure 1: median covered share by weekday.
    wd = numbers["weekday_median_share"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(list(wd.keys()), [v * 100 for v in wd.values()], color=BAR)
    ax.set_ylabel("Median share of day covered (%)")
    ax.set_xlabel("Weekday (Kyiv)")
    ax.set_title("Share of day with an alert active somewhere in Ukraine, by weekday")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Volunteer feed, 2022-02-25 to 2026-10-11, partial first/last days excluded. "
             "National measure of recorded alert time.", fontsize=7, color=PLAIN)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_WEEKDAY, dpi=150)
    plt.close(fig)

    # Figure 2: histogram of daily covered share.
    full = daily[daily["has_records"] & ~daily["partial"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(full["covered_share"] * 100, bins=np.arange(0, 102, 2), color=BAR)
    ax.set_xlabel("Covered share of the day (%)")
    ax.set_ylabel("Days")
    ax.set_title("Distribution of daily covered share (days with records)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Covered = at least one alert active somewhere in Ukraine. Days with no records "
             "excluded, not zero.", fontsize=7, color=PLAIN)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_HIST, dpi=150)
    plt.close(fig)

    d = numbers["daily_share_distribution"]
    print(f"days analysed {d['n_days']}; median {d['median']:.3f}, p90 {d['p90']:.3f}, p10 {d['p10']:.3f}")
    print(f"days without records {numbers['meta']['days_without_records']}; partial excluded "
          f"{numbers['meta']['partial_days_excluded']}")
    print(f"violations daily {numbers['check_daily_minutes_le_1440']['violations']}, "
          f"weekly {numbers['check_weekly_minutes_le_10080']['violations']}")
    print(f"wrote {JSON_OUT}, {DAILY_CSV}, {FIG_WEEKDAY}, {FIG_HIST}")


if __name__ == "__main__":
    main()
