from __future__ import annotations

from datetime import date
from decimal import Decimal
from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.database.models import AttendanceRecord, Expense, Payroll, Site, User, Worker, WorkerSiteAssignment
from src.schemas.site import (
    SiteAssignmentResponse,
    SiteCreateRequest,
    SiteExpenseBreakdownItem,
    SiteExpenseSummaryResponse,
    SiteListResponse,
    SiteResponse,
    SiteStatsResponse,
    SiteUpdateRequest,
    SiteWorkerAssignmentRequest,
    SiteWorkerResponse,
)


def decimal_or_zero(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def join_worker_name(worker: Worker) -> str:
    return " ".join(part for part in [worker.first_name, worker.last_name] if part)


def base_site_query() -> Select[tuple[Site]]:
    return select(Site).options(selectinload(Site.site_manager))


def get_site_by_id(
    db: Session,
    *,
    organization_id: str,
    site_id: str,
    required: bool = False,
) -> Site | None:
    site = db.execute(
        base_site_query().where(Site.organization_id == organization_id, Site.id == site_id)
    ).scalar_one_or_none()
    if site is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


def get_worker_for_assignment(db: Session, *, organization_id: str, worker_id: str) -> Worker:
    worker = db.execute(
        select(Worker)
        .options(selectinload(Worker.assignments))
        .where(Worker.organization_id == organization_id, Worker.id == worker_id)
    ).scalar_one_or_none()
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    return worker


def validate_site_manager(db: Session, *, organization_id: str, site_manager_user_id: Optional[str]) -> None:
    if site_manager_user_id is None:
        return
    exists = db.execute(
        select(User.id).where(User.organization_id == organization_id, User.id == site_manager_user_id)
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site manager not found")


def field_supplied(payload: SiteCreateRequest | SiteUpdateRequest, field_name: str) -> bool:
    if isinstance(payload, SiteCreateRequest):
        return True
    return field_name in payload.model_fields_set


def apply_site_fields(site: Site, payload: SiteCreateRequest | SiteUpdateRequest) -> None:
    for field_name in (
        "site_code",
        "name",
        "client_name",
        "project_name",
        "city",
        "state",
        "status",
        "start_date",
        "end_date",
        "site_manager_user_id",
    ):
        if field_supplied(payload, field_name):
            setattr(site, field_name, getattr(payload, field_name))

    if site.end_date is not None and site.end_date < site.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date cannot be before start date")


def active_worker_counts(db: Session, *, organization_id: str, site_ids: list[str]) -> dict[str, int]:
    if not site_ids:
        return {}
    rows = db.execute(
        select(Worker.assigned_site_id, func.count(Worker.id))
        .where(
            Worker.organization_id == organization_id,
            Worker.assigned_site_id.in_(site_ids),
            Worker.status == "active",
        )
        .group_by(Worker.assigned_site_id)
    ).all()
    return {str(site_id): count for site_id, count in rows if site_id is not None}


def expense_totals(db: Session, *, organization_id: str, site_ids: list[str]) -> dict[str, Decimal]:
    if not site_ids:
        return {}
    rows = db.execute(
        select(Expense.site_id, func.sum(Expense.amount))
        .where(Expense.organization_id == organization_id, Expense.site_id.in_(site_ids))
        .group_by(Expense.site_id)
    ).all()
    return {site_id: decimal_or_zero(total) for site_id, total in rows}


def create_site(db: Session, *, organization_id: str, payload: SiteCreateRequest) -> Site:
    validate_site_manager(db, organization_id=organization_id, site_manager_user_id=payload.site_manager_user_id)
    site = Site(organization_id=organization_id)
    apply_site_fields(site, payload)

    try:
        db.add(site)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Site could not be created because a unique field already exists",
        ) from exc

    return get_site_by_id(db, organization_id=organization_id, site_id=site.id, required=True)


def update_site(db: Session, *, organization_id: str, site_id: str, payload: SiteUpdateRequest) -> Site:
    site = get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)
    validate_site_manager(db, organization_id=organization_id, site_manager_user_id=payload.site_manager_user_id)
    apply_site_fields(site, payload)

    try:
        db.add(site)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Site could not be updated because a unique field already exists",
        ) from exc

    return get_site_by_id(db, organization_id=organization_id, site_id=site.id, required=True)


def delete_site(db: Session, *, organization_id: str, site_id: str) -> None:
    site = get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)
    site.status = "inactive"
    site.end_date = site.end_date or date.today()
    db.add(site)
    db.commit()


