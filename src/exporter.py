"""Module for serializing qualified tenders to CSV and JSON formats."""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.models import QualifiedTender

logger = logging.getLogger(__name__)


class Exporter:
    """Exports qualified tenders to structured files for local analysis and archiving."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize the exporter with an output directory."""
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, tenders: list[QualifiedTender], prefix: str = "tenders") -> Path:
        """Export qualified tenders to both CSV and JSON formats.

        Args:
            tenders: List of QualifiedTender models.
            prefix: Filename prefix.

        Returns:
            Path to the generated CSV file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.output_dir / f"{prefix}_{timestamp}.csv"
        json_path = self.output_dir / f"{prefix}_{timestamp}.json"

        # Also write to latest.csv for easy reference
        latest_csv_path = self.output_dir / "latest_matching_tenders.csv"

        self._export_csv(tenders, csv_path)
        self._export_csv(tenders, latest_csv_path)
        self._export_json(tenders, json_path)

        logger.info(f"Saved {len(tenders)} tenders to {csv_path}")
        return csv_path

    def _export_csv(self, tenders: list[QualifiedTender], path: Path) -> None:
        """Serialize tenders to CSV."""
        fieldnames = [
            "tender_no",
            "organ_of_state",
            "province",
            "category",
            "relevance_score",
            "is_qualified",
            "recommended_action",
            "closing_date",
            "contact_email",
            "contact_person",
            "telephone",
            "keyword_matches",
            "attached_documents",
            "executive_summary",
            "full_description",
        ]

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for t in tenders:
                eval_data = t.ai_evaluation
                row = {
                    "tender_no": t.tender_no,
                    "organ_of_state": t.organ_of_state,
                    "province": t.province,
                    "category": t.category,
                    "relevance_score": f"{eval_data.relevance_score:.1f}"
                    if eval_data
                    else "N/A",
                    "is_qualified": "YES"
                    if (eval_data and eval_data.is_qualified)
                    else "NO",
                    "recommended_action": eval_data.recommended_action
                    if eval_data
                    else "Review",
                    "closing_date": t.closing_date or "N/A",
                    "contact_email": t.contact_email or "",
                    "contact_person": t.contact_person or "",
                    "telephone": t.telephone or "",
                    "keyword_matches": ", ".join(t.keyword_matches),
                    "attached_documents": "; ".join(t.attached_documents),
                    "executive_summary": eval_data.executive_summary
                    if eval_data
                    else "",
                    "full_description": t.description,
                }
                writer.writerow(row)

    def _export_json(self, tenders: list[QualifiedTender], path: Path) -> None:
        """Serialize tenders to JSON."""
        data = [t.model_dump() for t in tenders]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
