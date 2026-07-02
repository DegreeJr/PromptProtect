"""SQLite persistence for detection audit logs (SQLAlchemy 2.0).

Lightweight setup suitable for a hackathon demo: a single SQLite file
(`singkap.db` in the backend working dir) holding one row per /api/analyze call.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# check_same_thread=False so FastAPI's threadpool can share the connection.
_engine = create_engine(
    "sqlite:///./singkap.db",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create tables if they don't exist. Called at app startup."""
    # Import models so they're registered on Base.metadata before create_all.
    from app.models import detection_log  # noqa: F401

    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