def list_sites(
    db: Session,
    *,
    organization_id: str,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    site_manager_user_id: Optional[str] = None,
) -> SiteListResponse:
    query = base_site_query().where(Site.organization_id == organization_id)
    count_query = select(func.count(Site.id)).where(Site.organization_id == organization_id)

    if search:
        like_term = f"%{search.strip()}%"
        search_filter = or_(
            Site.site_code.ilike(like_term),
            Site.name.ilike(like_term),
            Site.client_name.ilike(like_term),
            Site.project_name.ilike(like_term),
            Site.city.ilike(like_term),
            Site.state.ilike(like_term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if status_filter:
        normalized_status = status_filter.strip().lower()
        query = query.where(Site.status == normalized_status)
        count_query = count_query.where(Site.status == normalized_status)

    if city:
        normalized_city = city.strip()
        query = query.where(Site.city == normalized_city)
        count_query = count_query.where(Site.city == normalized_city)

    if state:
        normalized_state = state.strip()
        query = query.where(Site.state == normalized_state)
        count_query = count_query.where(Site.state == normalized_state)

    if site_manager_user_id:
        query = query.where(Site.site_manager_user_id == site_manager_user_id)
        count_query = count_query.where(Site.site_manager_user_id == site_manager_user_id)

    total = db.execute(count_query).scalar_one()
    offset = (page - 1) * page_size
    sites = list(db.execute(query.order_by(Site.created_at.desc()).offset(offset).limit(page_size)).scalars().all())
    site_ids = [site.id for site in sites]
    worker_counts = active_worker_counts(db, organization_id=organization_id, site_ids=site_ids)
    totals = expense_totals(db, organization_id=organization_id, site_ids=site_ids)

    return SiteListResponse(
        items=[to_site_response(site, worker_counts=worker_counts, expense_totals_by_site=totals) for site in sites],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


def sync_worker_site_assignment(
    db: Session,
    *,
    worker: Worker,
    organization_id: str,
    site_id: Optional[str],
    assigned_from: date,
    is_primary: bool = True,
) -> WorkerSiteAssignment | None:
    active_assignments = [
        assignment
        for assignment in worker.assignments
        if assignment.is_primary == is_primary and assignment.status == "active"
    ]

    for assignment in active_assignments:
        if site_id and assignment.site_id == site_id:
            worker.assigned_site_id = site_id if is_primary else worker.assigned_site_id
            return assignment
        assignment.status = "inactive"
        assignment.assigned_to = assigned_from if assigned_from >= assignment.assigned_from else assignment.assigned_from

    if is_primary:
        worker.assigned_site_id = site_id
    if site_id is None:
        return None

    assignment = WorkerSiteAssignment(
        organization_id=organization_id,
        worker_id=worker.id,
        site_id=site_id,
        is_primary=is_primary,
        status="active",
        assigned_from=assigned_from,
    )
    db.add(assignment)
    return assignment


def assign_worker_to_site(
    db: Session,
    *,
    organization_id: str,
    site_id: str,
    payload: SiteWorkerAssignmentRequest,
) -> WorkerSiteAssignment:
    get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)
    worker = get_worker_for_assignment(db, organization_id=organization_id, worker_id=payload.worker_id)
    assignment = sync_worker_site_assignment(
        db,
        worker=worker,
        organization_id=organization_id,
        site_id=site_id,
        assigned_from=payload.assigned_from or date.today(),
        is_primary=payload.is_primary,
    )

    try:
        db.add(worker)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Worker assignment already exists") from exc

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignment could not be created")
    return db.execute(
        select(WorkerSiteAssignment).where(WorkerSiteAssignment.id == assignment.id)
    ).scalar_one()


def unassign_worker_from_site(
    db: Session,
    *,
    organization_id: str,
    site_id: str,
    worker_id: str,
) -> None:
    get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)
    worker = get_worker_for_assignment(db, organization_id=organization_id, worker_id=worker_id)
    assignment = db.execute(
        select(WorkerSiteAssignment).where(
            WorkerSiteAssignment.organization_id == organization_id,
            WorkerSiteAssignment.site_id == site_id,
            WorkerSiteAssignment.worker_id == worker_id,
            WorkerSiteAssignment.status == "active",
        )
    ).scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active worker assignment not found")

    today = date.today()
    assignment.status = "inactive"
    assignment.assigned_to = today if today >= assignment.assigned_from else assignment.assigned_from
    if worker.assigned_site_id == site_id and assignment.is_primary:
        worker.assigned_site_id = None

    db.add_all([assignment, worker])
    db.commit()


def list_site_workers(db: Session, *, organization_id: str, site_id: str) -> list[SiteWorkerResponse]:
    get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)
    rows = db.execute(
        select(Worker, WorkerSiteAssignment)
        .join(WorkerSiteAssignment, WorkerSiteAssignment.worker_id == Worker.id)
        .where(
            Worker.organization_id == organization_id,
            WorkerSiteAssignment.organization_id == organization_id,
            WorkerSiteAssignment.site_id == site_id,
            WorkerSiteAssignment.status == "active",
        )
        .order_by(Worker.first_name.asc(), Worker.last_name.asc())
    ).all()

    return [
        SiteWorkerResponse(
            id=worker.id,
            worker_code=worker.worker_code,
            name=join_worker_name(worker),
            mobile=worker.phone,
            trade=worker.trade,
            daily_wage=worker.default_wage_rate,
            status=worker.status,
            assigned_from=assignment.assigned_from,
            assignment_id=assignment.id,
        )
        for worker, assignment in rows
    ]


