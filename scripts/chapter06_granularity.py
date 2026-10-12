"""Chapter 6 analysis: granularity of the official feed and what the December 2025 change does to counts.

Official rows carry a `level` (oblast, raion, hromada). From 2025-12-01 (UTC, by started_at) the feed
moved almost entirely to raion-level rows. This script measures:

  1. Official records by level and month (2022-03 to 2026-09). Figure.
  2. Granularity: for each official (oblast, started_at) instant, how many raion records share it.
  3. Hromada records: share and period.
  4. Name check: oblast names per period, Kyiv City, last official row for Luhanska oblast.
  5. Matching: volunteer alerts matched within 5 minutes using (a) oblast-level official rows only and
     (b) all official levels, by period, inside the official coverage window (2022-03-15 to 2026-09-07).
     Matches are cross-checked against an independent searchsorted implementation.
  6. Count inflation: official records per volunteer alert, records per oblast per day, and median
     records per event (event = one oblast + started_at instant). Figure.
  7. Every number above in output/analysis/chapter06_numbers.json.

Descriptive only. Nothing here says anything about threats or about which feed is correct.

Writes:
  output/analysis/chapter06_levels_by_month.csv   (gitignored)
  output/analysis/chapter06_numbers.json          (gitignored)
  docs/chapters/figures/ch06_levels_by_month.png
  docs/chapters/figures/ch06_records_per_event.png
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.feed_integrity import nearest_match  # noqa: E402
from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
FIG_DIR = Path("docs/chapters/figures")
OUT_DIR = Path("output/analysis")
OUT_JSON = OUT_DIR / "chapter06_numbers.json"
OUT_MONTHLY = OUT_DIR / "chapter06_levels_by_month.csv"

BREAK = pd.Timestamp("2025-12-01", tz="UTC")
WINDOW_START = pd.Timestamp("2022-03-15", tz="UTC")
WINDOW_END_EXCL = pd.Timestamp("2026-09-08", tz="UTC")  # official feed ends on 2026-09-07
TOLERANCE = pd.Timedelta(minutes=5)
LEVELS = ["oblast", "raion", "hromada"]
KNOWN = {
    "pre": {"oblast": 64842, "raion": 19324, "hromada": 14787},
    "post": {"raion": 79980, "hromada": 6025, "oblast": 472},
    "pre_names": 25,
    "post_names": 24,
}
EPOCH = pd.Timestamp(0, tz="UTC")

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
INK = "#1f2933"
MUTED = "#9aa5b1"
LEVEL_COLORS = {"oblast": "#2b6cb0", "raion": "#dd6b20", "hromada": "#38a169"}


def period_label(ts: pd.Series) -> pd.Series:
    return ts.ge(BREAK).map({False: "pre", True: "post"})


def seconds(s: pd.Series) -> np.ndarray:
    return (s - EPOCH).dt.total_seconds().to_numpy()


def brute_match(left: pd.DataFrame, right: pd.DataFrame, left_name: str, right_name: str) -> pd.Series:
    """Independent check: same-oblast start within TOLERANCE via searchsorted, not merge_asof."""
    out = pd.Series(False, index=left.index)
    tol = TOLERANCE.total_seconds()
    for oblast, grp in left.groupby(left_name):
        ref = right.loc[right[right_name] == oblast, "started_at"].sort_values()
        if ref.empty:
            continue
        arr = seconds(ref)
        t = seconds(grp["started_at"])
        idx = np.searchsorted(arr, t)
        lo = np.clip(idx - 1, 0, len(arr) - 1)
        hi = np.clip(idx, 0, len(arr) - 1)
        close = (np.abs(arr[lo] - t) <= tol) | (np.abs(arr[hi] - t) <= tol)
        out.loc[grp.index] = close
    return out


def match_rate(vol: pd.DataFrame, off: pd.DataFrame) -> dict:
    """Matched share of volunteer alerts by period, using nearest_match, with a brute-force cross-check."""
    m = nearest_match(vol, off, "region", "oblast", tol=TOLERANCE)["other_start"].notna().reindex(vol.index)
    m = m.fillna(False).astype(bool)
    check = brute_match(vol, off, "region", "oblast")
    result = {"nearest_match_vs_bruteforce_disagreements": int((m != check).sum())}
    for per in ["pre", "post", "all"]:
        sel = vol.index if per == "all" else vol.index[period_label(vol["started_at"]) == per]
        result[per] = {"volunteer_alerts": int(len(sel)), "matched": int(m.loc[sel].sum()),
                       "matched_share": round(float(m.loc[sel].mean()), 4) if len(sel) else None}
    return result


def main() -> None:
    official, volunteer = vadimkin.load_both(RAW_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    numbers: dict = {"break_utc": str(BREAK.date()), "known_facts_checked": {}}

    off = official.copy()
    off["period"] = period_label(off["started_at"])
    numbers["official_rows"] = int(len(off))
    numbers["official_span"] = [str(off["started_at"].min()), str(off["started_at"].max())]

    # 1. Levels by period and month
    by_period = off.groupby(["period", "level"]).size().unstack(fill_value=0)
    numbers["levels_by_period"] = {p: {lv: int(by_period.loc[p, lv]) for lv in LEVELS} for p in ["pre", "post"]}
    numbers["known_facts_checked"]["levels_by_period_match"] = all(
        numbers["levels_by_period"][p][lv] == KNOWN[p][lv] for p in ["pre", "post"] for lv in LEVELS
    )

    off["month"] = off["started_at"].dt.tz_convert("UTC").dt.tz_localize(None).dt.to_period("M")
    months = pd.period_range("2022-03", "2026-09", freq="M")
    monthly = off.groupby(["month", "level"]).size().unstack(fill_value=0).reindex(months, fill_value=0)
    for lv in LEVELS:
        if lv not in monthly.columns:
            monthly[lv] = 0
    monthly = monthly[LEVELS]
    monthly.index.name = "month"
    monthly.to_csv(OUT_MONTHLY)

    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(monthly))
    bottom = np.zeros(len(monthly))
    for lv in LEVELS:
        vals = monthly[lv].to_numpy()
        ax.bar(x, vals, bottom=bottom, color=LEVEL_COLORS[lv], width=0.85, label=lv, linewidth=0)
        bottom += vals
    brk = list(monthly.index).index(pd.Period("2025-12", freq="M"))
    ax.axvline(brk - 0.5, color=INK, lw=1, ls="--")
    ax.text(brk - 0.6, ax.get_ylim()[1] * 0.97, "1 Dec 2025 (raion share already rising from May 2025)", fontsize=8, color=INK, va="top", ha="right")
    ticks = [i for i, m in enumerate(monthly.index) if m.month in (1, 7)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(monthly.index[i]) for i in ticks], rotation=0, fontsize=8)
    ax.set_ylabel("Official records per month")
    ax.set_title("Official records by level and month, 2022-03 to 2026-09", loc="left", color=INK)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "ch06_levels_by_month.png")
    plt.close(fig)

    # 2. Granularity: raion records sharing one (oblast, started_at) instant
    inst = off.groupby(["oblast", "started_at"]).agg(
        n_all=("level", "size"),
        n_raion=("level", lambda s: int((s == "raion").sum())),
        period=("period", "first"),
    ).reset_index()
    gran = {}
    for per in ["pre", "post"]:
        s = inst[inst["period"] == per]
        with_raion = s[s["n_raion"] > 0]
        gran[per] = {
            "instants": int(len(s)),
            "raion_per_instant_median": float(s["n_raion"].median()),
            "raion_per_instant_p90": float(s["n_raion"].quantile(0.9)),
            "share_instants_with_raion": round(float((s["n_raion"] > 0).mean()), 4),
            "instants_with_raion": int(len(with_raion)),
            "raion_per_raion_instant_median": float(with_raion["n_raion"].median()) if len(with_raion) else None,
            "raion_per_raion_instant_p90": float(with_raion["n_raion"].quantile(0.9)) if len(with_raion) else None,
            "all_records_per_instant_median": float(s["n_all"].median()),
            "all_records_per_instant_p90": float(s["n_all"].quantile(0.9)),
        }
    numbers["granularity"] = gran

    # 3. Hromada share
    numbers["hromada"] = {
        "share_all": round(float((off["level"] == "hromada").mean()), 4),
        "share_by_period": {p: round(float((off.loc[off["period"] == p, "level"] == "hromada").mean()), 4)
                            for p in ["pre", "post"]},
        "rows_by_period": {p: int((off.loc[off["period"] == p, "level"] == "hromada").sum()) for p in ["pre", "post"]},
        "first_row": str(off.loc[off["level"] == "hromada", "started_at"].min()),
        "rows_by_year": {str(y): int(n) for y, n in off[off["level"] == "hromada"].groupby(off["started_at"].dt.year).size().items()},
    }

    # 4. Name check
    names = {p: sorted(off.loc[off["period"] == p, "oblast"].unique()) for p in ["pre", "post"]}
    lug = off.loc[off["oblast"] == "Luhanska oblast", "started_at"]
    kyiv_city = off[off["oblast"] == "Kyiv City"]
    kyiv_2026 = kyiv_city[kyiv_city["started_at"].dt.year == 2026]
    numbers["names"] = {
        "count_pre": len(names["pre"]),
        "count_post": len(names["post"]),
        "pre_only": sorted(set(names["pre"]) - set(names["post"])),
        "post_only": sorted(set(names["post"]) - set(names["pre"])),
        "all_names_count": int(off["oblast"].nunique()),
        "volunteer_region_names_not_in_official": sorted(set(volunteer["region"].dropna()) - set(off["oblast"].dropna())),
        "luhanska_first_row": str(lug.min()) if len(lug) else None,
        "luhanska_last_row": str(lug.max()) if len(lug) else None,
        "kyiv_city_rows_by_level_and_period": {
            p: {lv: int(n) for lv, n in kyiv_city[kyiv_city["period"] == p].groupby("level").size().items()}
            for p in ["pre", "post"]
        },
        "kyiv_city_rows_2026": int(len(kyiv_2026)),
        "kyiv_city_rows_2026_level": {lv: int(n) for lv, n in kyiv_2026.groupby("level").size().items()},
        "kyiv_city_post_break_first_row": str(kyiv_city.loc[kyiv_city["period"] == "post", "started_at"].min()),
    }
    numbers["known_facts_checked"]["names_25_24"] = (
        numbers["names"]["count_pre"] == KNOWN["pre_names"] and numbers["names"]["count_post"] == KNOWN["post_names"]
    )
    numbers["known_facts_checked"]["kyiv_city_2026_448"] = numbers["names"]["kyiv_city_rows_2026"] == 448

    # 5. Matching (volunteer alerts inside the official coverage window)
    vol = volunteer[(volunteer["started_at"] >= WINDOW_START) & (volunteer["started_at"] < WINDOW_END_EXCL)].copy()
    tail = volunteer[(volunteer["started_at"] > off["started_at"].max()) & (volunteer["started_at"] < WINDOW_END_EXCL)]
    numbers["window"] = {
        "start": str(WINDOW_START.date()),
        "end_inclusive": "2026-09-07",
        "volunteer_alerts_in_window": int(len(vol)),
        "volunteer_alerts_after_last_official_start_inside_window": int(len(tail)),
    }
    vol_p = vol.copy()
    off_oblast = off[off["level"] == "oblast"]
    numbers["matching"] = {
        "a_oblast_level_only": match_rate(vol_p, off_oblast),
        "b_all_levels": match_rate(vol_p, off),
    }
    numbers["matching"]["note"] = (
        "Oblast-level official rows after 2025-12-01 are Kyiv City only, so (a) post-break measures Kyiv City alone."
    )
    post_oblast_names = sorted(off_oblast.loc[off_oblast["period"] == "post", "oblast"].unique())
    numbers["matching"]["oblast_level_names_post"] = post_oblast_names

    # 6. Count inflation
    evt_size = off.groupby(["oblast", "started_at"]).size().rename("n").reset_index()
    evt_size["period"] = period_label(evt_size["started_at"])
    off_day = off.assign(day=off["started_at"].dt.tz_convert("UTC").dt.date)
    per_oblast_day = off_day.groupby(["oblast", "day"]).size()
    def period_stats(start: pd.Timestamp, end: pd.Timestamp) -> dict:
        in_p = (off["started_at"] >= start) & (off["started_at"] < end)
        days = (end - start).days
        n_rows = int(in_p.sum())
        n_names = int(off.loc[in_p, "oblast"].nunique())
        n_vol = int(((vol["started_at"] >= start) & (vol["started_at"] < end)).sum())
        ev = evt_size[(evt_size["started_at"] >= start) & (evt_size["started_at"] < end)]
        e = ev["n"]
        per_oblast_day_in = per_oblast_day[
            (pd.to_datetime(per_oblast_day.index.get_level_values("day")) >= start.tz_localize(None))
            & (pd.to_datetime(per_oblast_day.index.get_level_values("day")) < end.tz_localize(None))
        ]
        return {
            "days": days,
            "official_rows": n_rows,
            "oblast_names_in_period": n_names,
            "volunteer_alerts": n_vol,
            "official_rows_per_volunteer_alert": round(n_rows / n_vol, 3),
            "official_rows_per_oblast_per_day": round(n_rows / (days * n_names), 3),
            "oblast_day_median_rows": float(per_oblast_day_in.median()),
            "oblast_day_p90_rows": float(per_oblast_day_in.quantile(0.9)),
            "events": int(len(e)),
            "records_per_event_median": float(e.median()),
            "records_per_event_p90": float(e.quantile(0.9)),
            "records_per_event_mean": round(float(e.mean()), 3),
        }

    infl = {}
    for per in ["pre", "post"]:
        start, end = (WINDOW_START, BREAK) if per == "pre" else (BREAK, WINDOW_END_EXCL)
        infl[per] = period_stats(start, end)
    # Sensitivity: the raion share starts rising in May 2025 and jumps Aug-Nov 2025, so the
    # pre-break baseline is also taken as 2024-01-01 to 2025-07-31, which excludes that transition.
    infl["pre_clean_2024_01_to_2025_07"] = period_stats(pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-08-01", tz="UTC"))
    numbers["inflation"] = infl
    numbers["raion_share_by_month"] = {
        str(m): round(float(r), 4)
        for m, r in (monthly["raion"] / monthly.sum(axis=1)).loc["2024-01":"2026-09"].items()
    }
    ratio_pre = infl["pre"]["official_rows_per_oblast_per_day"]
    ratio_post = infl["post"]["official_rows_per_oblast_per_day"]
    numbers["inflation"]["post_over_pre_rows_per_oblast_per_day"] = round(ratio_post / ratio_pre, 3)
    numbers["inflation"]["post_over_pre_rows_per_volunteer_alert"] = round(
        infl["post"]["official_rows_per_volunteer_alert"] / infl["pre"]["official_rows_per_volunteer_alert"], 3)

    fig, ax = plt.subplots(figsize=(6, 4.2))
    labels = ["Before 2025-12-01", "From 2025-12-01"]
    med = [infl["pre"]["records_per_event_median"], infl["post"]["records_per_event_median"]]
    p90 = [infl["pre"]["records_per_event_p90"], infl["post"]["records_per_event_p90"]]
    x = np.arange(len(labels))
    w = 0.34
    bars_m = ax.bar(x - w / 2, med, w, color=[MUTED, LEVEL_COLORS["raion"]], label="median")
    bars_p = ax.bar(x + w / 2, p90, w, color="white", edgecolor=[MUTED, LEVEL_COLORS["raion"]], hatch="//", label="90th percentile")
    for bars in (bars_m, bars_p):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"{b.get_height():g}", ha="center", color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Official records per event")
    ax.set_title("Records per event (oblast + start instant)", loc="left", color=INK, fontsize=10)
    ax.set_ylim(0, max(p90) * 1.25)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "ch06_records_per_event.png")
    plt.close(fig)

    numbers["granularity_and_levels_note"] = (
        "Event = one oblast with one started_at instant in the official feed. Median records per event "
        "shows how many official rows one siren event becomes."
    )
    OUT_JSON.write_text(json.dumps(numbers, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MONTHLY}")
    print("levels by period:", numbers["levels_by_period"])
    print("known facts:", numbers["known_facts_checked"])
    print("granularity:", json.dumps(gran, indent=1))
    print("matching:", json.dumps(numbers["matching"], indent=1, default=str))
    print("inflation:", json.dumps(infl, indent=1))


if __name__ == "__main__":
    main()
