from __future__ import annotations

from calendar import month_name, monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.database.models import AttendanceRecord, Payment, Payroll, PayrollPeriod, Site, Worker
from src.schemas.payroll import (
    AdvancePaymentCreateRequest,
    PaymentResponse,
    PayrollCalculateRequest,
    PayrollCalculationSummaryResponse,
    PayrollPaymentCreateRequest,
    PayrollPeriodCreateRequest,
    PayrollPeriodResponse,
    PayrollResponse,
)
from src.services.attendance import PAID_DAYS_BY_STATUS
from src.services.workers import join_name


MONEY = Decimal("0.01")
HOURS = Decimal("0.01")
SETTLED_PAYMENT_STATUSES = {"completed"}


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def quantize_hours(value: Decimal) -> Decimal:
    return value.quantize(HOURS, rounding=ROUND_HALF_UP)


def base_payroll_period_query() -> Select[tuple[PayrollPeriod]]:
    return select(PayrollPeriod).options(selectinload(PayrollPeriod.payrolls))


def base_payroll_query() -> Select[tuple[Payroll]]:
    return select(Payroll).options(
        selectinload(Payroll.payroll_period),
        selectinload(Payroll.worker),
        selectinload(Payroll.site),
        selectinload(Payroll.payments),
    )


def base_payment_query() -> Select[tuple[Payment]]:
    return select(Payment).options(
        selectinload(Payment.payroll),
        selectinload(Payment.worker),
        selectinload(Payment.site),
    )


def get_payroll_period_by_id(
    db: Session,
    *,
    organization_id: str,
    payroll_period_id: str,
    required: bool = False,
) -> PayrollPeriod | None:
    payroll_period = db.execute(
        base_payroll_period_query().where(
            PayrollPeriod.organization_id == organization_id,
            PayrollPeriod.id == payroll_period_id,
        )
    ).scalar_one_or_none()
    if payroll_period is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll period not found")
    return payroll_period


def get_payroll_by_id(
    db: Session,
    *,
    organization_id: str,
    payroll_id: str,
    required: bool = False,
) -> Payroll | None:
    payroll = db.execute(
        base_payroll_query().where(
            Payroll.organization_id == organization_id,
            Payroll.id == payroll_id,
        )
    ).scalar_one_or_none()
    if payroll is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll not found")
    return payroll


def get_worker_by_id(db: Session, *, organization_id: str, worker_id: str) -> Worker:
    worker = db.execute(
        select(Worker).where(
            Worker.organization_id == organization_id,
            Worker.id == worker_id,
        )
    ).scalar_one_or_none()
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    return worker


def get_site_by_id(db: Session, *, organization_id: str, site_id: str) -> Site:
    site = db.execute(
        select(Site).where(
            Site.organization_id == organization_id,
            Site.id == site_id,
        )
    ).scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


def create_monthly_payroll_period(
    db: Session,
    *,
    organization_id: str,
    created_by_user_id: str,
    payload: PayrollPeriodCreateRequest,
) -> PayrollPeriod:
    period_start = date(payload.year, payload.month, 1)
    period_end = date(payload.year, payload.month, monthrange(payload.year, payload.month)[1])
    name = payload.name or f"{month_name[payload.month]} {payload.year}"

    payroll_period = PayrollPeriod(
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        name=name,
        period_start=period_start,
        period_end=period_end,
        pay_date=payload.pay_date,
        status="draft",
    )
    try:
        db.add(payroll_period)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payroll period could not be created because a period with this name already exists",
        ) from exc

    return get_payroll_period_by_id(
        db,
        organization_id=organization_id,
        payroll_period_id=payroll_period.id,
        required=True,
    )


def list_payroll_periods(
    db: Session,
    *,
    organization_id: str,
    status_filter: Optional[str] = None,
) -> list[PayrollPeriod]:
    query = base_payroll_period_query().where(PayrollPeriod.organization_id == organization_id)
    if status_filter:
        query = query.where(PayrollPeriod.status == status_filter.strip().lower())
    return list(db.execute(query.order_by(PayrollPeriod.period_start.desc())).scalars().all())


def get_existing_payroll(
    db: Session,
    *,
    organization_id: str,
    payroll_period_id: str,
    worker_id: str,
) -> Payroll | None:
    return db.execute(
        base_payroll_query().where(
            Payroll.organization_id == organization_id,
            Payroll.payroll_period_id == payroll_period_id,
            Payroll.worker_id == worker_id,
        )
    ).scalar_one_or_none()


