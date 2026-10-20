from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SiteCreateRequest(BaseModel):
    site_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    client_name: Optional[str] = Field(default=None, max_length=150)
    project_name: Optional[str] = Field(default=None, max_length=150)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="active", max_length=20)
    start_date: date
    end_date: Optional[date] = None
    site_manager_user_id: Optional[str] = None

    @field_validator("site_code")
    @classmethod
    def normalize_site_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name", "client_name", "project_name", "city", "state")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = " ".join(value.strip().split())
        return normalized or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"active", "inactive", "completed", "on_hold"}
        if normalized not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @model_validator(mode="after")
    def validate_dates(self) -> "SiteCreateRequest":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return self


class SiteUpdateRequest(BaseModel):
    site_code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    client_name: Optional[str] = Field(default=None, max_length=150)
    project_name: Optional[str] = Field(default=None, max_length=150)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=20)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    site_manager_user_id: Optional[str] = None

    @field_validator("site_code")
    @classmethod
    def normalize_site_code(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value else value

    @field_validator("name", "client_name", "project_name", "city", "state")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = " ".join(value.strip().split())
        return normalized or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        allowed = {"active", "inactive", "completed", "on_hold"}
        if normalized not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return normalized


class SiteWorkerAssignmentRequest(BaseModel):
    worker_id: str
    assigned_from: Optional[date] = None
    is_primary: bool = True


class SiteAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    worker_id: str
    site_id: str
    is_primary: bool
    status: str
    assigned_from: date
    assigned_to: Optional[date]
    created_at: datetime
    updated_at: datetime


class SiteWorkerResponse(BaseModel):
    id: str
    worker_code: str
    name: str
    mobile: Optional[str]
    trade: Optional[str]
    daily_wage: Decimal
    status: str
    assigned_from: Optional[date]
    assignment_id: Optional[str]


class SiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    site_code: str
    name: str
    client_name: Optional[str]
    project_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    status: str
    start_date: date
    end_date: Optional[date]
    site_manager_user_id: Optional[str]
    site_manager_name: Optional[str]
    active_worker_count: int
    total_expense_amount: Decimal
    created_at: datetime
    updated_at: datetime


class SiteListResponse(BaseModel):
    items: list[SiteResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class SiteStatsResponse(BaseModel):
    site_id: str
    active_worker_count: int
    total_worker_assignments: int
    attendance_records: int
    present_days: Decimal
    absent_days: int
    paid_days: Decimal
    regular_hours: Decimal
    overtime_hours: Decimal
    payroll_count: int
    gross_payroll: Decimal
    net_payroll: Decimal
    expense_count: int
    total_expenses: Decimal


class SiteExpenseBreakdownItem(BaseModel):
    key: str
    expense_count: int
    total_amount: Decimal


class SiteExpenseSummaryResponse(BaseModel):
    site_id: str
    total_expenses: Decimal
    expense_count: int
    by_status: list[SiteExpenseBreakdownItem]
    by_category: list[SiteExpenseBreakdownItem]
