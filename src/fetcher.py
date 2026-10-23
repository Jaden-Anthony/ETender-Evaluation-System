"""Client for querying the South African National Treasury eTenders endpoint."""

import logging
from typing import ClassVar

import requests

from src.config import Config
from src.models import RawTender, TenderDocument

logger = logging.getLogger(__name__)


class ETenderFetcher:
    """Retrieves active tenders directly from the portal's JSON endpoint."""

    DEFAULT_HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(
        self,
        endpoint_url: str | None = None,
        timeout: int = 30,
        batch_size: int = 250,
    ):
        """Initialize the fetcher with endpoint settings."""
        self.endpoint_url = endpoint_url or Config.ETENDER_API_URL
        self.timeout = timeout
        self.batch_size = batch_size

    def fetch_active_tenders(
        self, max_records: int | None = None
    ) -> list[RawTender]:
        """Fetch all currently advertised active tenders.

        Args:
            max_records: Optional maximum number of tenders to fetch.

        Returns:
            List of parsed RawTender objects.
        """
        all_tenders: list[RawTender] = []
        start = 0
        total_records: int | None = None

        logger.info(f"Connecting to {self.endpoint_url}...")

        while True:
            params = {
                "status": 1,  # 1 = Currently Advertised
                "draw": 1,
                "start": start,
                "length": self.batch_size,
            }

            try:
                response = requests.get(
                    self.endpoint_url,
                    headers=self.DEFAULT_HEADERS,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()
            except requests.RequestException as err:
                logger.error(f"Failed to fetch batch at offset {start}: {err}")
                break

            if total_records is None:
                total_records = payload.get("recordsTotal", 0)
                logger.info(f"Total active tenders on portal: {total_records}")

            raw_rows = payload.get("data", [])
            if not raw_rows:
                break

            for row in raw_rows:
                parsed = self._parse_tender(row)
                if parsed:
                    all_tenders.append(parsed)
                    if max_records and len(all_tenders) >= max_records:
                        logger.info(f"Reached record limit ({max_records})")
                        return all_tenders

            start += len(raw_rows)
            logger.info(f"Progress: {start}/{total_records} tenders loaded")

            if total_records is not None and start >= total_records:
                break

        logger.info(f"Successfully fetched {len(all_tenders)} raw tenders")
        return all_tenders

    def _parse_tender(self, row: dict) -> RawTender | None:
        """Convert a raw API dictionary into a typed RawTender model."""
        try:
            tender_id = row.get("id")
            tender_no = (row.get("tender_No") or f"ID-{tender_id}").strip()
            organ = (
                row.get("organ_of_State")
                or row.get("department")
                or "Unknown Organ of State"
            ).strip()

            docs: list[TenderDocument] = []
            for doc in row.get("supportDocument", []) or []:
                if isinstance(doc, dict) and doc.get("fileName"):
                    docs.append(
                        TenderDocument(
                            document_id=doc.get("supportDocumentID"),
                            file_name=doc.get("fileName").strip(),
                            extension=doc.get("extension"),
                        )
                    )

            return RawTender(
                id=tender_id,
                tender_no=tender_no,
                organ_of_state=organ,
                province=row.get("province") or "National",
                category=row.get("category") or "General",
                tender_type=row.get("type"),
                description=(row.get("description") or "").strip(),
                date_published=row.get("date_Published"),
                closing_date=row.get("closing_Date"),
                contact_person=row.get("contactPerson"),
                contact_email=row.get("email"),
                telephone=row.get("telephone"),
                documents=docs,
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(f"Error parsing tender row: {exc}")
            return None
