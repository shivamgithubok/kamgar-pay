from __future__ import annotations

from datetime import date
from decimal import Decimal
from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import Select, extract, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.database.models import Expense, Site, User, Worker
from src.schemas.expense import (
    ExpenseCreateRequest,
    ExpenseListResponse,
    ExpenseMetricsSummaryResponse,
    ExpenseResponse,
    ExpenseUpdateRequest,
    MonthlyExpenseSummaryItem,
    MonthlyExpenseSummaryResponse,
)
from src.services.sites import get_site_by_id


def decimal_or_zero(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def join_worker_name(worker: Optional[Worker]) -> Optional[str]:
    if worker is None:
        return None
    return " ".join(part for part in [worker.first_name, worker.last_name] if part) or None


def base_expense_query() -> Select[tuple[Expense]]:
    return select(Expense).options(
        selectinload(Expense.site),
        selectinload(Expense.worker),
        selectinload(Expense.submitted_by_user),
        selectinload(Expense.approved_by_user),
    )


def get_expense_by_id(
    db: Session,
    *,
    organization_id: str,
    expense_id: str,
    required: bool = True,
) -> Expense | None:
    expense = db.execute(
        base_expense_query().where(Expense.organization_id == organization_id, Expense.id == expense_id)
    ).scalar_one_or_none()
    if expense is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


def validate_worker_exists(db: Session, *, organization_id: str, worker_id: Optional[str]) -> None:
    if worker_id is None:
        return
    exists = db.execute(
        select(Worker.id).where(Worker.organization_id == organization_id, Worker.id == worker_id)
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")


def create_expense(
    db: Session,
    *,
    organization_id: str,
    submitted_by_user_id: str,
    payload: ExpenseCreateRequest,
) -> Expense:
    # Ensure site exists and belongs to organization
    get_site_by_id(db, organization_id=organization_id, site_id=payload.site_id, required=True)
    validate_worker_exists(db, organization_id=organization_id, worker_id=payload.worker_id)

    expense = Expense(
        organization_id=organization_id,
        site_id=payload.site_id,
        worker_id=payload.worker_id,
        submitted_by_user_id=submitted_by_user_id,
        category=payload.category.strip(),
        expense_date=payload.expense_date,
        amount=payload.amount,
        payment_mode=payload.payment_mode,
        vendor_name=payload.vendor_name.strip() if payload.vendor_name else None,
        description=payload.description,
        status="draft",
        receipt_required=payload.receipt_required,
    )

    try:
        db.add(expense)
        db.commit()
        # Dispatch notification to organization admins
        try:
            from src.services.notifications import notify_organization_admins
            notify_organization_admins(
                db,
                organization_id=organization_id,
                notification_type="expense_created",
                title="New Site Expense Created",
                message=f"New expense of INR {expense.amount} for '{expense.category}' was logged.",
                worker_id=payload.worker_id,
            )
        except Exception as notif_err:
            print(f"Notification dispatch warning: {notif_err}")

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create expense",
        ) from exc

    return get_expense_by_id(db, organization_id=organization_id, expense_id=expense.id, required=True)


def update_expense(
    db: Session,
    *,
    organization_id: str,
    expense_id: str,
    approved_by_user_id: Optional[str] = None,
    payload: ExpenseUpdateRequest,
) -> Expense:
    expense = get_expense_by_id(db, organization_id=organization_id, expense_id=expense_id, required=True)

    if payload.site_id is not None:
        get_site_by_id(db, organization_id=organization_id, site_id=payload.site_id, required=True)
        expense.site_id = payload.site_id

    if payload.worker_id is not None:
        validate_worker_exists(db, organization_id=organization_id, worker_id=payload.worker_id)
        expense.worker_id = payload.worker_id

    if payload.category is not None:
        expense.category = payload.category.strip()
    if payload.amount is not None:
        expense.amount = payload.amount
    if payload.expense_date is not None:
        expense.expense_date = payload.expense_date
    if payload.payment_mode is not None:
        expense.payment_mode = payload.payment_mode
    if payload.vendor_name is not None:
        expense.vendor_name = payload.vendor_name.strip() if payload.vendor_name else None
    if payload.description is not None:
        expense.description = payload.description
    if payload.receipt_required is not None:
        expense.receipt_required = payload.receipt_required

    if payload.status is not None:
        new_status = payload.status.strip().lower()
        expense.status = new_status
        if new_status in ("approved", "paid") and approved_by_user_id:
            expense.approved_by_user_id = approved_by_user_id

    try:
        db.add(expense)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update expense",
        ) from exc

    return get_expense_by_id(db, organization_id=organization_id, expense_id=expense_id, required=True)


def delete_expense(db: Session, *, organization_id: str, expense_id: str) -> None:
    expense = get_expense_by_id(db, organization_id=organization_id, expense_id=expense_id, required=True)
    db.delete(expense)
    db.commit()


