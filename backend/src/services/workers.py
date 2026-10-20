from __future__ import annotations

from datetime import date
from decimal import Decimal
from math import ceil
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.database.models import Payment, Worker, WorkerSiteAssignment
from src.schemas.worker import (
    AddressDetails,
    BankDetails,
    WorkerCreateRequest,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdateRequest,
)
from src.services.sites import get_site_by_id


def base_worker_query() -> Select[tuple[Worker]]:
    return select(Worker).options(
        selectinload(Worker.assigned_site),
        selectinload(Worker.assignments).selectinload(WorkerSiteAssignment.site),
    )


def split_name(name: str) -> tuple[str, Optional[str]]:
    parts = name.split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else None
    return first_name, last_name


def join_name(worker: Worker) -> str:
    return " ".join(part for part in [worker.first_name, worker.last_name] if part)


def get_worker_by_id(
    db: Session,
    *,
    organization_id: str,
    worker_id: str,
    required: bool = False,
) -> Worker | None:
    worker = db.execute(
        base_worker_query().where(Worker.organization_id == organization_id, Worker.id == worker_id)
    ).scalar_one_or_none()
    if worker is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    return worker


def field_supplied(payload: WorkerCreateRequest | WorkerUpdateRequest, field_name: str) -> bool:
    if isinstance(payload, WorkerCreateRequest):
        return True
    return field_name in payload.model_fields_set


def apply_worker_fields(worker: Worker, payload: WorkerCreateRequest | WorkerUpdateRequest) -> None:
    if field_supplied(payload, "worker_code") and payload.worker_code is not None:
        worker.worker_code = payload.worker_code
    if field_supplied(payload, "name") and payload.name is not None:
        worker.first_name, worker.last_name = split_name(payload.name)
    if field_supplied(payload, "mobile"):
        worker.phone = payload.mobile
    if field_supplied(payload, "aadhaar"):
        worker.aadhaar_number = payload.aadhaar
    if field_supplied(payload, "trade"):
        worker.trade = payload.trade.strip() if payload.trade else None
    if field_supplied(payload, "daily_wage") and payload.daily_wage is not None:
        worker.default_wage_rate = payload.daily_wage
    if field_supplied(payload, "pf_rate_percent") and payload.pf_rate_percent is not None:
        worker.pf_rate_percent = payload.pf_rate_percent
    if field_supplied(payload, "joining_date") and payload.joining_date is not None:
        worker.joined_on = payload.joining_date
    if field_supplied(payload, "status") and getattr(payload, "status", None) is not None:
        worker.status = payload.status

    if field_supplied(payload, "address"):
        address = payload.address
        if address is None:
            worker.address_line1 = None
            worker.address_line2 = None
            worker.city = None
            worker.state = None
            worker.postal_code = None
        else:
            worker.address_line1 = address.line1
            worker.address_line2 = address.line2
            worker.city = address.city
            worker.state = address.state
            worker.postal_code = address.postal_code

    if field_supplied(payload, "bank_details"):
        bank_details = payload.bank_details
        if bank_details is None:
            worker.bank_account_holder_name = None
            worker.bank_name = None
            worker.bank_account_number = None
            worker.ifsc_code = None
            worker.bank_account_masked = None
        else:
            worker.bank_account_holder_name = bank_details.account_holder_name
            worker.bank_name = bank_details.bank_name
            worker.bank_account_number = bank_details.account_number
            worker.ifsc_code = bank_details.ifsc_code
            worker.bank_account_masked = mask_account_number(bank_details.account_number)


def mask_account_number(account_number: Optional[str]) -> Optional[str]:
    if not account_number:
        return None
    if len(account_number) <= 4:
        return account_number
    return f"{'*' * (len(account_number) - 4)}{account_number[-4:]}"


def sync_worker_assignment(
    db: Session,
    *,
    worker: Worker,
    organization_id: str,
    assigned_site_id: Optional[str],
    effective_date: date,
) -> None:
    active_assignments = [
        assignment
        for assignment in worker.assignments
        if assignment.is_primary and assignment.status == "active"
    ]

    for assignment in active_assignments:
        if assigned_site_id and assignment.site_id == assigned_site_id:
            worker.assigned_site_id = assigned_site_id
            return
        assignment.status = "inactive"
        assignment.assigned_to = effective_date if effective_date >= assignment.assigned_from else assignment.assigned_from

    worker.assigned_site_id = assigned_site_id
    if assigned_site_id is None:
        return

    get_site_by_id(db, organization_id=organization_id, site_id=assigned_site_id, required=True)
    db.add(
        WorkerSiteAssignment(
            organization_id=organization_id,
            worker_id=worker.id,
            site_id=assigned_site_id,
            is_primary=True,
            status="active",
            assigned_from=effective_date,
        )
    )


def create_worker(db: Session, *, organization_id: str, payload: WorkerCreateRequest) -> Worker:
    worker = Worker(
        organization_id=organization_id,
        employment_type="daily_wage",
        wage_type="daily",
        status="active",
        joined_on=payload.joining_date,
    )
    apply_worker_fields(worker, payload)

    try:
        db.add(worker)
        db.flush()
        sync_worker_assignment(
            db,
            worker=worker,
            organization_id=organization_id,
            assigned_site_id=payload.assigned_site_id,
            effective_date=payload.joining_date,
        )
        db.commit()
        # Dispatch notification to organization admins
        try:
            from src.services.notifications import notify_organization_admins
            w_name = join_name(worker)
            notify_organization_admins(
                db,
                organization_id=organization_id,
                notification_type="worker_created",
                title="New Worker Added",
                message=f"Worker '{w_name}' ({worker.worker_code}) was added to the workforce roster.",
                worker_id=worker.id,
            )
        except Exception as notif_err:
            print(f"Notification dispatch warning: {notif_err}")

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker could not be created because a unique field already exists",
        ) from exc

    return get_worker_by_id(db, organization_id=organization_id, worker_id=worker.id, required=True)


