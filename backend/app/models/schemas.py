from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    content: str = Field(..., description="Untrusted content to scan for prompt injection")
    source: str | None = Field(default=None, description="Origin of the content, e.g. 'web', 'document', 'email'")


class AnalyzeResponse(BaseModel):
    is_injection: bool
    confidence: float
    label: str
    spotlighted_content: str
    latency_ms: float
    device: str | None = None
    details: str | None = None
    detection_source: str | None = Field(
        default=None,
        description="Which layer flagged the content: 'ml_model', 'heuristic_pattern', 'both', or 'none'",
    )
    matched_patterns: list[str] = Field(
        default_factory=list,
        description="Labels of jailbreak heuristic patterns that matched (empty if none)",
    )
