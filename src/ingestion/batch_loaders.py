"""Batch data loaders for Ukrainian air raid alerts from multiple sources.

Handles ingestion from Vadimkin, Kaggle, ACLED, and ISW with validation,
schema enforcement, and Kafka publishing.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from avro.io import BinaryEncoder, DatumWriter
from avro.schema import parse as parse_schema

logger = logging.getLogger(__name__)


class BatchLoader(ABC):
    """Abstract base class for batch data loaders."""

    def __init__(self, kafka_brokers: Optional[str] = None, output_dir: str = "data/raw/"):
        """Initialize batch loader.

        Args:
            kafka_brokers: Comma-separated Kafka broker addresses (optional).
            output_dir: Directory to save Parquet files.
        """
        self.kafka_brokers = kafka_brokers
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load data from source.

        Returns:
            DataFrame with raw data.
        """
        pass

    @abstractmethod
    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate DataFrame against target schema.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.
        """
        pass

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data to target schema.

        Args:
            df: Raw DataFrame.

        Returns:
            Transformed DataFrame.
        """
        pass

    def save_parquet(self, df: pd.DataFrame, filename: str) -> Path:
        """Save DataFrame to Parquet.

        Args:
            df: DataFrame to save.
            filename: Output filename.

        Returns:
            Path to saved file.
        """
        output_path = self.output_dir / filename
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved {len(df)} records to {output_path}")
        return output_path

    def publish_to_kafka(self, df: pd.DataFrame, topic: str, schema: Dict[str, Any]) -> int:
        """Publish DataFrame records to Kafka topic as Avro.

        Args:
            df: DataFrame with records to publish.
            topic: Kafka topic name.
            schema: Avro schema dict.

        Returns:
            Number of records published.
        """
        if not self.kafka_brokers:
            logger.warning(f"No Kafka brokers configured; skipping publish to {topic}")
            return 0

        try:
            from kafka import KafkaProducer
        except ImportError:
            logger.warning("kafka-python not installed; skipping Kafka publish")
            return 0

        avro_schema = parse_schema(json.dumps(schema))
        producer = KafkaProducer(bootstrap_servers=self.kafka_brokers.split(","))

        count = 0
        for _, row in df.iterrows():
            record = row.to_dict()
            encoder = BinaryEncoder(BytesIO())
            writer = DatumWriter(avro_schema)
            writer.write(record, encoder)
            producer.send(topic, encoder.writer.getvalue())
            count += 1

        producer.flush()
        producer.close()
        logger.info(f"Published {count} records to Kafka topic '{topic}'")
        return count


