"""Expense routes — create and list expenses."""

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Response, status
from sqlalchemy.orm import Session
from fastapi import Depends

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.expense import ExpenseCreate, ExpenseListResponse
from app.services.expense_service import create_expense, list_expenses

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense (idempotent)",
)
def create(
    data: ExpenseCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Create an expense with idempotency support.

    Requires an `Idempotency-Key` header (UUID) for safe retries.
    Same key + same body = same response.
    Same key + different body = 409 Conflict.
    """
    if not idempotency_key or len(idempotency_key) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required (max 100 chars)",
        )

    try:
        response_body, status_code = create_expense(
            db=db,
            data=data,
            idempotency_key=idempotency_key,
            user_id=current_user.id,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

    import json
    return Response(
        content=json.dumps(response_body, default=str),
        status_code=status_code,
        media_type="application/json",
    )


@router.get(
    "",
    response_model=ExpenseListResponse,
    summary="List expenses with optional filtering and sorting",
)
def list_all(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    category: str | None = None,
    sort: str = "date_desc",
) -> ExpenseListResponse:
    """List expenses for the authenticated user.

    - `category`: Filter by category name (optional)
    - `sort`: `date_desc` (default, newest first) or `date_asc`
    """
    return list_expenses(
        db=db,
        user_id=current_user.id,
        category=category,
        sort=sort,
    )
