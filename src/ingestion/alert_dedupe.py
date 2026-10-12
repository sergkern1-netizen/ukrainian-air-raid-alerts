"""
Ingest rule for siren-alert datasets: drop rows that are identical in every column.

Vadimkin's official file contains each alert twice, as an exact copy, in about 38% of
rows (docs/data_inspection_gate1.md). Rows that match in every column, including
timestamps to the second, carry no extra information, so dropping them loses nothing.
Rows that differ in any column are kept, because they may be distinct signals.
"""

import logging
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def drop_exact_duplicates(df: pd.DataFrame, source: str) -> Tuple[pd.DataFrame, int]:
    """
    Remove rows that are identical in every column and log how many were dropped.

    Args:
        df: Raw alert records from one source file.
        source: Source name used in the log line, e.g. 'official'.

    Returns:
        Tuple of (deduplicated DataFrame with a fresh index, number of rows dropped).
    """
    duplicated = df.duplicated()
    dropped = int(duplicated.sum())
    deduped = df.loc[~duplicated].reset_index(drop=True)
    logger.info(f"[{source}] dropped {dropped:,} exact duplicate rows; kept {len(deduped):,}")
    return deduped, dropped