class VadimkinLoader(BatchLoader):
    """Load air raid alert data from Vadimkin GitHub releases."""

    GITHUB_API_URL = (
        "https://api.github.com/repos/Vadimkin/"
        "ukrainian-air-raid-sirens-dataset/releases"
    )

    def __init__(self, kafka_brokers: Optional[str] = None, output_dir: str = "data/raw/"):
        """Initialize Vadimkin loader."""
        super().__init__(kafka_brokers, output_dir)
        self.source_id = "vadimkin"

    def load(self) -> pd.DataFrame:
        """Load latest CSV from GitHub releases.

        Returns:
            DataFrame with raw alert data.
        """
        logger.info("Fetching latest release from Vadimkin GitHub...")
        try:
            resp = requests.get(self.GITHUB_API_URL, timeout=10)
            resp.raise_for_status()
            releases = resp.json()

            if not releases:
                raise ValueError("No releases found in Vadimkin repository")

            # Find latest release with asset
            for release in releases:
                for asset in release.get("assets", []):
                    if asset["name"].endswith(".csv"):
                        csv_url = asset["browser_download_url"]
                        logger.info(f"Downloading {asset['name']} from {csv_url}")
                        csv_resp = requests.get(csv_url, timeout=30)
                        csv_resp.raise_for_status()
                        df = pd.read_csv(BytesIO(csv_resp.content))
                        logger.info(f"Loaded {len(df)} records from Vadimkin")
                        return df

            raise ValueError("No CSV asset found in releases")
        except Exception as e:
            logger.error(f"Failed to load Vadimkin data: {e}")
            raise

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate required columns for Vadimkin data.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.
        """
        required_cols = {"started_at", "finished_at", "location"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.error(f"Missing required columns: {missing}")
            return False
        return True

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Vadimkin data to alerts_raw schema.

        Args:
            df: Raw Vadimkin DataFrame.

        Returns:
            Transformed DataFrame.
        """
        if not self.validate_schema(df):
            raise ValueError("Schema validation failed")

        # Parse dates to UTC timestamps (milliseconds)
        df["event_time"] = pd.to_datetime(df["started_at"], utc=True).astype("int64") // 1_000_000
        df["ingested_at"] = int(datetime.utcnow().timestamp() * 1000)
        df["source_id"] = self.source_id

        # Map Vadimkin columns to alerts_raw schema
        transformed = pd.DataFrame({
            "event_time": df["event_time"],
            "ingested_at": df["ingested_at"],
            "source_id": df["source_id"],
            "alert_count_15m": 1,  # Each record is one alert
            "alert_count_1h": 1,
            "alert_count_6h": 1,
            "alert_count_24h": 1,
            "active_flag": df["finished_at"].isna(),
            "oblast": df["location"].str.split(",").str[0] if "location" in df.columns else None,
            "h3": None,
            "duration": (
                (pd.to_datetime(df["finished_at"], utc=True).astype("int64") // 1_000_000
                 - df["event_time"]).fillna(0).astype("Int64")
            ) if "finished_at" in df.columns else None,
            "time_since_last_alert": None,
            "neighbor_active_count": 0,
            "inferred_end_flag": df["finished_at"].isna() if "finished_at" in df.columns else False,
        })

        logger.info(f"Transformed {len(transformed)} Vadimkin records")
        return transformed


class KaggleLoader(BatchLoader):
    """Load air raid alert data from Kaggle dataset."""

    DATASET_NAME = "p0stscriptum/air-raid-dataset"

    def __init__(self, kafka_brokers: Optional[str] = None, output_dir: str = "data/raw/"):
        """Initialize Kaggle loader."""
        super().__init__(kafka_brokers, output_dir)
        self.source_id = "kaggle"
        self.license = "CC-BY-NC-SA 4.0: Non-commercial use only"

    def load(self) -> pd.DataFrame:
        """Load Kaggle dataset using kaggle API.

        Returns:
            DataFrame with raw alert data.

        Raises:
            ImportError: If kaggle package not installed.
        """
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            logger.error("kaggle package not installed; install with: pip install kaggle")
            raise

        logger.info(f"Loading Kaggle dataset: {self.DATASET_NAME}")
        try:
            api = KaggleApi()
            api.authenticate()

            # Download to temp directory
            download_dir = self.output_dir / ".kaggle_temp"
            download_dir.mkdir(parents=True, exist_ok=True)

            api.dataset_download_files(self.DATASET_NAME, path=download_dir, unzip=True)

            # Find CSV file
            csv_files = list(download_dir.glob("*.csv"))
            if not csv_files:
                raise ValueError(f"No CSV files found in {download_dir}")

            df = pd.read_csv(csv_files[0])
            logger.info(f"Loaded {len(df)} records from Kaggle")
            return df
        except Exception as e:
            logger.error(f"Failed to load Kaggle data: {e}")
            raise

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate required columns for Kaggle data.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.
        """
        required_cols = {"start_time", "end_time", "region"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.error(f"Missing required columns: {missing}")
            return False
        return True

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Kaggle data to alerts_raw schema.

        Args:
            df: Raw Kaggle DataFrame.

        Returns:
            Transformed DataFrame.
        """
        if not self.validate_schema(df):
            raise ValueError("Schema validation failed")

        # Detect inferred end_time (NaN or specific marker)
        df["inferred_end_flag"] = df["end_time"].isna()

        # Parse dates to UTC timestamps (milliseconds)
        df["event_time"] = pd.to_datetime(df["start_time"], utc=True).astype("int64") // 1_000_000
        df["ingested_at"] = int(datetime.utcnow().timestamp() * 1000)
        df["source_id"] = self.source_id

        # Calculate duration if end_time available
        duration = None
        if "end_time" in df.columns and df["end_time"].notna().any():
            duration = (
                (pd.to_datetime(df["end_time"], utc=True).astype("int64") // 1_000_000
                 - df["event_time"]).fillna(0)
            )

        transformed = pd.DataFrame({
            "event_time": df["event_time"],
            "ingested_at": df["ingested_at"],
            "source_id": df["source_id"],
            "alert_count_15m": 1,
            "alert_count_1h": 1,
            "alert_count_6h": 1,
            "alert_count_24h": 1,
            "active_flag": df["inferred_end_flag"],
            "oblast": df["region"].str.strip() if "region" in df.columns else None,
            "h3": None,
            "duration": duration,
            "time_since_last_alert": None,
            "neighbor_active_count": 0,
            "inferred_end_flag": df["inferred_end_flag"],
        })

        inferred_count = df['inferred_end_flag'].sum()
        logger.info(
            f"Transformed {len(transformed)} Kaggle records "
            f"({inferred_count} inferred)"
        )
        return transformed


