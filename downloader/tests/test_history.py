"""Unit tests for downloader.history module."""

import csv
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest

from downloader.history import (
    HISTORY_CSV_COLUMNS,
    DownloadRecord,
    History,
)


class TestHistoryCsvColumns:
    """Tests for HISTORY_CSV_COLUMNS constant."""

    def test_columns_are_unique(self):
        """Test that all CSV columns are unique."""
        assert len(HISTORY_CSV_COLUMNS) == len(set(HISTORY_CSV_COLUMNS))

    def test_columns_contain_required_fields(self):
        """Test that all required fields are present in columns."""
        required_fields = [
            "name",
            "description",
            "category",
            "provider",
            "year",
            "page_url",
            "download_url",
            "format",
            "download_timestamp",
            "download_duration",
        ]
        for field in required_fields:
            assert field in HISTORY_CSV_COLUMNS

    def test_columns_count(self):
        """Test the number of columns."""
        assert len(HISTORY_CSV_COLUMNS) == 10


class TestDownloadRecord:
    """Tests for DownloadRecord dataclass."""

    def test_dataclass_fields(self):
        """Test that DownloadRecord has all expected fields."""
        record = DownloadRecord(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/download",
            format="csv",
            download_timestamp="2024-01-01T12:00:00",
            download_duration=120.5,
        )

        assert record.name == "test_source"
        assert record.description == "Test description"
        assert record.category == "test_category"
        assert record.provider == "test_provider"
        assert record.year == "2024"
        assert record.page_url == "https://example.com/page"
        assert record.download_url == "https://example.com/download"
        assert record.format == "csv"
        assert record.download_timestamp == "2024-01-01T12:00:00"
        assert record.download_duration == 120.5

    def test_from_dict_valid_data(self):
        """Test creating DownloadRecord from valid dictionary."""
        data = {
            "name": "test_source",
            "description": "Test description",
            "category": "test_category",
            "provider": "test_provider",
            "year": "2024",
            "page_url": "https://example.com/page",
            "download_url": "https://example.com/download",
            "format": "csv",
            "download_timestamp": "2024-01-01T12:00:00",
            "download_duration": "120.5",
        }

        record = DownloadRecord.from_dict(data)

        assert record.name == "test_source"
        assert record.download_duration == 120.5
        assert isinstance(record.download_duration, float)

    def test_from_dict_with_integer_duration(self):
        """Test creating DownloadRecord with integer duration (should convert to float)."""
        data = {
            "name": "test",
            "description": "test",
            "category": "test",
            "provider": "test",
            "year": "2024",
            "page_url": "https://example.com",
            "download_url": "https://example.com",
            "format": "csv",
            "download_timestamp": "2024-01-01T12:00:00",
            "download_duration": "120",  # integer as string
        }

        record = DownloadRecord.from_dict(data)
        assert record.download_duration == 120.0
        assert isinstance(record.download_duration, float)

    def test_from_dict_missing_required_field(self):
        """Test that from_dict raises KeyError for missing required field."""
        data = {
            "name": "test",
            "description": "test",
            "category": "test",
            "provider": "test",
            "year": "2024",
            "page_url": "https://example.com",
            "download_url": "https://example.com",
            "format": "csv",
            "download_timestamp": "2024-01-01T12:00:00",
            # missing download_duration
        }

        with pytest.raises(KeyError):
            DownloadRecord.from_dict(data)

    def test_to_dict(self):
        """Test converting DownloadRecord to dictionary."""
        record = DownloadRecord(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/download",
            format="csv",
            download_timestamp="2024-01-01T12:00:00",
            download_duration=120.5,
        )

        data = record.to_dict()

        assert data["name"] == "test_source"
        assert data["description"] == "Test description"
        assert data["category"] == "test_category"
        assert data["provider"] == "test_provider"
        assert data["year"] == "2024"
        assert data["page_url"] == "https://example.com/page"
        assert data["download_url"] == "https://example.com/download"
        assert data["format"] == "csv"
        assert data["download_timestamp"] == "2024-01-01T12:00:00"
        assert data["download_duration"] == 120.5

    def test_to_dict_returns_all_columns(self):
        """Test that to_dict returns all expected columns."""
        record = DownloadRecord(
            name="test",
            description="test",
            category="test",
            provider="test",
            year="2024",
            page_url="https://example.com",
            download_url="https://example.com",
            format="csv",
            download_timestamp="2024-01-01T12:00:00",
            download_duration=120.0,
        )

        data = record.to_dict()
        assert set(data.keys()) == set(HISTORY_CSV_COLUMNS)


