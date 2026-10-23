"""Unit tests for the Notifier module."""

from unittest.mock import MagicMock, patch

from src.models import AIEvaluation, PipelineStats, QualifiedTender
from src.notifier import Notifier


def test_build_digest_html():
    """Verify HTML email digest generation."""
    notifier = Notifier()
    eval_data = AIEvaluation(
        relevance_score=9.5,
        is_qualified=True,
        domain_tags=["Digital Marketing"],
        executive_summary="Global marketing campaign.",
        recommended_action="Apply",
    )
    tenders = [
        QualifiedTender(
            tender_no="SAT 351/26",
            organ_of_state="South African Tourism",
            province="Gauteng",
            description="Integrated marketing agency panel",
            keyword_matches=["marketing"],
            ai_evaluation=eval_data,
        )
    ]
    stats = PipelineStats(
        total_scanned=2000,
        candidate_matches=20,
        ai_qualified_count=1,
        elapsed_seconds=12.5,
        model_used="Ollama (qwen2.5:14b)",
    )

    html = notifier._build_digest_html(tenders, stats, "23 Oct 2026")
    assert "SAT 351/26" in html
    assert "South African Tourism" in html
    assert "9.5/10" in html
    assert "Global marketing campaign." in html
    assert "qwen2.5:14b" in html


def test_build_heartbeat_html():
    """Verify zero-match heartbeat email generation."""
    notifier = Notifier()
    stats = PipelineStats(
        total_scanned=2150,
        candidate_matches=0,
        ai_qualified_count=0,
        elapsed_seconds=10.0,
        model_used="Ollama",
    )

    html = notifier._build_heartbeat_html(stats, "23 Oct 2026")
    assert "2,150" in html
    assert "No new tenders" in html
    assert "System Healthy" in html


@patch("smtplib.SMTP_SSL")
def test_send_daily_digest_mocked(mock_smtp):
    """Verify SMTP transmission with mock."""
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    notifier = Notifier()
    notifier.config.GMAIL_SENDER = "test@company.com"
    notifier.config.GMAIL_APP_PASSWORD = "testpassword1234"
    notifier.config.TEAM_EMAILS = ["member1@company.com", "member2@company.com"]

    stats = PipelineStats(total_scanned=10, candidate_matches=1, ai_qualified_count=0)
    success = notifier.send_daily_digest([], stats)

    assert success is True
    assert mock_server.login.called
    assert mock_server.sendmail.called