def list_payrolls_for_period(
    db: Session,
    *,
    organization_id: str,
    payroll_period_id: str,
) -> list[Payroll]:
    get_payroll_period_by_id(
        db,
        organization_id=organization_id,
        payroll_period_id=payroll_period_id,
        required=True,
    )
    return list(
        db.execute(
            base_payroll_query()
            .where(
                Payroll.organization_id == organization_id,
                Payroll.payroll_period_id == payroll_period_id,
            )
            .order_by(Payroll.created_at.desc())
        )
        .scalars()
        .all()
    )


def get_settled_advance_amount(
    db: Session,
    *,
    organization_id: str,
    worker_id: str,
    start_date: date,
    end_date: date,
) -> Decimal:
    payments = db.execute(
        select(Payment.amount).where(
            Payment.organization_id == organization_id,
            Payment.worker_id == worker_id,
            Payment.payment_type == "advance",
            Payment.status.in_(SETTLED_PAYMENT_STATUSES),
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
        )
    ).scalars()
    return quantize_money(sum(payments, Decimal("0.00")))


def get_settled_payroll_payment_amount(payroll: Payroll) -> Decimal:
    return quantize_money(
        sum(
            (
                payment.amount
                for payment in payroll.payments
                if payment.payment_type == "payroll" and payment.status in SETTLED_PAYMENT_STATUSES
            ),
            Decimal("0.00"),
        )
    )


def get_effective_overtime_rate(worker: Worker) -> Decimal:
    if worker.overtime_rate > 0:
        return quantize_money(worker.overtime_rate)
    return quantize_money(worker.default_wage_rate / Decimal("8.00"))


def get_worker_pf_rate(worker: Worker) -> Decimal:
    return quantize_money(getattr(worker, "pf_rate_percent", Decimal("0.00")) or Decimal("0.00"))


def calculate_pf_amount(gross_amount: Decimal, pf_rate_percent: Decimal) -> Decimal:
    return quantize_money(gross_amount * pf_rate_percent / Decimal("100.00"))


