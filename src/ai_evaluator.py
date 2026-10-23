"""AI semantic evaluation module powered by local Ollama models."""

import json
import logging
import re

import requests

from src.config import Config
from src.models import AIEvaluation, RawTender

logger = logging.getLogger(__name__)


class OllamaEvaluator:
    """Evaluates tender candidates using a local Ollama LLM to eliminate false positives."""

    SYSTEM_PROMPT = """You are an expert commercial bid strategist and procurement analyst.
Your task is to evaluate a South African public sector tender and determine whether it represents a GENUINE business opportunity in:
1. AI Landscape: Machine learning, chatbots, predictive analytics, software automation, NLP, data science.
2. Digital Marketing & Services: Web development, online self-service portals, SEO, social media, digital PR, creative/branding campaigns, media production.

CRITICAL INSTRUCTION - ELIMINATE FALSE POSITIVES:
- Many tenders mention "automated" or "marketing" but are actually physical hardware, heavy industry, or agricultural commodities (e.g., automated coal testing machines, fuel pumps, physical vehicle parts, plumbing, construction).
- If the tender is for physical hardware, civil engineering, fuel pumps, or manual physical goods, YOU MUST SET:
  "is_qualified": false, and "relevance_score": between 1.0 and 4.0.
- Only set "is_qualified": true if this is genuinely a software, digital, creative, communications, or AI project.

You MUST respond ONLY with a valid JSON object in this exact schema:
{
  "relevance_score": 8.5,
  "is_qualified": true,
  "domain_tags": ["Digital Marketing", "Social Media"],
  "executive_summary": "South African Tourism is establishing a panel of global integrated marketing agencies to manage digital, PR, creative, and media campaigns over 3 years.",
  "recommended_action": "Apply - High Priority"
}
"""

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int = 60,
    ):
        """Initialize the Ollama evaluator."""
        self.base_url = (base_url or Config.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or Config.OLLAMA_MODEL
        self.timeout = timeout

    def evaluate_tender(
        self, tender: RawTender, matched_keywords: list[str]
    ) -> AIEvaluation:
        """Submit a candidate tender to Ollama for qualification and scoring.

        Args:
            tender: Candidate RawTender model.
            matched_keywords: Keywords that triggered candidate status.

        Returns:
            AIEvaluation model with score, qualification flag, and briefing.
        """
        user_prompt = (
            f"Tender Reference: {tender.tender_no}\n"
            f"Organ of State: {tender.organ_of_state} ({tender.province})\n"
            f"Category: {tender.category}\n"
            f"Closing Date: {tender.closing_date}\n"
            f"Triggered Keywords: {', '.join(matched_keywords)}\n"
            f"Description:\n{tender.description}\n"
        )

        payload = {
            "model": self.model_name,
            "system": self.SYSTEM_PROMPT,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for deterministic analysis
            },
        }

        try:
            url = f"{self.base_url}/api/generate"
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            raw_content = response.json().get("response", "").strip()

            return self._parse_llm_json(raw_content, tender)

        except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning(
                f"Ollama evaluation failed for {tender.tender_no}: {exc}. "
                "Using fallback heuristic evaluation."
            )
            return self._fallback_heuristic_evaluation(tender, matched_keywords)

    def _parse_llm_json(self, raw_content: str, tender: RawTender) -> AIEvaluation:
        """Parse and validate JSON returned by Ollama."""
        try:
            # Extract JSON substring if surrounded by markdown code blocks
            clean_str = raw_content
            json_match = re.search(r"\{[\s\S]*\}", raw_content)
            if json_match:
                clean_str = json_match.group(0)

            data = json.loads(clean_str)

            score = float(data.get("relevance_score", 5.0))
            is_qualified = bool(
                data.get("is_qualified", score >= Config.MIN_RELEVANCE_SCORE)
            )

            return AIEvaluation(
                relevance_score=max(1.0, min(10.0, score)),
                is_qualified=is_qualified,
                domain_tags=data.get("domain_tags", ["Digital/AI"]),
                executive_summary=data.get(
                    "executive_summary", tender.description[:250]
                ),
                recommended_action=data.get("recommended_action", "Review Opportunity"),
            )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            logger.warning(f"Failed to parse LLM JSON response: {exc}")
            return self._fallback_heuristic_evaluation(tender, [])

    def _fallback_heuristic_evaluation(
        self, tender: RawTender, matched_keywords: list[str]
    ) -> AIEvaluation:
        """Safe fallback evaluator when Ollama is offline or returns invalid JSON."""
        # Check for obvious false positives in fallback mode
        lower_desc = tender.description.lower()
        is_hardware = any(
            bad_word in lower_desc
            for bad_word in [
                "calorimeter",
                "coal",
                "fuel pump",
                "diesel",
                "pipe",
                "plumbing",
            ]
        )

        score = 3.0 if is_hardware else 7.0
        is_qualified = not is_hardware

        return AIEvaluation(
            relevance_score=score,
            is_qualified=is_qualified,
            domain_tags=matched_keywords or ["Keyword Match"],
            executive_summary=(
                f"Tender {tender.tender_no} by {tender.organ_of_state}: "
                f"{tender.description[:200]}..."
            ),
            recommended_action="Review specification documents",
        )
