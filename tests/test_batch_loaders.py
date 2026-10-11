"""Unit tests for batch data loaders with mocked external dependencies."""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.ingestion.batch_loaders import (
    VadimkinLoader,
    KaggleLoader,
    AcledLoader,
    IswLoader,
)


class TestVadimkinLoader:
    """Tests for VadimkinLoader."""

    @pytest.fixture
    def loader(self):
        """Create a VadimkinLoader instance."""
        return VadimkinLoader(output_dir="/tmp/test_data")

    def test_vadimkin_loader_parse_dates(self, loader):
        """Test Vadimkin loader parses dates to UTC correctly."""
        # Mock CSV data with dates
        csv_data = {
            "started_at": ["2022-02-24 08:00:00", "2022-02-24 09:30:00"],
            "finished_at": ["2022-02-24 10:00:00", pd.NaT],
            "location": ["Kyiv, Kyiv Oblast", "Kharkiv, Kharkiv Oblast"],
        }
        df_raw = pd.DataFrame(csv_data)

        # Mock the load method
        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            # Check that event_time is in milliseconds (as long integer)
            assert df_transformed["event_time"].dtype in ["int64", "Int64"]
            assert all(t > 0 for t in df_transformed["event_time"])

            # Check ingested_at is recent
            now_ms = int(datetime.utcnow().timestamp() * 1000)
            # Within 10 seconds
            assert all(abs(t - now_ms) < 10000 for t in df_transformed["ingested_at"])

            # Check source_id
            assert all(s == "vadimkin" for s in df_transformed["source_id"])

    def test_vadimkin_loader_inferred_flag(self, loader):
        """Test Vadimkin loader detects inferred end times."""
        csv_data = {
            "started_at": ["2022-02-24 08:00:00"],
            "finished_at": [pd.NaT],  # No end time = inferred
            "location": ["Kyiv, Kyiv Oblast"],
        }
        df_raw = pd.DataFrame(csv_data)

        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            # inferred_end_flag should be True when finished_at is NaT
            assert df_transformed["inferred_end_flag"].iloc[0]

    def test_vadimkin_loader_schema_validation(self, loader):
        """Test Vadimkin loader validates required columns."""
        # Missing required columns
        df_invalid = pd.DataFrame({
            "some_col": [1, 2, 3],
        })

        assert loader.validate_schema(df_invalid) is False

    def test_vadimkin_loader_valid_schema(self, loader):
        """Test Vadimkin loader accepts valid schema."""
        df_valid = pd.DataFrame({
            "started_at": ["2022-02-24"],
            "finished_at": ["2022-02-24"],
            "location": ["Kyiv"],
        })

        assert loader.validate_schema(df_valid) is True


class TestKaggleLoader:
    """Tests for KaggleLoader."""

    @pytest.fixture
    def loader(self):
        """Create a KaggleLoader instance."""
        return KaggleLoader(output_dir="/tmp/test_data")

    def test_kaggle_loader_inferred_flag(self, loader):
        """Test Kaggle loader detects inferred end times."""
        csv_data = {
            "start_time": ["2022-02-24 08:00:00", "2022-02-24 09:30:00"],
            "end_time": ["2022-02-24 10:00:00", pd.NaT],  # Second is inferred
            "region": ["Kyiv", "Kharkiv"],
        }
        df_raw = pd.DataFrame(csv_data)

        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            # First record has known end time (not inferred)
            assert not df_transformed["inferred_end_flag"].iloc[0]

            # Second record has NaN end time (inferred)
            assert df_transformed["inferred_end_flag"].iloc[1]

    def test_kaggle_loader_parse_dates(self, loader):
        """Test Kaggle loader parses dates correctly."""
        csv_data = {
            "start_time": ["2022-02-24 08:00:00"],
            "end_time": ["2022-02-24 10:00:00"],
            "region": ["Kyiv"],
        }
        df_raw = pd.DataFrame(csv_data)

        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            # Check event_time in milliseconds
            assert df_transformed["event_time"].dtype in ["int64", "Int64"]
            assert df_transformed["event_time"].iloc[0] > 0

            # Check duration calculation
            assert df_transformed["duration"].iloc[0] > 0

    def test_kaggle_loader_schema_validation(self, loader):
        """Test Kaggle loader validates required columns."""
        df_invalid = pd.DataFrame({
            "other_col": [1, 2, 3],
        })

        assert loader.validate_schema(df_invalid) is False

    def test_kaggle_loader_valid_schema(self, loader):
        """Test Kaggle loader accepts valid schema."""
        df_valid = pd.DataFrame({
            "start_time": ["2022-02-24"],
            "end_time": ["2022-02-24"],
            "region": ["Kyiv"],
        })

        assert loader.validate_schema(df_valid) is True

    def test_kaggle_loader_license(self, loader):
        """Test Kaggle loader documents license."""
        assert "CC-BY-NC-SA" in loader.license
        assert "Non-commercial" in loader.license


