import json
import logging
import random
import re
import tempfile
import time
from datetime import date, datetime
from pathlib import Path

import duckdb
import requests

logger = logging.getLogger(__name__)

BODACC_INIT_FILE_NAME = "bodacc-init.csv"
BODACC_INCREMENTAL_FILE_NAME = "bodacc-{}-{}.csv"
BODACC_INCREMENTAL_GLOB = "bodacc-*.csv"
BODACC_INCREMENTAL_PATTERN = re.compile(
    r"^bodacc-(?P<dateparution>\d{4}-\d{2}-\d{2})-(?P<numeroannonce>.+)\.csv$"
)
DATEPARUTION_COLUMN = "dateparution"
ID_COLUMN = "numeroannonce"

BODACC_API_URL = (
    "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/"
    "catalog/datasets/annonces-commerciales/records"
)


class BodaccIncremental:
    """
    Incremental downloader for the BODACC (Bulletin officiel des annonces
    civiles et commerciales) open data API.

    Tracks progress using a checkpoint of (dateparution, numeroannonce),
    derived either from the most recent incremental CSV file already written
    to raw_dir, or, if none exists yet, from the init file. Each call to
    fetch_new_lines pages through the API from that checkpoint onward, and
    write_incremental_csv persists the results as a new checkpointed CSV file.
    """

    def __init__(self, raw_dir: str | None = None) -> None:
        """
        Args:
            raw_dir: Directory where the init file and incremental CSV files
                are read from and written to. Defaults to
                datalake/raw/bodacc relative to this file's location.
        """
        if raw_dir is None:
            self.raw_dir = (
                Path(__file__).parent.parent.parent.parent
                / "datalake"
                / "raw"
                / "bodacc"
            )
        else:
            self.raw_dir = Path(raw_dir)

        self.bodacc_init_file_path = self.raw_dir / BODACC_INIT_FILE_NAME

    @staticmethod
    def _checkpoint_from_file(file_path: Path) -> tuple[date, int]:
        """
        Read the latest checkpoint from a CSV file.

        The checkpoint is determined by selecting the row with the greatest
        (dateparution, numeroannonce) pair.

        Args:
            file_path: Path to the CSV file.

        Returns:
            tuple[date, int]: The latest (dateparution, numeroannonce) checkpoint
            contained in the file.

        Raises:
            ValueError: If the file contains no rows.
        """

        query = f"""
            SELECT
                {DATEPARUTION_COLUMN},
                {ID_COLUMN}
            FROM "{file_path}"
            ORDER BY {DATEPARUTION_COLUMN} DESC, {ID_COLUMN} DESC
            LIMIT 1
        """

        with duckdb.connect(":memory:") as con:
            result = con.execute(query).fetchone()

        if not result:
            raise ValueError(f"No checkpoint found in {file_path}")

        return result[0], result[1]

    def _latest_incremental_checkpoint(self) -> tuple[date, int] | None:
        """
        Find the most recent checkpoint among existing incremental CSV files.

        Scans raw_dir for files matching bodacc-{dateparution}-{numeroannonce}.csv
        and parses the checkpoint from each filename directly, without opening
        or querying the file contents. The "most recent" checkpoint is the
        maximum (dateparution, numeroannonce) pair found, compared as a tuple
        (date first, then numeroannonce as a tiebreaker).

        Returns:
            tuple[date, int] | None: The latest (dateparution, numeroannonce)
            checkpoint found, or None if no incremental files exist in raw_dir.
        """

        latest: tuple[date, int] | None = None

        for path in self.raw_dir.glob(BODACC_INCREMENTAL_GLOB):
            match = BODACC_INCREMENTAL_PATTERN.match(path.name)
            if not match:
                continue

            file_date = date.fromisoformat(match.group("dateparution"))
            file_id = int(match.group("numeroannonce"))

            if latest is None or (file_date, file_id) > latest:
                latest = (file_date, file_id)

        return latest

    def get_checkpoint(self) -> tuple[date, int]:
        """
        Determine the current checkpoint to resume fetching from.

        Prefers the most recent incremental file's checkpoint, inferred
        purely from filenames in raw_dir. Falls back to reading the
        checkpoint from the init file's contents if no incremental files
        exist yet.

        Returns:
            tuple[date, int]: The (dateparution, numeroannonce) checkpoint
            to fetch new records from.

        Raises:
            FileNotFoundError: If neither incremental files nor an init
                file are present in raw_dir.
        """
        latest = self._latest_incremental_checkpoint()

        if latest is not None:
            return latest

        elif self.bodacc_init_file_path.exists():
            return self._checkpoint_from_file(self.bodacc_init_file_path)

        else:
            raise FileNotFoundError(f"No BODACC file found in {self.raw_dir}")

    def fetch_new_lines(
        self,
        checkpoint: tuple[date, int],
        batch_size: int = 100,
        min_jitter: float = 0.5,
        max_jitter: float = 1.5,
    ) -> list[dict]:
        """
        Fetch all new BODACC records published after the given checkpoint.

        Repeatedly queries the BODACC API in pages of batch_size, ordered by
        (dateparution, numeroannonce), advancing the checkpoint after each
        page to the last record fetched. Pagination stops once a page comes
        back smaller than batch_size (no more results) or empty. A random
        delay between min_jitter and max_jitter seconds is added between
        requests to avoid hammering the API.

        Args:
            checkpoint: (dateparution, numeroannonce) tuple to fetch records
                strictly after.
            batch_size: Number of records to request per API call.
            min_jitter: Minimum delay, in seconds, between successive requests.
            max_jitter: Maximum delay, in seconds, between successive requests.

        Returns:
            list[dict]: All new records fetched, in ascending order of
            (dateparution, numeroannonce), across every page retrieved.
        """
        checkpoint_date, checkpoint_id = checkpoint

        records = []

        logger.info(
            "Starting BODACC fetch from checkpoint=%s id=%s",
            checkpoint_date,
            checkpoint_id,
        )

        while True:
            where = (
                f'({DATEPARUTION_COLUMN} > "{checkpoint_date.isoformat()}") '
                f"OR "
                f'({DATEPARUTION_COLUMN} <= "{checkpoint_date.isoformat()}" AND {DATEPARUTION_COLUMN} >= "{checkpoint_date.isoformat()}" '
                f"AND {ID_COLUMN} > {checkpoint_id})"
            )

            params = {
                "where": where,
                "limit": batch_size,
                "order_by": f"{DATEPARUTION_COLUMN},{ID_COLUMN}",
            }

            response = requests.get(
                BODACC_API_URL,
                params=params,
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()
            batch = data.get("results", [])

            if not batch:
                break

            records.extend(batch)

            last = batch[-1]

            checkpoint_date = datetime.strptime(
                last[DATEPARUTION_COLUMN],
                "%Y-%m-%d",
            ).date()

            checkpoint_id = last[ID_COLUMN]

            logger.info(
                "Fetched %d records (total=%d), new checkpoint=%s %s",
                len(batch),
                len(records),
                checkpoint_date,
                checkpoint_id,
            )

            if len(batch) < batch_size:
                break

            time.sleep(
                random.uniform(
                    min_jitter,
                    max_jitter,
                )
            )

        logger.info(
            "BODACC fetch completed: %d records",
            len(records),
        )

        return records

    def write_incremental_csv(self, records: list[dict]) -> Path | None:
        """
        Write fetched records to a new checkpointed incremental CSV file.

        The output filename encodes the checkpoint of the last record in
        the list (bodacc-{dateparution}-{numeroannonce}.csv), so that a
        later call to get_checkpoint can resume from where this run left off.
        Records are written via a temporary JSON file, loaded with DuckDB's
        read_json_auto, and copied out to CSV.

        Args:
            records: Records to write, as returned by fetch_new_lines. Must
                be ordered so that the last element carries the checkpoint
                to encode in the filename.

        Returns:
            Path | None: Path to the written CSV file, or None if records
            was empty (nothing written).
        """
        if not records:
            logger.info("No new records to write.")
            return None

        last = records[-1]

        last_date = datetime.strptime(
            last[DATEPARUTION_COLUMN],
            "%Y-%m-%d",
        ).date()

        last_id = last[ID_COLUMN]

        output_path = self.raw_dir / BODACC_INCREMENTAL_FILE_NAME.format(
            last_date.isoformat(),
            last_id,
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as f:
            json.dump(records, f, ensure_ascii=False)
            json_path = f.name

        with duckdb.connect() as con:
            con.execute(f"""
                COPY (
                    SELECT *
                    FROM read_json_auto('{json_path}')
                )
                TO '{output_path}'
                (FORMAT CSV, HEADER);
            """)

        logger.info("Wrote %d records to %s", len(records), output_path)

        return output_path
