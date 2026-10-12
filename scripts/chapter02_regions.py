"""Chapter 2 analysis: regional spread of alerts.

Data: volunteer alert record, after exact-duplicate drop. Oblast = the record's `region` field.
Descriptive only. Counts describe recorded alerts, not people affected or threats.

Writes:
  docs/chapters/02-regional-spread.md   (written by hand from the numbers below)
  docs/chapters/figures/ch02_*.png
  output/analysis/chapter02_region_table.csv   (gitignored)
  output/analysis/chapter02_numbers.json        (gitignored)
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
SMALL = 50

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
INK = "#1f2933"
ACCENT = "#2b6cb0"
NIGHT = "#5a67d8"
MUTED = "#9aa5b1"


def short(name: str) -> str:
    return name.replace(" oblast", "").replace("Kyiv City", "Kyiv city")


def region_table(vol: pd.DataFrame, total_days: int) -> pd.DataFrame:
    d = (vol["finished_at"] - vol["started_at"]).dt.total_seconds() / 60
    v = vol.assign(dur=d)
    v = v[v["dur"] > 0]
    local = v["started_at"].dt.tz_convert(LOCAL)
    v = v.assign(local_day=local.dt.date, night=(local.dt.hour >= 22) | (local.dt.hour < 7))
    g = v.groupby("region")
    t = pd.DataFrame({
        "alerts": g.size(),
        "median_min": g["dur"].median().round(1),
        "p90_min": g["dur"].quantile(0.9).round(1),
        "share_over_60_min": g["dur"].apply(lambda s: (s > 60).mean()).round(3),
        "night_share": g["night"].mean().round(3),
        "days_with_alert": g["local_day"].nunique(),
    })
    t["share_of_days_with_alert"] = (t["days_with_alert"] / total_days).round(3)
    t["share_of_all_alerts"] = (t["alerts"] / t["alerts"].sum()).round(4)
    return t.sort_values("alerts", ascending=False)


def fig_bar(t: pd.DataFrame, col: str, title: str, xlabel: str, path: Path, fmt: str) -> None:
    s = t.sort_values(col, ascending=True)
    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    colors = [MUTED if n < SMALL else ACCENT for n in s["alerts"]]
    bars = ax.barh([short(x) for x in s.index], s[col], color=colors)
    for b, v in zip(bars, s[col]):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2, " " + fmt.format(v), va="center", color=INK, fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_year_heatmap(vol: pd.DataFrame, path: Path) -> None:
    local = vol["started_at"].dt.tz_convert(LOCAL)
    d = pd.DataFrame({"region": vol["region"], "year": local.dt.year})
    pivot = d.groupby(["region", "year"]).size().unstack("year", fill_value=0)
    order = pivot.sum(axis=1).sort_values(ascending=False).index
    pivot = pivot.loc[order]
    fig, ax = plt.subplots(figsize=(7.5, 7))
    im = ax.imshow(pivot.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels([short(x) for x in pivot.index], fontsize=8)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:,}", ha="center", va="center", fontsize=6.5,
                    color="white" if val > pivot.values.max() * 0.55 else INK)
    ax.set_title("Recorded alerts by oblast and year", loc="left", color=INK, fontweight="bold")
    ax.spines[:].set_visible(False)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Alerts")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    _, vol = vadimkin.load_both(RAW_DIR)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    local_days = vol["started_at"].dt.tz_convert(LOCAL).dt.date
    total_days = (pd.Timestamp(local_days.max()) - pd.Timestamp(local_days.min())).days + 1
    t = region_table(vol, total_days)
    t.to_csv(OUT_DIR / "chapter02_region_table.csv")

    fig_bar(t, "alerts", "Recorded alerts by oblast (all years)", "Alerts", FIG_DIR / "ch02_alerts_by_oblast.png", "{:,.0f}")
    fig_bar(t, "share_of_days_with_alert", "Share of days with at least one alert", "Share of days", FIG_DIR / "ch02_days_with_alert.png", "{:.0%}")
    fig_bar(t, "median_min", "Median alert duration by oblast", "Minutes", FIG_DIR / "ch02_median_duration.png", "{:.0f}")
    fig_year_heatmap(vol, FIG_DIR / "ch02_heatmap_by_year.png")

    numbers = {
        "oblasts": int(len(t)),
        "total_days": int(total_days),
        "top5_share_of_alerts": round(float(t["share_of_all_alerts"].head(5).sum()), 4),
        "top10_share_of_alerts": round(float(t["share_of_all_alerts"].head(10).sum()), 4),
        "small_sample_oblasts": [short(x) for x in t.index[t["alerts"] < SMALL]],
        "rows": t.reset_index().to_dict(orient="records"),
    }
    (OUT_DIR / "chapter02_numbers.json").write_text(json.dumps(numbers, indent=2, default=str), encoding="utf-8")
    print(t.to_string())
    print("top5 share", numbers["top5_share_of_alerts"], "top10 share", numbers["top10_share_of_alerts"])


if __name__ == "__main__":
    main()
