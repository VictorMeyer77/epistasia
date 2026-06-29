import argparse
import sys

from downloader.conf import Conf


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


def main():
    parser = argparse.ArgumentParser(description="Downloader CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    subparsers.add_parser("validate", help="Validate sources configuration")

    # Plan command (placeholder)
    subparsers.add_parser("plan", help="Show download plan")

    # Download command (placeholder)
    subparsers.add_parser("download", help="Download sources")

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(validate())
    elif args.command == "plan":
        print("Plan command: Not yet implemented")
        sys.exit(0)
    elif args.command == "download":
        print("Download command: Not yet implemented")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
