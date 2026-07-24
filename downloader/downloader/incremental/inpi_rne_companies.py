"""
INPI "Registre National des Entreprises" - diff/history client.

Downloads companies created/updated per calendar day via the
`/api/companies/diff` endpoint (paginating with the `searchAfter` cursor).

Results are written in batches:
    diff_<DAY>_<SEARCHAFTER>.json

When a day is completely downloaded, a marker file is written:
    diff_<DAY>_final.json

Checkpointing:
- If diff_<DAY>_final.json exists, the day is skipped.
- Otherwise, the latest batch file for that day is used to resume from the
  previous searchAfter cursor.

Download order is configurable:
- reverse=False (default): oldest -> newest
- reverse=True: newest -> oldest
"""

import glob
import json
import logging
import random
import re
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("inpi_diff")


class InpiRneCompaniesClient:
    """
    A client to fetch and store company diffs from the INPI API.

    Attributes:
        BASE_URL: Base URL for the INPI API.
        LOGIN_PATH: Endpoint for login.
        DIFF_PATH: Endpoint for fetching company diffs.
        SEARCH_AFTER_HEADER_CANDIDATES: Possible header names for the `searchAfter` cursor.
        FINAL_MARKER: Marker for final batch files.
    """

    BASE_URL: str = "https://registre-national-entreprises.inpi.fr"
    LOGIN_PATH: str = "/api/sso/login"
    DIFF_PATH: str = "/api/companies/diff"

    SEARCH_AFTER_HEADER_CANDIDATES: list[str] = [
        "pagination-search-after",
        "x-pagination-search-after",
        "search-after",
    ]

    FINAL_MARKER: str = "final"

    def __init__(
        self,
        username: str,
        password: str,
        output_dir: Path | str | None = None,
        start_date: str = "2023-01-01",
        end_date: str | None = None,
        reverse: bool = False,
        page_size: int = 100,
        batch_size: int = 10000,
        max_retries: int = 5,
        retry_backoff: float = 2.0,
        timeout: int = 30,
        extra_filters: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the INPIDiffClient.

        Args:
            username: INPI API username.
            password: INPI API password.
            output_dir: Directory to store downloaded data. If None, defaults to
                `Path(__file__).parent.parent.parent.parent / "datalake" / "raw"`.
            start_date: Start date for fetching diffs (YYYY-MM-DD).
            end_date: End date for fetching diffs (YYYY-MM-DD). Defaults to yesterday.
            reverse: If True, fetch from newest to oldest. Defaults to False.
            page_size: Number of results per API request.
            batch_size: Number of results per batch file. Must be a multiple of `page_size`.
            max_retries: Maximum retries for failed requests.
            retry_backoff: Base delay (in seconds) for retry backoff.
            timeout: Request timeout in seconds.
            extra_filters: Additional filters for the API request.
        """
        if batch_size % page_size != 0:
            raise ValueError("batch_size must be a multiple of page_size")

        self.username = username
        self.password = password
        self.output_dir = (
            Path(output_dir)
            if output_dir
            else Path(__file__).parent.parent.parent.parent
            / "datalake"
            / "raw"
            / "inpi-rne-companies"
        )
        self.start_date = start_date
        self.end_date = end_date or (date.today() - timedelta(days=1)).isoformat()
        self.reverse = reverse
        self.page_size = page_size
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout
        self.extra_filters = extra_filters or {}

        self.session = requests.Session()
        self.token: str | None = None

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def login(self) -> str:
        """
        Authenticate with the INPI API and store the token.

        Returns:
            The authentication token.
        """
        url = f"{self.BASE_URL}{self.LOGIN_PATH}"
        payload = {"username": self.username, "password": self.password}

        resp = self._request("POST", url, authenticated=False, json=payload)
        data = resp.json()

        token = data.get("token") or data.get("access_token") or data.get("id_token")
        if not token:
            raise RuntimeError(f"No token found in login response: {data}")

        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("Logged in.")

        return token

    def _request(
        self,
        method: str,
        url: str,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Make an HTTP request with retries and backoff.

        Args:
            method: HTTP method (e.g., "GET", "POST").
            url: Request URL.
            authenticated: If True, include authentication headers.
            **kwargs: Additional arguments for `requests.Session.request`.

        Returns:
            The HTTP response.

        Raises:
            RuntimeError: If the request fails after all retries.
        """
        last_exc = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)

                if (
                    authenticated
                    and resp.status_code == 401
                    and attempt < self.max_retries
                ):
                    logger.warning("401 -> re-login")
                    self.login()
                    continue

                if resp.status_code == 429 or resp.status_code >= 500:
                    wait = self.retry_backoff**attempt
                    logger.warning("HTTP %s retry in %.1fs", resp.status_code, wait)
                    time.sleep(wait + random.uniform(0, 0.5))  # Add jitter
                    continue

                resp.raise_for_status()
                return resp

            except requests.RequestException as exc:
                last_exc = exc
                wait = self.retry_backoff**attempt
                logger.warning(
                    "Retry %d/%d in %.1fs (%s)", attempt, self.max_retries, wait, exc
                )
                time.sleep(wait + random.uniform(0, 0.5))  # Add jitter

        raise RuntimeError("Request failed") from last_exc

    def _fetch_page(
        self,
        from_date: str,
        to_date: str,
        search_after: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        Fetch a single page of company diffs from the API.

        Args:
            from_date: Start date for the diff (YYYY-MM-DD).
            to_date: End date for the diff (YYYY-MM-DD).
            search_after: Cursor for pagination.

        Returns:
            A tuple of (rows, next_search_after), where:
                - rows: List of company diffs.
                - next_search_after: Cursor for the next page, or None.
        """
        url = f"{self.BASE_URL}{self.DIFF_PATH}"
        params = {
            "pageSize": self.page_size,
            "from": from_date,
            "to": to_date,
            **self.extra_filters,
        }

        if search_after:
            params["searchAfter"] = search_after

        resp = self._request("GET", url, params=params)
        data = resp.json()

        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = (
                data.get("companies") or data.get("data") or data.get("results") or []
            )
        else:
            rows = []

        next_search_after = None
        for h in self.SEARCH_AFTER_HEADER_CANDIDATES:
            if h in resp.headers:
                next_search_after = resp.headers[h]
                break

        if not next_search_after and rows:
            last = rows[-1]
            next_search_after = last.get("siren") or (last.get("formality") or {}).get(
                "siren"
            )

        return rows, next_search_after

    def _batch_path(self, day: str, cursor: str) -> Path:
        """
        Generate the file path for a batch file.

        Args:
            day: Date string (YYYY-MM-DD).
            cursor: SearchAfter cursor or FINAL_MARKER.

        Returns:
            The file path as a Path object.
        """
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", str(cursor))
        return self.output_dir / f"diff_{day}_{safe}.json"

    def _day_is_complete(self, day: str) -> bool:
        """
        Check if a day's diffs are fully downloaded.

        Args:
            day: Date string (YYYY-MM-DD).

        Returns:
            True if the day is complete, False otherwise.
        """
        return self._batch_path(day, self.FINAL_MARKER).exists()

    def _find_day_checkpoint(self, day: str) -> str | None:
        """
        Find the latest checkpoint for a day to resume downloading.

        Args:
            day: Date string (YYYY-MM-DD).

        Returns:
            The cursor to resume from, or None if no checkpoint exists.
        """
        pattern = str(self.output_dir / f"diff_{day}_*.json")
        files = [Path(f) for f in glob.glob(pattern) if not f.endswith("_final.json")]

        if not files:
            return None

        latest = max(files, key=lambda f: f.stat().st_mtime)
        prefix = f"diff_{day}_"
        cursor = latest.name[len(prefix) : -5]
        logger.info("Resume %s from %s", day, cursor)

        return cursor

    def _write_batch(self, day: str, rows: list[dict[str, Any]], cursor: str) -> None:
        """
        Write a batch of rows to a file.

        Args:
            day: Date string (YYYY-MM-DD).
            rows: List of company diffs.
            cursor: SearchAfter cursor or FINAL_MARKER.
        """
        path = self._batch_path(day, cursor)
        tmp_path = path.with_suffix(".tmp")

        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

        tmp_path.replace(path)
        logger.info("Saved %s (%d rows)", path.name, len(rows))

    def _iter_days(self) -> list[date]:
        """
        Iterate over days from start_date to end_date.

        Yields:
            Date objects for each day in the range.
        """
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)

        if self.reverse:
            d = end
            while d >= start:
                yield d
                d -= timedelta(days=1)
        else:
            d = start
            while d <= end:
                yield d
                d += timedelta(days=1)

    def _process_day(self, day: date) -> None:
        """
        Process a single day's diffs.

        Args:
            day: Date object for the day to process.
        """
        day_str = day.isoformat()

        if self._day_is_complete(day_str):
            logger.info("%s already complete", day_str)
            return

        from_date = (day - timedelta(days=1)).isoformat()
        to_date = day_str
        search_after = self._find_day_checkpoint(day_str)
        buffer: list[dict[str, Any]] = []

        while True:
            rows, next_cursor = self._fetch_page(from_date, to_date, search_after)

            if not rows:
                break

            buffer.extend(rows)

            if not next_cursor or next_cursor == search_after:
                break

            search_after = next_cursor

            while len(buffer) >= self.batch_size:
                batch = buffer[: self.batch_size]
                buffer = buffer[self.batch_size :]
                self._write_batch(day_str, batch, search_after)

        self._write_batch(day_str, buffer, self.FINAL_MARKER)
        logger.info("%s complete", day_str)

    def run(self) -> None:
        """Run the diff download process."""
        if not self.token:
            self.login()

        for day in self._iter_days():
            self._process_day(day)

        logger.info("Finished.")
