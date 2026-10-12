"""Chapter 3 analysis: waves and clusters of alerts.

A wave is a run of national start instants where each start is at most `gap` minutes after the
previous one (the same rule as scripts/alert_waves.py). Primary gap: 30 minutes. Sensitivity: 5 to 60.

Descriptive only. A wave is a grouping of recorded alerts, not an event with a known cause, a known
threat type or a known impact.

Writes:
  docs/chapters/figures/ch03_*.png
  output/analysis/chapter03_waves_gap30.csv   (one row per wave, gitignored)
  output/analysis/chapter03_numbers.json       (gitignored)
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
FIG_DIR = Path("docs/chapters/figures")
OUT_DIR = Path("output/analysis")
LOCAL = "Europe/Kyiv"
PRIMARY_GAP = 30
GAPS = [5, 10, 15, 30, 60]

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
INK = "#1f2933"
ACCENT = "#2b6cb0"
NIGHT = "#5a67d8"


def build_waves(vol: pd.DataFrame, gap_min: int) -> pd.DataFrame:
    rows = vol[["started_at", "finished_at", "region"]].copy()
    instants = rows["started_at"].drop_duplicates().sort_values().reset_index(drop=True)
    wave_of = (instants.diff() > pd.Timedelta(minutes=gap_min)).cumsum()
    rows["wave_id"] = rows["started_at"].map(dict(zip(instants, wave_of)))
    w = rows.groupby("wave_id").agg(
        start=("started_at", "min"),
        end=("finished_at", "max"),
        last_start=("started_at", "max"),
        oblasts=("region", "nunique"),
        records=("region", "size"),
    )
    w["duration_min"] = ((w["end"] - w["start"]).dt.total_seconds() / 60).clip(lower=0)
    w["spread_min"] = ((w["last_start"] - w["start"]).dt.total_seconds() / 60)
    w["start_local"] = w["start"].dt.tz_convert(LOCAL)
    return w.sort_values("start").reset_index(drop=True)


def fig_oblasts_per_wave(w: pd.DataFrame, path: Path) -> dict:
    capped = w["oblasts"].clip(upper=15)
    counts = capped.value_counts().sort_index().reindex(range(1, 16), fill_value=0)
    share = counts / counts.sum() * 100
    labels = [str(i) for i in range(1, 15)] + ["15+"]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar(labels, share.values, color=ACCENT)
    ax.set_xlabel("Oblasts in the wave")
    ax.set_ylabel("Share of waves (%)")
    ax.set_title("How many oblasts a wave touches", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {"single_oblast_share": round(float((w["oblasts"] == 1).mean()), 4)}


def fig_duration(w: pd.DataFrame, path: Path) -> dict:
    d = w["duration_min"]
    bins = [0, 30, 60, 120, 240, 480, 1440, 1e9]
    labels = ["under 30 min", "30–60 min", "1–2 h", "2–4 h", "4–8 h", "8–24 h", "over 24 h"]
    share = pd.cut(d, bins=bins, labels=labels, right=False).value_counts(normalize=True).reindex(labels) * 100
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    bars = ax.bar(labels, share.values, color=ACCENT)
    for b, v in zip(bars, share.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.0f}%", ha="center", color=INK, fontsize=8)
    ax.set_ylabel("Share of waves (%)")
    ax.set_title("How long a wave lasts from first to last alert", loc="left", color=INK, fontweight="bold")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {k: round(float(v), 2) for k, v in share.items()}


def fig_waves_per_year(w: pd.DataFrame, path: Path) -> dict:
    years = w["start_local"].dt.year
    per_year = w.groupby(years).agg(waves=("start", "size"), median_oblasts=("oblasts", "median"))
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.bar(per_year.index.astype(str), per_year["waves"], color=ACCENT)
    for x, n in zip(per_year.index.astype(str), per_year["waves"]):
        ax.text(x, n + 80, f"{n:,}", ha="center", color=INK, fontsize=8)
    ax.set_ylabel("Waves")
    ax.set_title("Waves per year (2026 is partial)", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {str(y): {"waves": int(r.waves), "median_oblasts": float(r.median_oblasts)} for y, r in per_year.iterrows()}


def sensitivity(vol: pd.DataFrame) -> list:
    rows = []
    for g in GAPS:
        w = build_waves(vol, g)
        rows.append({
            "gap_min": g,
            "waves": int(len(w)),
            "median_oblasts": float(w["oblasts"].median()),
            "p90_oblasts": float(w["oblasts"].quantile(0.9)),
            "median_duration_min": round(float(w["duration_min"].median()), 1),
            "share_over_6h": round(float((w["duration_min"] > 360).mean()), 4),
        })
    return rows


def main() -> None:
    _, vol = vadimkin.load_both(RAW_DIR)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    w = build_waves(vol, PRIMARY_GAP)
    w.to_csv(OUT_DIR / "chapter03_waves_gap30.csv", index=False)

    numbers = {
        "gap_min": PRIMARY_GAP,
        "waves": int(len(w)),
        "median_duration_min": round(float(w["duration_min"].median()), 1),
        "p90_duration_min": round(float(w["duration_min"].quantile(0.9)), 1),
        "median_spread_min": round(float(w["spread_min"].median()), 1),
        "p90_spread_min": round(float(w["spread_min"].quantile(0.9)), 1),
        "median_oblasts": float(w["oblasts"].median()),
        "p90_oblasts": float(w["oblasts"].quantile(0.9)),
        "p99_oblasts": float(w["oblasts"].quantile(0.99)),
        "max_oblasts": int(w["oblasts"].max()),
        "share_over_6h": round(float((w["duration_min"] > 360).mean()), 4),
        "longest_wave_hours": round(float(w["duration_min"].max()) / 60, 1),
        "sensitivity": sensitivity(vol),
    }
    numbers["oblasts_hist"] = fig_oblasts_per_wave(w, FIG_DIR / "ch03_oblasts_per_wave.png")
    numbers["duration_bands_pct"] = fig_duration(w, FIG_DIR / "ch03_wave_duration.png")
    numbers["per_year"] = fig_waves_per_year(w, FIG_DIR / "ch03_waves_per_year.png")

    biggest = w.nlargest(10, "oblasts")[["start_local", "oblasts", "records", "duration_min"]]
    numbers["largest_waves"] = [
        {"start_local": str(r.start_local), "oblasts": int(r.oblasts), "records": int(r.records),
         "duration_min": round(float(r.duration_min), 1)}
        for _, r in biggest.iterrows()
    ]
    (OUT_DIR / "chapter03_numbers.json").write_text(json.dumps(numbers, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in numbers.items() if k not in ("per_year",)}, indent=2, default=str))


if __name__ == "__main__":
    main()
