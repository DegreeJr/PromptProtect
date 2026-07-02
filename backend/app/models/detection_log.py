"""ORM model for a single /api/analyze detection record (audit trail)."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DetectionLog(Base):
    __tablename__ = "detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    # Privacy-conscious: keep a truncated preview for the audit table plus a
    # sha256 hash of the full input (so the raw text is not stored in full).
    input_preview: Mapped[str] = mapped_column(String(200))
    input_hash: Mapped[str] = mapped_column(String(64), index=True)

    is_injection: Mapped[bool] = mapped_column(Boolean, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    detection_source: Mapped[str] = mapped_column(String(32), index=True)
    latency_ms: Mapped[float] = mapped_column(Float)
