import argparse
import sys
from datetime import datetime

from downloader.conf import Conf
from downloader.downloader import Downloader
from downloader.history import History


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
    - Its latest download was before the --from date

    Args:
        from_date: Optional datetime. If provided, only show sources with no history
                   or with download_timestamp < from_date. If None, show only sources
                   with no history.

    Returns:
        list[SourceConfig] - Sources that need to be downloaded.
    """
    conf = Conf()
    history = History()
    sources = conf.get_all_sources()

    sources_to_download = []

    for source in sources:
        records = history.get_records_by_key(source.name, source.year)

        needs_download = False

        if not records:
            needs_download = True
        elif from_date is not None:
            latest_record = max(records, key=lambda r: r.download_timestamp)
            latest_timestamp = datetime.fromisoformat(latest_record.download_timestamp)
            if latest_timestamp < from_date:
                needs_download = True
        if needs_download:
            sources_to_download.append(source)

    return sources_to_download


def download(from_date: datetime | None = None):
    """
    Download sources based on the plan.

    Args:
        from_date: Optional datetime. If provided, only download sources not downloaded
                   since this date.

    Returns:
        0 on success, 1 on error or cancellation.
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
        sys.exit(download(from_date))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
