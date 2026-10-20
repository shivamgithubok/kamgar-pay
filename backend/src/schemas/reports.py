from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class WorkerPayrollReportItem(BaseModel):
    worker_id: str
    worker_code: str
    worker_name: str
    payroll_count: int
    attendance_days: Decimal
    regular_hours: Decimal
    overtime_hours: Decimal
    gross_amount: Decimal
    advance_amount: Decimal
    pf_amount: Decimal
    net_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class WorkerPayrollReportResponse(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]
    payroll_period_id: Optional[str]
    worker_id: Optional[str]
    site_id: Optional[str]
    total_workers: int
    total_gross_amount: Decimal
    total_advance_amount: Decimal
    total_pf_amount: Decimal
    total_net_amount: Decimal
    total_paid_amount: Decimal
    total_pending_amount: Decimal
    items: list[WorkerPayrollReportItem]


class SiteExpenseReportItem(BaseModel):
    site_id: str
    site_code: str
    site_name: str
    expense_count: int
    total_amount: Decimal
    draft_amount: Decimal
    approved_amount: Decimal
    paid_amount: Decimal
    rejected_amount: Decimal


class SiteExpenseReportResponse(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]
    site_id: Optional[str]
    category: Optional[str]
    status: Optional[str]
    total_sites: int
    total_expenses: int
    total_amount: Decimal
    items: list[SiteExpenseReportItem]


class AttendanceSummaryReportItem(BaseModel):
    site_id: str
    site_code: str
    site_name: str
    total_records: int
    present_days: Decimal
    absent_days: int
    half_days: int
    leave_days: int
    weekly_off_days: int
    paid_days: Decimal
    regular_hours: Decimal
    overtime_hours: Decimal


class AttendanceSummaryReportResponse(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]
    site_id: Optional[str]
    worker_id: Optional[str]
    total_sites: int
    total_records: int
    total_paid_days: Decimal
    total_regular_hours: Decimal
    total_overtime_hours: Decimal
    items: list[AttendanceSummaryReportItem]


class MonthlyPayrollReportItem(BaseModel):
    payroll_period_id: str
    period_name: str
    period_start: date
    period_end: date
    payroll_count: int
    worker_count: int
    attendance_days: Decimal
    regular_hours: Decimal
    overtime_hours: Decimal
    gross_amount: Decimal
    advance_amount: Decimal
    pf_amount: Decimal
    net_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class MonthlyPayrollReportResponse(BaseModel):
    year: Optional[int]
    month: Optional[int]
    payroll_period_id: Optional[str]
    total_periods: int
    total_payrolls: int
    total_gross_amount: Decimal
    total_advance_amount: Decimal
    total_pf_amount: Decimal
    total_net_amount: Decimal
    total_paid_amount: Decimal
    total_pending_amount: Decimal
    items: list[MonthlyPayrollReportItem]