def calculate_monthly_payroll(
    db: Session,
    *,
    organization_id: str,
    payroll_period_id: str,
    payload: PayrollCalculateRequest,
) -> PayrollCalculationSummaryResponse:
    payroll_period = get_payroll_period_by_id(
        db,
        organization_id=organization_id,
        payroll_period_id=payroll_period_id,
        required=True,
    )
    if payroll_period.status == "posted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Posted payroll periods cannot be recalculated",
        )
    if payload.site_id:
        get_site_by_id(db, organization_id=organization_id, site_id=payload.site_id)
    if payload.worker_ids:
        unique_worker_ids = sorted(set(payload.worker_ids))
        for worker_id in unique_worker_ids:
            get_worker_by_id(db, organization_id=organization_id, worker_id=worker_id)
    else:
        unique_worker_ids = []

    attendance_query = (
        select(AttendanceRecord)
        .options(selectinload(AttendanceRecord.worker), selectinload(AttendanceRecord.site))
        .where(
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.attendance_date >= payroll_period.period_start,
            AttendanceRecord.attendance_date <= payroll_period.period_end,
        )
    )
    if payload.site_id:
        attendance_query = attendance_query.where(AttendanceRecord.site_id == payload.site_id)
    if unique_worker_ids:
        attendance_query = attendance_query.where(AttendanceRecord.worker_id.in_(unique_worker_ids))

    attendance_records = list(db.execute(attendance_query).scalars().all())
    grouped_records: dict[str, list[AttendanceRecord]] = {}
    for record in attendance_records:
        grouped_records.setdefault(record.worker_id, []).append(record)

    generated_count = 0
    updated_count = 0
    skipped_count = 0
    payrolls: list[Payroll] = []

    try:
        for worker_id, records in grouped_records.items():
            worker = records[0].worker
            existing_payroll = get_existing_payroll(
                db,
                organization_id=organization_id,
                payroll_period_id=payroll_period_id,
                worker_id=worker_id,
            )
            if existing_payroll is not None and not payload.recalculate_existing:
                skipped_count += 1
                payrolls.append(existing_payroll)
                continue
            if existing_payroll is not None and existing_payroll.status == "posted":
                skipped_count += 1
                payrolls.append(existing_payroll)
                continue

            attendance_days = Decimal("0.00")
            regular_hours = Decimal("0.00")
            overtime_hours = Decimal("0.00")
            site_ids = {record.site_id for record in records}
            for record in records:
                attendance_days += PAID_DAYS_BY_STATUS.get(record.status, Decimal("0.00"))
                regular_hours += record.regular_hours
                overtime_hours += record.overtime_hours
                record.payroll_locked = True

            overtime_rate = get_effective_overtime_rate(worker)
            overtime_amount = quantize_money(overtime_hours * overtime_rate)
            wage_amount = quantize_money(worker.default_wage_rate * attendance_days)
            advance_amount = get_settled_advance_amount(
                db,
                organization_id=organization_id,
                worker_id=worker_id,
                start_date=payroll_period.period_start,
                end_date=payroll_period.period_end,
            )
            gross_amount = quantize_money(wage_amount + overtime_amount)
            pf_rate_percent = get_worker_pf_rate(worker)
            pf_amount = calculate_pf_amount(gross_amount, pf_rate_percent)
            net_amount = quantize_money(max(gross_amount - advance_amount - pf_amount, Decimal("0.00")))
            site_id = payload.site_id or (next(iter(site_ids)) if len(site_ids) == 1 else worker.assigned_site_id)

            payroll = existing_payroll or Payroll(
                organization_id=organization_id,
                payroll_period_id=payroll_period_id,
                worker_id=worker_id,
                status="draft",
            )
            payroll.site_id = site_id
            payroll.attendance_days = quantize_hours(attendance_days)
            payroll.regular_hours = quantize_hours(regular_hours)
            payroll.overtime_hours = quantize_hours(overtime_hours)
            payroll.gross_amount = gross_amount
            payroll.deduction_amount = advance_amount
            payroll.pf_amount = pf_amount
            payroll.net_amount = net_amount
            payroll.remarks = (
                f"Net Pay = ({worker.default_wage_rate} x {attendance_days}) "
                f"+ OT {overtime_amount} - Advance {advance_amount} "
                f"- PF {pf_amount} ({pf_rate_percent}%)"
            )
            db.add(payroll)
            payrolls.append(payroll)
            if existing_payroll is None:
                generated_count += 1
            else:
                updated_count += 1

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payroll could not be calculated because one or more rows conflict",
        ) from exc

    refreshed_payrolls = [
        get_payroll_by_id(db, organization_id=organization_id, payroll_id=payroll.id, required=True)
        for payroll in payrolls
    ]
    refreshed_period = get_payroll_period_by_id(
        db,
        organization_id=organization_id,
        payroll_period_id=payroll_period_id,
        required=True,
    )
    items = [to_payroll_response(payroll) for payroll in refreshed_payrolls]
    return PayrollCalculationSummaryResponse(
        payroll_period=to_payroll_period_response(refreshed_period),
        generated_count=generated_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
        total_gross_amount=quantize_money(sum((item.gross_amount for item in items), Decimal("0.00"))),
        total_advance_amount=quantize_money(sum((item.advance_amount for item in items), Decimal("0.00"))),
        total_pf_amount=quantize_money(sum((item.pf_amount for item in items), Decimal("0.00"))),
        total_net_amount=quantize_money(sum((item.net_amount for item in items), Decimal("0.00"))),
        total_paid_amount=quantize_money(sum((item.paid_amount for item in items), Decimal("0.00"))),
        total_pending_amount=quantize_money(sum((item.pending_amount for item in items), Decimal("0.00"))),
        items=items,
    )


def create_advance_payment(
    db: Session,
    *,
    organization_id: str,
    processed_by_user_id: str,
    payload: AdvancePaymentCreateRequest,
) -> Payment:
    get_worker_by_id(db, organization_id=organization_id, worker_id=payload.worker_id)
    if payload.site_id:
        get_site_by_id(db, organization_id=organization_id, site_id=payload.site_id)

    payment = Payment(
        organization_id=organization_id,
        worker_id=payload.worker_id,
        site_id=payload.site_id,
        processed_by_user_id=processed_by_user_id,
        payment_type="advance",
        payment_method=payload.payment_method,
        amount=payload.amount,
        payment_date=payload.payment_date,
        status=payload.status,
        external_reference=payload.external_reference,
        notes=payload.reason or payload.notes,
    )
    try:
        db.add(payment)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be created because a unique reference already exists",
        ) from exc
    return get_payment_by_id(db, organization_id=organization_id, payment_id=payment.id, required=True)


def record_payroll_payment(
    db: Session,
    *,
    organization_id: str,
    processed_by_user_id: str,
    payroll_id: str,
    payload: PayrollPaymentCreateRequest,
) -> Payment:
    payroll = get_payroll_by_id(db, organization_id=organization_id, payroll_id=payroll_id, required=True)
    paid_amount = get_settled_payroll_payment_amount(payroll)
    pending_amount = quantize_money(max(payroll.net_amount - paid_amount, Decimal("0.00")))
    if payload.status in SETTLED_PAYMENT_STATUSES and payload.amount > pending_amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment amount cannot exceed pending payroll amount",
        )

    payment = Payment(
        organization_id=organization_id,
        payroll_id=payroll.id,
        worker_id=payroll.worker_id,
        site_id=payroll.site_id,
        processed_by_user_id=processed_by_user_id,
        payment_type="payroll",
        payment_method=payload.payment_method,
        amount=payload.amount,
        payment_date=payload.payment_date,
        status=payload.status,
        external_reference=payload.external_reference,
        notes=payload.notes,
    )
    try:
        db.add(payment)
        if payload.status in SETTLED_PAYMENT_STATUSES and payload.amount == pending_amount:
            payroll.status = "paid"
            db.add(payroll)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be created because a unique reference already exists",
        ) from exc
    return get_payment_by_id(db, organization_id=organization_id, payment_id=payment.id, required=True)


