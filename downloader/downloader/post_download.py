import json
import re
from pathlib import Path

import polars as pl


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
    marche_file_path = Path(file_path.parent / f"commande-publique-marche_{year}.parquet")
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
        print(f"  Wrote Parquet file: {marche_file_path}")

        concession_df.write_parquet(concession_file_path)
        print(f"  Wrote Parquet file: {concession_file_path}")


def post(post_name: str, file_path: Path) -> None:
    """
    Execute a post-download processing script on a file.

    Args:
        post_name: Name of the post-processing script to execute.
                   Currently supported: "commande_publique"
        file_path: Path to the downloaded file to process.

    Raises:
        ValueError: If the specified post_name is not recognized.
    """
    if post_name == "commande_publique":
        commande_publique(file_path)
    else:
        raise ValueError(f"Unknown post-processing script: {post_name}")
