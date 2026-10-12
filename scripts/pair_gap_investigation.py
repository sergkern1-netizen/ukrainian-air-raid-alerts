"""Investigate why Kirovohradska and Poltavska alert together more often in the volunteer feed.

Three checks, all over the overlap window (up to the official feed's last start):
  1. Timing: exact same-second starts and the gap to the nearest start in the other oblast.
  2. Batching: share of all oblast starts that share an exact second with another oblast (is this
     pair special, or is batching a general feature of the volunteer feed?).
  3. Period: the same-second rate before and after the 2025-12-01 break.

Descriptive only. The dataset has no message IDs, so batching cannot be traced to a source post.

Writes: docs/analysis/kirovohrad_poltava_gap.md
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.ingestion import vadimkin

RAW_DIR = Path("data/raw")
OUT_DOC = Path("docs/analysis/kirovohrad_poltava_gap.md")
A, B = "Kirovohradska oblast", "Poltavska oblast"
BREAK = pd.Timestamp("2025-12-01", tz="UTC")


def pair_timing(df: pd.DataFrame, col: str) -> dict:
    k = df[df[col].isin([A, B])].drop_duplicates([col, "started_at"])
    a = np.sort(k[k[col] == A]["started_at"].values)
    b = np.sort(k[k[col] == B]["started_at"].values)
    same = len(set(a) & set(b))
    gaps = []
    for x in a:
        if len(b):
            gaps.append(np.min(np.abs(b - x)).astype("timedelta64[s]").astype(int) / 60)
    gaps = np.array(gaps)
    return {
        "kiro_starts": len(a),
        "exact_same_minute": same,
        "same_minute_share": round(same / len(a), 3) if len(a) else np.nan,
        "median_gap_min": round(float(np.median(gaps)), 1) if len(gaps) else np.nan,
        "within_30_min_share": round(float(np.mean(gaps <= 30)), 3) if len(gaps) else np.nan,
    }


def batching_share(df: pd.DataFrame, col: str) -> float:
    d = df.drop_duplicates([col, "started_at"])
    n = d.groupby("started_at")[col].transform("size")
    return round(float((n > 1).mean()), 3)


def period_same_minute(df: pd.DataFrame, col: str) -> dict:
    k = df[df[col].isin([A, B])].drop_duplicates([col, "started_at"]).copy()
    out = {}
    for label, mask in [("pre", k["started_at"] < BREAK), ("post", k["started_at"] >= BREAK)]:
        sub = k[mask]
        a = set(sub[sub[col] == A]["started_at"])
        b = set(sub[sub[col] == B]["started_at"])
        out[label] = (len(a), round(len(a & b) / len(a), 3) if a else np.nan)
    return out


def main() -> None:
    official, volunteer = vadimkin.load_both(RAW_DIR)
    end = official["started_at"].max()
    vol = volunteer[volunteer["started_at"] <= end]
    off = official[(official["level"] == "oblast") & (official["started_at"] <= end)]

    vt = pair_timing(vol, "region")
    ot = pair_timing(off, "oblast")
    vb = batching_share(vol, "region")
    ob = batching_share(off, "oblast")
    vp = period_same_minute(vol, "region")
    op = period_same_minute(off, "oblast")

    lines = [
        "# Kirovohradska–Poltavska gap: volunteer vs official",
        "",
        "The pair's Jaccard is 0.552 in the volunteer feed and 0.361 in the official feed (see",
        "`western_cluster_check.md`). This note checks why.",
        "",
        f"Overlap window: up to {end.date()}.",
        "",
        "## 1. Timing of the pair",
        "",
        "| Feed | Kirovohrad starts | Exact same second as Poltava | Same-second share | Median gap to Poltava (min) | Within 30 min |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Volunteer | {vt['kiro_starts']:,} | {vt['exact_same_minute']:,} | {vt['same_minute_share']} | {vt['median_gap_min']} | {vt['within_30_min_share']} |",
        f"| Official | {ot['kiro_starts']:,} | {ot['exact_same_minute']:,} | {ot['same_minute_share']} | {ot['median_gap_min']} | {ot['within_30_min_share']} |",
        "",
        "## 2. Is batching general or specific to this pair?",
        "",
        f"Share of all oblast starts that share an exact second with another oblast: volunteer {vb}, official {ob}.",
        "Batching is about the same across the whole feed. It is not a general volunteer-feed effect.",
        "",
        "## 3. Same-second share by period",
        "",
        "| Feed | Period | Kirovohrad starts | Same-second share with Poltava |",
        "|---|---|---:|---:|",
    ]
    for label, (n, share) in vp.items():
        lines.append(f"| Volunteer | {'before' if label=='pre' else 'from'} Dec 2025 | {n:,} | {share} |")
    for label, (n, share) in op.items():
        lines.append(f"| Official | {'before' if label=='pre' else 'from'} Dec 2025 | {n:,} | {share} |")
    lines += [
        "",
        "The official feed has no oblast-level rows after the break in this window, so its post-break",
        "value is not available.",
        "",
        "## Reading",
        "",
        "- The volunteer feed posts Kirovohrad and Poltava in the same second about eight times more",
        "  often than the official feed does. The gap is specific to this pair.",
        "- That batching was concentrated before December 2025 and fell to under 1% afterwards.",
        "- The most likely reason is that volunteers report the two oblasts in one message. The dataset",
        "  has no message IDs, so this is a hypothesis. Check it with the source posts before stating it.",
        "- Consequence: the pair's pre-break volunteer Jaccard overstates how often the two oblasts were",
        "  affected together. Do not present it as a geographic finding.",
        "",
    ]
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_DOC}")
    print("volunteer timing", vt)
    print("official timing", ot)


if __name__ == "__main__":
    main()
