"""Tests for the exact-duplicate ingest rule (src/ingestion/alert_dedupe.py)."""

import pandas as pd

from src.ingestion.alert_dedupe import drop_exact_duplicates


def _alerts(rows: list) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["oblast", "level", "started_at", "finished_at"]
    )


def test_identical_rows_are_dropped_and_counted() -> None:
    df = _alerts(
        [
            ("Kyivska oblast", "oblast", "2022-03-15 16:10:34", "2022-03-15 16:50:07"),
            ("Kyivska oblast", "oblast", "2022-03-15 16:10:34", "2022-03-15 16:50:07"),
            ("Sumska oblast", "oblast", "2022-03-15 16:11:25", "2022-03-15 16:54:23"),
        ]
    )

    deduped, dropped = drop_exact_duplicates(df, "test")

    assert dropped == 1
    assert len(deduped) == 2
    assert deduped.index.tolist() == [0, 1]


def test_rows_differing_in_any_column_are_kept() -> None:
    """Same region and start but different end time is a different record, so it stays."""
    df = _alerts(
        [
            ("Kyivska oblast", "oblast", "2022-03-15 16:10:34", "2022-03-15 16:50:07"),
            ("Kyivska oblast", "oblast", "2022-03-15 16:10:34", "2022-03-15 17:00:00"),
            ("Kyivska oblast", "raion", "2022-03-15 16:10:34", "2022-03-15 16:50:07"),
        ]
    )

    deduped, dropped = drop_exact_duplicates(df, "test")

    assert dropped == 0
    assert len(deduped) == 3


def test_no_duplicates_returns_input_unchanged() -> None:
    df = _alerts([("Kyivska oblast", "oblast", "2022-03-15 16:10:34", "2022-03-15 16:50:07")])

    deduped, dropped = drop_exact_duplicates(df, "test")

    assert dropped == 0
    pd.testing.assert_frame_equal(deduped, df)
