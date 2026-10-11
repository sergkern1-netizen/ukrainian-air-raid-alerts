"""
Configuration module for Ukrainian Air Raid Alerts analysis pipeline.
Loads environment variables using pydantic BaseSettings.
"""

from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    api_token: str
    """Alerts.in.ua API token for real-time monitoring."""

    kafka_brokers: str
    """Comma-separated list of Kafka broker addresses."""

    timescale_url: str
    """TimescaleDB connection URL."""

    redis_url: str
    """Redis connection URL for caching."""

    isw_scrape_url: str
    """URL for ISW (Institute for Study of War) data source."""

    telegram_api_id: Optional[int] = None
    """Telegram API ID for MTProto client."""

    telegram_api_hash: Optional[str] = None
    """Telegram API hash for MTProto client."""

    telegram_phone: Optional[str] = None
    """Phone number for Telegram authentication."""


def config() -> Settings:
    """Load and validate configuration from .env file.

    Returns:
        Settings: Validated configuration object.

    Raises:
        ValidationError: If any required environment variable is missing.
    """
    return Settings()
