"""Chapter 1 analysis: alert timing, duration and day/night rhythms.

Data: the volunteer alert feed (volunteer_data_en.csv), after exact-duplicate drop. Times are shown in
Kyiv local time for hours and nights. Waves use a 30-minute gap (scripts/alert_waves.py).

Descriptive only. A "night" is 22:00 to 07:00 local time. Nothing here estimates warning time or
impact: the feed has no launch or impact times.

Writes:
  docs/chapters/01-timing-and-rhythms.md   (text generated from the numbers below, plus the figures)
  docs/chapters/figures/ch01_*.png
  output/analysis/chapter01_numbers.json  (gitignored)
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
CHAPTER = Path("docs/chapters/01-timing-and-rhythms.md")
FIG_DIR = Path("docs/chapters/figures")
OUT_DIR = Path("output/analysis")
LOCAL = "Europe/Kyiv"
GAP = pd.Timedelta(minutes=30)
NIGHT_START, NIGHT_END = 22, 7

plt.rcParams.update({
    "figure.dpi": 130,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})
INK = "#1f2933"
ACCENT = "#2b6cb0"
NIGHT = "#5a67d8"
MUTED = "#9aa5b1"


def clean_durations(vol: pd.DataFrame) -> pd.Series:
    d = (vol["finished_at"] - vol["started_at"]).dt.total_seconds() / 60
    return d[d > 0]


def waves(vol: pd.DataFrame) -> pd.DataFrame:
    instants = vol["started_at"].drop_duplicates().sort_values().reset_index(drop=True)
    wave_of = (instants.diff() > GAP).cumsum()
    lookup = dict(zip(instants, wave_of))
    rows = vol.assign(wave_id=vol["started_at"].map(lookup))
    w = rows.groupby("wave_id").agg(start=("started_at", "min"), end=("finished_at", "max"))
    w["duration_min"] = (w["end"] - w["start"]).dt.total_seconds() / 60
    w["start_local"] = w["start"].dt.tz_convert(LOCAL)
    return w.sort_values("start").reset_index(drop=True)


def is_night(local_hour: pd.Series) -> pd.Series:
    return (local_hour >= NIGHT_START) | (local_hour < NIGHT_END)


def fig_duration(durations: pd.Series, path: Path) -> dict:
    bins = [0, 15, 30, 60, 120, 240, 1e9]
    labels = ["under 15 min", "15–30 min", "30–60 min", "1–2 hours", "2–4 hours", "over 4 hours"]
    shares = pd.cut(durations, bins=bins, labels=labels, right=False).value_counts(normalize=True).reindex(labels)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    bars = ax.bar(labels, shares.values * 100, color=ACCENT)
    for b, v in zip(bars, shares.values * 100):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.0f}%", ha="center", color=INK)
    ax.set_ylabel("Share of alerts (%)")
    ax.set_title("How long sirens lasted", loc="left", color=INK, fontweight="bold")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {label: round(float(v), 4) for label, v in shares.items()}


def fig_hour(starts_local: pd.Series, path: Path) -> dict:
    hour_share = starts_local.dt.hour.value_counts(normalize=True).reindex(range(24), fill_value=0) * 100
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    colors = [NIGHT if (h >= NIGHT_START or h < NIGHT_END) else ACCENT for h in range(24)]
    ax.bar(range(24), hour_share.values, color=colors)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hour of the day (Kyiv time)")
    ax.set_ylabel("Share of alert starts (%)")
    ax.set_title("When alerts start, by hour", loc="left", color=INK, fontweight="bold")
    ax.text(0.99, 0.95, "Dark bars: night, 22:00–07:00", transform=ax.transAxes, ha="right", va="top", color=NIGHT)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {str(h): round(float(v), 3) for h, v in hour_share.items()}


def fig_night_by_year(nights: pd.DataFrame, path: Path) -> dict:
    by_year = nights.groupby("year")["touched"].agg(["size", "mean"])
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(by_year.index, by_year["mean"] * 100, marker="o", color=NIGHT)
    for x, y, n in zip(by_year.index, by_year["mean"] * 100, by_year["size"]):
        ax.annotate(f"{y:.0f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", color=INK)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Nights with at least one alert (%)")
    ax.set_xlabel("Year")
    ax.set_title("Nights with an alert in the 22:00–07:00 window", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {str(y): {"nights": int(r["size"]), "share_touched": round(float(r["mean"]), 4)} for y, r in by_year.iterrows()}


def fig_alerts_per_day(per_day: pd.Series, path: Path) -> dict:
    capped = per_day.clip(upper=10)
    counts = capped.value_counts().sort_index().reindex(range(0, 11), fill_value=0)
    share = counts / counts.sum() * 100
    labels = [str(i) for i in range(0, 10)] + ["10+"]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar(labels, share.values, color=ACCENT)
    ax.set_xlabel("Separate alert waves in one day (30-minute gap)")
    ax.set_ylabel("Share of days (%)")
    ax.set_title("How many separate alert waves a day brings", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {
        "days": int(len(per_day)),
        "median": float(per_day.median()),
        "p90": float(per_day.quantile(0.9)),
        "share_no_wave": round(float((per_day == 0).mean()), 4),
        "share_3_or_more": round(float((per_day >= 3).mean()), 4),
    }


def main() -> None:
    _, vol = vadimkin.load_both(RAW_DIR)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    CHAPTER.parent.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    starts = vol.drop_duplicates("started_at")
    starts_local = starts["started_at"].dt.tz_convert(LOCAL)
    durations = clean_durations(vol)
    w = waves(vol)

    numbers = {
        "rows": int(len(vol)),
        "first_start_utc": str(vol["started_at"].min()),
        "last_start_utc": str(vol["started_at"].max()),
        "median_duration_min": round(float(durations.median()), 1),
        "p90_duration_min": round(float(durations.quantile(0.9)), 1),
        "share_under_30_min": round(float((durations < 30).mean()), 4),
        "share_over_60_min": round(float((durations > 60).mean()), 4),
        "share_over_180_min": round(float((durations > 180).mean()), 4),
        "night_start_share": round(float(is_night(starts_local.dt.hour).mean()), 4),
    }
    numbers["duration_bands"] = fig_duration(durations, FIG_DIR / "ch01_duration_bands.png")
    numbers["hour_share_pct"] = fig_hour(starts_local, FIG_DIR / "ch01_hour_of_day.png")

    # Nights: a local night starts at 22:00 on date D and runs to 07:00 on D+1.
    s = starts_local.to_frame("t")
    s["night_date"] = (s["t"] - pd.Timedelta(hours=NIGHT_END)).dt.date
    in_night = is_night(s["t"].dt.hour)
    touched = s[in_night].groupby("night_date").size()
    first_day, last_day = s["night_date"].min(), s["night_date"].max()
    all_nights = pd.Series(pd.date_range(first_day, last_day, freq="D").date)
    nights = pd.DataFrame({"night_date": all_nights})
    nights["touched"] = nights["night_date"].isin(touched.index)
    nights["year"] = pd.to_datetime(nights["night_date"]).dt.year
    numbers["nights_total"] = int(len(nights))
    numbers["nights_touched_share"] = round(float(nights["touched"].mean()), 4)
    numbers["nights_by_year"] = fig_night_by_year(nights, FIG_DIR / "ch01_nights_by_year.png")

    local_day = w["start_local"].dt.date
    per_day_raw = w.groupby(local_day).size()
    days = pd.Series(pd.date_range(local_day.min(), local_day.max(), freq="D").date)
    per_day = days.map(per_day_raw).fillna(0).astype(int)
    numbers["per_day"] = fig_alerts_per_day(per_day, FIG_DIR / "ch01_waves_per_day.png")
    numbers["waves_total"] = int(len(w))
    gaps = (w["start"].shift(-1) - w["end"]).dt.total_seconds().dropna() / 60
    gaps = gaps[gaps > 0]
    numbers["quiet_gap_median_min"] = round(float(gaps.median()), 1)
    numbers["quiet_gap_p10_min"] = round(float(gaps.quantile(0.1)), 1)

    (OUT_DIR / "chapter01_numbers.json").write_text(json.dumps(numbers, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in numbers.items() if k not in ("hour_share_pct",)}, indent=2, default=str))


if __name__ == "__main__":
    main()