class AcledLoader(BatchLoader):
    """Load conflict events from ACLED API."""

    API_URL = "https://api.acleddata.com/api/events/"
    MAX_RETRIES = 3

    def __init__(self, api_key: Optional[str] = None, kafka_brokers: Optional[str] = None,
                 output_dir: str = "data/raw/"):
        """Initialize ACLED loader.

        Args:
            api_key: ACLED API key.
            kafka_brokers: Kafka broker addresses.
            output_dir: Output directory.
        """
        super().__init__(kafka_brokers, output_dir)
        self.source_id = "acled"
        self.api_key = api_key
        self.params = {
            "country": "Ukraine",
            "limit": 1000,
        }

    def load(self) -> pd.DataFrame:
        """Load events from ACLED API with pagination.

        Returns:
            DataFrame with ACLED events.
        """
        logger.info("Fetching ACLED events for Ukraine...")
        all_records: List[Dict[str, Any]] = []
        offset = 0
        page = 1

        while True:
            params = {**self.params, "offset": offset}
            if self.api_key:
                params["api_key"] = self.api_key

            try:
                resp = requests.get(self.API_URL, params=params, timeout=10)

                if resp.status_code == 403:
                    logger.error("Access denied (403); check API key or registration")
                    raise ValueError("ACLED API access denied")
                elif resp.status_code == 404:
                    logger.warning("ACLED API endpoint not found (404)")
                    break
                elif resp.status_code != 200:
                    logger.error(f"ACLED API error {resp.status_code}: {resp.text}")
                    break

                data = resp.json()
                records = data.get("data", [])

                if not records:
                    logger.info(f"No more records at offset {offset}")
                    break

                all_records.extend(records)
                logger.info(
                    f"Page {page}: fetched {len(records)} records "
                    f"(total: {len(all_records)})"
                )

                offset += len(records)
                page += 1

                if len(records) < self.params["limit"]:
                    break

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                break

        if not all_records:
            logger.warning("No ACLED records fetched")
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        logger.info(f"Loaded {len(df)} ACLED records")
        return df

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate required ACLED columns.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.
        """
        if df.empty:
            return True

        required_cols = {"event_id_cnty", "event_type", "event_date"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.error(f"Missing required columns: {missing}")
            return False
        return True

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform ACLED events to osint_batch schema.

        Args:
            df: Raw ACLED DataFrame.

        Returns:
            Transformed DataFrame.
        """
        if df.empty:
            return pd.DataFrame()

        if not self.validate_schema(df):
            raise ValueError("Schema validation failed")

        # Parse date to UTC timestamp (milliseconds)
        df["event_time"] = (
            pd.to_datetime(df["event_date"], format="%d %b %Y", utc=True)
            .astype("int64") // 1_000_000
        )
        df["ingested_at"] = int(datetime.utcnow().timestamp() * 1000)

        transformed = pd.DataFrame({
            "event_time": df["event_time"],
            "ingested_at": df["ingested_at"],
            "source_id": self.source_id,
            "event_type": df["event_type"],
            "h3": None,
            "fatality_estimate": (
                df["fatalities"].astype("Int64")
                if "fatalities" in df.columns else None
            ),
            "source_confidence": 0.8,  # ACLED confidence
            "threat_level_by_region": None,
            "ops_intensity_index": None,
            "distance_frontline_km": None,
        })

        logger.info(f"Transformed {len(transformed)} ACLED events")
        return transformed


