"""
Entry point for Ukrainian Air Raid Alerts analysis pipeline.
Validates configuration on startup.
"""

from src.config import config


def main() -> None:
    """Load and validate configuration, then print status."""
    try:
        config()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        raise


if __name__ == "__main__":
    main()
