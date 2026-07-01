import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileFormat(Enum):
    """Enumeration of valid file formats for downloads."""

    PARQUET = "parquet"
    JSON = "json"
    XLSX = "xlsx"
    CSV = "csv"
    ZIP = "zip"


@dataclass
class SourceConfig:
    """
    Configuration for a single source file to download.

    Attributes:
        name: Unique identifier for the source.
        description: Human-readable description of the source.
        categorie: Category the source belongs to.
        provider: Organization or entity providing the data.
        year: Year or year range of the data (format: YYYY or YYYY-YYYY).
        page_url: URL to the source's information page.
        download_url: URL to download the data file.
        format: File format (one of FileFormat enum values).
    """

    name: str
    description: str
    categorie: str
    provider: str
    year: str
    page_url: str
    download_url: str
    format: str

    @staticmethod
    def _validate_year(year: str) -> None:
        """
        Validate year format.

        Args:
            year: The year string to validate.

        Raises:
            ValueError: If the year format is invalid. Must be YYYY or YYYY-YYYY.
        """
        pattern = r"^\d{4}(-\d{4})?$"
        if not re.match(pattern, year):
            raise ValueError(
                f"Invalid year format: '{year}'. "
                "Year must be in format YYYY (e.g., '2024') or YYYY-YYYY (e.g., '2024-2026')."
            )

    @staticmethod
    def _validate_format(fmt: str) -> None:
        """
        Validate file format.

        Args:
            fmt: The format string to validate.

        Raises:
            ValueError: If the format is not one of the valid FileFormat enum values.
        """
        valid_formats = {member.value for member in FileFormat}
        if fmt not in valid_formats:
            raise ValueError(
                f"Invalid format: '{fmt}'. "
                f"Format must be one of: {', '.join(sorted(valid_formats))}."
            )

    @classmethod
    def from_dict(cls, data: dict) -> "SourceConfig":
        """
        Create a SourceConfig from a dictionary.

        Args:
            data: Dictionary containing source configuration data.
                  Required keys: name, description, categorie, provider, year,
                  page_url, download_url, format.

        Returns:
            A new SourceConfig instance.

        Raises:
            ValueError: If year or format validation fails.
        """
        cls._validate_year(data["year"])
        cls._validate_format(data["format"])
        return cls(
            name=data["name"],
            description=data["description"],
            categorie=data["categorie"],
            provider=data["provider"],
            year=data["year"],
            page_url=data["page_url"],
            download_url=data["download_url"],
            format=data["format"],
        )


class Conf:
    """
    Configuration class that reads and validates sources from a JSON file.

    This class loads source configurations from a JSON file, validates them,
    and provides methods to access individual sources or all sources.
    It ensures there are no duplicate sources (based on name + year).
    """

    def __init__(self, sources_path: str | None = None):
        """
        Initialize the configuration.

        Args:
            sources_path: Path to the sources.json file.
                         Defaults to ../sources.json relative to this file.
        """
        if sources_path is None:
            self.sources_path = Path(__file__).parent.parent / "sources.json"
        else:
            self.sources_path = Path(sources_path)

        self.sources: list[SourceConfig] = []
        self._load_sources()

    def _load_sources(self) -> None:
        """
        Load sources from the JSON file.

        Raises:
            FileNotFoundError: If the sources file does not exist.
            ValueError: If the JSON is invalid or has duplicate sources.
            KeyError: If required fields are missing from the JSON data.
        """
        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.sources = [SourceConfig.from_dict(item) for item in data]
            self._validate_no_duplicates()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Sources file not found at {self.sources_path}. "
                "Please create sources.json with the required source configurations."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in sources file: {e}")
        except KeyError as e:
            raise ValueError(
                f"Missing required field in sources.json: {e}. "
                "Each source must have: name, description, categorie, provider, "
                "year, page_url, download_url, format"
            )

    def _validate_no_duplicates(self) -> None:
        """
        Validate that there are no duplicate sources.

        Checks that each source has a unique combination of name and year.

        Raises:
            ValueError: If duplicate sources are found (same name and year).
        """
        seen = set()
        for source in self.sources:
            key = (source.name, source.year)
            if key in seen:
                raise ValueError(
                    f"Duplicate source found: name='{source.name}', year='{source.year}'. "
                    "Each source must have a unique combination of name and year."
                )
            seen.add(key)

    def get_source(self, name: str) -> SourceConfig:
        """
        Get a source by its name.

        Args:
            name: The name of the source to retrieve.

        Returns:
            The SourceConfig object matching the given name.

        Raises:
            KeyError: If no source with the given name exists.
        """
        for source in self.sources:
            if source.name == name:
                return source
        raise KeyError(f"Source '{name}' not found")

    def get_all_sources(self) -> list[SourceConfig]:
        """
        Get all configured sources.

        Returns:
            List of all SourceConfig objects loaded from the sources file.
        """
        return self.sources

    def reload(self) -> None:
        """
        Reload sources from the JSON file.

        Clears the current sources list and reloads from the sources file.
        This is useful for refreshing the configuration without restarting.
        """
        self.sources = []
        self._load_sources()
