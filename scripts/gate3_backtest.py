"""
Gate 3 backtest: weekly volunteer target, rolling origins, R1 metrics.

    python scripts/gate3_backtest.py

Writes output/gate3_backtest.json. Also prints the official raion-to-oblast roll-up
cross-check (docs/gate3_results.md, section on validation).
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.forecasting.backtest import run_backtest, summarize  # noqa: E402
from src.forecasting.weekly import REGIME_START, weekly_totals  # noqa: E402
from src.ingestion.alert_dedupe import drop_exact_duplicates  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT = ROOT / "output" / "gate3_backtest.json"
DEFAULT_ORIGINS = 52


def load(name: str) -> pd.DataFrame:
    """Read a Vadimkin file and apply the ingest rule."""
    df = pd.read_csv(RAW / name, parse_dates=["started_at", "finished_at"])
    deduped, dropped = drop_exact_duplicates(df, name)
    logging.info(f"{name}: dropped {dropped:,} exact duplicates")
    return deduped


def official_rollup_check(official: pd.DataFrame, volunteer_weekly: pd.DataFrame) -> dict:
    """Roll official raion rows up to oblast-week totals and compare with the volunteer target."""
    # One event can appear as an oblast row and as several raion rows; count each
    # (oblast, start time) once so the roll-up does not double count.
    events = official[official.started_at >= volunteer_weekly.index.min()]
    events = events.drop_duplicates(subset=["oblast", "started_at"])
    weekly_all = weekly_totals(events)
    joined = volunteer_weekly[["alerts"]].join(
        weekly_all[["alerts"]], rsuffix="_official", how="inner"
    )
    out = {}
    for label, part in [
        ("all", joined),
        ("pre_dec_2025", joined[joined.index < REGIME_START]),
        ("from_dec_2025", joined[joined.index >= REGIME_START]),
    ]:
        out[label] = {
            "weeks": int(len(part)),
            "correlation": round(float(part["alerts"].corr(part["alerts_official"])), 3),
            "volunteer_to_official_ratio": round(
                float(part["alerts"].sum() / part["alerts_official"].sum()), 3
            ),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--origins",
        type=int,
        default=DEFAULT_ORIGINS,
        help="number of weekly origins at the end of the series (sensitivity runs)",
    )
    parser.add_argument("--out", type=Path, default=OUT, help="output JSON path")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    volunteer = load("volunteer_data_en.csv")
    official = load("official_data_en.csv")

    weekly = weekly_totals(volunteer)
    results = run_backtest(weekly, origins=args.origins)
    daily_counts = (
        volunteer.started_at.dt.floor("D")
        .value_counts()
        .sort_index()
        .reindex(
            pd.date_range(
                volunteer.started_at.min().normalize(),
                volunteer.started_at.max().normalize(),
                freq="D",
                tz="UTC",
            ),
            fill_value=0,
        )
        .astype(float)
    )
    summary = summarize(results, results["weeks"], daily=daily_counts)

    rollup = official_rollup_check(official, weekly)

    report = {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": "volunteer, oblast rows, Monday-start weeks, partial weeks dropped",
        "weeks_total": int(len(weekly)),
        "first_week": str(weekly.index.min().date()),
        "last_week": str(weekly.index.max().date()),
        "origins": int(len(results["weeks"])),
        "nb_fits_not_converged": int(results["nb_nonconverged"]),
        "metrics": summary,
        "official_rollup_vs_volunteer": rollup,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
