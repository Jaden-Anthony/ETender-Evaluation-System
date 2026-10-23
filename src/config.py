"""Configuration settings for the eTender scraper pipeline."""

import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv

# Load local environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration and keyword taxonomies."""

    # Project directories
    OUTPUT_DIR: Path = BASE_DIR / "output"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # API Endpoints
    ETENDER_API_URL: str = (
        "https://www.etenders.gov.za/Home/PaginatedTenderOpportunities"
    )

    # Google Workspace Email Settings
    GMAIL_SENDER: str = os.getenv("GMAIL_SENDER", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    TEAM_EMAILS: ClassVar[list[str]] = [
        email.strip()
        for email in os.getenv("TEAM_EMAILS", "").split(",")
        if email.strip()
    ]

    # Local Ollama AI Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

    # Evaluation Thresholds
    MIN_RELEVANCE_SCORE: float = float(os.getenv("MIN_RELEVANCE_SCORE", "6.0"))
    MAX_TENDERS_TO_ANALYZE: int = int(os.getenv("MAX_TENDERS_TO_ANALYZE", "60"))
    SEND_ZERO_MATCH_HEARTBEAT: bool = (
        os.getenv("SEND_ZERO_MATCH_HEARTBEAT", "true").lower() == "true"
    )
    ENABLE_WINDOWS_TOAST: bool = (
        os.getenv("ENABLE_WINDOWS_TOAST", "true").lower() == "true"
    )

    # Targeted Keyword Taxonomies
    AI_KEYWORDS: ClassVar[list[str]] = [
        "artificial intelligence",
        "machine learning",
        "predictive analytics",
        "predictive model",
        "predictive modelling",
        "chatbot",
        "chatbots",
        "automation",
        "automated system",
        "nlp",
        "natural language processing",
        "data science",
        "data analytics",
        "deep learning",
        "neural network",
        "generative ai",
        "computer vision",
        "business intelligence",
    ]

    DIGITAL_MARKETING_KEYWORDS: ClassVar[list[str]] = [
        "digital marketing",
        "digital services",
        "social media",
        "seo",
        "search engine optimization",
        "web development",
        "website development",
        "website design",
        "content creation",
        "digital campaign",
        "campaign management",
        "graphic design",
        "portal",
        "portals",
        "web portal",
        "online platform",
        "branding",
        "marketing",
        "communications",
        "media production",
        "videography",
        "audiovisual",
        "digital communication",
        "public relations",
        "advertising agency",
        "creative agency",
    ]


# Ensure directories exist
Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
