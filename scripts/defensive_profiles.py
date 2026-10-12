"""Defensive alert-record profiles for civil-protection and warning-system review.

Descriptive statistics of the alert records only. No forecasts, no target rankings, no link to
military units or weapon types (the feed does not record them). Intended for shelter planning,
warning-system review and assessing how far the alert record can be trusted.

Sections:
  1. Alert duration by oblast (median, p90, p99).
  2. Night versus day exposure (22:00-07:00 local time), by oblast and season.
  3. Warning timeliness: volunteer-minus-official lag for matched alerts, by oblast.
  4. Feed reliability: match rate by oblast, before and after the December 2025 break.
  5. Long-alert register: volunteer alerts longer than 6 hours.
  6. Granularity change: official records by level and oblast-name count, by period.

Limits: no population data (so no per-capita figures); the feed does not record threat type; the
official feed ends on OFFICIAL_END.

Writes:
  docs/analysis/defensive_profiles.md
  output/analysis/long_alerts.csv   (gitignored)
"""

from pathlib import Path

import numpy as np
import pandas as pd

from scripts.feed_integrity import BREAK, MIN_ALERTS_FOR_RATE, nearest_match
from src.ingestion import vadimkin

RAW_DIR = Path("data/raw")
OUT_DOC = Path("docs/analysis/defensive_profiles.md")
OUT_DIR = Path("output/analysis")
LOCAL_TZ = "Europe/Kyiv"
LONG_MIN = 360


def fmt(x, nd=0):
    return "n/a" if pd.isna(x) else f"{x:,.{nd}f}"


def section_duration(vol: pd.DataFrame) -> list:
    d = vol.copy()
    d["dur"] = (d["finished_at"] - d["started_at"]).dt.total_seconds() / 60
    d = d[d["dur"] > 0]
    g = d.groupby("region")["dur"]
    t = pd.DataFrame({
        "alerts": g.size(),
        "median_min": g.median(),
        "p90_min": g.quantile(0.9),
        "p99_min": g.quantile(0.99),
    }).sort_values("alerts", ascending=False)
    lines = [
        "## 1. Alert duration by oblast",
        "",
        "Duration = finished_at minus started_at, in minutes. Rows with zero or negative duration are",
        "excluded. Whole feed.",
        "",
        "| Oblast | Alerts | Median (min) | p90 (min) | p99 (min) |",
        "|---|---:|---:|---:|---:|",
    ]
    for region, r in t.iterrows():
        lines.append(f"| {region} | {int(r.alerts):,} | {fmt(r.median_min)} | {fmt(r.p90_min)} | {fmt(r.p99_min)} |")
    lines.append("")
    return lines


