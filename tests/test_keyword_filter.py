"""Unit tests for the keyword filtering engine."""

from src.keyword_filter import KeywordFilter
from src.models import RawTender


def test_keyword_matcher_finds_ai_terms():
    """Verify detection of specific AI keywords."""
    engine = KeywordFilter(ai_keywords=["machine learning", "automation", "automated"])
    text = "Development of a machine learning model for automation and automated classification."
    ai_hits, dm_hits = engine.find_matches(text)

    assert "machine learning" in ai_hits
    assert "automation" in ai_hits
    assert "automated" in ai_hits
    assert len(dm_hits) == 0


def test_keyword_matcher_finds_digital_marketing_terms():
    """Verify detection of digital marketing keywords."""
    engine = KeywordFilter(
        digital_marketing_keywords=["digital marketing", "seo", "branding"]
    )
    text = "Tender for creative branding and digital marketing services."
    ai_hits, dm_hits = engine.find_matches(text)

    assert len(ai_hits) == 0
    assert "branding" in dm_hits
    assert "digital marketing" in dm_hits


def test_keyword_matcher_respects_word_boundaries():
    """Verify that partial words do not trigger false positive matches."""
    engine = KeywordFilter(ai_keywords=["ai"])
    # 'tail' and 'chain' contain 'ai', but should NOT match standalone 'ai'
    text = "Supply of retail chain products"
    ai_hits, _ = engine.find_matches(text)
    assert len(ai_hits) == 0


def test_filter_candidates():
    """Verify candidate filtering extracts matching tenders only."""
    engine = KeywordFilter(
        ai_keywords=["automation"],
        digital_marketing_keywords=["portal"],
    )
    tenders = [
        RawTender(
            id=1,
            tender_no="T1",
            organ_of_state="Municipality",
            description="Design and implement revenue self-service portal systems",
        ),
        RawTender(
            id=2,
            tender_no="T2",
            organ_of_state="Municipality",
            description="Supply of standard office furniture and desks",
        ),
    ]

    candidates = engine.filter_candidates(tenders)
    assert len(candidates) == 1
    matched_tender, hits = candidates[0]
    assert matched_tender.tender_no == "T1"
    assert "portal" in hits
