"""
Acquisition and loading for the Vadimkin siren datasets (official and volunteer).

Files are downloaded once into data/raw/ (git-ignored). MANIFEST.json there records the
source URL, download time (UTC), byte size and SHA-256 of each file, so later runs can
detect upstream changes. Loading applies the exact-duplicate ingest rule.
"""

import hashlib
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from src.ingestion.alert_dedupe import drop_exact_duplicates

logger = logging.getLogger(__name__)

BASE_URL = (
    "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets"
)
OFFICIAL = "official_data_en.csv"
VOLUNTEER = "volunteer_data_en.csv"
REQUIRED_COLUMNS = {
    OFFICIAL: {"oblast", "level", "started_at", "finished_at"},
    VOLUNTEER: {"region", "started_at", "finished_at", "naive"},
}


def download(name: str, raw_dir: Path) -> Path:
    """Fetch one dataset file unless it is already present in raw_dir."""
    target = raw_dir / name
    if target.exists():
        return target
    raw_dir.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{name}"
    logger.info(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=60) as response, target.open("wb") as out:
        out.write(response.read())
    return target


def record_manifest(paths: list, raw_dir: Path) -> None:
    """Write size, SHA-256 and download time for each file to MANIFEST.json."""
    entries = {}
    for path in paths:
        entries[path.name] = {
            "url": f"{BASE_URL}/{path.name}",
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    (raw_dir / "MANIFEST.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def fetch_all(raw_dir: Path) -> Dict[str, Path]:
    """Ensure both files exist locally and refresh the manifest."""
    paths = {name: download(name, raw_dir) for name in (OFFICIAL, VOLUNTEER)}
    record_manifest(list(paths.values()), raw_dir)
    return paths


def load(path: Path, name: str) -> pd.DataFrame:
    """
    Read one dataset file, validate its schema, and apply the exact-duplicate ingest rule.

    Raises:
        ValueError: If required columns are missing or the file is empty (fail fast).
    """
    df = pd.read_csv(path, parse_dates=["started_at", "finished_at"])
    missing = REQUIRED_COLUMNS[name] - set(df.columns)
    if missing:
        raise ValueError(f"{name}: missing required columns {sorted(missing)}")
    if df.empty:
        raise ValueError(f"{name}: no rows")
    deduped, dropped = drop_exact_duplicates(df, name)
    logger.info(f"{name}: {len(deduped):,} rows after dropping {dropped:,} exact duplicates")
    return deduped


def load_both(raw_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the official and volunteer files from raw_dir."""
    official = load(raw_dir / OFFICIAL, OFFICIAL)
    volunteer = load(raw_dir / VOLUNTEER, VOLUNTEER)
    return official, volunteer