def get_payment_by_id(
    db: Session,
    *,
    organization_id: str,
    payment_id: str,
    required: bool = False,
) -> Payment | None:
    payment = db.execute(
        base_payment_query().where(
            Payment.organization_id == organization_id,
            Payment.id == payment_id,
        )
    ).scalar_one_or_none()
    if payment is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


def list_payment_history(
    db: Session,
    *,
    organization_id: str,
    worker_id: Optional[str] = None,
    payroll_id: Optional[str] = None,
    payment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[Payment]:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date",
        )

    query = base_payment_query().where(Payment.organization_id == organization_id)
    if worker_id:
        query = query.where(Payment.worker_id == worker_id)
    if payroll_id:
        query = query.where(Payment.payroll_id == payroll_id)
    if payment_type:
        query = query.where(Payment.payment_type == payment_type.strip().lower())
    if start_date:
        query = query.where(Payment.payment_date >= start_date)
    if end_date:
        query = query.where(Payment.payment_date <= end_date)

    return list(db.execute(query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())).scalars().all())


def to_payroll_period_response(payroll_period: PayrollPeriod) -> PayrollPeriodResponse:
    return PayrollPeriodResponse(
        id=payroll_period.id,
        organization_id=payroll_period.organization_id,
        name=payroll_period.name,
        period_start=payroll_period.period_start,
        period_end=payroll_period.period_end,
        pay_date=payroll_period.pay_date,
        status=payroll_period.status,
        payroll_count=len(payroll_period.payrolls),
        created_by_user_id=payroll_period.created_by_user_id,
        created_at=payroll_period.created_at,
        updated_at=payroll_period.updated_at,
    )


def to_payroll_response(payroll: Payroll) -> PayrollResponse:
    overtime_rate = get_effective_overtime_rate(payroll.worker)
    overtime_amount = quantize_money(payroll.overtime_hours * overtime_rate)
    paid_amount = get_settled_payroll_payment_amount(payroll)
    pending_amount = quantize_money(max(payroll.net_amount - paid_amount, Decimal("0.00")))
    return PayrollResponse(
        id=payroll.id,
        organization_id=payroll.organization_id,
        payroll_period_id=payroll.payroll_period_id,
        worker_id=payroll.worker_id,
        worker_code=payroll.worker.worker_code,
        worker_name=join_name(payroll.worker),
        site_id=payroll.site_id,
        site_name=payroll.site.name if payroll.site else None,
        daily_wage=payroll.worker.default_wage_rate,
        overtime_rate=overtime_rate,
        attendance_days=payroll.attendance_days,
        regular_hours=payroll.regular_hours,
        overtime_hours=payroll.overtime_hours,
        overtime_amount=overtime_amount,
        gross_amount=payroll.gross_amount,
        advance_amount=payroll.deduction_amount,
        pf_rate_percent=get_worker_pf_rate(payroll.worker),
        pf_amount=quantize_money(getattr(payroll, "pf_amount", Decimal("0.00")) or Decimal("0.00")),
        net_amount=payroll.net_amount,
        paid_amount=paid_amount,
        pending_amount=pending_amount,
        status=payroll.status,
        remarks=payroll.remarks,
        posted_at=payroll.posted_at,
        created_at=payroll.created_at,
        updated_at=payroll.updated_at,
    )


def to_payment_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        organization_id=payment.organization_id,
        payroll_id=payment.payroll_id,
        worker_id=payment.worker_id,
        worker_code=payment.worker.worker_code if payment.worker else None,
        worker_name=join_name(payment.worker) if payment.worker else None,
        site_id=payment.site_id,
        site_name=payment.site.name if payment.site else None,
        processed_by_user_id=payment.processed_by_user_id,
        payment_type=payment.payment_type,
        payment_method=payment.payment_method,
        amount=payment.amount,
        payment_date=payment.payment_date,
        status=payment.status,
        external_reference=payment.external_reference,
        notes=payment.notes,
        reason=payment.notes,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )
