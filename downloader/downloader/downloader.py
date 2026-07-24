"""Downloader module for downloading source files."""

import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from downloader.conf import SourceConfig
from downloader.history import DownloadRecord, History
from downloader.incremental import run_incremental
from downloader.post_download import post

logger = logging.getLogger(__name__)


class Downloader:
    """
    Downloads source files from a list of SourceConfig objects.

    There are two distinct download paths, chosen per-source based on
    `source.incremental`:

    - STANDARD sources are fetched directly from `source.download_url`,
      with retries/backoff handled by `_download_standard`. This is also
      used for the one-time initial fetch of an incremental source (its
      "-init" file).
    - INCREMENTAL sources, once their init file exists on disk, are
      subsequently updated via `_download_incremental`, which delegates
      to `downloader.incremental.run_incremental` instead of doing an
      HTTP download.

    `download_source` is the single entry point and dispatches to
    whichever path applies.

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
        Initialize the downloader.

        Args:
            output_dir: Directory where downloaded files are written. Defaults
                to datalake/raw relative to this file.
            timeout: HTTP request timeout, in seconds.
            retry_count: Number of retries for failed HTTP downloads.
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
            The filename, depending on the source type:
            - If source.incremental is True: "{name}-init.{format}"
            - If source.year is None (full refresh): "{name}_{current_year}.{format}"
            - Otherwise (historical, fixed year): "{name}_{safe_year}.{format}",
            where safe_year is source.year with "-" replaced by "_"
            (e.g. "2024-2026" -> "2024_2026").
        """

        if source.incremental:
            return f"{source.name}-init.{source.format}"
        elif source.year is None:
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

    def _download_standard(
        self, source: SourceConfig, destination: Path
    ) -> tuple[bool, DownloadRecord | None, str | None, Path | None]:
        """
        Download a source directly from its URL via HTTP, retrying up to
        self.retry_count times with a linearly increasing backoff on failure.

        Used for non-incremental sources, and for the one-time init fetch
        of incremental sources.

        Args:
            source: SourceConfig to download.
            destination: Path to save the file to.

        Returns:
            Same shape as `download_source`.
        """
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
                    incremental=False,
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
                logger.info(
                    f"Retry {attempt + 1}/{self.retry_count} for {source.name} in {wait_time}s..."
                )
                time.sleep(wait_time)

        duration = time.time() - start_time
        return False, None, last_error or "Unknown error", None

    def _download_incremental(
        self, source: SourceConfig
    ) -> tuple[bool, DownloadRecord | None, str | None, Path | None]:
        """
        Fetch the next increment for an already-initialized incremental
        source, via downloader.incremental.run_incremental.

        Args:
            source: SourceConfig to update.

        Returns:
            Same shape as `download_source`.
        """
        logger.info(f"  Load increment for {source.name}")
        start_time = time.time()

        try:
            path = run_incremental(source.name)
        except Exception as e:
            return False, None, str(e), None

        duration = time.time() - start_time

        download_record = DownloadRecord(
            name=source.name,
            description=source.description,
            category=source.category,
            provider=source.provider,
            year=datetime.now().strftime("%Y"),
            incremental=True,
            page_url=source.page_url,
            download_url=source.download_url,
            format=source.format,
            download_timestamp=datetime.now().isoformat(),
            download_duration=duration,
        )

        return True, download_record, None, path

    def increment_source(
        self, source: SourceConfig
    ) -> tuple[bool, DownloadRecord | None, str | None, Path | None]:
        """Backward-compatible alias for `_download_incremental`."""
        return self._download_incremental(source)

    def download_source(
        self, source: SourceConfig
    ) -> tuple[bool, DownloadRecord | None, str | None, Path | None]:
        """
        Download a single source and return a DownloadRecord for history.

        This method downloads the source file to a destination folder.
        The destination folder is determined by:
          - `source.folder` if it is provided (mandatory field).
          - If `source.folder` is not provided (should not happen as it is mandatory),
            defaults to `source.name`.

        If the source is incremental and either:
          - `source.download_url` is None (no init file), or
          - the destination file already exists,
        the method delegates to `_download_incremental`.
        Otherwise, it uses the standard HTTP download path via `_download_standard`.

        Args:
            source: The SourceConfig object representing the source to download.

        Returns:
            A tuple containing:
                - success (bool): True if the download succeeded or was skipped
                  (e.g., incremental init file already exists), False otherwise.
                - download_record (DownloadRecord | None): The download record for
                  history if a download occurred; None if skipped or failed.
                - error_message (str | None): Error message if the download failed;
                  None otherwise.
                - file_path (Path | None): Path to the downloaded or existing file
                  if successful or skipped; None if failed.
        """
        filename = self._generate_filename(source)
        destination_folder = self.output_dir / (
            source.folder if source.folder is not None else source.name
        )
        destination_folder.mkdir(exist_ok=True)
        destination = destination_folder / filename

        if source.incremental and (source.download_url is None or destination.exists()):
            return self._download_incremental(source)

        return self._download_standard(source, destination)

    def download_all(self, sources: list[SourceConfig]) -> list[DownloadRecord]:
        """
        Download all sources in the list.

        For each source that produces a DownloadRecord (i.e. a real download
        happened, not a skipped incremental init file):
            - If source.post is set, the corresponding post-processing script
              is executed with the downloaded file path as argument.
            - If self.history is configured, the record is added to history.

        Args:
            sources: SourceConfig objects to download.

        Returns:
            List of DownloadRecord objects for sources that were actually
            downloaded this run. Sources whose download failed, or whose
            incremental init file already existed (and so were skipped),
            are not included.
        """
        downloaded_records = []

        for source in sources:
            year_display = source.year or datetime.now().strftime("%Y")
            logger.info(
                f"Downloading {source.name} ({source.format}, {year_display})..."
            )
            success, download_record, error_message, file_path = self.download_source(
                source
            )

            if success and download_record:
                logger.info(f"  Success: Downloaded to {file_path}")
                logger.info(f"    Duration: {download_record.download_duration:.2f}s")
                downloaded_records.append(download_record)

                # Post-download hook
                if source.post:
                    logger.info(f"  Post download: {source.post}")
                    post(source.post, file_path)

                # Add to history
                if self.history is not None:
                    self.history.add_record(
                        name=download_record.name,
                        description=download_record.description,
                        category=download_record.category,
                        provider=download_record.provider,
                        year=download_record.year,
                        incremental=download_record.incremental,
                        page_url=download_record.page_url,
                        download_url=download_record.download_url,
                        format=download_record.format,
                        download_duration=download_record.download_duration,
                    )
            else:
                logger.error(f"  Failed: {error_message}")

        return downloaded_records
