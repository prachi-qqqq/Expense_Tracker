"""Expense service — business logic for expense creation and listing."""

import uuid
from decimal import Decimal

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.expense import Expense
from app.models.idempotency import IdempotencyKey
from app.schemas.expense import ExpenseCreate, ExpenseListResponse, ExpenseResponse
from app.utils.idempotency import hash_request


def create_expense(
    db: Session,
    data: ExpenseCreate,
    idempotency_key: str,
    user_id: uuid.UUID,
) -> tuple[dict, int]:
    """Create an expense with idempotency guarantees.

    Returns (response_body, status_code) tuple.

    Idempotency rules:
    1. Hash the request body (stable JSON serialization)
    2. If key exists:
       - Same hash → return stored response (HTTP 200)
       - Different hash → return 409 Conflict
    3. If key not exists:
       - Process request, store response + hash
       - Return response (HTTP 201)
    """
    request_data = data.model_dump(mode="json")
    current_hash = hash_request(request_data)

    # Check for existing idempotency key (within a transaction)
    existing_key = db.execute(
        select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
    ).scalar_one_or_none()

    if existing_key:
        if existing_key.request_hash == current_hash:
            logger.info(
                "Idempotent replay for key=%s", idempotency_key
            )
            return existing_key.response_body, existing_key.status_code
        else:
            logger.warning(
                "Idempotency conflict: key=%s has different payload",
                idempotency_key,
            )
            return {
                "detail": "Idempotency key already used with a different request body"
            }, 409

    # Create the expense
    expense = Expense(
        amount=data.amount,
        category=data.category.strip(),
        description=data.description.strip() if data.description else None,
        date=data.date,
        user_id=user_id,
    )
    db.add(expense)
    db.flush()  # Get the ID without committing

    # Build response
    expense_response = ExpenseResponse.model_validate(expense)
    response_body = expense_response.model_dump(mode="json")
    status_code = 201

    # Store idempotency record
    idem_record = IdempotencyKey(
        key=idempotency_key,
        request_hash=current_hash,
        response_body=response_body,
        status_code=status_code,
    )
    db.add(idem_record)

    # Commit both expense and idempotency record atomically
    db.commit()
    db.refresh(expense)

    logger.info("Expense created: id=%s, amount=%s", expense.id, expense.amount)
    return response_body, status_code


def list_expenses(
    db: Session,
    user_id: uuid.UUID,
    category: str | None = None,
    sort: str = "date_desc",
) -> ExpenseListResponse:
    """List expenses for a user with optional filtering and sorting."""
    query = select(Expense).where(Expense.user_id == user_id)

    # Filter by category
    if category:
        query = query.where(Expense.category == category)

    # Sorting
    if sort == "date_asc":
        query = query.order_by(Expense.date.asc(), Expense.created_at.asc())
    else:
        # Default: newest first
        query = query.order_by(Expense.date.desc(), Expense.created_at.desc())

    expenses = db.execute(query).scalars().all()

    # Compute total from visible list
    total = sum(
        (expense.amount for expense in expenses),
        Decimal("0.00"),
    )

    expense_responses = [
        ExpenseResponse.model_validate(expense) for expense in expenses
    ]

    return ExpenseListResponse(
        expenses=expense_responses,
        total=total,
        count=len(expense_responses),
    )
