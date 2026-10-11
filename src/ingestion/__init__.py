"""
Real-time and batch ingestion modules for Ukrainian air raid alerts.

This package provides:
- AsyncAlertsPoller: Real-time polling from alerts.in.ua API with failover
- Batch loaders for Vadimkin, Kaggle, ACLED, ISW data sources
"""

from src.ingestion.batch_loaders import (
    VadimkinLoader,
    KaggleLoader,
    AcledLoader,
    IswLoader,
)

try:
    from src.ingestion.alerts_in_ua_poller import AsyncAlertsPoller
except ImportError:
    AsyncAlertsPoller = None

__all__ = [
    "VadimkinLoader",
    "KaggleLoader",
    "AcledLoader",
    "IswLoader",
    "AsyncAlertsPoller",
]
