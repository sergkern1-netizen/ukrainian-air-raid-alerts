"""Chapter 8: reporting patterns behind the western-match and exact-second batching findings.

Descriptive only. The dataset has no message IDs, so the cause of exact-second batching cannot be
determined from these data. No reporting cause is asserted here.

Window: official coverage, 2022-03-15 to the official feed's last start (2026-09-07 05:28 UTC).
Matching: a volunteer alert is matched if any official alert (all levels) in the same oblast starts
within 5 minutes. Lag is volunteer start minus nearest official start.

Writes:
  output/analysis/chapter08_numbers.json
  output/analysis/chapter08_pair_batching.csv
  output/analysis/chapter08_precision_by_oblast_year.csv
  output/analysis/chapter08_batching_monthly.csv
  docs/chapters/figures/ch08_west_vs_rest_by_year.png
  docs/chapters/figures/ch08_batching_pairs.png
  docs/chapters/figures/ch08_batching_monthly.png
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.feed_integrity import nearest_match  # noqa: E402
from scripts.western_cluster_check import WESTERN, jaccard_table, oblast_wave_pairs  # noqa: E402
from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
OUT_DIR = Path("output/analysis")
FIG_DIR = Path("docs/chapters/figures")
JSON_OUT = OUT_DIR / "chapter08_numbers.json"
PAIR_CSV = OUT_DIR / "chapter08_pair_batching.csv"
YEAR_OBLAST_CSV = OUT_DIR / "chapter08_precision_by_oblast_year.csv"
MONTHLY_CSV = OUT_DIR / "chapter08_batching_monthly.csv"

WINDOW_START = pd.Timestamp("2022-03-15", tz="UTC")
BREAK = pd.Timestamp("2025-12-01", tz="UTC")
KP = ("Kirovohradska oblast", "Poltavska oblast")
MIN_SHARED = 50
MIN_KIRO_STARTS_FOR_PLOT = 20

# Palette: first two slots of the reference categorical palette (palette.md, light mode).
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#8a8984"
TEXT, GRID = "#0b0b0b", "#e4e3df"


def style_axes(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TEXT, labelsize=9)


def clean(obj):
    """Convert numpy/pandas values to JSON-safe Python types (NaN becomes null)."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def starts_by_oblast(df: pd.DataFrame, col: str) -> dict:
    """Distinct start instants per oblast."""
    d = df[[col, "started_at"]].drop_duplicates()
    return {k: set(v) for k, v in d.groupby(col)["started_at"]}


