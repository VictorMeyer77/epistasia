import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


class FileFormat(Enum):
    """Valid file formats for downloads."""

    PARQUET = "parquet"
    JSON = "json"
    XLSX = "xlsx"
    CSV = "csv"
    ZIP = "zip"


@dataclass
class SourceConfig:
    """Configuration for a single source file to download."""

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
        """Validate year format. Must be YYYY or YYYY-YYYY."""
        pattern = r"^\d{4}(-\d{4})?$"
        if not re.match(pattern, year):
            raise ValueError(
                f"Invalid year format: '{year}'. "
                "Year must be in format YYYY (e.g., '2024') or YYYY-YYYY (e.g., '2024-2026')."
            )

    @staticmethod
    def _validate_format(fmt: str) -> None:
        """Validate format. Must be one of: parquet, json, xlsx, csv, zip."""
        valid_formats = {member.value for member in FileFormat}
        if fmt not in valid_formats:
            raise ValueError(
                f"Invalid format: '{fmt}'. "
                f"Format must be one of: {', '.join(sorted(valid_formats))}."
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        """Create a SourceConfig from a dictionary."""
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
    """Configuration class that reads sources from ../sources.json."""

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

        self.sources: List[SourceConfig] = []
        self._load_sources()

    def _load_sources(self) -> None:
        """Load sources from the JSON file."""
        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.sources = [SourceConfig.from_dict(item) for item in data]
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

    def get_source(self, name: str) -> SourceConfig:
        """Get a source by name."""
        for source in self.sources:
            if source.name == name:
                return source
        raise KeyError(f"Source '{name}' not found")

    def get_all_sources(self) -> List[SourceConfig]:
        """Get all sources."""
        return self.sources

    def reload(self) -> None:
        """Reload sources from the JSON file."""
        self.sources = []
        self._load_sources()