def list_expenses(
    db: Session,
    *,
    organization_id: str,
    page: int = 1,
    page_size: int = 20,
    site_id: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
) -> ExpenseListResponse:
    query = base_expense_query().where(Expense.organization_id == organization_id)
    count_query = select(func.count(Expense.id)).where(Expense.organization_id == organization_id)

    if site_id:
        query = query.where(Expense.site_id == site_id)
        count_query = count_query.where(Expense.site_id == site_id)

    if category:
        query = query.where(Expense.category == category.strip())
        count_query = count_query.where(Expense.category == category.strip())

    if status_filter:
        query = query.where(Expense.status == status_filter.strip().lower())
        count_query = count_query.where(Expense.status == status_filter.strip().lower())

    if start_date:
        query = query.where(Expense.expense_date >= start_date)
        count_query = count_query.where(Expense.expense_date >= start_date)

    if end_date:
        query = query.where(Expense.expense_date <= end_date)
        count_query = count_query.where(Expense.expense_date <= end_date)

    if search:
        like_term = f"%{search.strip()}%"
        search_filter = or_(
            Expense.category.ilike(like_term),
            Expense.vendor_name.ilike(like_term),
            Expense.description.ilike(like_term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = db.execute(count_query).scalar_one()
    offset = (page - 1) * page_size
    expenses = list(db.execute(query.order_by(Expense.expense_date.desc(), Expense.created_at.desc()).offset(offset).limit(page_size)).scalars().all())

    return ExpenseListResponse(
        items=[to_expense_response(exp) for exp in expenses],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


def get_expense_metrics_summary(db: Session, *, organization_id: str) -> ExpenseMetricsSummaryResponse:
    today = date.today()

    # Total expenses amount & count
    total_row = db.execute(
        select(func.count(Expense.id), func.sum(Expense.amount)).where(Expense.organization_id == organization_id)
    ).one()
    total_count = total_row[0] or 0
    total_expenses = decimal_or_zero(total_row[1])

    # This month expenses
    this_month_row = db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.organization_id == organization_id,
            extract("year", Expense.expense_date) == today.year,
            extract("month", Expense.expense_date) == today.month,
        )
    ).scalar_one_or_none()
    this_month_expenses = decimal_or_zero(this_month_row)

    # Highest expense site
    highest_site_row = db.execute(
        select(Site.id, Site.name, func.sum(Expense.amount))
        .join(Site, Site.id == Expense.site_id)
        .where(Expense.organization_id == organization_id)
        .group_by(Site.id, Site.name)
        .order_by(func.sum(Expense.amount).desc())
        .limit(1)
    ).first()

    highest_site_id = highest_site_row[0] if highest_site_row else None
    highest_site_name = highest_site_row[1] if highest_site_row else None
    highest_site_amount = decimal_or_zero(highest_site_row[2]) if highest_site_row else Decimal("0.00")

    # Pending approvals count
    pending_count = db.execute(
        select(func.count(Expense.id)).where(
            Expense.organization_id == organization_id,
            Expense.status.in_(["draft", "review", "pending"]),
        )
    ).scalar_one()

    return ExpenseMetricsSummaryResponse(
        total_expenses=total_expenses,
        this_month_expenses=this_month_expenses,
        highest_expense_site_id=highest_site_id,
        highest_expense_site_name=highest_site_name,
        highest_expense_site_amount=highest_site_amount,
        pending_approvals_count=pending_count,
        total_count=total_count,
    )


def get_monthly_expense_summary(
    db: Session,
    *,
    organization_id: str,
    year: Optional[int] = None,
) -> MonthlyExpenseSummaryResponse:
    query = (
        select(
            extract("year", Expense.expense_date).label("year_num"),
            extract("month", Expense.expense_date).label("month_num"),
            func.count(Expense.id).label("expense_count"),
            func.sum(Expense.amount).label("total_amount"),
        )
        .where(Expense.organization_id == organization_id)
        .group_by(extract("year", Expense.expense_date), extract("month", Expense.expense_date))
    )

    if year is not None:
        query = query.where(extract("year", Expense.expense_date) == year)

    rows = db.execute(query.order_by(extract("year", Expense.expense_date).desc(), extract("month", Expense.expense_date).desc())).all()

    items = [
        MonthlyExpenseSummaryItem(
            year=int(row.year_num),
            month=int(row.month_num),
            expense_count=row.expense_count,
            total_amount=decimal_or_zero(row.total_amount),
        )
        for row in rows
    ]

    total_exp = sum((item.total_amount for item in items), Decimal("0.00"))
    total_cnt = sum(item.expense_count for item in items)

    return MonthlyExpenseSummaryResponse(
        year=year,
        total_expenses=total_exp,
        total_count=total_cnt,
        items=items,
    )


def to_expense_response(expense: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense.id,
        organization_id=expense.organization_id,
        site_id=expense.site_id,
        site_name=expense.site.name if expense.site else "Unknown Site",
        worker_id=expense.worker_id,
        worker_name=join_worker_name(expense.worker),
        submitted_by_user_id=expense.submitted_by_user_id,
        submitted_by_name=expense.submitted_by_user.full_name if expense.submitted_by_user else "Unknown User",
        approved_by_user_id=expense.approved_by_user_id,
        approved_by_name=expense.approved_by_user.full_name if expense.approved_by_user else None,
        category=expense.category,
        expense_date=expense.expense_date,
        amount=expense.amount,
        payment_mode=expense.payment_mode,
        vendor_name=expense.vendor_name,
        description=expense.description,
        status=expense.status,
        receipt_required=expense.receipt_required,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )
