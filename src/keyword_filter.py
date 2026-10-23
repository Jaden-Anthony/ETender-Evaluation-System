"""Keyword matching and candidate pre-filtering engine."""

import logging
import re

from src.config import Config
from src.models import RawTender

logger = logging.getLogger(__name__)


class KeywordFilter:
    """Pre-filters raw tenders using keyword taxonomies before AI evaluation."""

    def __init__(
        self,
        ai_keywords: list[str] | None = None,
        digital_marketing_keywords: list[str] | None = None,
    ):
        """Initialize filter with keyword taxonomies."""
        self.ai_keywords = ai_keywords or Config.AI_KEYWORDS
        self.dm_keywords = (
            digital_marketing_keywords or Config.DIGITAL_MARKETING_KEYWORDS
        )

        # Precompile regex patterns for performance and exact word matching
        self._ai_patterns = [
            (kw, re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE))
            for kw in self.ai_keywords
        ]
        self._dm_patterns = [
            (kw, re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE))
            for kw in self.dm_keywords
        ]

    def find_matches(self, text: str) -> tuple[list[str], list[str]]:
        """Search text for AI and Digital Marketing keyword matches.

        Args:
            text: String content (e.g. description, title, category).

        Returns:
            Tuple of (matched_ai_keywords, matched_dm_keywords).
        """
        if not text:
            return [], []

        ai_hits = [kw for kw, pattern in self._ai_patterns if pattern.search(text)]
        dm_hits = [kw for kw, pattern in self._dm_patterns if pattern.search(text)]

        return list(set(ai_hits)), list(set(dm_hits))

    def filter_candidates(
        self, tenders: list[RawTender]
    ) -> list[tuple[RawTender, list[str]]]:
        """Filter a list of raw tenders down to candidate matches.

        Args:
            tenders: List of RawTender models.

        Returns:
            List of tuples: (RawTender, combined_matched_keywords).
        """
        candidates: list[tuple[RawTender, list[str]]] = []

        for tender in tenders:
            searchable_text = (
                f"{tender.tender_no} {tender.description} "
                f"{tender.category} {tender.organ_of_state}"
            )
            ai_hits, dm_hits = self.find_matches(searchable_text)
            combined_hits = list(set(ai_hits + dm_hits))

            if combined_hits:
                candidates.append((tender, combined_hits))

        logger.info(
            f"Filtered {len(tenders)} tenders down to {len(candidates)} candidates"
        )
        return candidates
