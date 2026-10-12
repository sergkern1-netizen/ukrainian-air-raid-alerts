"""
Download and inspect the Vadimkin air-raid siren datasets (CLAUDE.md Gate 1).

    python scripts/inspect_vadimkin.py

Files are written to data/raw/ (git-ignored). A MANIFEST.json there records the
source URL, download time (UTC), byte size and SHA-256 of each file, so later
runs can detect upstream changes.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.ingestion import vadimkin  # noqa: E402
from src.ingestion.alert_dedupe import drop_exact_duplicates  # noqa: E402

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def inspect(official: pd.DataFrame, volunteer: pd.DataFrame) -> None:
    """Print the Gate 1 inspection report, applying the ingest dedupe rule first."""
    deduped, dropped = drop_exact_duplicates(official, "official")
    print("\n== official ==")
    print(
        f"rows: {len(official):,}  "
        f"range: {official.started_at.min()} .. {official.started_at.max()}"
    )
    print(f"raw rows: {len(official):,}")
    print(f"rows after ingest dedupe: {len(deduped):,} (dropped {dropped:,} exact duplicates)")
    official = deduped
    hours = (official.finished_at - official.started_at).dt.total_seconds() / 3600
    print(
        f"alerts longer than 24 h: {int((hours > 24).sum()):,}  "
        f"(>7 d: {int((hours > 168).sum()):,})"
    )
    print("level counts:", official.level.value_counts().to_dict())
    print("rows by year:", official.started_at.dt.year.value_counts().sort_index().to_dict())

    print("\n== volunteer ==")
    print(
        f"rows: {len(volunteer):,}  "
        f"range: {volunteer.started_at.min()} .. {volunteer.started_at.max()}"
    )
    minutes = (volunteer.finished_at - volunteer.started_at).dt.total_seconds() / 60
    print(f"naive (inferred end, 30 min): {volunteer.naive.mean():.1%}")
    print(f"duration max: {minutes.max():,.0f} min")

    print("\n== overlap ==")
    oblast = deduped[deduped.level == "oblast"][["oblast", "started_at"]]
    oblast = oblast.rename(columns={"oblast": "region"}).assign(official_hit=True)
    matched = pd.merge_asof(
        volunteer[["region", "started_at"]].sort_values("started_at"),
        oblast.sort_values("started_at"),
        on="started_at",
        by="region",
        direction="nearest",
        tolerance=pd.Timedelta("5min"),
    )
    print(
        "volunteer alerts with an official oblast alert within 5 min: "
        f"{matched.official_hit.notna().mean():.1%}"
    )


def main() -> int:
    paths = vadimkin.fetch_all(RAW_DIR)
    official = pd.read_csv(paths[vadimkin.OFFICIAL], parse_dates=["started_at", "finished_at"])
    volunteer = pd.read_csv(paths[vadimkin.VOLUNTEER], parse_dates=["started_at", "finished_at"])
    inspect(official, volunteer)
    print(f"\nmanifest: {RAW_DIR / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
