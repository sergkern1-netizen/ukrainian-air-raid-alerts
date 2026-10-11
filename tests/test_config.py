"""
Tests for configuration module.
Validates that all required environment variables are loaded correctly.
"""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError
from src.config import Settings, config


@pytest.fixture
def env_vars():
    """Load example environment variables from .env.example."""
    env_file = Path(__file__).parent.parent / ".env.example"
    env_dict = {}

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_dict[key.strip()] = value.strip()

    return env_dict


@pytest.fixture(autouse=True)
def setup_env(env_vars):
    """Set up environment variables for tests."""
    for key, value in env_vars.items():
        os.environ[key] = value

    yield

    # Cleanup
    for key in env_vars.keys():
        os.environ.pop(key, None)


def test_config_loads_successfully(env_vars):
    """Test that config loads all required fields from .env.example."""
    cfg = config()
    assert isinstance(cfg, Settings)


def test_all_required_fields_populated(env_vars):
    """Test that all required configuration fields are populated."""
    cfg = config()
    assert cfg.api_token
    assert cfg.kafka_brokers
    assert cfg.timescale_url
    assert cfg.redis_url
    assert cfg.isw_scrape_url


def test_missing_required_field_raises_error():
    """Test that missing required field raises ValidationError."""
    # Clear all env vars and provide a non-existent .env file path
    os.environ.pop("API_TOKEN", None)
    os.environ.pop("KAFKA_BROKERS", None)
    os.environ.pop("TIMESCALE_URL", None)
    os.environ.pop("REDIS_URL", None)
    os.environ.pop("ISW_SCRAPE_URL", None)

    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict

    class TestSettings(BaseSettings):
        model_config = ConfigDict(env_file=".env.nonexistent", case_sensitive=False)
        api_token: str
        kafka_brokers: str
        timescale_url: str
        redis_url: str
        isw_scrape_url: str

    with pytest.raises(ValidationError):
        TestSettings()


def test_config_returns_settings_instance(env_vars):
    """Test that config() returns a Settings instance."""
    result = config()
    assert isinstance(result, Settings)
    assert hasattr(result, "api_token")
    assert hasattr(result, "kafka_brokers")
    assert hasattr(result, "timescale_url")
    assert hasattr(result, "redis_url")
    assert hasattr(result, "isw_scrape_url")