def update_worker(
    db: Session,
    *,
    organization_id: str,
    worker_id: str,
    payload: WorkerUpdateRequest,
) -> Worker:
    worker = get_worker_by_id(db, organization_id=organization_id, worker_id=worker_id, required=True)
    apply_worker_fields(worker, payload)

    if "assigned_site_id" in payload.model_fields_set:
        effective_date = payload.joining_date or date.today()
        sync_worker_assignment(
            db,
            worker=worker,
            organization_id=organization_id,
            assigned_site_id=payload.assigned_site_id,
            effective_date=effective_date,
        )

    try:
        db.add(worker)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker could not be updated because a unique field already exists",
        ) from exc

    return get_worker_by_id(db, organization_id=organization_id, worker_id=worker.id, required=True)


def delete_worker(db: Session, *, organization_id: str, worker_id: str) -> None:
    worker = get_worker_by_id(db, organization_id=organization_id, worker_id=worker_id, required=True)
    worker.status = "inactive"
    worker.assigned_site_id = None

    for assignment in worker.assignments:
        if assignment.is_primary and assignment.status == "active":
            assignment.status = "inactive"
            assignment.assigned_to = date.today()

    db.add(worker)
    db.commit()


def list_workers(
    db: Session,
    *,
    organization_id: str,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    trade: Optional[str] = None,
    status_filter: Optional[str] = None,
    site_id: Optional[str] = None,
) -> WorkerListResponse:
    query = base_worker_query().where(Worker.organization_id == organization_id)
    count_query = select(func.count(Worker.id)).where(Worker.organization_id == organization_id)

    if search:
        like_term = f"%{search.strip()}%"
        search_filter = or_(
            Worker.worker_code.ilike(like_term),
            Worker.first_name.ilike(like_term),
            Worker.last_name.ilike(like_term),
            Worker.phone.ilike(like_term),
            Worker.aadhaar_number.ilike(like_term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if trade:
        normalized_trade = trade.strip()
        query = query.where(Worker.trade == normalized_trade)
        count_query = count_query.where(Worker.trade == normalized_trade)

    if status_filter:
        normalized_status = status_filter.strip().lower()
        query = query.where(Worker.status == normalized_status)
        count_query = count_query.where(Worker.status == normalized_status)

    if site_id:
        query = query.where(Worker.assigned_site_id == site_id)
        count_query = count_query.where(Worker.assigned_site_id == site_id)

    total = db.execute(count_query).scalar_one()
    offset = (page - 1) * page_size

    workers = list(
        db.execute(
            query.order_by(Worker.created_at.desc()).offset(offset).limit(page_size)
        ).scalars().all()
    )

    total_pages = ceil(total / page_size) if total else 0
    summaries = get_advance_summaries(db, organization_id=organization_id, worker_ids=[worker.id for worker in workers])
    return WorkerListResponse(
        items=[to_worker_response(worker, summaries.get(worker.id)) for worker in workers],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


def get_advance_summaries(
    db: Session,
    *,
    organization_id: str,
    worker_ids: list[str],
) -> dict[str, dict]:
    if not worker_ids:
        return {}

    payments = list(
        db.execute(
            select(Payment)
            .where(
                Payment.organization_id == organization_id,
                Payment.worker_id.in_(worker_ids),
                Payment.payment_type == "advance",
                Payment.status != "cancelled",
            )
            .order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        )
        .scalars()
        .all()
    )

    summaries: dict[str, dict] = {}
    for payment in payments:
        worker_id = payment.worker_id
        if worker_id is None:
            continue
        summary = summaries.setdefault(
            worker_id,
            {
                "advance_count": 0,
                "advance_total": Decimal("0.00"),
                "last_advance_date": None,
                "last_advance_reason": None,
            },
        )
        summary["advance_count"] += 1
        summary["advance_total"] += payment.amount
        if summary["last_advance_date"] is None:
            summary["last_advance_date"] = payment.payment_date
            summary["last_advance_reason"] = payment.notes
    return summaries


def to_worker_response(worker: Worker, summary: Optional[dict] = None) -> WorkerResponse:
    summary = summary or {}
    return WorkerResponse(
        id=worker.id,
        organization_id=worker.organization_id,
        worker_code=worker.worker_code,
        name=join_name(worker),
        mobile=worker.phone,
        aadhaar=worker.aadhaar_number,
        address=AddressDetails(
            line1=worker.address_line1,
            line2=worker.address_line2,
            city=worker.city,
            state=worker.state,
            postal_code=worker.postal_code,
        ),
        trade=worker.trade,
        daily_wage=worker.default_wage_rate,
        pf_rate_percent=worker.pf_rate_percent,
        joining_date=worker.joined_on,
        assigned_site_id=worker.assigned_site_id,
        assigned_site_name=worker.assigned_site.name if worker.assigned_site else None,
        bank_details=BankDetails(
            account_holder_name=worker.bank_account_holder_name,
            bank_name=worker.bank_name,
            account_number=worker.bank_account_number,
            ifsc_code=worker.ifsc_code,
        ),
        status=worker.status,
        advance_count=int(summary.get("advance_count") or 0),
        advance_total=summary.get("advance_total") or Decimal("0.00"),
        last_advance_date=summary.get("last_advance_date"),
        last_advance_reason=summary.get("last_advance_reason"),
        created_at=worker.created_at,
        updated_at=worker.updated_at,
    )
