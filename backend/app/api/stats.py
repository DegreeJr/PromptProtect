"""Analytics + audit-trail endpoints backed by the detection_logs table."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.detection_log import DetectionLog
from app.models.schemas import LogEntry, LogsResponse, SourceBreakdown, StatsResponse

router = APIRouter()

# Sources that represent a positive (blocked) detection.
_BLOCK_SOURCES = ("ml_model", "heuristic_pattern", "both")


@router.get("/stats", response_model=StatsResponse)
async def stats(db: Session = Depends(get_db)) -> StatsResponse:
    total_requests = db.scalar(select(func.count(DetectionLog.id))) or 0
    total_blocked = (
        db.scalar(
            select(func.count(DetectionLog.id)).where(DetectionLog.is_injection.is_(True))
        )
        or 0
    )
    avg_confidence = db.scalar(select(func.avg(DetectionLog.confidence)))
    avg_latency = db.scalar(select(func.avg(DetectionLog.latency_ms)))

    # Count blocked requests grouped by which layer caught them.
    rows = db.execute(
        select(DetectionLog.detection_source, func.count(DetectionLog.id))
        .where(DetectionLog.detection_source.in_(_BLOCK_SOURCES))
        .group_by(DetectionLog.detection_source)
    ).all()
    counts = {source: count for source, count in rows}

    breakdown: dict[str, SourceBreakdown] = {}
    for source in _BLOCK_SOURCES:
        count = counts.get(source, 0)
        pct = (count / total_blocked * 100) if total_blocked else 0.0
        breakdown[source] = SourceBreakdown(count=count, percentage=round(pct, 2))

    return StatsResponse(
        total_requests=total_requests,
        total_blocked=total_blocked,
        total_allowed=total_requests - total_blocked,
        detection_rate=round(total_blocked / total_requests, 4) if total_requests else 0.0,
        avg_confidence=round(avg_confidence, 4) if avg_confidence is not None else 0.0,
        avg_latency_ms=round(avg_latency, 3) if avg_latency is not None else 0.0,
        detection_source_breakdown=breakdown,
    )


@router.get("/logs", response_model=LogsResponse)
async def logs(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> LogsResponse:
    total = db.scalar(select(func.count(DetectionLog.id))) or 0

    rows = db.scalars(
        select(DetectionLog)
        .order_by(DetectionLog.timestamp.desc(), DetectionLog.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    items = [
        LogEntry(
            id=r.id,
            timestamp=r.timestamp,
            input_preview=r.input_preview,
            input_hash=r.input_hash,
            is_injection=r.is_injection,
            confidence=r.confidence,
            detection_source=r.detection_source,
            latency_ms=r.latency_ms,
        )
        for r in rows
    ]

    return LogsResponse(total=total, limit=limit, offset=offset, items=items)
