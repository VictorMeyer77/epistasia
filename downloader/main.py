import argparse
import sys
from datetime import datetime

from downloader.conf import Conf
from downloader.history import History


def validate():
    """Validate the sources configuration file."""
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
        0 on success, 1 on error.
    """
    try:
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
                latest_timestamp = datetime.fromisoformat(
                    latest_record.download_timestamp
                )
                if latest_timestamp < from_date:
                    needs_download = True
            if needs_download:
                sources_to_download.append(source)

        print("Download plan:")
        if sources_to_download:
            print(f"  {len(sources_to_download)} source(s) to download:")
            for source in sources_to_download:
                status = (
                    "NEW"
                    if not history.get_records_by_key(source.name, source.year)
                    else "UPDATE"
                )
                print(f"    [{status}] {source.name} ({source.format}, {source.year})")
        else:
            print("  All sources are up to date.")

        return 0
    except Exception as e:
        print(f"✗ Plan failed: {e}")
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

    # Download command (placeholder)
    subparsers.add_parser("download", help="Download sources")

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
        sys.exit(plan(from_date))
    elif args.command == "download":
        print("Download command: Not yet implemented")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
