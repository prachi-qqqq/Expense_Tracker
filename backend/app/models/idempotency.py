"""Idempotency key model for safe retries."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IdempotencyKey(Base):
    """Stores idempotency keys to prevent duplicate expense creation."""

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(
        String, primary_key=True, nullable=False
    )
    request_hash: Mapped[str] = mapped_column(
        String, nullable=False
    )
    response_body: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )
    status_code: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