class IswLoader(BatchLoader):
    """Load threat assessments from ISW (Institute for the Study of War)."""

    DEFAULT_URL = "https://www.understandingwar.org/backgrounder"

    def __init__(self, url: Optional[str] = None, kafka_brokers: Optional[str] = None,
                 output_dir: str = "data/raw/"):
        """Initialize ISW loader.

        Args:
            url: ISW briefing URL (optional).
            kafka_brokers: Kafka broker addresses.
            output_dir: Output directory.
        """
        super().__init__(kafka_brokers, output_dir)
        self.source_id = "isw"
        self.url = url or self.DEFAULT_URL

    def load(self) -> pd.DataFrame:
        """Load ISW daily assessment (mock implementation).

        Returns:
            DataFrame with threat level data.
        """
        logger.info(f"Fetching ISW assessment from {self.url}")
        try:
            resp = requests.get(self.url, timeout=10)
            resp.raise_for_status()

            # Extract threat assessment text from HTML
            text = resp.text
            records = self._extract_threat_assessments(text)

            if not records:
                logger.warning("No threat assessments extracted from ISW page")
                return pd.DataFrame()

            df = pd.DataFrame(records)
            logger.info(f"Extracted {len(df)} threat assessment records from ISW")
            return df
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch ISW data: {e}")
            return pd.DataFrame()

    def _extract_threat_assessments(self, html_text: str) -> List[Dict[str, Any]]:
        """Extract threat level assessments from HTML text (simplified).

        Args:
            html_text: HTML content.

        Returns:
            List of threat assessment records.
        """
        records = []

        # Simple regex pattern to find threat level mentions
        threat_patterns = {
            "high": r"(?i)(critical|high threat|intensive)",
            "moderate": r"(?i)(moderate|medium threat)",
            "low": r"(?i)(low threat|limited)",
        }

        regions = ["Kyiv", "Kharkiv", "Donetsk", "Luhansk", "Zaporizhzhia", "Sumy"]

        for region in regions:
            threat_keys = "|".join(threat_patterns.keys())
            pattern = rf"{region}[^.]*?({threat_keys})"
            region_match = re.search(pattern, html_text, re.IGNORECASE)
            if region_match:
                threat_text = region_match.group(0).lower()
                threat_level = None

                for level, pattern in threat_patterns.items():
                    if re.search(pattern, threat_text):
                        threat_level = level
                        break

                if threat_level:
                    records.append({
                        "region": region,
                        "threat_level": threat_level,
                        "event_date": datetime.utcnow().strftime("%d %b %Y"),
                    })

        return records

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate required ISW columns.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.
        """
        if df.empty:
            return True

        required_cols = {"region", "threat_level", "event_date"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            logger.error(f"Missing required columns: {missing}")
            return False
        return True

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform ISW threat assessments to osint_batch schema.

        Args:
            df: Raw ISW DataFrame.

        Returns:
            Transformed DataFrame.
        """
        if df.empty:
            return pd.DataFrame()

        if not self.validate_schema(df):
            raise ValueError("Schema validation failed")

        # Parse date to UTC timestamp (milliseconds)
        df["event_time"] = (
            pd.to_datetime(df["event_date"], format="%d %b %Y", utc=True)
            .astype("int64") // 1_000_000
        )
        df["ingested_at"] = int(datetime.utcnow().timestamp() * 1000)

        # Map threat level to intensity index
        threat_to_intensity = {"low": 0.33, "moderate": 0.66, "high": 1.0}
        df["ops_intensity_index"] = df["threat_level"].map(threat_to_intensity)

        transformed = pd.DataFrame({
            "event_time": df["event_time"],
            "ingested_at": df["ingested_at"],
            "source_id": self.source_id,
            "event_type": "threat_assessment",
            "h3": None,
            "fatality_estimate": None,
            "source_confidence": 0.7,  # ISW confidence
            "threat_level_by_region": df["threat_level"],
            "ops_intensity_index": df["ops_intensity_index"],
            "distance_frontline_km": None,
        })

        logger.info(f"Transformed {len(transformed)} ISW threat assessments")
        return transformed
