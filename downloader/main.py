import argparse
import sys
from datetime import datetime

from downloader.conf import Conf
from downloader.downloader import Downloader
from downloader.history import History

# Number of days after which a source should be re-downloaded
DOWNLOAD_REFRESH_DAYS = 180


def validate():
    """
    Validate the sources configuration file.

    Loads and validates the sources.json configuration file by attempting
    to parse it and create SourceConfig objects for each entry.

    Returns:
        int: 0 on success, 1 on validation failure.
    """
    try:
        conf = Conf()
        sources = conf.get_all_sources()
        print("✓ sources.json is valid")
        print(f"  Found {len(sources)} source(s):")
        for source in sources:
            print(f"    - {source.name} ({source.format}, {source.year})")
        return 0
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return 1


def plan(from_date: datetime | None = None):
    """
    Show download plan - sources that need to be downloaded.

    A source needs to be downloaded if:
    - It has no download history, OR
    - Its latest download was more than DOWNLOAD_REFRESH_DAYS days before the --from date

    By default, uses current datetime as --from date, so sources are re-downloaded
    if they were downloaded more than DOWNLOAD_REFRESH_DAYS days ago.

    Args:
        from_date: Optional datetime. If provided, only show sources with no history
                   or with download_timestamp older than DOWNLOAD_REFRESH_DAYS.
                   If None, defaults to current datetime, showing only sources not yet
                   downloaded or downloaded more than DOWNLOAD_REFRESH_DAYS days ago.

    Returns:
        list[SourceConfig] - Sources that need to be downloaded.
    """
    conf = Conf()
    history = History()
    sources = conf.get_all_sources()

    if from_date is None:
        from_date = datetime.now()

    sources_to_download = []

    for source in sources:
        records = history.get_records_by_key(source.name, source.year)

        needs_download = False

        if not records:
            needs_download = True
        else:
            latest_record = max(records, key=lambda r: r.download_timestamp)
            latest_timestamp = datetime.fromisoformat(
                latest_record.download_timestamp
            ).timestamp()
            threshold = latest_timestamp - 24 * 60 * 60 * DOWNLOAD_REFRESH_DAYS
            if threshold < from_date.timestamp():
                needs_download = True
        if needs_download:
            sources_to_download.append(source)

    return sources_to_download


def download_single(name: str, year: str):
    """
    Download a single specific source identified by name and year.

    Args:
        name: The name of the source to download.
        year: The year of the source to download.

    Returns:
        int: 0 on success, 1 on error.
    """
    try:
        conf = Conf()
        downloader = Downloader()

        matching_sources = [
            s for s in conf.get_all_sources() if s.name == name and s.year == year
        ]

        if not matching_sources:
            print(f"✗ No source found with name='{name}' and year='{year}'")
            return 1

        if len(matching_sources) > 1:
            print(f"✗ Multiple sources found with name='{name}' and year='{year}'")
            return 1

        source = matching_sources[0]
        print(f"Downloading {source.name} ({source.format}, {source.year})...")

        success, record, error, file_path = downloader.download_source(source)

        if success and record:
            print(f"  Success: Downloaded to {file_path}")
            print(f"    Duration: {record.download_duration:.2f}s")
        else:
            print(f"  Failed: {error}")
            return 1

        return 0

    except Exception as e:
        print(f"✗ Download failed: {e}")
        return 1


def download(from_date: datetime | None = None):
    """
    Download sources based on the plan.

    Downloads sources that either have no download history or were downloaded more
    than DOWNLOAD_REFRESH_DAYS days before the --from date.

    Args:
        from_date: Optional datetime. If provided, only download sources not downloaded
                   since this date. If None, defaults to current datetime, downloading
                   only sources not yet downloaded or downloaded more than
                   DOWNLOAD_REFRESH_DAYS days ago.

    Returns:
        int: 0 on success, 1 on error or cancellation.
    """
    try:
        history = History()
        sources_to_download = plan(from_date)

        if not sources_to_download:
            print("Download plan:")
            print("  All sources are up to date.")
            return 0

        print("Download plan:")
        print(f"  {len(sources_to_download)} source(s) to download:")
        for source in sources_to_download:
            records = history.get_records_by_key(source.name, source.year)
            status = "NEW" if not records else "UPDATE"
            print(f"    [{status}] {source.name} ({source.format}, {source.year})")

        response = input("\nProceed with download? [Y/N]: ").strip().upper()
        if response != "Y":
            print("Download cancelled.")
            return 1

        print("\nStarting download...")
        downloader = Downloader()
        downloader.download_all(sources_to_download)
        print("\nDownload complete!")
        return 0

    except Exception as e:
        print(f"✗ Download failed: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Downloader CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    subparsers.add_parser("validate", help="Validate sources configuration")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Show download plan")
    plan_parser.add_argument(
        "--from",
        type=str,
        dest="from_date",
        help="Only include sources not downloaded since this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
        default=None,
    )

    # Download command
    download_parser = subparsers.add_parser("download", help="Download sources")
    download_parser.add_argument(
        "--from",
        type=str,
        dest="from_date",
        help="Only download sources not downloaded since this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
        default=None,
    )
    download_parser.add_argument(
        "--name",
        type=str,
        dest="source_name",
        help="Download only a specific source by name (requires --year)",
        default=None,
    )
    download_parser.add_argument(
        "--year",
        type=str,
        dest="source_year",
        help="Download only a specific source by year (requires --name)",
        default=None,
    )

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(validate())
    elif args.command == "plan":
        from_date = None
        if args.from_date:
            try:
                from_date = datetime.fromisoformat(args.from_date)
            except ValueError:
                print(
                    f"✗ Invalid date format: {args.from_date}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                )
                sys.exit(1)
        sources = plan(from_date)
        print("Download plan:")
        if sources:
            print(f"  {len(sources)} source(s) to download:")
            history = History()
            for source in sources:
                records = history.get_records_by_key(source.name, source.year)
                status = "NEW" if not records else "UPDATE"
                print(f"    [{status}] {source.name} ({source.format}, {source.year})")
        else:
            print("  All sources are up to date.")
        sys.exit(0)
    elif args.command == "download":
        from_date = None
        if args.from_date:
            try:
                from_date = datetime.fromisoformat(args.from_date)
            except ValueError:
                print(
                    f"✗ Invalid date format: {args.from_date}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                )
                sys.exit(1)

        if args.source_name and args.source_year:
            sys.exit(download_single(args.source_name, args.source_year))
        elif args.source_name or args.source_year:
            print("✗ Both --name and --year must be provided together")
            sys.exit(1)

        sys.exit(download(from_date))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
