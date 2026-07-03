"""Unit tests for the Downloader module."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from downloader.conf import SourceConfig
from downloader.downloader import Downloader
from downloader.history import DownloadRecord


class TestGenerateFilename:
    """Tests for _generate_filename method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.downloader = Downloader(output_dir="/tmp/test")

    def test_filename_with_single_year(self):
        """Test filename generation with a single year."""
        source = SourceConfig(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/file.csv",
            format="csv",
        )
        result = self.downloader._generate_filename(source)
        assert result == "test_source_2024.csv"

    def test_filename_with_year_range(self):
        """Test filename generation with a year range (replaces - with _)."""
        source = SourceConfig(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024-2026",
            page_url="https://example.com/page",
            download_url="https://example.com/file.csv",
            format="csv",
        )
        result = self.downloader._generate_filename(source)
        assert result == "test_source_2024_2026.csv"

    def test_filename_with_parquet_format(self):
        """Test filename generation with parquet format."""
        source = SourceConfig(
            name="data",
            description="Test",
            category="cat",
            provider="prov",
            year="2025",
            page_url="https://example.com",
            download_url="https://example.com/data.parquet",
            format="parquet",
        )
        result = self.downloader._generate_filename(source)
        assert result == "data_2025.parquet"


class TestDownloadFile:
    """Tests for _download_file method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.downloader = Downloader(output_dir="/tmp/test")

    @patch("downloader.downloader.requests.get")
    def test_successful_download(self, mock_get):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b"test data"]
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            success, error = self.downloader._download_file(
                "https://example.com/file.csv", tmp_path
            )
            assert success is True
            assert error is None
            assert tmp_path.read_bytes() == b"test data"
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("downloader.downloader.requests.get")
    def test_failed_download_request_exception(self, mock_get):
        """Test failed download due to request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            success, error = self.downloader._download_file(
                "https://example.com/file.csv", tmp_path
            )
            assert success is False
            assert error == "Connection error"
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("downloader.downloader.requests.get")
    def test_failed_download_io_error(self, mock_get):
        """Test failed download due to IO error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.side_effect = IOError("Write error")
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            success, error = self.downloader._download_file(
                "https://example.com/file.csv", tmp_path
            )
            assert success is False
            assert error == "Write error"
        finally:
            tmp_path.unlink(missing_ok=True)


class TestDownloadSource:
    """Tests for download_source method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = Downloader(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("downloader.downloader.Downloader._download_file")
    @patch("downloader.downloader.time.sleep")
    def test_successful_download(self, mock_sleep, mock_download_file):
        """Test successful source download."""
        mock_download_file.return_value = (True, None)

        source = SourceConfig(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/file.csv",
            format="csv",
        )

        success, record, error = self.downloader.download_source(source)

        assert success is True
        assert record is not None
        assert isinstance(record, DownloadRecord)
        assert record.name == "test_source"
        assert record.format == "csv"
        assert error is None

    @patch("downloader.downloader.Downloader._download_file")
    def test_failed_download_after_retries(self, mock_download_file):
        """Test download fails after all retry attempts."""
        mock_download_file.return_value = (False, "Connection error")

        source = SourceConfig(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/file.csv",
            format="csv",
        )

        success, record, error = self.downloader.download_source(source)

        assert success is False
        assert record is None
        assert error == "Connection error"
        assert mock_download_file.call_count == 3  # Default retry_count is 3

    @patch("downloader.downloader.Downloader._download_file")
    @patch("downloader.downloader.time.sleep")
    def test_download_with_retry(self, mock_sleep, mock_download_file):
        """Test download succeeds after retry."""
        mock_download_file.side_effect = [
            (False, "First error"),
            (False, "Second error"),
            (True, None),
        ]

        source = SourceConfig(
            name="test_source",
            description="Test description",
            category="test_category",
            provider="test_provider",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/file.csv",
            format="csv",
        )

        success, record, error = self.downloader.download_source(source)

        assert success is True
        assert record is not None
        assert error is None
        assert mock_download_file.call_count == 3
        assert mock_sleep.call_count == 2


class TestDownloadAll:
    """Tests for download_all method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = Downloader(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("downloader.downloader.Downloader.download_source")
    def test_download_all_success(self, mock_download_source):
        """Test download_all with all successful downloads."""
        source1 = SourceConfig(
            name="source1",
            description="Desc1",
            category="cat1",
            provider="prov1",
            year="2024",
            page_url="https://example.com/page1",
            download_url="https://example.com/file1.csv",
            format="csv",
        )
        source2 = SourceConfig(
            name="source2",
            description="Desc2",
            category="cat2",
            provider="prov2",
            year="2025",
            page_url="https://example.com/page2",
            download_url="https://example.com/file2.json",
            format="json",
        )

        mock_download_source.side_effect = [
            (
                True,
                DownloadRecord(
                    name="source1",
                    description="Desc1",
                    category="cat1",
                    provider="prov1",
                    year="2024",
                    page_url="https://example.com/page1",
                    download_url="https://example.com/file1.csv",
                    format="csv",
                    download_timestamp=datetime.now().isoformat(),
                    download_duration=1.0,
                ),
                None,
            ),
            (
                True,
                DownloadRecord(
                    name="source2",
                    description="Desc2",
                    category="cat2",
                    provider="prov2",
                    year="2025",
                    page_url="https://example.com/page2",
                    download_url="https://example.com/file2.json",
                    format="json",
                    download_timestamp=datetime.now().isoformat(),
                    download_duration=2.0,
                ),
                None,
            ),
        ]

        result = self.downloader.download_all([source1, source2])

        assert len(result) == 2
        assert all(isinstance(r, DownloadRecord) for r in result)
        assert result[0].name == "source1"
        assert result[1].name == "source2"

    @patch("downloader.downloader.Downloader.download_source")
    def test_download_all_with_failures(self, mock_download_source):
        """Test download_all with some failures."""
        source1 = SourceConfig(
            name="source1",
            description="Desc1",
            category="cat1",
            provider="prov1",
            year="2024",
            page_url="https://example.com/page1",
            download_url="https://example.com/file1.csv",
            format="csv",
        )
        source2 = SourceConfig(
            name="source2",
            description="Desc2",
            category="cat2",
            provider="prov2",
            year="2025",
            page_url="https://example.com/page2",
            download_url="https://example.com/file2.json",
            format="json",
        )

        mock_download_source.side_effect = [
            (
                True,
                DownloadRecord(
                    name="source1",
                    description="Desc1",
                    category="cat1",
                    provider="prov1",
                    year="2024",
                    page_url="https://example.com/page1",
                    download_url="https://example.com/file1.csv",
                    format="csv",
                    download_timestamp=datetime.now().isoformat(),
                    download_duration=1.0,
                ),
                None,
            ),
            (False, None, "Download failed"),
        ]

        result = self.downloader.download_all([source1, source2])

        assert len(result) == 1
        assert result[0].name == "source1"


class TestDownloaderInit:
    """Tests for Downloader initialization."""

    def test_default_output_dir(self):
        """Test Downloader with default output directory."""
        with patch.object(Path, "mkdir") as mock_mkdir:
            downloader = Downloader()
            assert downloader.output_dir.exists() or mock_mkdir.called
            assert downloader.timeout == 30
            assert downloader.retry_count == 3

    def test_custom_output_dir(self):
        """Test Downloader with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = Downloader(output_dir=tmpdir)
            assert downloader.output_dir == Path(tmpdir)

    def test_custom_timeout_and_retry(self):
        """Test Downloader with custom timeout and retry count."""
        downloader = Downloader(timeout=60, retry_count=5)
        assert downloader.timeout == 60
        assert downloader.retry_count == 5
