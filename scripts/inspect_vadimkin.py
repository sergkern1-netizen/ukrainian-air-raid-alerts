"""
Download and inspect the Vadimkin air-raid siren datasets (CLAUDE.md Gate 1).

    python scripts/inspect_vadimkin.py

Files are written to data/raw/ (git-ignored). A MANIFEST.json there records the
source URL, download time (UTC), byte size and SHA-256 of each file, so later
runs can detect upstream changes.
"""

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.ingestion.alert_dedupe import drop_exact_duplicates  # noqa: E402

BASE_URL = (
    "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets"
)
FILES = ["official_data_en.csv", "volunteer_data_en.csv"]
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MANIFEST = RAW_DIR / "MANIFEST.json"


def download(name: str) -> Path:
    """Fetch one dataset file unless it is already present."""
    target = RAW_DIR / name
    if target.exists():
        return target
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{name}"
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=60) as response, target.open("wb") as out:
        out.write(response.read())
    return target


def record_manifest(paths: list) -> None:
    """Write size, SHA-256 and download time for each file."""
    entries = {}
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries[path.name] = {
            "url": f"{BASE_URL}/{path.name}",
            "bytes": path.stat().st_size,
            "sha256": digest,
            "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    MANIFEST.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


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
    paths = [download(name) for name in FILES]
    record_manifest(paths)
    official = pd.read_csv(paths[0], parse_dates=["started_at", "finished_at"])
    volunteer = pd.read_csv(paths[1], parse_dates=["started_at", "finished_at"])
    inspect(official, volunteer)
    print(f"\nmanifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
