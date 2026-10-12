"""
Per-oblast EDA on weekly volunteer counts (docs/eda_gate2.md lists this as not yet done).

    python scripts/eda_per_oblast.py

For each oblast: mean weekly count and zero-week share over the last 52 complete weeks,
dispersion (variance / mean), and lag-1 autocorrelation. Oblasts are then grouped by
sparsity so modelling choices can follow the data.
"""

import sys
from pathlib import Path

import pandas as pd
from statsmodels.tsa.stattools import acf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.forecasting.weekly import weekly_totals  # noqa: E402
from src.ingestion import vadimkin  # noqa: E402

WINDOW = 52
SPARSE_MEAN = 5.0  # mean alerts per week below which a series is treated as sparse
NO_ALERTS = 0.5  # mean alerts per week below which a series is treated as silent


def per_oblast_table(volunteer: pd.DataFrame) -> pd.DataFrame:
    """One row per oblast with sparsity and dispersion over the last WINDOW weeks."""
    total_weeks = weekly_totals(volunteer).index
    rows = []
    for region, group in volunteer.groupby("region"):
        weekly = weekly_totals(group)["alerts"].reindex(total_weeks, fill_value=0).astype(float)
        recent = weekly.iloc[-WINDOW:]
        mean = recent.mean()
        rows.append({
            "region": region,
            "mean_per_week": round(mean, 1),
            "zero_week_share_all": round((weekly == 0).mean(), 3),
            "zero_week_share_52": round((recent == 0).mean(), 3),
            "dispersion_52": round(recent.var() / mean, 1) if mean > 0 else None,
            "acf_lag1_52": (
                round(acf(recent, nlags=1, fft=True)[1], 2) if recent.std() > 0 else None
            ),
        })
    return pd.DataFrame(rows).sort_values("mean_per_week", ascending=False)


def classify(table: pd.DataFrame) -> pd.DataFrame:
    """Label each oblast as dense, sparse or silent."""
    def label(mean: float) -> str:
        if mean < NO_ALERTS:
            return "silent"
        if mean < SPARSE_MEAN:
            return "sparse"
        return "dense"

    table = table.copy()
    table["regime"] = table.mean_per_week.map(label)
    return table


def main() -> int:
    raw = ROOT / "data" / "raw"
    _, volunteer = vadimkin.load_both(raw)
    table = classify(per_oblast_table(volunteer))
    print(table.to_string(index=False))
    print("\ncounts by regime:", table.regime.value_counts().to_dict())
    return 0


if __name__ == "__main__":
    sys.exit(main())
