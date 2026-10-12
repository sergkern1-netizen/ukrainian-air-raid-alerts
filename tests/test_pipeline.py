"""End-to-end tests for run_pipeline.py on synthetic Vadimkin-format files."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import run_pipeline
from src.forecasting.weekly import weekly_totals
from src.ingestion import vadimkin


def _write_datasets(
    raw: Path,
    days: pd.DatetimeIndex,
    rng: np.random.Generator,
    gap: tuple = None,
    volunteer_columns: list = None,
) -> None:
    """Write synthetic volunteer and official CSVs with about 60 alerts per day."""
    rows = []
    for day in days:
        if gap and gap[0] <= day < gap[1]:
            continue
        for _ in range(int(rng.poisson(60))):
            start = day + pd.Timedelta(seconds=int(rng.integers(0, 86400)))
            rows.append(
                {
                    "region": "Kyivska oblast",
                    "started_at": start.isoformat(),
                    "finished_at": (start + pd.Timedelta(minutes=30)).isoformat(),
                    "naive": False,
                }
            )
    volunteer = pd.DataFrame(rows)
    if volunteer_columns is not None:
        volunteer = volunteer[volunteer_columns]
    volunteer.to_csv(raw / vadimkin.VOLUNTEER, index=False)

    official = pd.DataFrame(
        [
            {
                "oblast": "Kyivska oblast",
                "raion": None,
                "hromada": None,
                "level": "oblast",
                "started_at": "2024-01-01T10:00:00+00:00",
                "finished_at": "2024-01-01T10:30:00+00:00",
                "source": "official",
            }
        ]
    )
    official.to_csv(raw / vadimkin.OFFICIAL, index=False)


@pytest.fixture
def days() -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", "2024-12-31", freq="D", tz="UTC")


def test_pipeline_writes_forecast_and_report(
    tmp_path: Path, days, rng=np.random.default_rng(1)
) -> None:
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _write_datasets(raw, days, rng)

    report = run_pipeline.run(
        raw, out, origins=5, offline=True, as_of=pd.Timestamp("2025-01-02", tz="UTC")
    )

    assert (out / "forecast_results.csv").exists()
    assert (out / "pipeline_report.json").exists()
    weekly = weekly_totals(vadimkin.load(raw / vadimkin.VOLUNTEER, vadimkin.VOLUNTEER))
    expected_point = float(weekly.alerts.iloc[-4:].mean())
    forecast = pd.read_csv(out / "forecast_results.csv")
    assert forecast.loc[0, "point"] == pytest.approx(expected_point)
    assert forecast.loc[0, "lo80"] <= forecast.loc[0, "point"] <= forecast.loc[0, "hi80"]
    assert report["backtest"]["baseline"]["weekly_wape"] >= 0


def test_missing_required_column_fails_fast(
    tmp_path: Path, days, rng=np.random.default_rng(2)
) -> None:
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _write_datasets(raw, days, rng, volunteer_columns=["region", "started_at", "finished_at"])

    with pytest.raises(ValueError, match="missing required columns"):
        run_pipeline.run(
            raw, out, origins=5, offline=True, as_of=pd.Timestamp("2025-01-02", tz="UTC")
        )


def test_collection_stall_is_detected(tmp_path: Path, days, rng=np.random.default_rng(3)) -> None:
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _write_datasets(
        raw,
        days,
        rng,
        gap=(pd.Timestamp("2024-06-03", tz="UTC"), pd.Timestamp("2024-06-17", tz="UTC")),
    )

    with pytest.raises(RuntimeError, match="zero alerts"):
        run_pipeline.run(
            raw, out, origins=5, offline=True, as_of=pd.Timestamp("2025-01-02", tz="UTC")
        )


def test_stale_data_is_detected(tmp_path: Path, days, rng=np.random.default_rng(4)) -> None:
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _write_datasets(raw, days, rng)

    with pytest.raises(RuntimeError, match="stale"):
        run_pipeline.run(
            raw, out, origins=5, offline=True, as_of=pd.Timestamp("2026-06-01", tz="UTC")
        )


def test_offline_run_without_files_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        run_pipeline.run(tmp_path / "empty", tmp_path / "out", offline=True)


def test_cli_returns_nonzero_on_failure(tmp_path: Path) -> None:
    assert (
        run_pipeline.main(
            [
                "--offline",
                "--raw-dir",
                str(tmp_path / "missing"),
                "--out-dir",
                str(tmp_path / "out"),
            ]
        )
        == 1
    )
