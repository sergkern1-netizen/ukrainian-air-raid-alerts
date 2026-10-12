"""Chapter 7 analysis: provenance and data quality of the two Vadimkin siren files.

Descriptive only. Covers the source table, exact and key-level duplicates, calendar coverage,
inferred end times, zero or negative durations, field completeness, oblast names, official
level mix, timezone parse checks and the known-issue dates. Gaps are reported, not filled.
The Kaggle missile file is out of scope and is not read.

Raw counts are read straight from the CSVs. The deduplicated counts use vadimkin.load_both.

Writes:
  output/analysis/chapter07_numbers.json          (gitignored)
  docs/chapters/figures/ch07_coverage_by_year.png
"""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.ingestion import vadimkin  # noqa: E402

RAW_DIR = Path("data/raw")
FIG_DIR = Path("docs/chapters/figures")
OUT_DIR = Path("output/analysis")
OUT_JSON = OUT_DIR / "chapter07_numbers.json"
KYIV = "Europe/Kyiv"
FILES = {"official": vadimkin.OFFICIAL, "volunteer": vadimkin.VOLUNTEER}
NAME_COL = {"official": "oblast", "volunteer": "region"}

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
INK = "#1f2933"
PALETTE = {"official": "#3e6e8e", "volunteer": "#c77d3a"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def longest_run(flags: pd.Series) -> int:
    best = run = 0
    for v in flags.to_numpy():
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def main() -> None:
    manifest = json.loads((RAW_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    official, volunteer = vadimkin.load_both(RAW_DIR)
    deduped = {"official": official, "volunteer": volunteer}
    out: dict = {"sources": {}, "duplicates": {}, "coverage": {}, "inferred": {}, "durations": {},
                 "completeness": {}, "names": {}, "levels": {}, "timezone": {}, "known_issues": {}}

    raw = {}
    for key, name in FILES.items():
        path = RAW_DIR / name
        df_raw = pd.read_csv(path, parse_dates=["started_at", "finished_at"])
        raw[key] = df_raw
        m = manifest.get(name, {})
        sha = sha256(path)
        out["sources"][key] = {
            "file": name,
            "repository": "github.com/Vadimkin/ukrainian-air-raid-sirens-dataset",
            "manifest_url": m.get("url"),
            "rows_raw": int(len(df_raw)),
            "rows_after_dedupe": int(len(deduped[key])),
            "columns": list(df_raw.columns),
            "first_started_at": str(df_raw["started_at"].min()),
            "last_started_at": str(df_raw["started_at"].max()),
            "bytes_manifest": m.get("bytes"),
            "bytes_actual": path.stat().st_size,
            "sha256_manifest": m.get("sha256"),
            "sha256_actual": sha,
            "sha256_matches_manifest": sha == m.get("sha256"),
            "download_recorded_utc": m.get("recorded_utc"),
        }

        # Duplicates: exact (all columns) and key-level (same region/oblast + started_at, different finished_at).
        exact = int(df_raw.duplicated().sum())
        name_col = NAME_COL[key]
        grp = df_raw.groupby([name_col, "started_at"])["finished_at"].transform("nunique")
        size = df_raw.groupby([name_col, "started_at"])["finished_at"].transform("size")
        conflict = (size > 1) & (grp > 1)
        out["duplicates"][key] = {
            "exact_duplicate_rows_removed": exact,
            "rows_same_name_and_start_diff_finish": int(conflict.sum()),
            "share_of_raw_rows": round(float(conflict.mean()), 6),
            "groups_same_name_and_start_diff_finish": int(
                df_raw.loc[conflict].groupby([name_col, "started_at"]).ngroups
            ),
        }

        # Coverage: local (Kyiv) calendar days with zero records inside the file's span.
        days = deduped[key]["started_at"].dt.tz_convert(KYIV).dt.normalize().dt.tz_localize(None)
        present = set(days.dt.date)
        span = pd.date_range(min(present), max(present), freq="D")
        missing = pd.Series([d.date() not in present for d in span], index=span)
        out["coverage"][key] = {
            "first_local_day": str(min(present)),
            "last_local_day": str(max(present)),
            "span_days": int(len(span)),
            "days_with_records": int(len(present)),
            "days_zero_records": int(missing.sum()),
            "longest_zero_gap_days": longest_run(missing),
            "longest_zero_gap_ends_before": None,
        }
        if missing.any():
            best_end, best, run = None, 0, 0
            for d, v in missing.items():
                run = run + 1 if v else 0
                if run > best:
                    best, best_end = run, d
            out["coverage"][key]["longest_zero_gap_ends_before"] = str((best_end + pd.Timedelta(days=1)).date())

        # Durations.
        dur = (df_raw["finished_at"] - df_raw["started_at"]).dt.total_seconds()
        out["durations"][key] = {
            "zero_duration_rows": int((dur == 0).sum()),
            "negative_duration_rows": int((dur < 0).sum()),
            "median_minutes": round(float(dur.median() / 60), 2),
        }

        # Completeness on the raw file.
        miss = df_raw.isna().sum()
        out["completeness"][key] = {
            c: {"missing": int(miss[c]), "share": round(float(miss[c] / len(df_raw)), 6)} for c in df_raw.columns
        }

        # Timezone parse check: re-parse raw strings as UTC and count failures.
        strs = pd.read_csv(path, dtype=str, keep_default_na=False)
        failed = 0
        suffix_bad = 0
        for col in ("started_at", "finished_at"):
            vals = strs[col]
            parsed = pd.to_datetime(vals.replace("", None), utc=True, format="ISO8601", errors="coerce")
            failed += int((parsed.isna() & vals.ne("")).sum())
            suffix_bad += int((~vals.str.endswith("+00:00") & vals.ne("")).sum())
        out["timezone"][key] = {
            "started_at_dtype_after_parse": str(df_raw["started_at"].dtype),
            "finished_at_dtype_after_parse": str(df_raw["finished_at"].dtype),
            "tz_aware": bool(getattr(df_raw["started_at"].dt, "tz", None) is not None),
            "parse_failures": failed,
            "strings_not_ending_plus00_00": suffix_bad,
        }

    # Inferred end times.
    vol = raw["volunteer"]
    out["inferred"]["volunteer"] = {
        "naive_column_present": "naive" in vol.columns,
        "naive_true_rows_raw": int(vol["naive"].astype(str).str.lower().eq("true").sum()),
        "naive_share_raw": round(float(vol["naive"].astype(str).str.lower().eq("true").mean()), 6),
        "naive_true_share_by_year": {
            str(y): round(float(g["naive"].astype(str).str.lower().eq("true").mean()), 4)
            for y, g in vol.groupby(vol["started_at"].dt.year)
        },
    }
    off = raw["official"]
    out["inferred"]["official"] = {
        "naive_column_present": "naive" in off.columns,
        "source_values": {str(k): int(v) for k, v in off["source"].value_counts(dropna=False).items()},
    }

    # Names.
    off_names = set(deduped["official"]["oblast"].dropna().unique())
    vol_names = set(deduped["volunteer"]["region"].dropna().unique())
    out["names"] = {
        "official_count": len(off_names),
        "volunteer_count": len(vol_names),
        "official": sorted(off_names),
        "volunteer": sorted(vol_names),
        "only_in_official": sorted(off_names - vol_names),
        "only_in_volunteer": sorted(vol_names - off_names),
        "luhansk_like_official": sorted(n for n in off_names if "uhan" in n.lower()),
        "luhansk_like_volunteer": sorted(n for n in vol_names if "uhan" in n.lower()),
        "kyiv_city_official": sorted(n for n in off_names if "kyiv" in n.lower()),
        "kyiv_city_volunteer": sorted(n for n in vol_names if "kyiv" in n.lower()),
    }
    lug = deduped["official"][deduped["official"]["oblast"].str.contains("uhan", na=False)]
    out["names"]["luhansk_official_last_row"] = None if lug.empty else {
        "oblast": lug["oblast"].iloc[-1], "started_at": str(lug["started_at"].iloc[-1]), "rows": int(len(lug))
    }

    out["names"]["luhansk_volunteer_rows_raw"] = int(
        deduped["volunteer"]["region"].str.contains("uhan", na=False).sum())

    # Official level mix by year (deduplicated, UTC year).
    off_d = deduped["official"].copy()
    off_d["year"] = off_d["started_at"].dt.year
    ct = pd.crosstab(off_d["year"], off_d["level"])
    out["levels"] = {
        "by_year": {str(y): {lvl: int(ct.loc[y, lvl]) for lvl in ct.columns} for y in ct.index},
        "total": {str(k): int(v) for k, v in off_d["level"].value_counts().items()},
    }

    # Known issues.
    off_first = deduped["official"]["started_at"].min()
    off_last = deduped["official"]["started_at"].max()
    vol_last = deduped["volunteer"]["started_at"].max()
    out["known_issues"] = {
        "official_first_started_at_utc": str(off_first),
        "official_first_local_date": str(off_first.tz_convert(KYIV).date()),
        "official_last_started_at_utc": str(off_last),
        "official_last_local_date": str(off_last.tz_convert(KYIV).date()),
        "volunteer_last_started_at_utc": str(vol_last),
        "volunteer_last_local_date": str(vol_last.tz_convert(KYIV).date()),
    }

    # Rows per year per file (raw, UTC year) for the figure; deduplicated counts stored too.
    years = sorted(set(raw["official"]["started_at"].dt.year) | set(raw["volunteer"]["started_at"].dt.year))
    per_year = {k: raw[k]["started_at"].dt.year.value_counts().reindex(years, fill_value=0) for k in FILES}
    out["rows_per_year_raw"] = {k: {str(y): int(per_year[k][y]) for y in years} for k in FILES}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

    x = np.arange(len(years))
    w = 0.4
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(x - w / 2, per_year["official"].values, w, color=PALETTE["official"], label="official")
    ax.bar(x + w / 2, per_year["volunteer"].values, w, color=PALETTE["volunteer"], label="volunteer")
    ax.set_xticks(x, [str(y) for y in years])
    ax.set_ylabel("rows (raw, UTC year)")
    ax.set_title("Rows per year per file", color=INK, loc="left")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "ch07_coverage_by_year.png")
    plt.close(fig)

    print(json.dumps({k: out["sources"][k]["rows_raw"] for k in FILES}, indent=2))
    print(f"wrote {OUT_JSON} and {FIG_DIR / 'ch07_coverage_by_year.png'}")


if __name__ == "__main__":
    main()
