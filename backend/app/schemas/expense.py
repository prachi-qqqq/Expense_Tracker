"""Pydantic schemas for expense validation and serialization."""

from datetime import date as DateType, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    """Schema for creating a new expense."""

    amount: Decimal = Field(
        ..., gt=0, max_digits=10, decimal_places=2,
        description="Expense amount (must be positive)",
    )
    category: str = Field(
        ..., min_length=1, max_length=50,
        description="Expense category",
    )
    description: str | None = Field(
        None, max_length=255,
        description="Optional description",
    )
    date: DateType = Field(..., description="Expense date (ISO format)")

    @field_validator("amount", mode="before")
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ExpenseResponse(BaseModel):
    """Schema for expense data in responses."""

    id: UUID
    amount: Decimal
    category: str
    description: str | None
    date: DateType
    created_at: datetime
    user_id: UUID

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    """Schema for a list of expenses."""

    expenses: list[ExpenseResponse]
    total: Decimal
    count: int
