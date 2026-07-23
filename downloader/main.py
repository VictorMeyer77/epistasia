import argparse
import logging
import sys
from datetime import datetime

from downloader.conf import Conf
from downloader.downloader import Downloader
from downloader.history import History

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def validate():
    """
    Validate the sources configuration file.

    Loads and validates the sources.json configuration file by attempting
    to parse it and create SourceConfig objects for each entry.

    Returns:
        0 on success, 1 on validation failure.
    """
    try:
        conf = Conf()
        sources = conf.get_all_sources()
        logger.info("✓ sources.json is valid")
        logger.info(f"  Found {len(sources)} source(s):")
        for source in sources:
            logger.info(f"    - {source.name} ({source.format}, {source.year})")
        return 0
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        return 1


def plan():
    """
    Show download plan - sources that need to be downloaded.

    A source is included in the plan if:
    - It has no download history yet, regardless of year or incremental
      status, OR
    - It has year=None (a full refresh source) and either:
        - it is incremental (incremental sources are always re-included
          once they have an initial record, to keep pulling increments), OR
        - it is not incremental and its latest download was more than
          refresh_days days ago.

    Sources with a fixed year (year is not None, i.e. historical data)
    are only included if they have no existing download history; once
    downloaded, they are never re-included.

    Uses current datetime to determine what needs refreshing.

    Returns:
        list[SourceConfig] - Sources that need to be downloaded.
    """
    conf = Conf()
    history = History()
    sources = conf.get_all_sources()
    now = datetime.now()
    sources_to_download = []

    for source in sources:
        file_year = now.strftime("%Y") if source.year is None else source.year

        record = history.get_records_by_key(source.name, file_year)

        if not record:
            source.year = file_year
            sources_to_download.append(source)
        else:
            if source.year is not None:
                continue
            elif source.incremental:
                sources_to_download.append(source)
            else:
                threshold = (
                    datetime.fromisoformat(record.download_timestamp).timestamp()
                    + 24 * 60 * 60 * source.refresh_days
                )
                if threshold < now.timestamp():
                    sources_to_download.append(source)

    return sources_to_download


def download_single(name: str, year: str | None = None):
    """
    Download a single specific source identified by name and year.

    Args:
        name: Name of the source to download.
        year: Year of the source to download. Can be None for full refresh sources.

    Returns:
        0 on success, 1 on error.
    """
    try:
        conf = Conf()
        downloader = Downloader()
        now = datetime.now()
        source = conf.get_source(name, year)

        if not source:
            year_display = year or "None"
            logger.error(
                f"✗ No source found with name='{name}' and year='{year_display}'"
            )
            return 1

        file_year = now.strftime("%Y") if source.year is None else source.year
        logger.info(f"Downloading {source.name} ({source.format}, {file_year})...")

        success, record, error, file_path = downloader.download_source(source)

        if success and record:
            logger.info(f"  Success: Downloaded to {file_path}")
            logger.info(f"    Duration: {record.download_duration:.2f}s")
        else:
            logger.error(f"  Failed: {error}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        return 1


def download(yes: bool = False):
    """
    Download sources based on the plan.

    Selection of which sources need downloading is delegated to `plan()`
    (see its docstring for the exact criteria). This function displays
    that plan, optionally prompts for confirmation, and then runs the
    downloads.

    Args:
        yes: If True, skip the confirmation prompt and proceed with download.

    Returns:
        0 on success, 1 on error or cancellation.
    """
    try:
        history = History()
        sources_to_download = plan()

        if not sources_to_download:
            logger.info("Download plan:")
            logger.info("  All sources are up to date.")
            return 0

        logger.info("Download plan:")
        logger.info(f"  {len(sources_to_download)} source(s) to download:")
        for source in sources_to_download:
            if source.incremental:
                logger.info(f"    [INCREMENT] {source.name} ({source.format})")
            else:
                records = history.get_records_by_key(source.name, source.year)
                status = "NEW" if not records else "UPDATE"
                logger.info(
                    f"    [{status}] {source.name} ({source.format}, {source.year})"
                )

        if not yes:
            response = input("\nProceed with download? [Y/N]: ").strip().upper()
            if response != "Y":
                logger.info("Download cancelled.")
                return 1

        logger.info("\nStarting download...")
        downloader = Downloader()
        downloader.download_all(sources_to_download)
        logger.info("\nDownload complete!")
        return 0

    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Downloader CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    subparsers.add_parser("validate", help="Validate sources configuration")

    # Plan command
    subparsers.add_parser("plan", help="Show download plan")

    # Download command - for refreshing all full refresh sources
    download_parser = subparsers.add_parser(
        "download", help="Download and refresh all full refresh sources"
    )
    download_parser.add_argument(
        "--name",
        type=str,
        dest="name",
        help="Download only a specific full refresh source by name",
        default=None,
    )
    download_parser.add_argument(
        "--year",
        type=str,
        dest="year",
        help="Must be 'none' for full refresh sources",
        default=None,
    )
    download_parser.add_argument(
        "--yes",
        action="store_true",
        dest="yes",
        help="Skip confirmation prompt and proceed with download",
        default=False,
    )

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(validate())
    elif args.command == "plan":
        sources = plan()
        logger.info("Download plan:")
        if sources:
            logger.info(f"  {len(sources)} source(s) to download:")
            history = History()
            for source in sources:
                if source.incremental:
                    logger.info(f"    [INCREMENT] {source.name} ({source.format})")
                else:
                    records = history.get_records_by_key(source.name, source.year)
                    status = "NEW" if not records else "UPDATE"
                    logger.info(
                        f"    [{status}] {source.name} ({source.format}, {source.year})"
                    )
        else:
            logger.info("  All sources are up to date.")
        sys.exit(0)
    elif args.command == "download":
        if args.name:
            sys.exit(download_single(args.name, args.year))

        sys.exit(download(yes=args.yes))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
