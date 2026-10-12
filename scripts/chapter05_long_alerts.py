"""Chapter 5 analysis: are long volunteer alerts real, or record artefacts?

A "long" volunteer row is one whose finished_at minus started_at exceeds 6 hours.

Checks:
  1. Counts of long rows by oblast and by year (UTC).
  2. Plausibility: start hour (Europe/Kyiv), shared finished_at values, clustering in time, naive-flag share.
  3. Official cross-check: nearest official start in the same oblast within 5 minutes, for all levels and
     for oblast level only. For matched pairs the official finish is the latest official finish among
     official rows with that oblast and start instant. Compares volunteer duration with official duration.
  4. Wave-level: 20 longest waves at a 30-minute gap; records and oblasts per wave; low records-per-hour flag.
  5. Figures in docs/chapters/figures/ch05_*.png.
  6. Every number used above in output/analysis/chapter05_numbers.json.

Descriptive only. Official agreement is a cross-check, not ground truth.

Writes:
  output/analysis/chapter05_long_alerts.csv   (gitignored)
  output/analysis/chapter05_numbers.json      (gitignored)
  docs/chapters/figures/ch05_*.png
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.alert_waves import build_waves  # noqa: E402
from scripts.feed_integrity import nearest_match  # noqa: E402
from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
FIG_DIR = Path("docs/chapters/figures")
OUT_DIR = Path("output/analysis")
OUT_CSV = OUT_DIR / "chapter05_long_alerts.csv"
OUT_JSON = OUT_DIR / "chapter05_numbers.json"

LONG_HOURS = 6.0
LOCAL_TZ = "Europe/Kyiv"
TOP_OBLASTS = 15
TOP_WAVES = 20
WAVE_GAP_MIN = 30
LONG_WAVE_HOURS = 24.0
LOW_RATE_PER_HOUR = 1 / 3
RATIO_FLAG = 3.0
TOP_SHARED_FINISH = 5

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
INK = "#1f2933"
ACCENT = "#2b6cb0"
MUTED = "#9aa5b1"


def official_finish_map(off: pd.DataFrame) -> dict:
    """(oblast, started_at) -> latest finished_at among official rows with that key."""
    return off.groupby(["oblast", "started_at"])["finished_at"].max().to_dict()


def attach_official(long: pd.DataFrame, off: pd.DataFrame, tag: str, fin_map: dict) -> pd.DataFrame:
    """Nearest same-oblast official start within 5 min, with official finish and duration ratio."""
    m = nearest_match(long, off, "region", "oblast").reindex(long.index)
    matched = m["other_start"].notna()
    fin = pd.to_datetime(
        pd.Series(
            [fin_map.get((o, s)) if pd.notna(s) else None for o, s in zip(m["oblast"], m["other_start"])],
            index=long.index,
        ),
        utc=True,
    )
    off_dur_h = (fin - m["other_start"]).dt.total_seconds() / 3600
    vol_dur_h = long["duration_h"]
    ratio = (vol_dur_h / off_dur_h).where(off_dur_h > 0)
    return pd.DataFrame(
        {
            "duration_h": vol_dur_h,
            f"{tag}_matched": matched,
            f"{tag}_lag_sec": m["lag_sec"],
            f"{tag}_official_finish": fin,
            f"{tag}_official_dur_h": off_dur_h,
            f"{tag}_ratio": ratio,
        },
        index=long.index,
    )


def ratio_stats(df: pd.DataFrame, tag: str) -> dict:
    """Summary of the volunteer/official duration ratio over matched pairs with a usable official finish."""
    valid = df[f"{tag}_ratio"].dropna()
    return {
        "matched_long_rows": int(df[f"{tag}_matched"].sum()),
        "pairs_with_official_duration": int(len(valid)),
        "median_ratio_volunteer_over_official": round(float(valid.median()), 3) if len(valid) else None,
        "share_volunteer_at_least_3x_official": round(float((valid >= RATIO_FLAG).mean()), 3) if len(valid) else None,
        "count_volunteer_at_least_3x_official": int((valid >= RATIO_FLAG).sum()),
        "median_official_dur_h": round(float(df.loc[valid.index, f"{tag}_official_dur_h"].median()), 3) if len(valid) else None,
        "median_volunteer_dur_h_on_pairs": round(float(df.loc[valid.index, "duration_h"].median()), 3) if len(valid) else None,
    }


def wave_table(vol: pd.DataFrame) -> pd.DataFrame:
    """One row per wave at the 30-minute gap, with records (volunteer rows starting inside it) and oblasts."""
    waves = build_waves(vol, WAVE_GAP_MIN).sort_values("wave_start").reset_index(drop=True)
    starts = pd.DatetimeIndex(waves["wave_start"])
    ends = waves["wave_end"].reset_index(drop=True)
    rows = vol[["started_at", "region"]].reset_index(drop=True)
    pos = starts.searchsorted(rows["started_at"], side="right") - 1
    pos_c = np.where(pos >= 0, pos, 0)
    inside = (pos >= 0) & (rows["started_at"] <= ends.iloc[pos_c].reset_index(drop=True)).to_numpy()
    rw = rows[inside].assign(wave=pos[inside])
    agg = rw.groupby("wave").agg(records=("region", "size"), oblasts=("region", "nunique"))
    agg = agg.reindex(range(len(waves)), fill_value=0)
    out = waves.join(agg)
    out["duration_h"] = out["duration_min"] / 60
    out["records_per_hour"] = np.where(out["duration_h"] > 0, out["records"] / out["duration_h"].where(out["duration_h"] > 0), np.nan)
    return out


def fig_duration_hist(durations: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    edges = np.logspace(np.log10(LONG_HOURS), np.log10(durations.max() * 1.01), 30)
    ax.hist(durations, bins=edges, color=ACCENT)
    ax.set_xscale("log")
    ax.set_xlabel("Volunteer alert duration (hours, log scale)")
    ax.set_ylabel("Long rows")
    ax.set_title("Durations of volunteer alerts over 6 hours", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_by_oblast(counts: pd.Series, path: Path) -> None:
    top = counts.head(TOP_OBLASTS)[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.barh(top.index, top.values, color=ACCENT)
    ax.set_xlabel("Volunteer rows over 6 hours")
    ax.set_title(f"Long alerts by oblast (top {TOP_OBLASTS})", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_by_month(monthly: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    x = monthly.index.to_timestamp()
    ax.bar(x, monthly.values, width=20, color=ACCENT)
    ax.set_ylabel("Long rows started in month")
    ax.set_title("Long volunteer alerts by month", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def to_builtin(o):
    if isinstance(o, dict):
        return {str(k): to_builtin(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_builtin(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


def main() -> None:
    official, vol = vadimkin.load_both(RAW_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    numbers: dict = {}

    vol = vol.reset_index(drop=True)
    vol["duration_h"] = (vol["finished_at"] - vol["started_at"]).dt.total_seconds() / 3600
    numbers["volunteer_rows"] = int(len(vol))
    numbers["official_rows"] = int(len(official))
    numbers["official_level_counts"] = official["level"].value_counts().to_dict()
    numbers["negative_durations"] = int((vol["duration_h"] < 0).sum())
    numbers["threshold_hours"] = LONG_HOURS
    for h in (6, 12, 24):
        numbers[f"rows_over_{h}h"] = int((vol["duration_h"] > h).sum())

    long = vol[vol["duration_h"] > LONG_HOURS].copy()
    numbers["long_rows"] = int(len(long))
    numbers["long_rows_naive_flag"] = int(long["naive"].sum())
    numbers["naive_share_all_rows"] = round(float(vol["naive"].mean()), 4)
    numbers["naive_share_long_rows"] = round(float(long["naive"].mean()), 4) if len(long) else None
    numbers["long_duration_max_h"] = round(float(long["duration_h"].max()), 2)
    numbers["long_duration_median_h"] = round(float(long["duration_h"].median()), 2)

    # 1. Counts by oblast and year
    by_oblast = long["region"].value_counts()
    numbers["long_by_oblast"] = by_oblast.to_dict()
    numbers["oblasts_with_long_rows"] = int(len(by_oblast))
    by_year = long["started_at"].dt.year.value_counts().sort_index()
    numbers["long_by_year_utc"] = {int(k): int(v) for k, v in by_year.items()}

    # 2. Plausibility
    local = long["started_at"].dt.tz_convert(LOCAL_TZ)
    hour_long = local.dt.hour.value_counts().reindex(range(24), fill_value=0)
    hour_all = vol["started_at"].dt.tz_convert(LOCAL_TZ).dt.hour.value_counts(normalize=True).reindex(range(24), fill_value=0)
    numbers["long_start_hour_local_counts"] = hour_long.tolist()
    numbers["long_start_hour_local_share"] = (hour_long / len(long)).round(4).tolist()
    numbers["all_start_hour_local_share"] = hour_all.round(4).tolist()
    numbers["long_start_hour_local_peak"] = int(hour_long.idxmax())

    fin_counts_long = long["finished_at"].value_counts()
    fin_counts_all = vol["finished_at"].value_counts()
    numbers["long_distinct_finished_at"] = int(len(fin_counts_long))
    numbers["long_rows_sharing_finished_at"] = int(fin_counts_long[fin_counts_long > 1].sum())
    numbers["long_top_shared_finished_at"] = [
        {"finished_at": k.isoformat(), "rows": int(v)} for k, v in fin_counts_long.head(TOP_SHARED_FINISH).items()
    ]
    numbers["all_rows_sharing_finished_at_share"] = round(float((vol["finished_at"].map(fin_counts_all) > 1).mean()), 4)

    long_sorted = long.sort_values("started_at")
    gap_h = long_sorted["started_at"].diff().dt.total_seconds() / 3600
    numbers["long_gap_to_previous_long_row_h_median"] = round(float(gap_h.median()), 2)
    numbers["long_share_within_24h_of_previous_long_row"] = round(float((gap_h <= 24).mean()), 4)
    days = local.dt.date.value_counts()
    numbers["long_distinct_local_days"] = int(len(days))
    numbers["long_max_rows_one_local_day"] = int(days.max())
    numbers["long_top_local_days"] = {str(k): int(v) for k, v in days.head(5).items()}
    numbers["long_share_rows_on_days_with_2plus"] = round(float(local.dt.date.map(days).ge(2).mean()), 4)

    # 3. Official cross-check
    fin_map = official_finish_map(official)
    off_oblast = official[official["level"] == "oblast"].copy()
    any_df = attach_official(long, official, "any", fin_map)
    obl_df = attach_official(long, off_oblast, "oblast", fin_map)
    numbers["official_match_any_level"] = ratio_stats(any_df, "any")
    numbers["official_match_oblast_level"] = ratio_stats(obl_df, "oblast")
    numbers["official_match_any_level_share"] = round(float(any_df["any_matched"].mean()), 4)
    numbers["official_match_oblast_level_share"] = round(float(obl_df["oblast_matched"].mean()), 4)

    # Per-oblast matched count for the any-level check
    long_out = long.join(any_df.drop(columns="duration_h")).join(obl_df.drop(columns="duration_h"))
    long_out["local_start_hour"] = local.dt.hour
    long_out["year_utc"] = long["started_at"].dt.year
    long_out["naive"] = long["naive"]
    export = long_out[
        ["region", "started_at", "finished_at", "duration_h", "naive", "year_utc", "local_start_hour",
         "any_matched", "any_lag_sec", "any_official_finish", "any_official_dur_h", "any_ratio",
         "oblast_matched", "oblast_lag_sec", "oblast_official_finish", "oblast_official_dur_h", "oblast_ratio"]
    ].sort_values("started_at")
    export["duration_h"] = export["duration_h"].round(3)
    export.to_csv(OUT_CSV, index=False)
    numbers["long_csv_rows"] = int(len(export))

    # 4. Wave level
    waves = wave_table(vol)
    numbers["waves_gap30_total"] = int(len(waves))
    numbers["waves_gap30_over_6h"] = int((waves["duration_h"] > LONG_HOURS).sum())
    numbers["waves_gap30_over_24h"] = int((waves["duration_h"] > LONG_WAVE_HOURS).sum())
    top = waves.sort_values("duration_h", ascending=False).head(TOP_WAVES).copy()
    top["low_rate_flag"] = top["records_per_hour"] < LOW_RATE_PER_HOUR
    numbers["top_waves_gap30"] = [
        {
            "wave_start": r.wave_start.isoformat(),
            "wave_end": r.wave_end.isoformat(),
            "duration_h": round(float(r.duration_h), 2),
            "records": int(r.records),
            "oblasts": int(r.oblasts),
            "records_per_hour": round(float(r.records_per_hour), 3),
            "low_rate_flag": bool(r.low_rate_flag),
        }
        for r in top.itertuples()
    ]
    numbers["top_waves_low_rate_flagged"] = int(top["low_rate_flag"].sum())
    numbers["waves_gap30_low_rate_flagged_all_over_24h"] = int(
        ((waves["duration_h"] > LONG_WAVE_HOURS) & (waves["records_per_hour"] < LOW_RATE_PER_HOUR)).sum()
    )
    longest = waves.sort_values("duration_h", ascending=False).iloc[0]
    numbers["longest_wave_gap30"] = {
        "wave_start": longest.wave_start.isoformat(),
        "duration_h": round(float(longest.duration_h), 2),
        "records": int(longest.records),
        "oblasts": int(longest.oblasts),
    }

    # 5. Figures
    fig_duration_hist(long["duration_h"], FIG_DIR / "ch05_duration_hist.png")
    fig_by_oblast(by_oblast, FIG_DIR / "ch05_long_by_oblast.png")
    monthly = long["started_at"].dt.tz_convert(None).dt.to_period("M").value_counts().sort_index()
    full = pd.period_range(monthly.index.min(), monthly.index.max(), freq="M")
    monthly = monthly.reindex(full, fill_value=0)
    numbers["long_by_month_utc"] = {str(k): int(v) for k, v in monthly.items()}
    fig_by_month(monthly, FIG_DIR / "ch05_long_by_month.png")

    # 6. Write numbers
    OUT_JSON.write_text(json.dumps(to_builtin(numbers), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Summary
    print(f"volunteer rows {numbers['volunteer_rows']:,}; long rows (>6h) {numbers['long_rows']:,}; "
          f"over 12h {numbers['rows_over_12h']}; over 24h {numbers['rows_over_24h']}")
    print(f"naive flag on long rows: {numbers['long_rows_naive_flag']} "
          f"(all rows share {numbers['naive_share_all_rows']:.3f})")
    print(f"longest long row: {numbers['long_duration_max_h']} h; median {numbers['long_duration_median_h']} h")
    print("top oblasts: " + ", ".join(f"{k} {v}" for k, v in by_oblast.head(5).items()))
    print("by year (UTC): " + ", ".join(f"{k} {v}" for k, v in numbers["long_by_year_utc"].items()))
    print(f"start hour (Kyiv) peak {numbers['long_start_hour_local_peak']:02d}:00; "
          f"share of long rows at 00-05 Kyiv: {sum(numbers['long_start_hour_local_share'][0:6]):.3f} "
          f"vs all rows {sum(numbers['all_start_hour_local_share'][0:6]):.3f}")
    print(f"long rows sharing a finished_at with another long row: {numbers['long_rows_sharing_finished_at']} "
          f"(distinct finish values {numbers['long_distinct_finished_at']})")
    print(f"top shared finish: {numbers['long_top_shared_finished_at'][0]}")
    print(f"long rows within 24h of previous long row: {numbers['long_share_within_24h_of_previous_long_row']:.3f}; "
          f"max long rows on one Kyiv day: {numbers['long_max_rows_one_local_day']}")
    for tag in ("official_match_any_level", "official_match_oblast_level"):
        s = numbers[tag]
        print(f"{tag}: matched {s['matched_long_rows']}/{numbers['long_rows']}; pairs with official duration "
              f"{s['pairs_with_official_duration']}; median ratio {s['median_ratio_volunteer_over_official']}; "
              f"share >=3x {s['share_volunteer_at_least_3x_official']}")
    print(f"waves gap 30: {numbers['waves_gap30_total']:,}; over 6h {numbers['waves_gap30_over_6h']}; "
          f"over 24h {numbers['waves_gap30_over_24h']}")
    lw = numbers["longest_wave_gap30"]
    print(f"longest wave: start {lw['wave_start']} duration {lw['duration_h']} h, "
          f"records {lw['records']}, oblasts {lw['oblasts']}")
    print(f"top {TOP_WAVES} waves flagged low rate (<1 record per 3 h): {numbers['top_waves_low_rate_flagged']}")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {FIG_DIR}/ch05_duration_hist.png, ch05_long_by_oblast.png, ch05_long_by_month.png")


if __name__ == "__main__":
    main()
