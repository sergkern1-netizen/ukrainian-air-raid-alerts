"""Feed integrity: how well the volunteer feed agrees with the official feed, over time and place.

Definition (same as docs/gate3_results.md, section 4): a volunteer alert is matched if an official
alert in the same oblast starts within 5 minutes. The reverse check (recall) asks the same of
oblast-level official alerts. Lag is the signed difference volunteer start minus nearest official start.

Descriptive only. A low match rate means the feeds disagree, not that either one is wrong.
Small-count regions are reported with their counts and flagged.

Writes:
  docs/analysis/feed_integrity.md
  output/analysis/feed_integrity_monthly.csv
  output/analysis/feed_integrity_by_oblast.csv
"""

from pathlib import Path

import pandas as pd

from src.ingestion import vadimkin

RAW_DIR = Path("data/raw")
OUT_DOC = Path("docs/analysis/feed_integrity.md")
OUT_DIR = Path("output/analysis")
TOLERANCE = pd.Timedelta(minutes=5)
BREAK = pd.Timestamp("2025-12-01", tz="UTC")
MIN_ALERTS_FOR_RATE = 50


def nearest_match(left: pd.DataFrame, right: pd.DataFrame, left_name: str, right_name: str,
                  tol: pd.Timedelta = TOLERANCE) -> pd.DataFrame:
    """Attach the nearest same-oblast start from `right` to each row of `left`, within tolerance."""
    a = left[["started_at", left_name]].rename(columns={left_name: "oblast"}).reset_index()
    b = right[["started_at", right_name]].rename(columns={right_name: "oblast"}).copy()
    b = b.rename(columns={"started_at": "other_start"}).sort_values("other_start")
    a = a.sort_values("started_at")
    merged = pd.merge_asof(
        a, b, left_on="started_at", right_on="other_start", by="oblast",
        direction="nearest", tolerance=tol,
    )
    merged["lag_sec"] = (merged["started_at"] - merged["other_start"]).dt.total_seconds()
    return merged.set_index("index").sort_index()


def main() -> None:
    official, volunteer = vadimkin.load_both(RAW_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    names_vol = set(volunteer["region"].dropna().unique())
    names_off = set(official["oblast"].dropna().unique())
    only_vol = sorted(names_vol - names_off)
    only_off = sorted(names_off - names_vol)

    # The official feed ends on OFFICIAL_END. Volunteer alerts after that cannot match anything,
    # so they are excluded from match rates and reported separately.
    official_end = official["started_at"].max()
    vol_after_end = int((volunteer["started_at"] > official_end).sum())
    volunteer = volunteer[volunteer["started_at"] <= official_end]

    vol = volunteer.copy()
    matched_join = nearest_match(vol, official, "region", "oblast")
    vol["matched"] = matched_join["other_start"].notna()
    vol["lag_sec"] = matched_join["lag_sec"]

    off_oblast = official[official["level"] == "oblast"].copy()
    off_oblast["matched"] = nearest_match(off_oblast, volunteer, "oblast", "region")["other_start"].notna()

    vol["period"] = vol["started_at"].ge(BREAK).map({False: "pre-Dec 2025", True: "post-Dec 2025"})
    vol["month"] = vol["started_at"].dt.tz_convert("UTC").dt.tz_localize(None).dt.to_period("M")

    monthly = vol.groupby("month").agg(
        volunteer_alerts=("matched", "size"),
        matched_share=("matched", "mean"),
        median_lag_sec=("lag_sec", "median"),
    ).round({"matched_share": 3})
    monthly.to_csv(OUT_DIR / "feed_integrity_monthly.csv")

    periods = vol.groupby("period").agg(
        volunteer_alerts=("matched", "size"),
        matched_share=("matched", "mean"),
        median_abs_lag_sec=("lag_sec", lambda s: s.abs().median()),
        p90_abs_lag_sec=("lag_sec", lambda s: s.abs().quantile(0.9)),
    ).round(3)

    by_oblast = vol.pivot_table(index="region", columns="period", values="matched", aggfunc=["mean", "size"])
    by_oblast.columns = [f"{stat}_{per}" for stat, per in by_oblast.columns]
    by_oblast = by_oblast.rename(columns=lambda c: c.replace("mean_", "match_").replace("size_", "n_"))
    by_oblast.to_csv(OUT_DIR / "feed_integrity_by_oblast.csv")

    recall = off_oblast.assign(period=off_oblast["started_at"].ge(BREAK).map({False: "pre-Dec 2025", True: "post-Dec 2025"}))
    recall_by_period = recall.groupby("period")["matched"].agg(["size", "mean"]).round(3)

    lines = [
        "# Feed integrity: volunteer vs official alert agreement",
        "",
        "Definition: a volunteer alert is matched if an official alert in the same oblast starts within",
        "5 minutes (as in `gate3_results.md`). Recall is the same test for oblast-level official alerts.",
        "Descriptive only. A low match rate means the feeds disagree, not that either is wrong.",
        "",
        f"Overlap window: volunteer alerts up to the official feed's last start ({official_end.date()}).",
        f"Volunteer alerts after that date ({vol_after_end:,}) cannot be matched and are excluded from all rates.",
        "The Gate 3 figure of 44.8% after December 2025 included those alerts as unmatched and is biased low;",
        "the overlap-only figure is reported here.",
        "",
        "## Name check",
        "",
        f"- Volunteer region names not in the official feed: {only_vol or 'none'}",
        f"- Official oblast names not in the volunteer feed: {only_off or 'none'}",
        "",
        "## Precision and lag by period",
        "",
        "| Period | Volunteer alerts | Matched share | Median abs lag (s) | p90 abs lag (s) |",
        "|---|---:|---:|---:|---:|",
    ]
    for per, r in periods.iterrows():
        lines.append(f"| {per} | {int(r.volunteer_alerts):,} | {r.matched_share:.3f} | {r.median_abs_lag_sec:.0f} | {r.p90_abs_lag_sec:.0f} |")
    lines += [
        "",
        "## Recall (oblast-level official alerts with a volunteer match)",
        "",
        "| Period | Official oblast alerts | Matched share |",
        "|---|---:|---:|",
    ]
    for per, r in recall_by_period.iterrows():
        lines.append(f"| {per} | {int(r['size']):,} | {r['mean']:.3f} |")
    lines += [
        "",
        "## Monthly matched share",
        "",
        f"Full table: `output/analysis/feed_integrity_monthly.csv`. Months with fewer than {MIN_ALERTS_FOR_RATE} volunteer alerts are noisy.",
        "",
        "## By oblast",
        "",
        f"Full table: `output/analysis/feed_integrity_by_oblast.csv`. Oblasts with fewer than {MIN_ALERTS_FOR_RATE} alerts in a period are small-sample.",
        "",
    ]
    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_DOC}")
    print(periods.to_string())


if __name__ == "__main__":
    main()
