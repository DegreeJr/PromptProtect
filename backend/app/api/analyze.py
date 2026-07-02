import hashlib
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.detection_log import DetectionLog
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.classifier import classify, get_device
from app.services.jailbreak_heuristic import detect as detect_jailbreak
from app.services.spotlight import spotlight

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalyzeResponse:
    start = time.perf_counter()

    # Layer 1 — spotlighting preprocessing (provenance marking, display only).
    spotlighted = spotlight(request.content)

    # Layer 2 — RoBERTa injection classifier (BIPIA fine-tuned, indirect injection).
    ml_is_injection, ml_confidence, ml_label = classify(request.content)

    # Layer 3 — direct-jailbreak heuristic (covers gap in BIPIA training data).
    heuristic_is_injection, matched_patterns = detect_jailbreak(request.content)

    # Combine with OR logic: either layer flagging => final verdict is injection.
    is_injection = ml_is_injection or heuristic_is_injection

    if ml_is_injection and heuristic_is_injection:
        detection_source = "both"
    elif ml_is_injection:
        detection_source = "ml_model"
    elif heuristic_is_injection:
        detection_source = "heuristic_pattern"
    else:
        detection_source = "none"

    # Confidence: when the heuristic catches something the ML missed, surface high
    # certainty (regex match is deterministic); otherwise report the model's
    # injection-class probability.
    if heuristic_is_injection and not ml_is_injection:
        confidence = 1.0
    else:
        confidence = ml_confidence

    label = "injection" if is_injection else "benign"

    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    # Persist to audit log (privacy-conscious: truncated preview + full-text hash).
    log = DetectionLog(
        input_preview=request.content[:200],
        input_hash=hashlib.sha256(request.content.encode("utf-8")).hexdigest(),
        is_injection=is_injection,
        confidence=confidence,
        detection_source=detection_source,
        latency_ms=latency_ms,
    )
    db.add(log)
    db.commit()

    return AnalyzeResponse(
        is_injection=is_injection,
        confidence=confidence,
        label=label,
        spotlighted_content=spotlighted,
        latency_ms=latency_ms,
        device=get_device(),
        details="RoBERTa (DegreeJr/singkap-ai-roberta, BIPIA) + heuristik jailbreak langsung.",
        detection_source=detection_source,
        matched_patterns=matched_patterns,
    )