def instant_batching(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """One row per (oblast, exact start second); flags whether another oblast starts that second."""
    d = df[[col, "started_at"]].drop_duplicates().copy()
    d["n_oblasts"] = d.groupby("started_at")[col].transform("size")
    d["batched"] = d["n_oblasts"] > 1
    return d


def jaccard_western_means(vol: pd.DataFrame, off_oblast: pd.DataFrame) -> dict:
    vw, vp = oblast_wave_pairs(vol, "region")
    ow, op = oblast_wave_pairs(off_oblast, "oblast")
    vj, oj = jaccard_table(vw, vp), jaccard_table(ow, op)

    def west(t: pd.DataFrame) -> pd.DataFrame:
        return t[t["oblast_a"].isin(WESTERN) & t["oblast_b"].isin(WESTERN)]

    wv, wo = west(vj), west(oj)
    return {
        "volunteer_mean": round(float(wv["jaccard"].mean()), 3),
        "volunteer_pairs": int(len(wv)),
        "official_mean": round(float(wo["jaccard"].mean()), 3),
        "official_pairs": int(len(wo)),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    official, volunteer = vadimkin.load_both(RAW_DIR)

    end = official["started_at"].max()
    print(f"Window: {WINDOW_START.date()} to {end.isoformat()} (official last start)")

    off_all = official[(official["started_at"] >= WINDOW_START) & (official["started_at"] <= end)].copy()
    off_oblast = off_all[off_all["level"] == "oblast"].copy()
    vol = volunteer[(volunteer["started_at"] >= WINDOW_START) & (volunteer["started_at"] <= end)]
    vol = vol.reset_index(drop=True)

    vol["group"] = np.where(vol["region"].isin(WESTERN), "western", "rest")
    vol["year"] = vol["started_at"].dt.year
    vol["month"] = vol["started_at"].dt.tz_convert(None).dt.to_period("M")
    vol["pre_break"] = vol["started_at"] < BREAK

    m = nearest_match(vol, off_all, "region", "oblast")
    vol["matched"] = m["other_start"].notna().values
    vol["lag_sec"] = m["lag_sec"].values
    print(f"Volunteer alerts in window: {len(vol):,}; official rows: {len(off_all):,} "
          f"(oblast-level {len(off_oblast):,})")

    numbers: dict = {
        "window": {
            "start": WINDOW_START.isoformat(),
            "end": end.isoformat(),
            "volunteer_alerts": int(len(vol)),
            "official_rows_all_levels": int(len(off_all)),
            "official_rows_oblast": int(len(off_oblast)),
        }
    }

    # --- Check of the known Jaccard facts, with the same windows the existing script uses ---
    vol_script = volunteer[volunteer["started_at"] <= end]
    off_script = official[(official["level"] == "oblast") & (official["started_at"] <= end)]
    numbers["check_western_jaccard"] = {
        "window_as_in_western_cluster_check": jaccard_western_means(vol_script, off_script),
        "window_from_2022_03_15": jaccard_western_means(vol, off_oblast),
    }

    # --- 1. Precision by year, western vs rest ---
    year_group = vol.groupby(["group", "year"]).agg(
        volunteer_alerts=("matched", "size"), matched_share=("matched", "mean")
    ).reset_index()
    per_oblast = vol.groupby(["region", "year"]).agg(
        volunteer_alerts=("matched", "size"), matched_share=("matched", "mean")
    ).reset_index()
    per_oblast.to_csv(YEAR_OBLAST_CSV, index=False)

    prepost = vol[vol["region"].isin(["Lvivska oblast", "Volynska oblast"])].groupby(
        ["region", "pre_break"]).agg(volunteer_alerts=("matched", "size"), matched_share=("matched", "mean"))
    numbers["1_precision_by_year"] = {
        "definition": "volunteer alerts matched to any official alert (all levels) within 5 min",
        "period": f"{WINDOW_START.date()} to {end.date()}",
        "by_group_year": year_group.round(4).to_dict("records"),
        "western_oblasts": sorted(WESTERN),
        "lvivska_volynska_pre_post_break": [
            {"region": r, "period": "before 2025-12-01" if pb else "from 2025-12-01",
             "volunteer_alerts": int(row.volunteer_alerts), "matched_share": round(float(row.matched_share), 4)}
            for (r, pb), row in prepost.iterrows()
        ],
        "per_oblast_year_csv": str(YEAR_OBLAST_CSV),
    }

    fig, ax = plt.subplots(figsize=(8, 4.2))
    style_axes(ax)
    for grp, colour, label in [("western", BLUE, "Western 8 oblasts"), ("rest", ORANGE, "Other 17 oblasts")]:
        sub = year_group[year_group["group"] == grp]
        ax.plot(sub["year"], sub["matched_share"] * 100, color=colour, linewidth=2, marker="o", label=label)
    ax.set_xticks(sorted(vol["year"].unique()))
    ax.set_xticklabels([f"{y}*" if y in (2022, 2026) else str(y) for y in sorted(vol["year"].unique())])
    ax.set_ylabel("Volunteer alerts matched within 5 min (%)", color=TEXT)
    ax.set_ylim(0, 100)
    ax.set_title("Volunteer alerts matched to an official alert, by year", loc="left", color=TEXT, fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    fig.text(0.01, 0.01, "* partial year: 2022 from 15 Mar, 2026 to 7 Sep. Pooled over alerts in each group.",
             fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_DIR / "ch08_west_vs_rest_by_year.png", dpi=150)
    plt.close(fig)

    # --- 2. Shared starts by ordered oblast pair: volunteer vs official (oblast-level) ---
    vol_sets = starts_by_oblast(vol, "region")
    off_sets = starts_by_oblast(off_oblast, "oblast")
    names = sorted(set(vol_sets) | set(off_sets))
    rows = []
    for a in names:
        va, oa = vol_sets.get(a, set()), off_sets.get(a, set())
        for b in names:
            if a == b:
                continue
            vs = len(va & vol_sets.get(b, set()))
            os_ = len(oa & off_sets.get(b, set()))
            vsh = vs / len(va) if va else np.nan
            osh = os_ / len(oa) if oa else np.nan
            rows.append({
                "oblast_a": a, "oblast_b": b,
                "volunteer_starts_a": len(va), "volunteer_shared": vs, "volunteer_share": vsh,
                "official_starts_a": len(oa), "official_shared": os_, "official_share": osh,
                "difference": vsh - osh, "scored": vs >= MIN_SHARED,
            })
    pairs = pd.DataFrame(rows).sort_values("difference", ascending=False)
    pairs.to_csv(PAIR_CSV, index=False)
    scored = pairs[pairs["scored"]]
    top = scored.head(15)

    numbers["2_pair_batching"] = {
        "definition": ("share of oblast A's start instants at which oblast B also starts in the same second; "
                       "difference = volunteer share minus official oblast-level share"),
        "period": f"{WINDOW_START.date()} to {end.date()}",
        "min_volunteer_shared_starts": MIN_SHARED,
        "pairs_total_ordered": int(len(pairs)),
        "pairs_scored": int(len(scored)),
        "top_by_difference_scored": clean(top.to_dict("records")),
        "full_table_csv": str(PAIR_CSV),
    }

    fig, ax = plt.subplots(figsize=(8.5, 6))
    style_axes(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    short = lambda s: s.replace(" oblast", "").replace("Kyiv City", "Kyiv city")  # noqa: E731
    labels = [f"{short(r.oblast_a)} to {short(r.oblast_b)} (n={r.volunteer_shared})" for r in top.itertuples()]
    y = np.arange(len(top))[::-1]
    ax.barh(y, top["difference"] * 100, color=BLUE, height=0.6)
    for yi, r in zip(y, top.itertuples()):
        ax.text(r.difference * 100 + 0.3, yi, f"vol {r.volunteer_share*100:.1f}%, off {r.official_share*100:.1f}%",
                va="center", fontsize=7.5, color=TEXT)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("Volunteer minus official share of starts in the same second (percentage points)", color=TEXT)
    ax.set_xlim(0, top["difference"].max() * 100 * 1.45)
    ax.set_title(f"Top {len(top)} scored oblast pairs by excess same-second shared starts (volunteer feed)",
                 loc="left", color=TEXT, fontsize=11)
    fig.text(0.01, 0.01, "Direction A to B: share of A's starts that coincide with a B start. "
             f"Pairs with at least {MIN_SHARED} volunteer shared starts. Window {WINDOW_START.date()} to {end.date()}.",
             fontsize=7.5, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG_DIR / "ch08_batching_pairs.png", dpi=150)
    plt.close(fig)

    # --- 3. Shared starts over time: all oblasts, and Kirovohradska with Poltavska ---
    vol_inst = instant_batching(vol, "region")
    vol_inst["month"] = vol_inst["started_at"].dt.tz_convert(None).dt.to_period("M")
    all_m = vol_inst.groupby("month")["batched"].agg(oblast_starts="size", batched_share="mean")

    kp_rows = vol[vol["region"].isin(KP)][["region", "started_at"]].drop_duplicates()
    kiro = kp_rows[kp_rows["region"] == KP[0]].copy()
    polt_instants = set(kp_rows.loc[kp_rows["region"] == KP[1], "started_at"])
    kiro["with_poltava"] = kiro["started_at"].isin(polt_instants)
    kiro["month"] = kiro["started_at"].dt.tz_convert(None).dt.to_period("M")
    kiro["pre_break"] = kiro["started_at"] < BREAK
    kp_m = kiro.groupby("month")["with_poltava"].agg(kiro_starts="size", kiro_with_poltava_share="mean")

    monthly = all_m.join(kp_m, how="outer")
    monthly.index = monthly.index.astype(str)
    monthly.round(4).to_csv(MONTHLY_CSV)

    kp_pp = kiro.groupby("pre_break")["with_poltava"].agg(kiro_starts="size", same_minute="sum", share="mean")
    kp_pp_out = {("before 2025-12-01" if pb else "from 2025-12-01"): {
        "kiro_starts": int(r.kiro_starts), "same_minute": int(r.same_minute), "share": round(float(r.share), 4)}
        for pb, r in kp_pp.iterrows()}

    # Official oblast-level comparison for the same pair
    off_inst = instant_batching(off_oblast, "oblast")
    off_kp = off_oblast[off_oblast["oblast"].isin(KP)][["oblast", "started_at"]].drop_duplicates()
    off_polt = set(off_kp.loc[off_kp["oblast"] == KP[1], "started_at"])
    off_kiro = off_kp[off_kp["oblast"] == KP[0]]
    off_kp_share = float(off_kiro["started_at"].isin(off_polt).mean())
    off_post_break_rows = int((off_oblast["started_at"] >= BREAK).sum())
    off_post_break_kp = int(((off_oblast["started_at"] >= BREAK) & off_oblast["oblast"].isin(KP)).sum())

    # Reconciliation with scripts/pair_gap_investigation.py (its window has no start filter)
    vol_pg = volunteer[volunteer["started_at"] <= end]
    off_pg = official[(official["level"] == "oblast") & (official["started_at"] <= end)]

    numbers["3_batching_over_time"] = {
        "definition_all": "share of (oblast, exact second) volunteer starts where another oblast also starts that second",
        "period": f"{WINDOW_START.date()} to {end.date()}",
        "overall_volunteer_share": round(float(vol_inst["batched"].mean()), 4),
        "overall_volunteer_starts": int(len(vol_inst)),
        "overall_official_oblast_share": round(float(off_inst["batched"].mean()), 4),
        "overall_official_oblast_starts": int(len(off_inst)),
        "overall_no_start_filter_volunteer_share": round(float(instant_batching(vol_pg, "region")["batched"].mean()), 4),
        "overall_no_start_filter_official_share": round(float(instant_batching(off_pg, "oblast")["batched"].mean()), 4),
        "kiro_poltava_definition": "share of Kirovohradska starts with a Poltavska start in the same second",
        "kiro_poltava_pre_post_break_volunteer": kp_pp_out,
        "kiro_poltava_official_share_overall": round(off_kp_share, 4),
        "kiro_poltava_official_kiro_starts": int(len(off_kiro)),
        "official_oblast_rows_from_2025_12_01": off_post_break_rows,
        "official_kp_rows_from_2025_12_01": off_post_break_kp,
        "monthly_csv": str(MONTHLY_CSV),
    }

    x = pd.PeriodIndex(monthly.index, freq="M").to_timestamp()
    kp_plot = np.where(monthly["kiro_starts"].fillna(0) >= MIN_KIRO_STARTS_FOR_PLOT,
                       monthly["kiro_with_poltava_share"] * 100, np.nan)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    style_axes(ax)
    ax.plot(x, monthly["batched_share"] * 100, color=BLUE, linewidth=1.8, marker="o", markersize=3,
            label="All oblasts: starts sharing a second with another oblast")
    ax.plot(x, kp_plot, color=ORANGE, linewidth=1.8, marker="o", markersize=3,
            label="Kirovohradska starts sharing a second with Poltavska")
    ax.axvline(BREAK.tz_convert(None), color=GREY, linestyle="--", linewidth=1)
    ax.text(BREAK.tz_convert(None), 30, "  1 Dec 2025", fontsize=8, color=GREY, va="top")
    ax.set_ylabel("Share of volunteer starts (%)", color=TEXT)
    ax.set_ylim(bottom=0)
    ax.set_title("Same-second shared starts in the volunteer feed, by month", loc="left", color=TEXT, fontsize=11)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.text(0.01, 0.01, f"Kirovohradska line shows months with at least {MIN_KIRO_STARTS_FOR_PLOT} Kirovohradska starts. "
             "Months with fewer are blank.", fontsize=7.5, color=GREY)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_DIR / "ch08_batching_monthly.png", dpi=150)
    plt.close(fig)

    # --- 4. Lag by group for matched alerts ---
    mm = vol[vol["matched"]]
    lag = mm.groupby("group")["lag_sec"].agg(matched_alerts="size", median_signed_lag_sec="median")
    numbers["4_lag_by_group"] = {
        "definition": "median signed lag (volunteer minus nearest official start, all levels), matched alerts only",
        "period": f"{WINDOW_START.date()} to {end.date()}",
        "matched_alerts_total": int(len(mm)),
        "volunteer_alerts": int(len(vol)),
        "by_group": clean(lag.reset_index().to_dict("records")),
        "by_oblast": clean(mm.groupby("region")["lag_sec"].agg(matched_alerts="size",
                                                             median_signed_lag_sec="median")
                           .reset_index().to_dict("records")),
    }

    # --- Summary of findings: number, denominator, period ---
    pg = numbers["3_batching_over_time"]
    p1 = numbers["1_precision_by_year"]["lvivska_volynska_pre_post_break"]
    numbers["5_summary"] = [
        {"finding": "Western 8 oblasts, volunteer precision by year (see table 1)",
         "value": "see by_group_year", "denominator": "volunteer alerts per group-year",
         "period": f"{WINDOW_START.date()} to {end.date()}"},
        {"finding": "Lvivska and Volynska precision before/after 2025-12-01",
         "value": {r["region"]: {r["period"]: r["matched_share"]} for r in p1},
         "denominator": "volunteer alerts per oblast and period", "period": "pre and post 2025-12-01"},
        {"finding": "Overall exact-second batching, volunteer",
         "value": pg["overall_volunteer_share"], "denominator": pg["overall_volunteer_starts"],
         "period": f"{WINDOW_START.date()} to {end.date()}"},
        {"finding": "Overall exact-second batching, official oblast-level",
         "value": pg["overall_official_oblast_share"], "denominator": pg["overall_official_oblast_starts"],
         "period": f"{WINDOW_START.date()} to {end.date()}"},
        {"finding": "Kirovohradska starts with Poltavska same second, volunteer, before/after break",
         "value": kp_pp_out, "denominator": "Kirovohradska volunteer starts per period",
         "period": "before and from 2025-12-01"},
        {"finding": "Kirovohradska starts with Poltavska same second, official oblast-level",
         "value": pg["kiro_poltava_official_share_overall"], "denominator": pg["kiro_poltava_official_kiro_starts"],
         "period": f"{WINDOW_START.date()} to {end.date()}"},
    ]
    numbers["cause_note"] = ("The dataset has no message IDs. The cause of exact-second batching cannot be "
                             "determined from these data; no reporting cause is asserted.")

    JSON_OUT.write_text(json.dumps(clean(numbers), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- Compact console summary ---
    west_by_year = year_group[year_group["group"] == "western"].set_index("year")
    rest_by_year = year_group[year_group["group"] == "rest"].set_index("year")
    print("\n1. Matched share by year (volunteer alerts, all-level match within 5 min)")
    print(f"   {'year':<6}{'west n':>8}{'west %':>9}{'rest n':>9}{'rest %':>9}")
    for yr in west_by_year.index:
        print(f"   {yr:<6}{int(west_by_year.loc[yr, 'volunteer_alerts']):>8,}"
              f"{west_by_year.loc[yr, 'matched_share']*100:>8.1f}%"
              f"{int(rest_by_year.loc[yr, 'volunteer_alerts']):>9,}"
              f"{rest_by_year.loc[yr, 'matched_share']*100:>8.1f}%")
    for r in p1:
        print(f"   {r['region']}: {r['period']}: {r['matched_share']*100:.1f}% (n={r['volunteer_alerts']:,})")

    jc = numbers["check_western_jaccard"]
    print("\nJaccard check (western 8, mean over pairs)")
    print(f"   script window: vol {jc['window_as_in_western_cluster_check']['volunteer_mean']} "
          f"(n={jc['window_as_in_western_cluster_check']['volunteer_pairs']}), "
          f"off {jc['window_as_in_western_cluster_check']['official_mean']} "
          f"(n={jc['window_as_in_western_cluster_check']['official_pairs']})")
    print(f"   from 2022-03-15: vol {jc['window_from_2022_03_15']['volunteer_mean']}, "
          f"off {jc['window_from_2022_03_15']['official_mean']}")

    print(f"\n2. Top {len(top)} scored pairs by volunteer minus official same-second share (A to B, n = volunteer shared)")
    for r in top.itertuples():
        print(f"   {short(r.oblast_a)[:22]:<22} to {short(r.oblast_b)[:22]:<22} n={r.volunteer_shared:>4} "
              f"vol {r.volunteer_share*100:5.1f}%  off {r.official_share*100:5.1f}%  diff {r.difference*100:+5.1f}pp")
    print(f"   pairs scored: {len(scored)} of {len(pairs)} ordered pairs")

    print("\n3. Shared starts over time")
    print(f"   all oblasts, volunteer: {pg['overall_volunteer_share']*100:.1f}% of {pg['overall_volunteer_starts']:,} starts; "
          f"official oblast-level: {pg['overall_official_oblast_share']*100:.1f}% of {pg['overall_official_oblast_starts']:,}")
    print(f"   no start filter (pair_gap window): vol {pg['overall_no_start_filter_volunteer_share']*100:.1f}%, "
          f"off {pg['overall_no_start_filter_official_share']*100:.1f}%")
    for k, v in kp_pp_out.items():
        print(f"   Kiro with Poltava, volunteer {k}: {v['share']*100:.1f}% of {v['kiro_starts']:,} Kiro starts")
    print(f"   Kiro with Poltava, official oblast-level overall: {off_kp_share*100:.1f}% of {len(off_kiro):,}")
    print(f"   official oblast-level rows from 2025-12-01 in window: {off_post_break_rows:,} "
          f"(Kiro/Polt: {off_post_break_kp:,})")

    print("\n4. Median signed lag, matched alerts (volunteer minus official, seconds)")
    for r in lag.reset_index().itertuples():
        print(f"   {r.group:<8} median {r.median_signed_lag_sec:>7.1f} s  n={r.matched_alerts:,}")

    print(f"\nWrote {JSON_OUT}")
    print(f"Wrote {PAIR_CSV}, {YEAR_OBLAST_CSV}, {MONTHLY_CSV}")
    print("Figures: ch08_west_vs_rest_by_year.png, ch08_batching_pairs.png, ch08_batching_monthly.png")


if __name__ == "__main__":
    main()
