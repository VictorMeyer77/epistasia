"""Unit tests for downloader.conf module."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

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
            "folder": "test_folder",
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
        assert config.folder == "test_folder"
        assert config.post is None

    def test_from_dict_with_post_field(self):
        """Test creating SourceConfig with post field from dictionary."""
        data = {
            "name": "test_source",
            "description": "Test description",
            "category": "test_category",
            "provider": "test_provider",
            "year": "2024",
            "page_url": "https://example.com/page",
            "download_url": "https://example.com/download",
            "format": "json",
            "folder": "test_folder",
            "post": "json_to_parquet",
        }

        config = SourceConfig.from_dict(data)

        assert config.name == "test_source"
        assert config.post == "json_to_parquet"

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
            "folder": "test_folder",
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
            "folder": "test_folder",
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
            "folder": "test_folder",
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
            # missing format and folder
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
            folder="test_folder",
            post=None,
            refresh_days=None,
            incremental=None,
        )

        assert config.name == "test"
        assert config.description == "desc"
        assert config.category == "cat"
        assert config.provider == "prov"
        assert config.year == "2024"
        assert config.page_url == "https://example.com/page"
        assert config.download_url == "https://example.com/download"
        assert config.format == "csv"
        assert config.folder == "test_folder"
        assert config.post is None
        assert config.refresh_days is None
        assert config.incremental is None

    def test_post_field_default_none(self):
        """Test that post field can be set to None."""
        config = SourceConfig(
            name="test",
            description="desc",
            category="cat",
            provider="prov",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/download",
            format="csv",
            folder="test_folder",
            post=None,
            refresh_days=None,
            incremental=None,
        )
        assert config.post is None

    def test_post_field_with_value(self):
        """Test that post field can be set to a string value."""
        config = SourceConfig(
            name="test",
            description="desc",
            category="cat",
            provider="prov",
            year="2024",
            page_url="https://example.com/page",
            download_url="https://example.com/download",
            format="csv",
            folder="test_folder",
            post="convert_to_parquet",
            refresh_days=None,
            incremental=None,
        )
        assert config.post == "convert_to_parquet"

    def test_refresh_days_field(self):
        """Test that refresh_days field can be set to an integer value."""
        config = SourceConfig(
            name="test",
            description="desc",
            category="cat",
            provider="prov",
            year=None,
            page_url="https://example.com/page",
            download_url="https://example.com/download",
            format="csv",
            folder="test_folder",
            post=None,
            refresh_days=30,
            incremental=None,
        )
        assert config.refresh_days == 30


class TestConfClass:
    """Tests for Conf class."""

    def test_init_with_default_path(self):
        """Test Conf initialization with default path."""
        # This test assumes sources.yaml exists in the parent directory
        conf = Conf()
        assert len(conf.sources) > 0

    def test_init_with_custom_path(self):
        """Test Conf initialization with custom path."""
        # Create a temporary sources file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "custom_folder",
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
            Conf("nonexistent_path.yaml")

    def test_load_sources_invalid_yaml(self):
        """Test that loading sources raises ValueError for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key:\n\tvalue: bad")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                Conf(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_sources_missing_required_field(self):
        """Test that loading sources raises ValueError for missing required field."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "test_folder",
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "folder1",
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
                        "folder": "folder2",
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "folder1",
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
                        "folder": "folder2",
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "folder1",
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
                        "folder": "folder2",
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
        """Test getting a source by name and year."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "find_me_folder",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            source = conf.get_source("find_me", "2024")
            assert source.name == "find_me"
            assert source.description == "Find me"
        finally:
            Path(temp_path).unlink()

    def test_get_source_not_found(self):
        """Test getting a non-existent source returns None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "existing_folder",
                    }
                ],
                f,
            )
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            source = conf.get_source("nonexistent", "2024")
            assert source is None
        finally:
            Path(temp_path).unlink()

    def test_get_all_sources(self):
        """Test getting all sources."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
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
                    "folder": f"folder{i}",
                }
                for i in range(3)
            ]
            yaml.dump(sources_data, f)
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
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
                        "folder": "original_folder",
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
                yaml.dump(
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
                            "folder": "updated_folder",
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("[]")
            temp_path = f.name

        try:
            conf = Conf(temp_path)
            assert conf.sources_path == Path(temp_path)
        finally:
            Path(temp_path).unlink()