class TestAcledLoader:
    """Tests for AcledLoader."""

    @pytest.fixture
    def loader(self):
        """Create an AcledLoader instance."""
        return AcledLoader(api_key="test_key", output_dir="/tmp/test_data")

    def test_acled_loader_pagination(self, loader):
        """Test ACLED loader paginates results correctly."""
        # Mock API responses
        page1_response = {
            "data": [
                {
                    "event_id_cnty": "1001",
                    "event_type": "Protests",
                    "event_date": "24 Feb 2022",
                    "fatalities": 0,
                },
                {
                    "event_id_cnty": "1002",
                    "event_type": "Violence against civilians",
                    "event_date": "25 Feb 2022",
                    "fatalities": 5,
                },
            ]
        }

        # Mock requests.get to return paginated data
        with patch('requests.get') as mock_get:
            # First call returns data, second call returns empty
            mock_response1 = Mock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = page1_response

            mock_response2 = Mock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {"data": []}

            mock_get.side_effect = [mock_response1, mock_response2]

            df = loader.load()

            # Should have 2 records
            assert len(df) == 2
            assert df.iloc[0]["event_id_cnty"] == "1001"
            assert df.iloc[1]["event_id_cnty"] == "1002"

    def test_acled_loader_handles_missing_key(self, loader):
        """Test ACLED loader handles missing API key gracefully."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="access denied"):
                loader.load()

    def test_acled_loader_handles_404(self, loader):
        """Test ACLED loader handles 404 endpoint not found."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            df = loader.load()

            # Should return empty DataFrame on 404
            assert df.empty

    def test_acled_loader_transform(self, loader):
        """Test ACLED loader transforms data to osint_batch schema."""
        acled_data = {
            "event_id_cnty": ["1001"],
            "event_type": ["Protests"],
            "event_date": ["24 Feb 2022"],
            "fatalities": [0],
        }
        df_raw = pd.DataFrame(acled_data)

        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            # Check schema fields
            assert "event_time" in df_transformed.columns
            assert "ingested_at" in df_transformed.columns
            assert "source_id" in df_transformed.columns
            assert "event_type" in df_transformed.columns
            assert df_transformed["source_id"].iloc[0] == "acled"

    def test_acled_loader_schema_validation(self, loader):
        """Test ACLED loader validates required columns."""
        df_invalid = pd.DataFrame({
            "other_col": [1, 2, 3],
        })

        # Empty DataFrame should be valid
        assert loader.validate_schema(pd.DataFrame()) is True

        # Invalid schema should fail
        assert loader.validate_schema(df_invalid) is False

    def test_acled_loader_valid_schema(self, loader):
        """Test ACLED loader accepts valid schema."""
        df_valid = pd.DataFrame({
            "event_id_cnty": ["1001"],
            "event_type": ["Protests"],
            "event_date": ["24 Feb 2022"],
        })

        assert loader.validate_schema(df_valid) is True


class TestIswLoader:
    """Tests for IswLoader."""

    @pytest.fixture
    def loader(self):
        """Create an IswLoader instance."""
        return IswLoader(output_dir="/tmp/test_data")

    def test_isw_loader_extract_threat_level(self, loader):
        """Test ISW loader extracts threat levels from HTML."""
        html_text = """
        <html>
            <body>
                Kyiv region: The threat level is high and operational intensity remains critical.
                Kharkiv region: Moderate threat levels observed in recent assessments.
                Donetsk region: Low threat level with limited engagement.
            </body>
        </html>
        """

        records = loader._extract_threat_assessments(html_text)

        # Should extract at least one region with threat level
        assert len(records) >= 1

    def test_isw_loader_threat_to_intensity_mapping(self, loader):
        """Test ISW loader maps threat levels to intensity index."""
        isw_data = {
            "region": ["Kyiv", "Kharkiv", "Donetsk"],
            "threat_level": ["high", "moderate", "low"],
            "event_date": ["24 Feb 2022", "24 Feb 2022", "24 Feb 2022"],
        }
        df_raw = pd.DataFrame(isw_data)

        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            # Check intensity index mapping
            assert df_transformed["ops_intensity_index"].iloc[0] == 1.0  # high
            assert df_transformed["ops_intensity_index"].iloc[1] == 0.66  # moderate
            assert df_transformed["ops_intensity_index"].iloc[2] == 0.33  # low

    def test_isw_loader_schema_validation(self, loader):
        """Test ISW loader validates required columns."""
        df_invalid = pd.DataFrame({
            "other_col": [1, 2, 3],
        })

        # Empty DataFrame should be valid
        assert loader.validate_schema(pd.DataFrame()) is True

        # Invalid schema should fail
        assert loader.validate_schema(df_invalid) is False

    def test_isw_loader_valid_schema(self, loader):
        """Test ISW loader accepts valid schema."""
        df_valid = pd.DataFrame({
            "region": ["Kyiv"],
            "threat_level": ["high"],
            "event_date": ["24 Feb 2022"],
        })

        assert loader.validate_schema(df_valid) is True

    def test_isw_loader_transform(self, loader):
        """Test ISW loader transforms to osint_batch schema."""
        isw_data = {
            "region": ["Kyiv"],
            "threat_level": ["high"],
            "event_date": ["24 Feb 2022"],
        }
        df_raw = pd.DataFrame(isw_data)

        with patch.object(loader, 'load', return_value=df_raw):
            df_loaded = loader.load()
            df_transformed = loader.transform(df_loaded)

            assert "event_time" in df_transformed.columns
            assert "ingested_at" in df_transformed.columns
            assert "source_id" in df_transformed.columns
            assert "threat_level_by_region" in df_transformed.columns
            assert df_transformed["source_id"].iloc[0] == "isw"


class TestLoaderIntegration:
    """Integration tests for batch loaders."""

    def test_loader_parquet_save(self):
        """Test loaders can prepare data to Parquet format."""
        loader = VadimkinLoader(output_dir="/tmp/test_data")

        # Create sample data
        df = pd.DataFrame({
            "event_time": [1645526400000],
            "ingested_at": [int(datetime.utcnow().timestamp() * 1000)],
            "source_id": ["vadimkin"],
            "alert_count_15m": [1],
            "alert_count_1h": [1],
            "alert_count_6h": [1],
            "alert_count_24h": [1],
            "active_flag": [False],
            "oblast": ["Kyiv"],
            "h3": [None],
            "duration": [7200000],
            "time_since_last_alert": [None],
            "neighbor_active_count": [0],
            "inferred_end_flag": [False],
        })

        # Mock the to_parquet method since pyarrow may not be installed
        with patch.object(df, 'to_parquet') as mock_save:
            output_path = loader.save_parquet(df, "test_alerts.parquet")

            # Verify to_parquet was called
            mock_save.assert_called_once()
            assert output_path.name == "test_alerts.parquet"
