from datetime import datetime

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


class SourceBreakdown(BaseModel):
    count: int
    percentage: float  # share of total_blocked


class StatsResponse(BaseModel):
    total_requests: int
    total_blocked: int
    total_allowed: int
    detection_rate: float  # total_blocked / total_requests
    avg_confidence: float
    avg_latency_ms: float
    # keys: ml_model, heuristic_pattern, both (share of blocked requests)
    detection_source_breakdown: dict[str, SourceBreakdown]


class LogEntry(BaseModel):
    id: int
    timestamp: datetime
    input_preview: str
    input_hash: str
    is_injection: bool
    confidence: float
    detection_source: str
    latency_ms: float


class LogsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[LogEntry]
