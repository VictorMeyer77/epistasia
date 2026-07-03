"""Unit tests for downloader.conf module."""

import json
import tempfile
from pathlib import Path
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from downloader.conf import Conf, FileFormat, SourceConfig


class TestFileFormat:
    """Tests for FileFormat enum."""

    def test_file_format_values(self):
        """Test that FileFormat enum has expected values."""
        assert FileFormat.PARQUET.value == "parquet"
        assert FileFormat.JSON.value == "json"
        assert FileFormat.XLSX.value == "xlsx"
        assert FileFormat.CSV.value == "csv"
        assert FileFormat.ZIP.value == "zip"

    def test_file_format_all_values_are_strings(self):
        """Test that all FileFormat values are strings."""
        for fmt in FileFormat:
            assert isinstance(fmt.value, str)

    def test_file_format_set_of_values(self):
        """Test getting all valid format values as a set."""
        valid_formats = {member.value for member in FileFormat}
        expected = {"parquet", "json", "xlsx", "csv", "zip"}
        assert valid_formats == expected


class TestSourceConfigValidation:
    """Tests for SourceConfig validation methods."""

    def test_validate_year_valid_single_year(self):
        """Test validation of valid single year format."""
        SourceConfig._validate_year("2024")
        SourceConfig._validate_year("1999")
        SourceConfig._validate_year("2000")

    def test_validate_year_valid_year_range(self):
        """Test validation of valid year range format."""
        SourceConfig._validate_year("2024-2026")
        SourceConfig._validate_year("2000-2010")
        SourceConfig._validate_year("1999-2000")

    def test_validate_year_invalid_format_too_short(self):
        """Test validation fails for year with too few digits."""
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("24")

    def test_validate_year_invalid_format_too_long(self):
        """Test validation fails for year with too many digits."""
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("20245")

    def test_validate_year_invalid_format_wrong_separator(self):
        """Test validation fails for year range with wrong separator."""
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("2024/2026")

    def test_validate_year_invalid_format_non_numeric(self):
        """Test validation fails for non-numeric year."""
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("abcd")

    def test_validate_year_invalid_format_empty(self):
        """Test validation fails for empty year."""
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("")

    def test_validate_year_invalid_range_format(self):
        """Test validation fails for malformed year range."""
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("2024-")
        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig._validate_year("-2026")

    def test_validate_format_valid_formats(self):
        """Test validation of all valid formats."""
        for fmt in FileFormat:
            SourceConfig._validate_format(fmt.value)

    def test_validate_format_valid_format_strings(self):
        """Test validation with valid format strings."""
        SourceConfig._validate_format("csv")
        SourceConfig._validate_format("json")
        SourceConfig._validate_format("parquet")

    def test_validate_format_invalid_format(self):
        """Test validation fails for invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            SourceConfig._validate_format("invalid")
        with pytest.raises(ValueError, match="Invalid format"):
            SourceConfig._validate_format("txt")
        with pytest.raises(ValueError, match="Invalid format"):
            SourceConfig._validate_format("")

    def test_validate_format_case_sensitive(self):
        """Test that format validation is case-sensitive."""
        with pytest.raises(ValueError, match="Invalid format"):
            SourceConfig._validate_format("CSV")
        with pytest.raises(ValueError, match="Invalid format"):
            SourceConfig._validate_format("Json")


class TestSourceConfigFromDict:
    """Tests for SourceConfig.from_dict method."""

    def test_from_dict_valid_data(self):
        """Test creating SourceConfig from valid dictionary."""
        data = {
            "name": "test_source",
            "description": "Test description",
            "category": "test_category",
            "provider": "test_provider",
            "year": "2024",
            "page_url": "https://example.com/page",
            "download_url": "https://example.com/download",
            "format": "csv",
        }

        config = SourceConfig.from_dict(data)

        assert config.name == "test_source"
        assert config.description == "Test description"
        assert config.category == "test_category"
        assert config.provider == "test_provider"
        assert config.year == "2024"
        assert config.page_url == "https://example.com/page"
        assert config.download_url == "https://example.com/download"
        assert config.format == "csv"

    def test_from_dict_valid_year_range(self):
        """Test creating SourceConfig with valid year range."""
        data = {
            "name": "multi_year",
            "description": "Multi year dataset",
            "category": "test",
            "provider": "test",
            "year": "2020-2024",
            "page_url": "https://example.com",
            "download_url": "https://example.com/download",
            "format": "json",
        }

        config = SourceConfig.from_dict(data)
        assert config.year == "2020-2024"

    def test_from_dict_invalid_year(self):
        """Test that from_dict raises ValueError for invalid year."""
        data = {
            "name": "test",
            "description": "test",
            "category": "test",
            "provider": "test",
            "year": "invalid",
            "page_url": "https://example.com",
            "download_url": "https://example.com",
            "format": "csv",
        }

        with pytest.raises(ValueError, match="Invalid year format"):
            SourceConfig.from_dict(data)

    def test_from_dict_invalid_format(self):
        """Test that from_dict raises ValueError for invalid format."""
        data = {
            "name": "test",
            "description": "test",
            "category": "test",
            "provider": "test",
            "year": "2024",
            "page_url": "https://example.com",
            "download_url": "https://example.com",
            "format": "invalid",
        }

        with pytest.raises(ValueError, match="Invalid format"):
            SourceConfig.from_dict(data)

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
            # missing format
        }

        with pytest.raises(KeyError):
            SourceConfig.from_dict(data)


class TestSourceConfigDataclass:
    """Tests for SourceConfig dataclass properties."""

    def test_dataclass_fields(self):
        """Test that SourceConfig has all expected fields."""
        config = SourceConfig(
            name="test",
            description="desc",
            category="cat",
            provider="prov",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/download",
            format="csv",
        )

        assert config.name == "test"
        assert config.description == "desc"
        assert config.category == "cat"
        assert config.provider == "prov"
        assert config.year == "2024"
        assert config.page_url == "https://example.com/page"
        assert config.download_url == "https://example.com/download"
        assert config.format == "csv"


class TestConfClass:
    """Tests for Conf class."""

    def test_init_with_default_path(self):
        """Test Conf initialization with default path."""
        # This test assumes sources.json exists in the parent directory
        conf = Conf()
        assert len(conf.sources) > 0

    def test_init_with_custom_path(self):
        """Test Conf initialization with custom path."""
        # Create a temporary sources.json file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "custom_source",
                        "description": "Custom source",
                        "category": "custom",
                        "provider": "custom",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com/download",
                        "format": "json",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            assert len(conf.sources) == 1
            assert conf.sources[0].name == "custom_source"
        finally:
            Path(temp_path).unlink()

    def test_load_sources_file_not_found(self):
        """Test that loading sources raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Sources file not found"):
            Conf("nonexistent_path.json")

    def test_load_sources_invalid_json(self):
        """Test that loading sources raises ValueError for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                Conf(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_sources_missing_required_field(self):
        """Test that loading sources raises ValueError for missing required field."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "test",
                        "description": "test",
                        # missing category
                        "provider": "test",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required field"):
                Conf(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_no_duplicates_valid(self):
        """Test that duplicate validation passes for unique sources."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "source1",
                        "description": "desc1",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    },
                    {
                        "name": "source2",
                        "description": "desc2",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "json",
                    },
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            assert len(conf.sources) == 2
        finally:
            Path(temp_path).unlink()

    def test_validate_no_duplicates_same_name_different_year(self):
        """Test that sources with same name but different years are allowed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "source",
                        "description": "desc1",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    },
                    {
                        "name": "source",
                        "description": "desc2",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2025",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "json",
                    },
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            assert len(conf.sources) == 2
        finally:
            Path(temp_path).unlink()

    def test_validate_no_duplicates_fails(self):
        """Test that duplicate validation fails for same name and year."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "source",
                        "description": "desc1",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    },
                    {
                        "name": "source",
                        "description": "desc2",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "json",
                    },
                ],
                f,
            )
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Duplicate source found"):
                Conf(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_get_source_found(self):
        """Test getting a source by name."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "find_me",
                        "description": "Find me",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            source = conf.get_source("find_me")
            assert source.name == "find_me"
            assert source.description == "Find me"
        finally:
            Path(temp_path).unlink()

    def test_get_source_not_found(self):
        """Test getting a non-existent source raises KeyError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "existing",
                        "description": "Existing",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            with pytest.raises(KeyError, match="Source 'nonexistent' not found"):
                conf.get_source("nonexistent")
        finally:
            Path(temp_path).unlink()

    def test_get_all_sources(self):
        """Test getting all sources."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            sources_data = [
                {
                    "name": f"source{i}",
                    "description": f"desc{i}",
                    "category": "cat",
                    "provider": "prov",
                    "year": "2024",
                    "page_url": "https://example.com",
                    "download_url": "https://example.com",
                    "format": "csv",
                }
                for i in range(3)
            ]
            json.dump(sources_data, f)
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            all_sources = conf.get_all_sources()
            assert len(all_sources) == 3
            assert all_sources[0].name == "source0"
            assert all_sources[1].name == "source1"
            assert all_sources[2].name == "source2"
        finally:
            Path(temp_path).unlink()

    def test_reload(self):
        """Test reloading sources from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "name": "original",
                        "description": "Original",
                        "category": "cat",
                        "provider": "prov",
                        "year": "2024",
                        "page_url": "https://example.com",
                        "download_url": "https://example.com",
                        "format": "csv",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            assert len(conf.sources) == 1
            assert conf.sources[0].name == "original"

            # Modify the file
            with open(temp_path, "w") as f:
                json.dump(
                    [
                        {
                            "name": "updated",
                            "description": "Updated",
                            "category": "cat",
                            "provider": "prov",
                            "year": "2025",
                            "page_url": "https://example.com",
                            "download_url": "https://example.com",
                            "format": "json",
                        }
                    ],
                    f,
                )

            # Reload
            conf.reload()
            assert len(conf.sources) == 1
            assert conf.sources[0].name == "updated"
            assert conf.sources[0].year == "2025"
        finally:
            Path(temp_path).unlink()

    def test_sources_path_attribute(self):
        """Test that sources_path is set correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            assert conf.sources_path == Path(temp_path)
        finally:
            Path(temp_path).unlink()


class TestConfIntegration:
    """Integration tests for Conf class with real sources.json."""

    def test_load_real_sources_json(self):
        """Test loading the actual sources.json file."""
        # This test uses the real sources.json from the project
        conf = Conf()
        sources = conf.get_all_sources()

        # Should have the sources from the real file
        assert len(sources) >= 2  # At least the example datasets

        # Check that we can find specific sources
        example_source = conf.get_source("example_dataset")
        assert example_source.description == "Example dataset for testing"
        assert example_source.format == "csv"
        assert example_source.year == "2024"

        multi_year_source = conf.get_source("multi_year_dataset")
        assert multi_year_source.year == "2024-2026"
        assert multi_year_source.format == "parquet"

    def test_real_sources_no_duplicates(self):
        """Test that the real sources.json has no duplicates."""
        conf = Conf()
        sources = conf.get_all_sources()

        # Check for duplicates by name+year
        seen = set()
        for source in sources:
            key = (source.name, source.year)
            assert key not in seen, f"Duplicate source: {key}"
            seen.add(key)