def get_site_stats(db: Session, *, organization_id: str, site_id: str) -> SiteStatsResponse:
    get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)

    worker_count = db.execute(
        select(func.count(Worker.id)).where(
            Worker.organization_id == organization_id,
            Worker.assigned_site_id == site_id,
            Worker.status == "active",
        )
    ).scalar_one()
    assignment_count = db.execute(
        select(func.count(WorkerSiteAssignment.id)).where(
            WorkerSiteAssignment.organization_id == organization_id,
            WorkerSiteAssignment.site_id == site_id,
        )
    ).scalar_one()
    attendance_row = db.execute(
        select(
            func.count(AttendanceRecord.id),
            func.sum(case((AttendanceRecord.status == "present", 1), else_=0)),
            func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)),
            func.sum(case((AttendanceRecord.status == "present", 1), (AttendanceRecord.status == "half_day", 0.5), else_=0)),
            func.sum(AttendanceRecord.regular_hours),
            func.sum(AttendanceRecord.overtime_hours),
        ).where(AttendanceRecord.organization_id == organization_id, AttendanceRecord.site_id == site_id)
    ).one()
    payroll_row = db.execute(
        select(func.count(Payroll.id), func.sum(Payroll.gross_amount), func.sum(Payroll.net_amount)).where(
            Payroll.organization_id == organization_id,
            Payroll.site_id == site_id,
        )
    ).one()
    expense_row = db.execute(
        select(func.count(Expense.id), func.sum(Expense.amount)).where(
            Expense.organization_id == organization_id,
            Expense.site_id == site_id,
        )
    ).one()

    return SiteStatsResponse(
        site_id=site_id,
        active_worker_count=worker_count,
        total_worker_assignments=assignment_count,
        attendance_records=attendance_row[0],
        present_days=decimal_or_zero(attendance_row[1]),
        absent_days=int(attendance_row[2] or 0),
        paid_days=decimal_or_zero(attendance_row[3]),
        regular_hours=decimal_or_zero(attendance_row[4]),
        overtime_hours=decimal_or_zero(attendance_row[5]),
        payroll_count=payroll_row[0],
        gross_payroll=decimal_or_zero(payroll_row[1]),
        net_payroll=decimal_or_zero(payroll_row[2]),
        expense_count=expense_row[0],
        total_expenses=decimal_or_zero(expense_row[1]),
    )


def get_site_expense_summary(db: Session, *, organization_id: str, site_id: str) -> SiteExpenseSummaryResponse:
    get_site_by_id(db, organization_id=organization_id, site_id=site_id, required=True)
    total_row = db.execute(
        select(func.count(Expense.id), func.sum(Expense.amount)).where(
            Expense.organization_id == organization_id,
            Expense.site_id == site_id,
        )
    ).one()
    status_rows = db.execute(
        select(Expense.status, func.count(Expense.id), func.sum(Expense.amount))
        .where(Expense.organization_id == organization_id, Expense.site_id == site_id)
        .group_by(Expense.status)
        .order_by(Expense.status.asc())
    ).all()
    category_rows = db.execute(
        select(Expense.category, func.count(Expense.id), func.sum(Expense.amount))
        .where(Expense.organization_id == organization_id, Expense.site_id == site_id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()

    return SiteExpenseSummaryResponse(
        site_id=site_id,
        expense_count=total_row[0],
        total_expenses=decimal_or_zero(total_row[1]),
        by_status=[
            SiteExpenseBreakdownItem(key=key, expense_count=count, total_amount=decimal_or_zero(total))
            for key, count, total in status_rows
        ],
        by_category=[
            SiteExpenseBreakdownItem(key=key, expense_count=count, total_amount=decimal_or_zero(total))
            for key, count, total in category_rows
        ],
    )


def to_site_response(
    site: Site,
    *,
    worker_counts: Optional[dict[str, int]] = None,
    expense_totals_by_site: Optional[dict[str, Decimal]] = None,
) -> SiteResponse:
    worker_counts = worker_counts or {}
    expense_totals_by_site = expense_totals_by_site or {}
    return SiteResponse(
        id=site.id,
        organization_id=site.organization_id,
        site_code=site.site_code,
        name=site.name,
        client_name=site.client_name,
        project_name=site.project_name,
        city=site.city,
        state=site.state,
        status=site.status,
        start_date=site.start_date,
        end_date=site.end_date,
        site_manager_user_id=site.site_manager_user_id,
        site_manager_name=site.site_manager.full_name if site.site_manager else None,
        active_worker_count=worker_counts.get(site.id, 0),
        total_expense_amount=expense_totals_by_site.get(site.id, Decimal("0.00")),
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


def to_assignment_response(assignment: WorkerSiteAssignment) -> SiteAssignmentResponse:
    return SiteAssignmentResponse(
        id=assignment.id,
        organization_id=assignment.organization_id,
        worker_id=assignment.worker_id,
        site_id=assignment.site_id,
        is_primary=assignment.is_primary,
        status=assignment.status,
        assigned_from=assignment.assigned_from,
        assigned_to=assignment.assigned_to,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )
