import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Define the CSV schema - all SourceConfig fields plus download metadata
HISTORY_CSV_COLUMNS = [
    "name",
    "description",
    "categorie",
    "provider",
    "year",
    "page_url",
    "download_url",
    "format",
    "download_timestamp",
    "download_duration",
]


@dataclass
class DownloadRecord:
    """Represents a single download history record."""

    name: str
    description: str
    categorie: str
    provider: str
    year: str
    page_url: str
    download_url: str
    format: str
    download_timestamp: str
    download_duration: float

    @classmethod
    def from_dict(cls, data: Dict) -> "DownloadRecord":
        """
        Create a DownloadRecord from a dictionary.

        Args:
            data: Dictionary containing all the required fields to create a DownloadRecord.
                 Must include: name, description, categorie, provider, year, page_url,
                 download_url, format, download_timestamp, download_duration.

        Returns:
            DownloadRecord instance populated with data from the dictionary.
        """
        return cls(
            name=data["name"],
            description=data["description"],
            categorie=data["categorie"],
            provider=data["provider"],
            year=data["year"],
            page_url=data["page_url"],
            download_url=data["download_url"],
            format=data["format"],
            download_timestamp=data["download_timestamp"],
            download_duration=float(data["download_duration"]),
        )

    def to_dict(self) -> Dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary containing all DownloadRecord fields.
        """
        return {
            "name": self.name,
            "description": self.description,
            "categorie": self.categorie,
            "provider": self.provider,
            "year": self.year,
            "page_url": self.page_url,
            "download_url": self.download_url,
            "format": self.format,
            "download_timestamp": self.download_timestamp,
            "download_duration": self.download_duration,
        }


class History:
    """
    Maintains a CSV file containing download history of source data.

    The CSV file is located at datalake/raw/download_history.csv and contains
    all SourceConfig fields plus download_timestamp and download_duration.
    """

    def __init__(self, history_path: Optional[str] = None):
        """
        Initialize the History class.

        Args:
            history_path: Path to the history CSV file.
                         Defaults to datalake/raw/download_history.csv relative to the
                         downloader directory.
        """
        if history_path is None:
            # Default path: ~/datalake/raw/download_history.csv
            self.history_path = (
                Path(__file__).parent.parent.parent
                / "datalake"
                / "raw"
                / "download_history.csv"
            )
        else:
            self.history_path = Path(history_path)

        # Create file with headers if it doesn't exist
        if not self.history_path.exists():
            self.create_file()

    def create_file(self) -> None:
        """
        Create the history CSV file with headers.

        Creates a new CSV file at the specified history path with the defined
        column headers if the file doesn't already exist.
        """
        with open(self.history_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_CSV_COLUMNS)
            writer.writeheader()

    def add_record(
        self,
        name: str,
        description: str,
        categorie: str,
        provider: str,
        year: str,
        page_url: str,
        download_url: str,
        format: str,
        download_duration: float,
    ) -> None:
        """
        Add a new download record to the history.

        Args:
            name: Source name
            description: Source description
            categorie: Source category
            provider: Source provider
            year: Source year
            page_url: Source page URL
            download_url: Source download URL
            format: File format
            download_duration: Duration in seconds
        """
        record = {
            "name": name,
            "description": description,
            "categorie": categorie,
            "provider": provider,
            "year": year,
            "page_url": page_url,
            "download_url": download_url,
            "format": format,
            "download_timestamp": datetime.now().isoformat(),
            "download_duration": download_duration,
        }

        self._append_record(record)

    def _append_record(self, record: Dict) -> None:
        """
        Append a validated record to the CSV file.

        Args:
            record: Dictionary containing the record data to append.
                   Must match the HISTORY_CSV_COLUMNS schema.
        """
        with open(self.history_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_CSV_COLUMNS)
            writer.writerow(record)

    def read_all(self) -> List[DownloadRecord]:
        """
        Read all records from the history file.

        Returns:
            List of DownloadRecord objects.
        """
        if not self.history_path.exists():
            return []

        records = []
        with open(self.history_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if set(reader.fieldnames) != set(HISTORY_CSV_COLUMNS):
                raise ValueError(
                    f"CSV file has incorrect schema. "
                    f"Expected: {HISTORY_CSV_COLUMNS}, Got: {reader.fieldnames}"
                )

            for row in reader:
                try:
                    records.append(DownloadRecord.from_dict(row))
                except (KeyError, ValueError) as e:
                    raise ValueError(f"Invalid record in CSV: {e}")

        return records

    def clear(self) -> None:
        """
        Clear all records from the history file.

        Recreates the history file with only the header row, removing all existing records.
        """
        self.create_file()

    def exists(self, name: str, year: str, provider: str) -> bool:
        """
        Check if a record with the given parameters already exists.

        Args:
            name: Source name
            year: Source year
            provider: Source provider

        Returns:
            True if a matching record exists, False otherwise.
        """
        all_records = self.read_all()
        for record in all_records:
            if (
                record.name == name
                and record.year == year
                and record.provider == provider
            ):
                return True
        return False

    def get_records_by_key(
        self, source_name: str, source_year: str
    ) -> List[DownloadRecord]:
        """
        Get all download records matching the given source name and year.

        Args:
            source_name: The name of the source to filter by.
            source_year: The year of the source to filter by.

        Returns:
            List of DownloadRecord objects that match both the source name and year.
        """
        all_records = self.read_all()
        return [
            r for r in all_records if r.name == source_name and r.year == source_year
        ]

    def get_records_by_download_timestamp(
        self, timestamp: datetime
    ) -> List[DownloadRecord]:
        """
        Get all download records with download_timestamp before the given timestamp.

        Args:
            timestamp: Datetime threshold. Records with download_timestamp < timestamp are returned.

        Returns:
            List of DownloadRecord objects with download_timestamp before the given date.
        """
        all_records = self.read_all()
        matching_records = []
        for record in all_records:
            if datetime.fromisoformat(record.download_timestamp) < timestamp:
                matching_records.append(record)
        return matching_records

    @property
    def file_path(self) -> str:
        """
        Get the absolute path to the history file.

        Returns:
            Absolute path to the history CSV file as a string.
        """
        return str(self.history_path.absolute())

    @property
    def record_count(self) -> int:
        """
        Get the number of records in the history file.

        Returns:
            Count of download records in the history file.
        """
        return len(self.read_all())

    def __len__(self) -> int:
        """
        Return the number of records.

        Returns:
            The count of download records in the history file.
        """
        return self.record_count

    def __repr__(self) -> str:
        """
        Return a string representation of the History object.

        Returns:
            String containing the file path and record count.
        """
        return f"History(file_path='{self.file_path}', record_count={len(self)})"
