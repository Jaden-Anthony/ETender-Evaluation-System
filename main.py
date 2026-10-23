"""CLI entrypoint for the South African eTender AI scraper and notifier."""

import argparse
import logging
import sys

from src.ai_evaluator import OllamaEvaluator
from src.config import Config
from src.pipeline import ETenderPipeline


def setup_logging():
    """Configure logging to console and rolling log file."""
    log_file = Config.LOGS_DIR / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape and AI-evaluate South African eTenders for AI and Digital Marketing."
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip dispatching the Google Workspace email digest.",
    )
    parser.add_argument(
        "--no-toast",
        action="store_true",
        help="Skip Windows desktop toast notification.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of raw tenders fetched (useful for testing).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fast test run: limits to 50 tenders and disables email dispatch.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=Config.OLLAMA_MODEL,
        help=f"Ollama model to use for analysis (default: {Config.OLLAMA_MODEL}).",
    )
    return parser.parse_args()


def main():
    """Execute the pipeline with parsed CLI parameters."""
    setup_logging()
    args = parse_args()

    send_email = not (args.no_email or args.dry_run)
    show_toast = not (args.no_toast or args.dry_run)
    limit = 50 if args.dry_run else args.limit

    evaluator = OllamaEvaluator(model_name=args.model)
    pipeline = ETenderPipeline(evaluator=evaluator)

    stats = pipeline.run(
        send_email=send_email,
        show_toast=show_toast,
        max_tenders=limit,
    )

    print("\n" + "=" * 50)
    print(f"eTender Pipeline Finished in {stats.elapsed_seconds:.1f}s")
    print(f"Total Tenders Scanned: {stats.total_scanned}")
    print(f"Initial Candidates:   {stats.candidate_matches}")
    print(f"AI Qualified Bids:    {stats.ai_qualified_count}")
    print(f"Model Evaluator:      {stats.model_used}")
    print("=" * 50)


if __name__ == "__main__":
    main()
