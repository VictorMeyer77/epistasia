import os
from pathlib import Path

from downloader.incremental.bodacc import BodaccIncremental
from downloader.incremental.inpi_rne_companies import InpiRneCompaniesClient


def run_incremental(name: str) -> Path | None:
    """
    Run the incremental download process for a named data source.

    Dispatches to the appropriate incremental handler. The handler is
    responsible for determining the current checkpoint, fetching any new
    records, and writing them to a new incremental file.

    Args:
        name: Identifier of the incremental source to run. Currently only
            "bodacc" is supported.

    Returns:
        Path | None: Path to the generated incremental CSV file, or None if
            no new records were found.

    Raises:
        ValueError: If name does not match a supported incremental process.
    """
    if name == "bodacc":
        incr = BodaccIncremental()
        checkpoint = incr.get_checkpoint()
        records = incr.fetch_new_lines(checkpoint)
        return incr.write_incremental_csv(records)
    elif name == "inpi-rne-companies":
        inpi_client = InpiRneCompaniesClient(
            username=os.environ["INPI_USERNAME"],
            password=os.environ["INPI_PASSWORD"],
            start_date=os.environ["INPI_START_DATE"],
            reverse=False,
        )
        inpi_client.run()
    else:
        raise ValueError(f"Unknown incremental process: {name}")
