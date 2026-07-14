"""Downloader module for downloading source files."""

import time
from datetime import datetime
from pathlib import Path

import requests

from downloader.conf import SourceConfig
from downloader.history import DownloadRecord, History
from downloader.post_download import post


class Downloader:
    """
    Downloads source files from a list of SourceConfig objects.

    Files are saved to the datalake/raw/ directory with filename
    format: {name}_{year}.{format}.

    If a source has a post-processing script specified (source.post), it will be
    executed after successful download with the downloaded file path as argument.
    """

    def __init__(
        self,
        output_dir: str | None = None,
        timeout: int = 30,
        retry_count: int = 3,
    ):
        """
        Initialize the Downloader.

        Args:
            output_dir: Directory to save downloaded files.
                       Defaults to ../../datalake/raw/ relative to this file.
            timeout: Request timeout in seconds.
            retry_count: Number of retries for failed downloads.
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / "datalake" / "raw"
        else:
            self.output_dir = Path(output_dir)

        self.timeout = timeout
        self.retry_count = retry_count
        self.history = History()

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, source: SourceConfig) -> str:
        """
        Generate a filename from source name and year.

        Args:
            source: SourceConfig containing source metadata.

        Returns:
            The filename as {name}_{year}.{format}
            If year is None, uses current year for the filename.
        """
        if source.year is None:
            current_year = datetime.now().strftime("%Y")
            return f"{source.name}_{current_year}.{source.format}"
        else:
            safe_year = source.year.replace("-", "_")
            return f"{source.name}_{safe_year}.{source.format}"

    def _download_file(
        self, url: str, destination: Path, timeout: int = 30
    ) -> tuple[bool, str | None]:
        """
        Download a file from a URL to a destination path.

        Args:
            url: URL to download from.
            destination: Path to save the file.
            timeout: Request timeout in seconds.

        Returns:
            tuple[bool, str | None]:
                - success (bool): True if download succeeded, False otherwise
                - error_message (str | None): Error message if failed, None if successful
        """
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return True, None

        except requests.exceptions.RequestException as e:
            return False, str(e)
        except IOError as e:
            return False, str(e)

    def download_source(
        self, source: SourceConfig
    ) -> tuple[bool, DownloadRecord | None, str | None, Path | None]:
        """
        Download a single source and return a DownloadRecord for history.

        Args:
            source: SourceConfig to download.

        Returns:
            tuple[bool, DownloadRecord | None, str | None, Path | None]
            - success (bool): True if download succeeded, False otherwise
            - download_record (DownloadRecord | None): Download record for history if successful
            - error_message (str | None): Error message if failed, None if successful
            - file_path (Path | None): Path to the downloaded file if successful, None otherwise
        """
        filename = self._generate_filename(source)
        destination = self.output_dir / filename

        start_time = time.time()
        last_error = None

        for attempt in range(self.retry_count):
            success, error_message = self._download_file(
                source.download_url, destination, self.timeout
            )

            if success:
                duration = time.time() - start_time
                download_record = DownloadRecord(
                    name=source.name,
                    description=source.description,
                    category=source.category,
                    provider=source.provider,
                    year=source.year or datetime.now().strftime("%Y"),
                    page_url=source.page_url,
                    download_url=source.download_url,
                    format=source.format,
                    download_timestamp=datetime.now().isoformat(),
                    download_duration=duration,
                )
                return True, download_record, None, destination

            last_error = error_message

            if attempt < self.retry_count - 1:
                wait_time = (attempt + 1) * 2
                print(
                    f"Retry {attempt + 1}/{self.retry_count} for {source.name} in {wait_time}s..."
                )
                time.sleep(wait_time)

        duration = time.time() - start_time
        return False, None, last_error or "Unknown error", None

    def download_all(self, sources: list[SourceConfig]) -> list[DownloadRecord]:
        """
        Download all sources in the list.

        For each source, if post-processing is specified (source.post is not None),
        the corresponding post-processing script will be executed with the downloaded
        file path as argument.

        Args:
            sources: SourceConfig objects to download.

        Returns:
            List of DownloadRecord objects for successful downloads.
        """
        downloaded_records = []

        for source in sources:
            year_display = source.year or datetime.now().strftime("%Y")
            print(f"Downloading {source.name} ({source.format}, {year_display})...")
            success, download_record, error_message, file_path = self.download_source(
                source
            )

            if success and download_record:
                print(f"  Success: Downloaded to {file_path}")
                print(f"    Duration: {download_record.download_duration:.2f}s")
                downloaded_records.append(download_record)

                # Post Download
                if source.post:
                    print(f"  Post download: {source.post}")
                    post(source.post, file_path)

                # Add to history
                if self.history is not None:
                    self.history.add_record(
                        name=download_record.name,
                        description=download_record.description,
                        category=download_record.category,
                        provider=download_record.provider,
                        year=download_record.year,
                        page_url=download_record.page_url,
                        download_url=download_record.download_url,
                        format=download_record.format,
                        download_duration=download_record.download_duration,
                    )
            else:
                print(f"  Failed: {error_message}")

        return downloaded_records
