"""Unit tests for the Ollama AI evaluator."""

from src.ai_evaluator import OllamaEvaluator
from src.models import RawTender


def test_parse_llm_json_valid():
    """Verify parsing valid LLM JSON response."""
    evaluator = OllamaEvaluator()
    tender = RawTender(
        id=1,
        tender_no="T1",
        organ_of_state="Org",
        description="Portal development",
    )
    raw_json = (
        '{"relevance_score": 9.2, "is_qualified": true, '
        '"domain_tags": ["Portals", "Web Development"], '
        '"executive_summary": "High value portal development bid.", '
        '"recommended_action": "Apply Immediately"}'
    )

    result = evaluator._parse_llm_json(raw_json, tender)
    assert result.relevance_score == 9.2
    assert result.is_qualified is True
    assert "Portals" in result.domain_tags
    assert result.recommended_action == "Apply Immediately"


def test_parse_llm_json_with_markdown_ticks():
    """Verify JSON parsing when model wraps response in markdown code blocks."""
    evaluator = OllamaEvaluator()
    tender = RawTender(id=2, tender_no="T2", organ_of_state="Org", description="Desc")
    raw_response = (
        "```json\n"
        '{"relevance_score": 8.0, "is_qualified": true, "domain_tags": ["AI"], '
        '"executive_summary": "AI summary", "recommended_action": "Review"}\n'
        "```"
    )

    result = evaluator._parse_llm_json(raw_response, tender)
    assert result.relevance_score == 8.0
    assert result.is_qualified is True


def test_fallback_heuristic_filters_hardware():
    """Verify fallback heuristics identify physical hardware as unqualified."""
    evaluator = OllamaEvaluator()
    tender = RawTender(
        id=3,
        tender_no="T3",
        organ_of_state="Org",
        description="Supply of fully automated calorimeter instrument for coal testing",
    )

    result = evaluator._fallback_heuristic_evaluation(tender, ["automated"])
    assert result.is_qualified is False
    assert result.relevance_score < 5.0
