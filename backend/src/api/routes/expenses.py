from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.expense import (
    ExpenseCreateRequest,
    ExpenseListResponse,
    ExpenseMetricsSummaryResponse,
    ExpenseResponse,
    ExpenseUpdateRequest,
    MonthlyExpenseSummaryResponse,
)
from src.services.expenses import (
    create_expense,
    delete_expense,
    get_expense_by_id,
    get_expense_metrics_summary,
    get_monthly_expense_summary,
    list_expenses,
    to_expense_response,
    update_expense,
)

router = APIRouter()


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_expense_route(
    payload: ExpenseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> ExpenseResponse:
    expense = create_expense(
        db,
        organization_id=current_user.organization_id,
        submitted_by_user_id=current_user.id,
        payload=payload,
    )
    return to_expense_response(expense)


@router.get("", response_model=ExpenseListResponse)
@router.get("/", response_model=ExpenseListResponse, include_in_schema=False)
def list_expenses_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    site_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None, max_length=50),
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> ExpenseListResponse:
    return list_expenses(
        db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        site_id=site_id,
        category=category,
        status_filter=status_filter,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


@router.get("/summary", response_model=ExpenseMetricsSummaryResponse)
def get_expense_metrics_summary_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> ExpenseMetricsSummaryResponse:
    return get_expense_metrics_summary(db, organization_id=current_user.organization_id)


@router.get("/monthly-summary", response_model=MonthlyExpenseSummaryResponse)
def get_monthly_expense_summary_route(
    year: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> MonthlyExpenseSummaryResponse:
    return get_monthly_expense_summary(db, organization_id=current_user.organization_id, year=year)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense_route(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> ExpenseResponse:
    expense = get_expense_by_id(db, organization_id=current_user.organization_id, expense_id=expense_id, required=True)
    return to_expense_response(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense_route(
    expense_id: str,
    payload: ExpenseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> ExpenseResponse:
    expense = update_expense(
        db,
        organization_id=current_user.organization_id,
        expense_id=expense_id,
        approved_by_user_id=current_user.id,
        payload=payload,
    )
    return to_expense_response(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense_route(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin")),
) -> Response:
    delete_expense(db, organization_id=current_user.organization_id, expense_id=expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
