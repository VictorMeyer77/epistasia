import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml


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
        category: Category the source belongs to.
        provider: Organization or entity providing the data.
        page_url: URL to the source's information page.
        download_url: URL to download the data file.
        format: File format (one of FileFormat enum values).
        folder: Folder where the downloaded file will be stored. If None, name will be used.
        year: Year or year range of the data (format: YYYY or YYYY-YYYY).
              If None, the table is considered a full refresh and current year
              will be used for file output name.
        post: Optional name of post-download processing script to run.
              If None, no post-processing is performed. Defaults to None.
        refresh_days: Number of days after which the source should be re-downloaded.
                     If None, defaults to a standard refresh period. When year is not None
                     (historical data), this should only be run with single download.
        incremental: Whether the source is re-checked and downloaded incrementally
                     on every run. If True, year and refresh_days must both be None.
                     Defaults to None (non-incremental).
    """

    name: str
    description: str
    category: str
    provider: str
    page_url: str
    download_url: str | None
    format: str
    folder: str | None
    year: str | None
    post: str | None
    refresh_days: int | None
    incremental: bool | None

    def __post_init__(self):
        """Validate all constraints after initialization."""
        self._validate_year(self.year)
        self._validate_format(self.format)
        self._validate_year_refresh_days_combination(
            self.year, self.refresh_days, self.incremental
        )
        self._validate_download_url(self.download_url, self.incremental)

    @staticmethod
    def _validate_download_url(
        download_url: str | None, incremental: bool | None
    ) -> None:
        """
        Validate that download_url is only None if incremental is True.

        Args:
            download_url: The download URL to validate.
            incremental: Whether the source is incremental.

        Raises:
            ValueError: If download_url is None but incremental is not True.
        """
        if download_url is None and incremental is not True:
            raise ValueError(
                "download_url can only be None if incremental is True. "
                "Non-incremental sources must have a download_url."
            )

    @staticmethod
    def _validate_year(year: str | None) -> None:
        """
        Validate year format.

        Args:
            year: The year string to validate. Can be None for full refresh sources.

        Raises:
            ValueError: If the year format is invalid. Must be YYYY or YYYY-YYYY.
        """
        if year is None:
            return

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

    @staticmethod
    def _validate_year_refresh_days_combination(
        year: str | None, refresh_days: int | None, incremental: bool | None
    ) -> None:
        """
        Validate the combination of year, refresh_days, and incremental.

        Rules:
        - If incremental is True, year and refresh_days must both be None.
        - Otherwise (incremental is False/None):
            - If year is None (full refresh), refresh_days must be set.
            - If year is set (historical), refresh_days should not be set (use download_single).

        Args:
            year: The year value to check.
            refresh_days: The refresh_days value to check.
            incremental: Whether the source is downloaded incrementally.

        Raises:
            ValueError: If the combination is invalid according to the rules above.
        """
        if incremental:
            if year is not None or refresh_days is not None:
                raise ValueError(
                    "If incremental is True, year and refresh_days must both be None. "
                    "Incremental sources are re-checked on every run and should not "
                    "carry a fixed year or refresh_days."
                )
            return

        if year is None and refresh_days is None:
            raise ValueError(
                "If year is None (full refresh) and incremental is not True, "
                "refresh_days must be set. Full refresh sources need a refresh frequency."
            )

        if year is not None and refresh_days is not None:
            raise ValueError(
                "If year is set (historical data), refresh_days should not be set. "
                "Historical sources should only be downloaded with download_single command."
            )

    @classmethod
    def from_dict(cls, data: dict) -> "SourceConfig":
        """
        Create a SourceConfig from a dictionary.

        Args:
            data: Dictionary containing source configuration data.
                Required keys: name, description, category, provider,
                page_url, download_url, format, folder.
                Optional keys: year, post, refresh_days, incremental.

        Returns:
            A new SourceConfig instance.

        Raises:
            ValueError: If year or format validation fails, or if year,
                refresh_days, and incremental are set to an invalid
                combination (see _validate_year_refresh_days_combination).
        """
        cls._validate_year(data.get("year"))
        cls._validate_format(data["format"])
        cls._validate_year_refresh_days_combination(
            data.get("year"), data.get("refresh_days"), data.get("incremental")
        )
        cls._validate_download_url(data.get("download_url"), data.get("incremental"))
        return cls(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            provider=data["provider"],
            year=data.get("year"),
            page_url=data["page_url"],
            download_url=data.get("download_url"),
            format=data["format"],
            folder=data.get("folder"),
            post=data.get("post"),
            refresh_days=data.get("refresh_days"),
            incremental=data.get("incremental"),
        )


class Conf:
    """
    Configuration class that reads and validates sources from a YAML file.

    This class loads source configurations from a YAML file, validates them,
    and provides methods to access individual sources or all sources.
    It ensures there are no duplicate sources (based on name + year).
    """

    def __init__(self, sources_path: str | None = None):
        """
        Initialize the configuration.

        Args:
            sources_path: Path to the sources.yaml file.
                         Defaults to ../sources.yaml relative to this file.
        """
        if sources_path is None:
            self.sources_path = Path(__file__).parent.parent / "sources.yaml"
        else:
            self.sources_path = Path(sources_path)

        self.sources: list[SourceConfig] = []
        self._load_sources()

    def _load_sources(self) -> None:
        """
        Load sources from the YAML file.

        Raises:
            FileNotFoundError: If the sources file does not exist.
            ValueError: If the YAML is invalid or has duplicate sources.
            KeyError: If required fields are missing from the YAML data.
        """
        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self.sources = [SourceConfig.from_dict(item) for item in data]
            self._validate_no_duplicates()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Sources file not found at {self.sources_path}. "
                "Please create sources.yaml with the required source configurations."
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in sources file: {e}")
        except KeyError as e:
            raise ValueError(
                f"Missing required field in sources.yaml: {e}. "
                "Each source must have: name, description, category, provider, "
                "page_url, download_url, format, folder. "
                "Optional: year, post, refresh_days, incremental"
            )

    def _validate_no_duplicates(self) -> None:
        """
        Validate that there are no duplicate sources.

        Checks that each source has a unique combination of name and year.
        Sources with year=None are treated as a special case for uniqueness.

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

    def get_source(self, name: str, year: str | None) -> SourceConfig | None:
        """
        Get a source by its name and year.

        Args:
            name: The name of the source to retrieve.
            year: The year of the source to retrieve. Can be None for full refresh sources.

        Returns:
            The SourceConfig object matching the given name and year, or None if not found.
        """
        for source in self.sources:
            if source.name == name and source.year == year:
                return source
        return None

    def get_all_sources(self) -> list[SourceConfig]:
        """
        Get all configured sources.

        Returns:
            List of all SourceConfig objects loaded from the sources file.
        """
        return self.sources

    def reload(self) -> None:
        """
        Reload sources from the YAML file.

        Clears the current sources list and reloads from the sources file.
        This is useful for refreshing the configuration without restarting.
        """
        self.sources = []
        self._load_sources()
