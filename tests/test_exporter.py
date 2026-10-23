"""Unit tests for the Exporter module."""

from pathlib import Path

from src.exporter import Exporter
from src.models import AIEvaluation, QualifiedTender


def test_exporter_writes_csv_and_json(tmp_path: Path):
    """Verify that exporter writes valid CSV and JSON files."""
    exporter = Exporter(output_dir=tmp_path)
    eval_data = AIEvaluation(
        relevance_score=8.5,
        is_qualified=True,
        domain_tags=["AI"],
        executive_summary="AI briefing",
        recommended_action="Apply",
    )
    tenders = [
        QualifiedTender(
            tender_no="T-100",
            organ_of_state="City of Cape Town",
            province="Western Cape",
            category="Information Technology",
            description="AI Chatbot development",
            attached_documents=["spec.pdf"],
            keyword_matches=["chatbot"],
            ai_evaluation=eval_data,
        )
    ]

    csv_path = exporter.export(tenders, prefix="test_run")
    assert csv_path.exists()
    assert (tmp_path / "latest_matching_tenders.csv").exists()

    content = csv_path.read_text(encoding="utf-8-sig")
    assert "T-100" in content
    assert "City of Cape Town" in content
    assert "8.5" in content
