"""Pipeline orchestrator for the South African eTender scraping workflow."""

import logging
import time

from src.ai_evaluator import OllamaEvaluator
from src.config import Config
from src.exporter import Exporter
from src.fetcher import ETenderFetcher
from src.keyword_filter import KeywordFilter
from src.models import PipelineStats, QualifiedTender
from src.notifier import Notifier

logger = logging.getLogger(__name__)


class ETenderPipeline:
    """Coordinates fetching, filtering, AI evaluation, exporting, and notifications."""

    def __init__(
        self,
        fetcher: ETenderFetcher | None = None,
        filter_engine: KeywordFilter | None = None,
        evaluator: OllamaEvaluator | None = None,
        exporter: Exporter | None = None,
        notifier: Notifier | None = None,
    ):
        """Initialize the pipeline with modular components."""
        self.fetcher = fetcher or ETenderFetcher()
        self.filter_engine = filter_engine or KeywordFilter()
        self.evaluator = evaluator or OllamaEvaluator()
        self.exporter = exporter or Exporter()
        self.notifier = notifier or Notifier()

    def run(
        self,
        send_email: bool = True,
        show_toast: bool = True,
        max_tenders: int | None = None,
    ) -> PipelineStats:
        """Execute the complete end-to-end eTender pipeline.

        Args:
            send_email: Whether to dispatch the email digest.
            show_toast: Whether to display a Windows desktop toast.
            max_tenders: Optional limit for testing/debugging.

        Returns:
            PipelineStats telemetry.
        """
        start_time = time.time()
        logger.info("=== Starting eTender Scraping & AI Analysis Pipeline ===")

        # 1. Fetch live active tenders
        raw_tenders = self.fetcher.fetch_active_tenders(max_records=max_tenders)
        total_scanned = len(raw_tenders)

        # 2. Pre-filter by keywords
        candidates = self.filter_engine.filter_candidates(raw_tenders)
        candidate_count = len(candidates)

        # 3. AI Semantic Evaluation & False-Positive Elimination
        qualified_tenders: list[QualifiedTender] = []
        max_eval = min(candidate_count, Config.MAX_TENDERS_TO_ANALYZE)

        logger.info(
            f"Evaluating top {max_eval} candidates with Ollama ({self.evaluator.model_name})..."
        )

        for idx, (tender, kw_matches) in enumerate(candidates[:max_eval], 1):
            logger.info(
                f"[{idx}/{max_eval}] Analyzing {tender.tender_no}: {tender.organ_of_state}"
            )
            evaluation = self.evaluator.evaluate_tender(tender, kw_matches)

            # Accept if qualified or meets score threshold
            if (
                evaluation.is_qualified
                and evaluation.relevance_score >= Config.MIN_RELEVANCE_SCORE
            ):
                doc_names = [d.file_name for d in tender.documents]
                qualified_tender = QualifiedTender(
                    tender_no=tender.tender_no,
                    organ_of_state=tender.organ_of_state,
                    province=tender.province,
                    category=tender.category,
                    closing_date=tender.closing_date,
                    date_published=tender.date_published,
                    description=tender.description,
                    contact_person=tender.contact_person,
                    contact_email=tender.contact_email,
                    telephone=tender.telephone,
                    attached_documents=doc_names,
                    keyword_matches=kw_matches,
                    ai_evaluation=evaluation,
                )
                qualified_tenders.append(qualified_tender)
            else:
                logger.info(
                    f"Excluded false positive: {tender.tender_no} "
                    f"(Score: {evaluation.relevance_score:.1f})"
                )

        # Sort descending by relevance score
        qualified_tenders.sort(
            key=lambda t: t.ai_evaluation.relevance_score if t.ai_evaluation else 0.0,
            reverse=True,
        )

        elapsed = time.time() - start_time
        stats = PipelineStats(
            total_scanned=total_scanned,
            candidate_matches=candidate_count,
            ai_qualified_count=len(qualified_tenders),
            elapsed_seconds=elapsed,
            model_used=f"Ollama ({self.evaluator.model_name})",
            status_message="Success",
        )

        # 4. Export results to local CSV & JSON
        csv_path = self.exporter.export(qualified_tenders)

        # 5. Notifications
        if send_email:
            self.notifier.send_daily_digest(qualified_tenders, stats, csv_path=csv_path)

        if show_toast:
            toast_msg = (
                f"Scanned {total_scanned:,} tenders. "
                f"Qualified {len(qualified_tenders)} AI/Digital bids in {elapsed:.1f}s."
            )
            self.notifier.show_windows_toast("eTender Intelligence", toast_msg)

        logger.info(
            f"=== Pipeline Completed in {elapsed:.1f}s: "
            f"{len(qualified_tenders)} qualified tenders exported to {csv_path} ==="
        )
        return stats
