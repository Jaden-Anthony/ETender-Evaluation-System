"""Data models for raw tenders, AI evaluations, and pipeline telemetry."""


from pydantic import BaseModel, Field


class TenderDocument(BaseModel):
    """Metadata for documents/specifications attached to a tender."""

    document_id: str | None = None
    file_name: str
    extension: str | None = None


class RawTender(BaseModel):
    """Raw tender record retrieved from the eTenders portal JSON endpoint."""

    id: int
    tender_no: str
    organ_of_state: str
    province: str | None = "National"
    category: str | None = "General"
    tender_type: str | None = None
    description: str = ""
    date_published: str | None = None
    closing_date: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    telephone: str | None = None
    documents: list[TenderDocument] = Field(default_factory=list)


class AIEvaluation(BaseModel):
    """Result of an LLM semantic qualification assessment."""

    relevance_score: float = Field(
        ..., description="Relevance score from 1.0 to 10.0 for AI/Digital Marketing"
    )
    is_qualified: bool = Field(
        ..., description="True if this is a genuine match, False if false positive"
    )
    domain_tags: list[str] = Field(
        default_factory=list,
        description="Assigned tags (e.g. AI, Machine Learning, Digital Marketing)",
    )
    executive_summary: str = Field(
        ..., description="2-3 sentence executive briefing of the opportunity"
    )
    recommended_action: str = Field(
        ..., description="Action recommendation (e.g. Apply, Review, Monitor, Ignore)"
    )


class QualifiedTender(BaseModel):
    """Enriched tender ready for team distribution."""

    tender_no: str
    organ_of_state: str
    province: str | None = "National"
    category: str | None = "General"
    closing_date: str | None = None
    date_published: str | None = None
    description: str
    contact_person: str | None = None
    contact_email: str | None = None
    telephone: str | None = None
    attached_documents: list[str] = Field(default_factory=list)
    keyword_matches: list[str] = Field(default_factory=list)
    ai_evaluation: AIEvaluation | None = None


class PipelineStats(BaseModel):
    """Execution telemetry for heartbeat and email reporting."""

    total_scanned: int = 0
    candidate_matches: int = 0
    ai_qualified_count: int = 0
    elapsed_seconds: float = 0.0
    model_used: str = "Ollama (qwen2.5:14b)"
    status_message: str = "Success"
