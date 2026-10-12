"""
MVP pipeline: acquire -> validate -> preprocess -> weekly target -> backtest -> forecast -> report.

    python run_pipeline.py                 # download if needed, then run everything
    python run_pipeline.py --offline       # use files already in data/raw/ only

Outputs (output/, git-ignored):
    forecast_results.csv     next-week point forecast and intervals
    pipeline_report.json     data checks, backtest metrics, decision record

Each stage logs a UTC timestamp. Any failed check stops the run with a non-zero exit code.
Decision basis: docs/gate3_results.md (approved R1 metrics; trailing four-week mean baseline).
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.forecasting.backtest import LEVELS, ORIGINS, run_backtest, summarize  # noqa: E402
from src.forecasting.weekly import weekly_totals  # noqa: E402
from src.ingestion import vadimkin  # noqa: E402

BASELINE_WINDOW = 4
MAX_STALENESS_DAYS = 14
DEFAULT_RAW = ROOT / "data" / "raw"
DEFAULT_OUT = ROOT / "output"

logger = logging.getLogger("pipeline")


def stage(name: str) -> None:
    """Log the start of a stage with a UTC timestamp."""
    logger.info(f"[{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}] {name}")


def check_weekly(weekly: pd.DataFrame, origins: int) -> dict:
    """
    Fail fast on data problems that would make the backtest meaningless.

    A complete week with zero alerts is treated as a collection stall, since the volunteer
    feed has had no such week in its history.
    """
    if len(weekly) < origins + BASELINE_WINDOW + 1:
        raise RuntimeError(
            f"only {len(weekly)} complete weeks; need {origins + BASELINE_WINDOW + 1}"
        )
    zero_weeks = weekly.index[weekly.alerts == 0]
    if len(zero_weeks):
        raise RuntimeError(
            f"{len(zero_weeks)} complete week(s) with zero alerts, first {zero_weeks[0].date()}: "
            "possible collection stall"
        )
    return {"complete_weeks": int(len(weekly)), "zero_weeks": 0}


def check_freshness(volunteer: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    """Fail if the newest record is more than MAX_STALENESS_DAYS older than as_of."""
    last_record = volunteer["started_at"].max()
    gap_days = (as_of - last_record).days
    if gap_days > MAX_STALENESS_DAYS:
        raise RuntimeError(
            f"data is stale: newest record {last_record.date()}, "
            f"as-of {as_of.date()} ({gap_days} days later)"
        )
    return {
        "newest_record_utc": last_record.isoformat(),
        "as_of_utc": as_of.isoformat(),
        "days_since_newest_record": gap_days,
    }


def baseline_forecast(weekly: pd.DataFrame, residuals: np.ndarray) -> dict:
    """
    Point forecast for the next week and empirical intervals from backtest residuals.

    The intervals are the residual quantiles of the same baseline over the backtest. They are
    not model-based, and they are optimistic because the residuals are in-sample for the
    backtest. Docs/gate3_results.md states this.
    """
    y = weekly["alerts"].astype(float)
    point = float(y.iloc[-BASELINE_WINDOW:].mean())
    row = {"point": point}
    for level in LEVELS:
        lo_q, hi_q = np.quantile(residuals, [(1 - level) / 2, (1 + level) / 2])
        tag = f"{int(level * 100)}"
        row[f"lo{tag}"] = max(point + float(lo_q), 0.0)
        row[f"hi{tag}"] = max(point + float(hi_q), 0.0)
    return row


def run(
    raw_dir: Path = DEFAULT_RAW,
    out_dir: Path = DEFAULT_OUT,
    origins: int = ORIGINS,
    offline: bool = False,
    as_of: Optional[pd.Timestamp] = None,
) -> dict:
    """
    Run the full pipeline and return the report dictionary.

    Args:
        as_of: Reference time for the freshness check. Defaults to now (UTC). Pass a fixed
            date to reproduce an earlier run.
    """
    as_of = pd.Timestamp.now(tz="UTC") if as_of is None else pd.Timestamp(as_of)
    as_of = as_of.tz_localize("UTC") if as_of.tzinfo is None else as_of.tz_convert("UTC")
    stage("acquire")
    if not offline:
        vadimkin.fetch_all(raw_dir)
    else:
        missing = [n for n in (vadimkin.OFFICIAL, vadimkin.VOLUNTEER) if not (raw_dir / n).exists()]
        if missing:
            raise FileNotFoundError(f"offline run but missing {missing} in {raw_dir}")

    stage("validate and preprocess")
    official, volunteer = vadimkin.load_both(raw_dir)

    stage("weekly target")
    weekly = weekly_totals(volunteer)
    weekly_checks = check_weekly(weekly, origins)
    freshness = check_freshness(volunteer, as_of)
    daily = (
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

    stage("backtest")
    results = run_backtest(weekly, origins=origins)
    metrics = summarize(results, results["weeks"], daily=daily)
    residuals = results["actual"] - np.array(results["baseline"].mean)

    stage("forecast")
    next_week = weekly.index[-1] + pd.Timedelta(days=7)
    forecast = baseline_forecast(weekly, residuals)
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "week_start_utc": next_week.date().isoformat(),
                "model": "trailing_4_week_mean",
                **forecast,
            }
        ]
    ).to_csv(out_dir / "forecast_results.csv", index=False)

    stage("report")
    report = {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decision": "Gate 3 deliverable: trailing four-week mean baseline (trigger T1)",
        "approved_metrics": "R1: weekly WAPE primary; daily WAPE secondary; interval coverage",
        "origins": origins,
        "data": {
            "official_rows_after_dedupe": int(len(official)),
            "volunteer_rows": int(len(volunteer)),
            "volunteer_first_record": volunteer.started_at.min().isoformat(),
            "volunteer_last_record": volunteer.started_at.max().isoformat(),
            "official_last_record": official.started_at.max().isoformat(),
        },
        "checks": {**weekly_checks, **freshness},
        "backtest": metrics,
        "forecast": {"week_start_utc": next_week.date().isoformat(), **forecast},
        "limitations": "docs/gate3_results.md",
    }
    (out_dir / "pipeline_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    stage(f"done: forecast {next_week.date()} point={forecast['point']:.1f}")
    return report


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--offline", action="store_true", help="do not download; use data/raw/ only"
    )
    parser.add_argument(
        "--origins", type=int, default=ORIGINS, help="backtest origins (default 52)"
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--as-of", default=None, help="freshness reference date, e.g. 2026-10-12")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        run(
            args.raw_dir, args.out_dir, origins=args.origins, offline=args.offline, as_of=args.as_of
        )
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        logger.error(f"pipeline stopped: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
