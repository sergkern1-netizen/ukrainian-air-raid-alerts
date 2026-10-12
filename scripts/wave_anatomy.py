"""Wave anatomy: which oblasts take part in each alert wave, and which oblasts alert together.

Uses the same wave definition as scripts/alert_waves.py (gap threshold on national start instants).
Descriptive only. Counts are over the whole volunteer feed; small-count oblasts are flagged.

Writes:
  docs/analysis/wave_anatomy.md
  output/analysis/wave_oblast_participation.csv   (one row per wave and oblast, gitignored)
"""

from itertools import combinations
from pathlib import Path

import pandas as pd

from src.ingestion import vadimkin

RAW_DIR = Path("data/raw")
OUT_DOC = Path("docs/analysis/wave_anatomy.md")
OUT_DIR = Path("output/analysis")
GAP_MINUTES = 30
MIN_WAVES_FOR_PAIR = 20


def assign_waves(volunteer: pd.DataFrame, gap_minutes: int) -> pd.DataFrame:
    """Return the volunteer rows with a `wave_id` column."""
    rows = volunteer[["started_at", "region"]].copy()
    instants = rows["started_at"].drop_duplicates().sort_values().reset_index(drop=True)
    wave_of_instant = (instants.diff() > pd.Timedelta(minutes=gap_minutes)).cumsum()
    rows["wave_id"] = rows["started_at"].map(dict(zip(instants, wave_of_instant)))
    return rows


def main() -> None:
    _, volunteer = vadimkin.load_both(RAW_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    rows = assign_waves(volunteer, GAP_MINUTES)
    participation = rows.drop_duplicates(["wave_id", "region"])[["wave_id", "region"]]
    participation.to_csv(OUT_DIR / "wave_oblast_participation.csv", index=False)

    regions_per_wave = participation.groupby("wave_id")["region"].apply(lambda s: sorted(set(s)))
    n_regions = regions_per_wave.map(len).astype(int)
    total_waves = len(regions_per_wave)

    single = int((n_regions == 1).sum())
    multi = int((n_regions > 1).sum())
    size_table = n_regions.astype(float).describe(percentiles=[0.5, 0.9, 0.99]).round(1)

    region_waves = participation["region"].value_counts()
    region_share = (region_waves / total_waves * 100).round(1)

    pair_counts: dict = {}
    for regions in regions_per_wave:
        for a, b in combinations(regions, 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    # Rank by Jaccard (shared waves / waves either oblast is in). Raw counts favour the most
    # frequently affected oblasts, so they would show frequency, not association.
    pairs = pd.DataFrame(
        [(a, b, n) for (a, b), n in pair_counts.items()],
        columns=["oblast_a", "oblast_b", "waves_together"],
    )
    pairs["jaccard"] = pairs.apply(
        lambda r: r.waves_together / (region_waves[r.oblast_a] + region_waves[r.oblast_b] - r.waves_together),
        axis=1,
    ).round(3)
    pairs = pairs[pairs.waves_together >= MIN_WAVES_FOR_PAIR].sort_values("jaccard", ascending=False).head(15)

    lines = [
        "# Wave anatomy: oblast participation and co-occurrence",
        "",
        f"Gap threshold: {GAP_MINUTES} minutes. Waves: {total_waves:,}.",
        "",
        f"- Waves with one oblast: {single:,} ({single / total_waves:.1%}).",
        f"- Waves with two or more oblasts: {multi:,} ({multi / total_waves:.1%}).",
        "",
        "## Oblasts per wave",
        "",
        "| Statistic | Oblasts |",
        "|---|---:|",
    ]
    for stat in ["mean", "50%", "90%", "99%"]:
        label = {"50%": "median", "90%": "p90", "99%": "p99"}.get(stat, stat)
        lines.append(f"| {label} | {size_table[stat]} |")
    lines += [
        "",
        "## Share of waves each oblast takes part in (top 15)",
        "",
        "| Oblast | Waves | Share of all waves (%) |",
        "|---|---:|---:|",
    ]
    for region, count in region_waves.head(15).items():
        lines.append(f"| {region} | {count:,} | {region_share[region]} |")
    lines += [
        "",
        "## Oblast pairs that alert in the same wave (top 15 by Jaccard)",
        "",
        f"Jaccard = shared waves / waves either oblast is in. Pairs with fewer than {MIN_WAVES_FOR_PAIR} shared waves are not listed.",
        "",
        "| Oblast A | Oblast B | Waves together | Jaccard |",
        "|---|---|---:|---:|",
    ]
    for _, r in pairs.iterrows():
        lines.append(f"| {r.oblast_a} | {r.oblast_b} | {int(r.waves_together):,} | {r.jaccard} |")
    lines += [
        "",
        "Co-occurrence means both oblasts appeared in the same wave. It does not show that one caused",
        "the other, and it does not identify which oblast was targeted.",
        "",
        "Caution: the top Jaccard pairs are western oblasts. Gate 3 documents that the volunteer feed",
        "over-reports in the west relative to the official feed (docs/gate3_results.md). A western",
        "co-occurrence cluster may therefore reflect the reporting channel as much as the events. Check",
        "it against the official feed's oblast-level matches before reading it as a geographic pattern.",
        "",
    ]
    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_DOC}: {total_waves:,} waves, {single:,} single-oblast")


if __name__ == "__main__":
    main()
