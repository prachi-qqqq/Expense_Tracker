"""Expense model."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Expense(Base):
    """Financial expense record, scoped to a user."""

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expense_amount_positive"),
        Index("ix_expenses_category", "category"),
        Index("ix_expenses_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    date: Mapped[date] = mapped_column(
        Date, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship(back_populates="expenses")  # noqa: F821
