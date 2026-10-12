"""Segment the volunteer alert feed into waves at several gap thresholds.

A wave is a run of national start instants where each start is at most `gap` minutes after the
previous one. A start instant is any distinct `started_at` value across all oblasts.

Descriptive analysis only. Missing weeks are not zero-filled: a week with no wave is reported
as "no record", not as a quiet week.

Writes:
  docs/analysis/alert_waves.md        summary tables for the report
  output/analysis/waves_gap{G}.csv    one row per wave (gitignored)
"""

from pathlib import Path

import pandas as pd

from src.ingestion import vadimkin

RAW_DIR = Path("data/raw")
OUT_DOC = Path("output/analysis/alert_waves.md")
OUT_CSV_DIR = Path("output/analysis")
GAPS_MINUTES = [5, 10, 15, 30, 60]


def build_waves(volunteer: pd.DataFrame, gap_minutes: int) -> pd.DataFrame:
    """Return one row per wave for the given gap threshold."""
    rows = volunteer[["started_at", "finished_at", "region"]].copy()
    rows["finished_at"] = rows[["started_at", "finished_at"]].max(axis=1)

    instants = (
        rows.groupby("started_at")
        .agg(last_finish=("finished_at", "max"), regions=("region", "nunique"))
        .sort_index()
    )
    gap = instants.index.to_series().diff() > pd.Timedelta(minutes=gap_minutes)
    wave_id = gap.cumsum()

    waves = instants.groupby(wave_id).agg(
        wave_start=("last_finish", lambda s: s.index.min()),
        wave_end=("last_finish", "max"),
        start_instants=("last_finish", "size"),
        region_alerts=("regions", "sum"),
    )
    waves["wave_start"] = instants.index.to_series().groupby(wave_id).min()
    waves["duration_min"] = (waves["wave_end"] - waves["wave_start"]).dt.total_seconds() / 60
    return waves.reset_index(drop=True)


def summarise(waves: pd.DataFrame, gap_minutes: int) -> dict:
    """Headline numbers for one gap threshold."""
    weeks = waves["wave_start"].dt.tz_convert("UTC").dt.normalize()
    weeks = weeks - pd.to_timedelta(weeks.dt.weekday, unit="D")
    return {
        "gap_min": gap_minutes,
        "waves": int(len(waves)),
        "waves_over_6h": int((waves["duration_min"] > 360).sum()),
        "median_duration_min": round(waves["duration_min"].median(), 1),
        "p90_duration_min": round(waves["duration_min"].quantile(0.9), 1),
        "median_start_instants": int(waves["start_instants"].median()),
        "p90_start_instants": int(waves["start_instants"].quantile(0.9)),
        "weeks_with_at_least_one_wave": int(weeks.nunique()),
    }


def main() -> None:
    _, volunteer = vadimkin.load_both(RAW_DIR)
    OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    summaries = []
    for gap in GAPS_MINUTES:
        waves = build_waves(volunteer, gap)
        waves.to_csv(OUT_CSV_DIR / f"waves_gap{gap}.csv", index=False)
        summaries.append(summarise(waves, gap))
        print(f"gap {gap:>3} min: {len(waves):,} waves")

    table = pd.DataFrame(summaries)
    lines = [
        "# Alert waves: sensitivity to the gap threshold",
        "",
        "Source: volunteer feed (`volunteer_data_en.csv`, after exact-duplicate drop). A wave is a",
        "run of national start instants, each at most `gap` minutes after the previous one.",
        "Weeks are counted only where a wave was observed. Missing weeks are not zero-filled.",
        "",
        "| Gap (min) | Waves | Waves over 6 h | Median duration (min) | p90 duration (min) | Median start instants | p90 start instants | Weeks with a wave |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in table.iterrows():
        lines.append(
            f"| {int(r.gap_min)} | {int(r.waves):,} | {int(r.waves_over_6h):,} | {r.median_duration_min} | "
            f"{r.p90_duration_min} | {int(r.median_start_instants)} | {int(r.p90_start_instants)} | "
            f"{int(r.weeks_with_at_least_one_wave)} |"
        )
    lines += [
        "",
        "Waves over 6 hours are either real long alerts or unclosed records. The feed does not say",
        "which. Treat them as a feed-integrity question before reading them as events.",
        "",
        "Per-wave CSVs are written to `output/analysis/` (gitignored). `region_alerts` counts",
        "region-alert pairs in a wave, not distinct regions.",
        "",
    ]
    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_DOC}")


if __name__ == "__main__":
    main()
