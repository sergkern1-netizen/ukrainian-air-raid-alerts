"""Chapter 4 analysis: how reliable the volunteer alert record is, measured against the official record.

Definitions (same as scripts/feed_integrity.py):
  Precision: share of volunteer alerts with ANY official alert (any level) in the same oblast within the tolerance.
  Recall: share of official oblast-level alerts with a volunteer alert in the same oblast within the tolerance.
  (Oblast-level official rows are almost absent after December 2025, so precision uses all levels.)
  The window starts on the official feed's first start (2022-03-15); earlier volunteer alerts cannot be matched.
  Lag: volunteer start minus nearest official start, for matched pairs (seconds).

Overlap window: up to the official feed's last start. Agreement is not accuracy: the official record is a
cross-check, not ground truth, and the volunteer record has no independent ground truth.

Writes:
  docs/chapters/figures/ch04_*.png
  output/analysis/chapter04_numbers.json   (gitignored)
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.feed_integrity import BREAK, MIN_ALERTS_FOR_RATE, nearest_match  # noqa: E402
from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
FIG_DIR = Path("docs/chapters/figures")
OUT_DIR = Path("output/analysis")
TOLERANCES_MIN = [1, 5, 10, 30]

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
INK = "#1f2933"
ACCENT = "#2b6cb0"
ORANGE = "#dd6b20"
MUTED = "#9aa5b1"


def precision(vol: pd.DataFrame, off: pd.DataFrame, tol: pd.Timedelta) -> pd.Series:
    m = nearest_match(vol, off, "region", "oblast", tol=tol)
    return m["other_start"].notna()


def recall(off: pd.DataFrame, vol: pd.DataFrame, tol: pd.Timedelta) -> pd.Series:
    m = nearest_match(off, vol, "oblast", "region", tol=tol)
    return m["other_start"].notna()


def fig_monthly(vol: pd.DataFrame, matched: pd.Series, path: Path) -> pd.DataFrame:
    d = pd.DataFrame({"t": vol["started_at"].dt.tz_convert(None), "m": matched.values})
    monthly = d.groupby(d["t"].dt.to_period("M")).agg(alerts=("m", "size"), share=("m", "mean"))
    monthly = monthly[monthly["alerts"] >= MIN_ALERTS_FOR_RATE]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    x = monthly.index.to_timestamp()
    ax.plot(x, monthly["share"] * 100, color=ACCENT, marker="o", ms=3)
    ax.axvline(BREAK.tz_convert(None), color=ORANGE, ls="--", lw=1)
    ax.text(BREAK.tz_convert(None), 95, " Dec 2025 break", color=ORANGE, va="top", fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Volunteer alerts matched (%)")
    ax.set_title("Monthly agreement with the official record", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return monthly


def fig_lag(lags: pd.Series, path: Path) -> dict:
    clipped = lags.clip(-300, 300)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.hist(clipped, bins=np.arange(-300, 301, 10), color=ACCENT)
    ax.axvline(0, color=INK, lw=1)
    ax.set_xlabel("Volunteer start minus official start (seconds; clipped at ±300)")
    ax.set_ylabel("Matched alerts")
    ax.set_title("How far apart matched start times are", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {
        "median_s": round(float(lags.median()), 1),
        "iqr_s": [round(float(lags.quantile(0.25)), 1), round(float(lags.quantile(0.75)), 1)],
        "share_within_60s": round(float((lags.abs() <= 60).mean()), 4),
    }


def fig_oblast_dumbbell(table: pd.DataFrame, path: Path) -> None:
    t = table.dropna(subset=["precision_pre", "precision_post"]).sort_values("precision_pre")
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    y = np.arange(len(t))
    ax.hlines(y, t["precision_post"] * 100, t["precision_pre"] * 100, color=MUTED, lw=2)
    ax.scatter(t["precision_pre"] * 100, y, color=ACCENT, label="Before Dec 2025", zorder=3)
    ax.scatter(t["precision_post"] * 100, y, color=ORANGE, label="From Dec 2025", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([x.replace(" oblast", "").replace("Kyiv City", "Kyiv city") for x in t.index], fontsize=8)
    ax.set_xlabel("Volunteer alerts matched (%)")
    ax.set_xlim(0, 100)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    ax.set_title("Agreement by oblast, before and after the break", loc="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    official, volunteer = vadimkin.load_both(RAW_DIR)
    end = official["started_at"].max()
    vol = volunteer[volunteer["started_at"] <= end].copy()
    official_start = official["started_at"].min()
    vol = vol[vol["started_at"] >= official_start].copy()
    off_all = official[official["started_at"] <= end].copy()
    off = off_all[off_all["level"] == "oblast"].copy()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tol5 = pd.Timedelta(minutes=5)
    matched = precision(vol, off_all, tol5)
    vol["matched"] = matched.values
    vol["period"] = np.where(vol["started_at"] >= BREAK, "post", "pre")

    off_m = recall(off, vol, tol5)
    off = off.assign(matched=off_m.values, period=np.where(off["started_at"] >= BREAK, "post", "pre"))

    six_before = vol.loc[(vol.started_at >= "2025-06-01") & (vol.started_at < BREAK), "matched"].mean()
    six_after = vol.loc[(vol.started_at >= BREAK) & (vol.started_at < "2026-06-01"), "matched"].mean()
    monthly_series = vol.set_index("started_at")["matched"].resample("MS").mean()
    trend_2023_2025 = np.polyfit(
        range(len(monthly_series["2023-01":"2025-11"])), monthly_series["2023-01":"2025-11"].values * 100, 1
    )[0] * 12

    numbers = {
        "window_start": str(official_start.date()),
        "window_end": str(end.date()),
        "step_test": {
            "six_months_before_break": round(float(six_before), 4),
            "six_months_after_break": round(float(six_after), 4),
        },
        "trend_2023_2025_pp_per_year": round(float(trend_2023_2025), 2),
        "volunteer_alerts_in_window": int(len(vol)),
        "official_oblast_alerts_in_window": int(len(off)),
        "precision_all": round(float(vol["matched"].mean()), 4),
        "precision_pre": round(float(vol.loc[vol.period == "pre", "matched"].mean()), 4),
        "precision_post": round(float(vol.loc[vol.period == "post", "matched"].mean()), 4),
        "recall_all": round(float(off["matched"].mean()), 4),
        "recall_pre": round(float(off.loc[off.period == "pre", "matched"].mean()), 4),
        "recall_post": round(float(off.loc[off.period == "post", "matched"].mean()), 4),
    }

    monthly = fig_monthly(vol, vol["matched"], FIG_DIR / "ch04_monthly_agreement.png")
    numbers["months_plotted"] = int(len(monthly))

    m_full = nearest_match(vol, off_all, "region", "oblast", tol=tol5)
    lags = m_full["lag_sec"].dropna()
    numbers["lag"] = fig_lag(lags, FIG_DIR / "ch04_lag_histogram.png")

    sens = []
    for t in TOLERANCES_MIN:
        tol = pd.Timedelta(minutes=t)
        p = precision(vol, off_all, tol).mean()
        r = recall(off, vol, tol).mean()
        sens.append({"tolerance_min": t, "precision": round(float(p), 4), "recall": round(float(r), 4)})
    numbers["tolerance_sensitivity"] = sens

    table = (
        vol.groupby(["region", "period"])["matched"].agg(["size", "mean"]).unstack("period")
    )
    table.columns = [f"{a}_{b}" for a, b in table.columns]
    table = table.rename(columns={
        "size_pre": "n_pre", "size_post": "n_post", "mean_pre": "precision_pre", "mean_post": "precision_post",
    })
    table["small_pre"] = table["n_pre"] < MIN_ALERTS_FOR_RATE
    table["small_post"] = table["n_post"] < MIN_ALERTS_FOR_RATE
    table = table.sort_values("n_pre", ascending=False)
    table.to_csv(OUT_DIR / "chapter04_by_oblast.csv")
    fig_oblast_dumbbell(table[(~table.small_pre) & (~table.small_post)], FIG_DIR / "ch04_agreement_by_oblast.png")
    numbers["oblasts_scored_both_periods"] = int(((~table.small_pre) & (~table.small_post)).sum())
    numbers["oblasts_dropping"] = int((table.dropna(subset=["precision_pre", "precision_post"])
                                       .loc[lambda x: (~x.small_pre) & (~x.small_post)]
                                       .eval("precision_pre > precision_post")).sum())

    (OUT_DIR / "chapter04_numbers.json").write_text(json.dumps(numbers, indent=2, default=str), encoding="utf-8")
    print(json.dumps(numbers, indent=2, default=str))


if __name__ == "__main__":
    main()
