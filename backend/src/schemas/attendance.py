from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


ATTENDANCE_STATUSES = {"present", "absent", "half_day", "leave", "weekly_off"}


class AttendanceEntryBase(BaseModel):
    worker_id: str
    site_id: str
    attendance_date: date
    status: str = Field(max_length=20)
    ot_hours: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, max_digits=5)
    remarks: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ATTENDANCE_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(ATTENDANCE_STATUSES))}")
        return normalized


class MarkAttendanceRequest(AttendanceEntryBase):
    pass


class BulkAttendanceRequest(BaseModel):
    entries: list[MarkAttendanceRequest] = Field(min_length=1, max_length=500)


class OvertimeUpdateRequest(BaseModel):
    ot_hours: Decimal = Field(ge=0, decimal_places=2, max_digits=5)
    remarks: Optional[str] = Field(default=None, max_length=1000)


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    worker_id: str
    worker_code: str
    worker_name: str
    site_id: str
    site_name: str
    attendance_date: date
    status: str
    regular_hours: Decimal
    ot_hours: Decimal
    approval_status: str
    payroll_locked: bool
    remarks: Optional[str]
    captured_by_user_id: str
    approved_by_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class BulkAttendanceResponse(BaseModel):
    created_count: int
    updated_count: int
    items: list[AttendanceResponse]


class MonthlyAttendanceDay(BaseModel):
    attendance_id: str
    attendance_date: date
    site_id: str
    site_name: str
    status: str
    regular_hours: Decimal
    ot_hours: Decimal
    approval_status: str
    payroll_locked: bool


class MonthlyAttendanceWorkerReport(BaseModel):
    worker_id: str
    worker_code: str
    worker_name: str
    present_days: Decimal
    absent_days: int
    half_days: int
    leave_days: int
    weekly_off_days: int
    paid_days: Decimal
    regular_hours: Decimal
    ot_hours: Decimal
    total_records: int
    days: list[MonthlyAttendanceDay]


class MonthlyAttendanceReportResponse(BaseModel):
    year: int
    month: int
    start_date: date
    end_date: date
    site_id: Optional[str]
    worker_id: Optional[str]
    total_workers: int
    total_records: int
    total_paid_days: Decimal
    total_regular_hours: Decimal
    total_ot_hours: Decimal
    workers: list[MonthlyAttendanceWorkerReport]
