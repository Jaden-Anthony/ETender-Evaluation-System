"""Unit tests for Pydantic data models."""

from src.models import AIEvaluation, QualifiedTender, RawTender, TenderDocument


def test_raw_tender_instantiation():
    """Verify RawTender instantiates with valid and default fields."""
    tender = RawTender(
        id=101,
        tender_no="T123/2026",
        organ_of_state="City of Ekurhuleni",
        description="Supply of AI machine learning solutions",
        documents=[
            TenderDocument(
                document_id="doc-1",
                file_name="spec.pdf",
                extension=".pdf",
            )
        ],
    )
    assert tender.id == 101
    assert tender.tender_no == "T123/2026"
    assert tender.province == "National"
    assert len(tender.documents) == 1
    assert tender.documents[0].file_name == "spec.pdf"


def test_ai_evaluation_model():
    """Verify AIEvaluation serialization and constraints."""
    evaluation = AIEvaluation(
        relevance_score=8.5,
        is_qualified=True,
        domain_tags=["AI", "Machine Learning"],
        executive_summary="Strategic AI opportunity for predictive analytics.",
        recommended_action="Apply",
    )
    assert evaluation.relevance_score == 8.5
    assert evaluation.is_qualified is True
    assert "AI" in evaluation.domain_tags


def test_qualified_tender_model():
    """Verify QualifiedTender attaches AI evaluation correctly."""
    evaluation = AIEvaluation(
        relevance_score=9.0,
        is_qualified=True,
        domain_tags=["Digital Marketing"],
        executive_summary="Pan-African digital marketing campaign.",
        recommended_action="High Priority",
    )
    tender = QualifiedTender(
        tender_no="SAT 351/26",
        organ_of_state="South African Tourism",
        description="Global integrated marketing agency tender",
        keyword_matches=["digital marketing", "branding"],
        ai_evaluation=evaluation,
    )
    assert tender.tender_no == "SAT 351/26"
    assert tender.ai_evaluation.relevance_score == 9.0
