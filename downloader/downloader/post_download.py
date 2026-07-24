import json
import logging
import re
import shutil
import tempfile
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)


def commande_publique(file_path: Path) -> None:
    """
    Process commande_publique JSON file into separate Parquet files.

    Takes a JSON file containing 'marches' data with 'marche' and 'contrat-concession'
    arrays, and writes each as a separate Parquet file.

    Args:
        file_path: Path to the input JSON file. The year is extracted from the filename
                   stem to name the output files.

    Raises:
        ValueError: If the filename doesn't contain a 4-digit year.
        KeyError: If the expected keys are not found in the JSON data.
    """
    year = int(re.search(r"(\d{4})", file_path.stem).group(1))
    marche_file_path = Path(
        file_path.parent / f"commande-publique-marche_{year}.parquet"
    )
    concession_file_path = Path(
        file_path.parent / f"commande-publique-concession_{year}.parquet"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

        marche_df = pl.DataFrame(data["marches"]["marche"], strict=False)
        concession_df = pl.DataFrame(
            data["marches"]["contrat-concession"], strict=False
        )

        marche_df.write_parquet(marche_file_path)
        logger.info(f"  Wrote Parquet file: {marche_file_path}")

        concession_df.write_parquet(concession_file_path)
        logger.info(f"  Wrote Parquet file: {concession_file_path}")


def anct_subvention_ville_2019(file_path: Path) -> None:
    """
    Clean the ANCT "subvention ville 2019" raw file in place.

    Rewrites the file (encoded in cp1252) to:
      - drop the first line if it consists only of semicolons
        (e.g. ";;;;;;;;;;;;;"), a spurious header sometimes present
        in the raw export
      - replace triple double-quotes with a single double-quote
        on every line, fixing an over-escaping artifact in the source data

    Args:
        file_path: Path to the file to clean. The file is overwritten
                   in place via an atomic replace (temp file + move).
    """
    with file_path.open("r", encoding="cp1252") as src:
        first_line = src.readline()
        skip_first_line = first_line.strip() and set(first_line.strip()) == {";"}
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="cp1252",
            newline="",
            delete=False,
            dir=file_path.parent,
        ) as tmp:
            if not skip_first_line:
                tmp.write(first_line.replace('"""', '"'))
            for line in src:
                tmp.write(line.replace('"""', '"'))
    shutil.move(tmp.name, file_path)


def post(post_name: str, file_path: Path) -> None:
    """
    Execute a post-download processing script on a file.

    Args:
        post_name: Name of the post-processing script to execute.
                   Currently supported: "commande_publique",
                   "anct_subvention_ville_2019".
        file_path: Path to the downloaded file to process.

    Raises:
        ValueError: If the specified post_name is not recognized.
    """
    if post_name == "commande_publique":
        commande_publique(file_path)
    elif post_name == "anct_subvention_ville_2019":
        anct_subvention_ville_2019(file_path)
    else:
        raise ValueError(f"Unknown post-processing script: {post_name}")
