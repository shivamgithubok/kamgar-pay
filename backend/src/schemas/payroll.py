from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


PAYMENT_METHODS = {"cash", "bank_transfer", "upi", "cheque"}
PAYMENT_STATUSES = {"pending", "completed", "cancelled"}


class PayrollPeriodCreateRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    pay_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        return " ".join(value.strip().split()) if value else value


class PayrollPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    period_start: date
    period_end: date
    pay_date: Optional[date]
    status: str
    payroll_count: int
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime


class PayrollCalculateRequest(BaseModel):
    site_id: Optional[str] = None
    worker_ids: list[str] = Field(default_factory=list, max_length=500)
    recalculate_existing: bool = True


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    payroll_period_id: str
    worker_id: str
    worker_code: str
    worker_name: str
    site_id: Optional[str]
    site_name: Optional[str]
    daily_wage: Decimal
    overtime_rate: Decimal
    attendance_days: Decimal
    regular_hours: Decimal
    overtime_hours: Decimal
    overtime_amount: Decimal
    gross_amount: Decimal
    advance_amount: Decimal
    pf_rate_percent: Decimal
    pf_amount: Decimal
    net_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    status: str
    remarks: Optional[str]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PayrollCalculationSummaryResponse(BaseModel):
    payroll_period: PayrollPeriodResponse
    generated_count: int
    updated_count: int
    skipped_count: int
    total_gross_amount: Decimal
    total_advance_amount: Decimal
    total_pf_amount: Decimal
    total_net_amount: Decimal
    total_paid_amount: Decimal
    total_pending_amount: Decimal
    items: list[PayrollResponse]


class PaymentCreateBase(BaseModel):
    worker_id: str
    site_id: Optional[str] = None
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)
    payment_date: date
    payment_method: str = Field(default="cash", max_length=20)
    status: str = Field(default="completed", max_length=20)
    external_reference: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PAYMENT_METHODS:
            raise ValueError(f"Payment method must be one of: {', '.join(sorted(PAYMENT_METHODS))}")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PAYMENT_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(PAYMENT_STATUSES))}")
        return normalized

    @field_validator("external_reference")
    @classmethod
    def normalize_reference(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class AdvancePaymentCreateRequest(PaymentCreateBase):
    reason: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: Optional[str]) -> Optional[str]:
        return " ".join(value.strip().split()) if value else value


class PayrollPaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)
    payment_date: date
    payment_method: str = Field(default="cash", max_length=20)
    status: str = Field(default="completed", max_length=20)
    external_reference: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PAYMENT_METHODS:
            raise ValueError(f"Payment method must be one of: {', '.join(sorted(PAYMENT_METHODS))}")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PAYMENT_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(PAYMENT_STATUSES))}")
        return normalized

    @field_validator("external_reference")
    @classmethod
    def normalize_reference(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    payroll_id: Optional[str]
    worker_id: Optional[str]
    worker_code: Optional[str]
    worker_name: Optional[str]
    site_id: Optional[str]
    site_name: Optional[str]
    processed_by_user_id: Optional[str]
    payment_type: str
    payment_method: str
    amount: Decimal
    payment_date: date
    status: str
    external_reference: Optional[str]
    notes: Optional[str]
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