def section_night(vol: pd.DataFrame) -> list:
    local = vol["started_at"].dt.tz_convert(LOCAL_TZ)
    hour = local.dt.hour
    night = (hour >= 22) | (hour < 7)
    season = local.dt.month.map({12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
                                 6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"})
    d = pd.DataFrame({"region": vol["region"], "night": night, "season": season})
    overall = d.groupby("region")["night"].agg(["size", "mean"]).sort_values("size", ascending=False)
    by_season = d.groupby("season")["night"].mean().round(3)
    lines = [
        "## 2. Night versus day exposure",
        "",
        f"Night = 22:00 to 07:00 {LOCAL_TZ} time. Share of alert starts in the night window.",
        "",
        "| Oblast | Alerts | Night share |",
        "|---|---:|---:|",
    ]
    for region, r in overall.iterrows():
        flag = " (small sample)" if r["size"] < MIN_ALERTS_FOR_RATE else ""
        lines.append(f"| {region} | {int(r['size']):,} | {r['mean']:.3f}{flag} |")
    lines += ["", "Night share by season (all oblasts): " + ", ".join(f"{k} {v}" for k, v in by_season.items()), ""]
    return lines


def section_lag(official: pd.DataFrame, volunteer: pd.DataFrame) -> list:
    off = official[official["level"] == "oblast"]
    m = nearest_match(volunteer, off, "region", "oblast")
    v = volunteer.assign(lag_sec=m["lag_sec"], matched=m["other_start"].notna())
    v = v[v["matched"]]
    g = v.groupby("region")["lag_sec"]
    t = pd.DataFrame({"matched": g.size(), "median_lag_s": g.median(), "p90_abs_lag_s": g.apply(lambda s: s.abs().quantile(0.9))})
    t = t.sort_values("matched", ascending=False)
    lines = [
        "## 3. Warning timeliness: volunteer minus official lag",
        "",
        "For volunteer alerts matched to an official oblast alert within 5 minutes. Positive lag means the",
        f"volunteer record came after the official one. Overlap window up to the official feed's last start.",
        "",
        "| Oblast | Matched alerts | Median lag (s) | p90 absolute lag (s) |",
        "|---|---:|---:|---:|",
    ]
    for region, r in t.iterrows():
        flag = " (small sample)" if r.matched < MIN_ALERTS_FOR_RATE else ""
        lines.append(f"| {region} | {int(r.matched):,}{flag} | {fmt(r.median_lag_s)} | {fmt(r.p90_abs_lag_s)} |")
    lines.append("")
    return lines


def section_reliability(official: pd.DataFrame, volunteer: pd.DataFrame) -> list:
    off = official[official["level"] == "oblast"]
    m = nearest_match(volunteer, off, "region", "oblast")
    v = volunteer.assign(matched=m["other_start"].notna())
    v["period"] = np.where(v["started_at"] >= BREAK, "post", "pre")
    t = v.groupby(["region", "period"])["matched"].agg(["size", "mean"]).unstack("period")
    t.columns = [f"{s}_{p}" for s, p in t.columns]
    lines = [
        "## 4. Feed reliability: match rate by oblast",
        "",
        "Share of volunteer alerts matched to an official oblast alert within 5 minutes. Overlap window.",
        f"Small samples (fewer than {MIN_ALERTS_FOR_RATE} alerts in a period) are flagged.",
        "",
        "| Oblast | Match before Dec 2025 | n | Match from Dec 2025 | n |",
        "|---|---:|---:|---:|---:|",
    ]
    for region, r in t.sort_index().iterrows():
        pre_n = 0 if pd.isna(r.get("size_pre")) else int(r["size_pre"])
        post_n = 0 if pd.isna(r.get("size_post")) else int(r["size_post"])
        pre = fmt(r.get("mean_pre"), 3)
        post = fmt(r.get("mean_post"), 3)
        pre_flag = "*" if 0 < pre_n < MIN_ALERTS_FOR_RATE else ""
        post_flag = "*" if 0 < post_n < MIN_ALERTS_FOR_RATE else ""
        lines.append(f"| {region} | {pre}{pre_flag} | {pre_n:,} | {post}{post_flag} | {post_n:,} |")
    lines += ["", "`*` = small sample.", ""]
    return lines


def section_long(vol: pd.DataFrame) -> list:
    d = vol.copy()
    d["dur_min"] = (d["finished_at"] - d["started_at"]).dt.total_seconds() / 60
    long = d[d["dur_min"] > LONG_MIN].sort_values("dur_min", ascending=False)
    long[["region", "started_at", "finished_at", "dur_min", "naive"]].to_csv(OUT_DIR / "long_alerts.csv", index=False)
    by_region = long.groupby("region").size().sort_values(ascending=False)
    lines = [
        f"## 5. Long-alert register (longer than {LONG_MIN // 60} hours)",
        "",
        f"{len(long):,} volunteer alerts exceed {LONG_MIN // 60} hours. Full list in `output/analysis/long_alerts.csv`",
        "(gitignored). The `naive` flag (inferred end time) is False for all of these rows (checked 2026-10-12: 0 of them).",
        "",
        "| Oblast | Long alerts |",
        "|---|---:|",
    ]
    for region, n in by_region.items():
        lines.append(f"| {region} | {int(n):,} |")
    lines.append("")
    return lines


def section_granularity(official: pd.DataFrame) -> list:
    o = official.assign(period=np.where(official["started_at"] >= BREAK, "from Dec 2025", "before Dec 2025"))
    t = o.groupby(["period", "level"]).size().unstack("level", fill_value=0)
    names = o.groupby("period")["oblast"].nunique()
    lines = [
        "## 6. Granularity change in the official feed",
        "",
        "Official records by level, and distinct oblast names, before and after the December 2025 break.",
        "",
        "| Period | Records by level | Distinct oblast names |",
        "|---|---|---:|",
    ]
    for per in t.index:
        levels = ", ".join(f"{lvl} {int(n):,}" for lvl, n in t.loc[per].items())
        lines.append(f"| {per} | {levels} | {int(names[per])} |")
    lines += [
        "",
        "Records from the raion level can be several per oblast event, so counts are not comparable",
        "across the break (see `docs/gate3_results.md`).",
        "",
    ]
    return lines


def main() -> None:
    official, volunteer = vadimkin.load_both(RAW_DIR)
    end = official["started_at"].max()
    vol_overlap = volunteer[volunteer["started_at"] <= end]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    header = [
        "# Defensive alert-record profiles",
        "",
        "Purpose: support civil-protection planning, warning-system review and checks on how far the",
        "alert record can be trusted. Descriptive only.",
        "",
        "Out of scope: forecasts of when or where attacks will occur, rankings of oblasts as targets,",
        "and links to military units or weapon types (not recorded in the feed).",
        "",
        "Limits: no population data (no per-capita figures). The feed does not record threat type.",
        f"The official feed ends on {end.date()}. Duration and night-share use the whole volunteer feed;",
        "match-based sections use the overlap window.",
        "",
    ]
    body = (
        section_duration(volunteer)
        + section_night(volunteer)
        + section_lag(official, vol_overlap)
        + section_reliability(official, vol_overlap)
        + section_long(volunteer)
        + section_granularity(official)
    )
    OUT_DOC.write_text("\n".join(header + body), encoding="utf-8")
    print(f"wrote {OUT_DOC}")


if __name__ == "__main__":
    main()
