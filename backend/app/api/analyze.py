import time

from fastapi import APIRouter

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.classifier import classify, get_device
from app.services.spotlight import spotlight

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    start = time.perf_counter()

    # Layer 1 — spotlighting preprocessing.
    spotlighted = spotlight(request.content)

    # Layer 2 — RoBERTa injection classifier (BIPIA fine-tuned, from HF Hub).
    is_injection, confidence, label = classify(request.content)

    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    return AnalyzeResponse(
        is_injection=is_injection,
        confidence=confidence,
        label=label,
        spotlighted_content=spotlighted,
        latency_ms=latency_ms,
        device=get_device(),
        details="RoBERTa (DegreeJr/singkap-ai-roberta) fine-tuned pada BIPIA.",
    )
