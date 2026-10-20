from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
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
from src.services.payroll import (
    calculate_monthly_payroll,
    create_advance_payment,
    create_monthly_payroll_period,
    get_payroll_by_id,
    get_payroll_period_by_id,
    list_payment_history,
    list_payroll_periods,
    list_payrolls_for_period,
    record_payroll_payment,
    to_payment_response,
    to_payroll_period_response,
    to_payroll_response,
)


router = APIRouter()


@router.post("/periods", response_model=PayrollPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_payroll_period_route(
    payload: PayrollPeriodCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PayrollPeriodResponse:
    payroll_period = create_monthly_payroll_period(
        db,
        organization_id=current_user.organization_id,
        created_by_user_id=current_user.id,
        payload=payload,
    )
    return to_payroll_period_response(payroll_period)


@router.get("/periods", response_model=list[PayrollPeriodResponse])
def list_payroll_periods_route(
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> list[PayrollPeriodResponse]:
    periods = list_payroll_periods(
        db,
        organization_id=current_user.organization_id,
        status_filter=status_filter,
    )
    return [to_payroll_period_response(period) for period in periods]


@router.get("/periods/{payroll_period_id}", response_model=PayrollPeriodResponse)
def get_payroll_period_route(
    payroll_period_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PayrollPeriodResponse:
    payroll_period = get_payroll_period_by_id(
        db,
        organization_id=current_user.organization_id,
        payroll_period_id=payroll_period_id,
        required=True,
    )
    return to_payroll_period_response(payroll_period)


@router.post("/periods/{payroll_period_id}/calculate", response_model=PayrollCalculationSummaryResponse)
def calculate_monthly_payroll_route(
    payroll_period_id: str,
    payload: PayrollCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PayrollCalculationSummaryResponse:
    return calculate_monthly_payroll(
        db,
        organization_id=current_user.organization_id,
        payroll_period_id=payroll_period_id,
        payload=payload,
    )


@router.get("/periods/{payroll_period_id}/entries", response_model=list[PayrollResponse])
def list_period_payroll_entries_route(
    payroll_period_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> list[PayrollResponse]:
    payrolls = list_payrolls_for_period(
        db,
        organization_id=current_user.organization_id,
        payroll_period_id=payroll_period_id,
    )
    return [to_payroll_response(payroll) for payroll in payrolls]


@router.get("/entries/{payroll_id}", response_model=PayrollResponse)
def get_payroll_entry_route(
    payroll_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PayrollResponse:
    payroll = get_payroll_by_id(
        db,
        organization_id=current_user.organization_id,
        payroll_id=payroll_id,
        required=True,
    )
    return to_payroll_response(payroll)


@router.post("/advances", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_advance_payment_route(
    payload: AdvancePaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PaymentResponse:
    payment = create_advance_payment(
        db,
        organization_id=current_user.organization_id,
        processed_by_user_id=current_user.id,
        payload=payload,
    )
    return to_payment_response(payment)


@router.post("/entries/{payroll_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_partial_payroll_payment_route(
    payroll_id: str,
    payload: PayrollPaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PaymentResponse:
    payment = record_payroll_payment(
        db,
        organization_id=current_user.organization_id,
        processed_by_user_id=current_user.id,
        payroll_id=payroll_id,
        payload=payload,
    )
    return to_payment_response(payment)


@router.get("/payments/history", response_model=list[PaymentResponse])
def payment_history_route(
    worker_id: Optional[str] = Query(default=None),
    payroll_id: Optional[str] = Query(default=None),
    payment_type: Optional[str] = Query(default=None, max_length=30),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> list[PaymentResponse]:
    payments = list_payment_history(
        db,
        organization_id=current_user.organization_id,
        worker_id=worker_id,
        payroll_id=payroll_id,
        payment_type=payment_type,
        start_date=start_date,
        end_date=end_date,
    )
    return [to_payment_response(payment) for payment in payments]