class TestHistoryClass:
    """Tests for History class."""

    def test_init_with_default_path(self):
        """Test History initialization with default path."""
        # This test uses a temporary directory to avoid creating files in the wrong location
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the default path calculation
            history = History(history_path=Path(temp_dir) / "download_history.csv")
            assert history.history_path.exists()

    def test_init_with_custom_path(self):
        """Test History initialization with custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_history.csv"
            history = History(str(custom_path))
            assert history.history_path == custom_path
            assert history.history_path.exists()

    def test_create_file_creates_csv_with_headers(self):
        """Test that create_file creates a CSV file with headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            _ = History(str(history_path))

            # File should exist with headers
            assert history_path.exists()

            with open(history_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "name" in content
                assert "download_timestamp" in content
                assert "download_duration" in content

    def test_add_record_and_read_all(self):
        """Test adding records and reading them back."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add a record
            history.add_record(
                name="test_source",
                description="Test description",
                category="test_category",
                provider="test_provider",
                year="2024",
                page_url="https://example.com/page",
                download_url="https://example.com/download",
                format="csv",
                download_duration=120.5,
            )

            # Read all records
            records = history.read_all()
            assert len(records) == 1
            assert records[0].name == "test_source"
            assert records[0].description == "Test description"
            assert records[0].download_duration == 120.5
            assert "download_timestamp" in records[0].to_dict()

    def test_add_multiple_records(self):
        """Test adding multiple records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add multiple records
            for i in range(3):
                history.add_record(
                    name=f"source{i}",
                    description=f"Description {i}",
                    category="category",
                    provider="provider",
                    year="2024",
                    page_url="https://example.com",
                    download_url="https://example.com",
                    format="csv",
                    download_duration=float(i),
                )

            # Read all records
            records = history.read_all()
            assert len(records) == 3
            assert records[0].name == "source0"
            assert records[1].name == "source1"
            assert records[2].name == "source2"

    def test_clear(self):
        """Test clearing all records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add records
            history.add_record(
                name="test",
                description="test",
                category="test",
                provider="test",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            # Verify record exists
            assert len(history.read_all()) == 1

            # Clear records
            history.clear()

            # Verify records are cleared
            assert len(history.read_all()) == 0

            # Verify file still exists with headers
            assert history.history_path.exists()

    def test_exists_true(self):
        """Test exists method returns True for existing record."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add a record
            history.add_record(
                name="existing_source",
                description="test",
                category="test",
                provider="existing_provider",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            # Check if record exists
            assert (
                history.exists("existing_source", "2024", "existing_provider") is True
            )

    def test_exists_false(self):
        """Test exists method returns False for non-existing record."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Check for non-existing record
            assert history.exists("nonexistent", "2024", "nonexistent") is False

    def test_exists_different_provider(self):
        """Test exists method distinguishes by provider."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add a record
            history.add_record(
                name="source",
                description="test",
                category="test",
                provider="provider1",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            # Same name and year, different provider should not exist
            assert history.exists("source", "2024", "provider2") is False

    def test_get_records_by_key(self):
        """Test getting records by source name and year."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add multiple records
            history.add_record(
                name="source1",
                description="test",
                category="test",
                provider="provider",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            history.add_record(
                name="source1",
                description="test",
                category="test",
                provider="provider",
                year="2025",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=15.0,
            )

            history.add_record(
                name="source2",
                description="test",
                category="test",
                provider="provider",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=20.0,
            )

            # Get records for source1
            records = history.get_records_by_key("source1", "2024")
            assert len(records) == 1
            assert records[0].name == "source1"
            assert records[0].year == "2024"

            # Get records for source1 with different year
            records = history.get_records_by_key("source1", "2025")
            assert len(records) == 1
            assert records[0].name == "source1"
            assert records[0].year == "2025"

            # Get records for non-existing source
            records = history.get_records_by_key("nonexistent", "2024")
            assert len(records) == 0

    def test_get_records_by_download_timestamp(self):
        """Test getting records by download timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Add first record
            history.add_record(
                name="early_source",
                description="test",
                category="test",
                provider="provider",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            # Small delay to ensure different timestamps
            import time

            time.sleep(0.01)

            # Add second record
            history.add_record(
                name="late_source",
                description="test",
                category="test",
                provider="provider",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            # Get all records
            all_records = history.read_all()
            assert len(all_records) == 2

            # Get the timestamp from the second record
            late_timestamp = datetime.fromisoformat(all_records[1].download_timestamp)

            # Get records before late timestamp (should include both)
            records = history.get_records_by_download_timestamp(
                late_timestamp + timedelta(seconds=1)
            )
            assert len(records) == 2

            # Get records before early timestamp (should include none)
            early_timestamp = datetime.fromisoformat(all_records[0].download_timestamp)
            records = history.get_records_by_download_timestamp(early_timestamp)
            assert len(records) == 0

            # Get records before late timestamp (should include only first)
            records = history.get_records_by_download_timestamp(late_timestamp)
            assert len(records) == 1
            assert records[0].name == "early_source"

    def test_file_path_property(self):
        """Test file_path property returns absolute path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            file_path = history.file_path
            assert isinstance(file_path, str)
            assert Path(file_path).is_absolute()
            assert Path(file_path).exists()

    def test_record_count_property(self):
        """Test record_count property."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # New file should have 0 records
            assert history.record_count == 0

            # Add a record
            history.add_record(
                name="test",
                description="test",
                category="test",
                provider="test",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            assert history.record_count == 1

    def test_len_dunder(self):
        """Test __len__ method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            assert len(history) == 0

            history.add_record(
                name="test",
                description="test",
                category="test",
                provider="test",
                year="2024",
                page_url="https://example.com",
                download_url="https://example.com",
                format="csv",
                download_duration=10.0,
            )

            assert len(history) == 1

    def test_repr_dunder(self):
        """Test __repr__ method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            repr_str = repr(history)
            assert "History" in repr_str
            assert "file_path" in repr_str
            assert "record_count" in repr_str
            assert "0" in repr_str  # Should show 0 records

    def test_read_all_empty_file(self):
        """Test reading from an empty history file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            records = history.read_all()
            assert records == []

    def test_read_all_nonexistent_file(self):
        """Test reading from a non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "nonexistent.csv"
            history = History(str(history_path))

            # File should be created by init, so this should return empty list
            records = history.read_all()
            assert records == []

    def test_read_all_invalid_schema(self):
        """Test reading from a file with invalid schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "invalid_history.csv"

            # Create a file with invalid schema
            with open(history_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["invalid_column"])
                writer.writeheader()

            history = History(str(history_path))

            with pytest.raises(ValueError, match="CSV file has incorrect schema"):
                history.read_all()

    def test_read_all_invalid_record(self):
        """Test reading from a file with invalid record."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "invalid_record_history.csv"

            # Create a file with valid schema but invalid record
            with open(history_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=HISTORY_CSV_COLUMNS)
                writer.writeheader()
                # Write a row with invalid download_duration
                writer.writerow(
                    {
                        "name": "test",
                        "description": "test",
                        "category": "test",
                        "provider": "test",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                        "download_timestamp": "2024-01-01T12:00:00",
                        "download_duration": "invalid",  # This should cause an error
                    }
                )

            history = History(str(history_path))

            with pytest.raises(ValueError, match="Invalid record in CSV"):
                history.read_all()

    def test_append_record_directly(self):
        """Test _append_record method directly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # Append a record directly
            record = {
                "name": "direct_append",
                "description": "test",
                "category": "test",
                "provider": "test",
                "year": "2024",
                "page_url": "https://example.com",
                "download_url": "https://example.com",
                "format": "csv",
                "download_timestamp": "2024-01-01T12:00:00",
                "download_duration": 15.0,
            }

            history._append_record(record)

            # Read back and verify
            records = history.read_all()
            assert len(records) == 1
            assert records[0].name == "direct_append"

    def test_multiple_operations_sequence(self):
        """Test a sequence of operations on History."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "test_history.csv"
            history = History(str(history_path))

            # 1. Add records
            for i in range(3):
                history.add_record(
                    name=f"source{i}",
                    description=f"Description {i}",
                    category="category",
                    provider="provider",
                    year="2024",
                    page_url="https://example.com",
                    download_url="https://example.com",
                    format="csv",
                    download_duration=float(i * 10),
                )

            assert len(history) == 3

            # 2. Check existence
            assert history.exists("source0", "2024", "provider") is True
            assert history.exists("source1", "2024", "provider") is True
            assert history.exists("nonexistent", "2024", "provider") is False

            # 3. Get records by key
            records = history.get_records_by_key("source1", "2024")
            assert len(records) == 1
            assert records[0].name == "source1"

            # 4. Clear and verify
            history.clear()
            assert len(history) == 0
            assert history.record_count == 0

            # 5. Add new records after clear
            history.add_record(
                name="new_source",
                description="New",
                category="new",
                provider="new",
                year="2025",
                page_url="https://new.com",
                download_url="https://new.com",
                format="json",
                download_duration=5.0,
            )

            assert len(history) == 1
            assert history.exists("new_source", "2025", "new") is True
