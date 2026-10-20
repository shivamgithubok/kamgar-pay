from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SiteCostItem(BaseModel):
    site_id: str
    site_code: str
    site_name: str
    labour_cost: Decimal
    expense_cost: Decimal
    total_cost: Decimal
    active_workers: int


class MonthlyTrendItem(BaseModel):
    label: str  # e.g. "Jan 2026" or "2026-01"
    year: int
    month: int
    labour_cost: Decimal
    expense_cost: Decimal
    total_payroll: Decimal
    total_cost: Decimal


class WorkerPaymentSummaryItem(BaseModel):
    worker_id: str
    worker_code: str
    worker_name: str
    trade: Optional[str] = None
    assigned_site_name: Optional[str] = None
    gross_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    advance_amount: Decimal


class LabourCostAnalyticsResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    site_id: Optional[str] = None
    total_labour_cost: Decimal
    monthly_labour_cost: Decimal
    average_worker_cost: Decimal
    total_active_workers: int
    total_overtime_hours: Decimal
    site_wise_labour_cost: list[SiteCostItem]
    monthly_trend: list[MonthlyTrendItem]
    worker_payment_summary: list[WorkerPaymentSummaryItem]


class AttendanceTrendItem(BaseModel):
    label: str
    date_str: str
    present_count: int
    absent_count: int
    leave_count: int
    overtime_hours: Decimal
    attendance_rate: float


class WorkerAttendanceRankItem(BaseModel):
    worker_id: str
    worker_code: str
    worker_name: str
    trade: Optional[str] = None
    site_name: Optional[str] = None
    present_days: float
    absent_days: int
    overtime_hours: Decimal
    attendance_rate: float


class AttendanceAnalyticsResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    site_id: Optional[str] = None
    overall_attendance_rate: float
    absence_rate: float
    total_records: int
    total_present: float
    total_absent: int
    total_leave: int
    total_overtime_hours: Decimal
    absence_trends: list[AttendanceTrendItem]
    worker_rankings: list[WorkerAttendanceRankItem]


class MonthlyPayrollTrendItem(BaseModel):
    label: str
    year: int
    month: int
    gross_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    advance_amount: Decimal
    worker_count: int


class PayrollAnalyticsResponse(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    site_id: Optional[str] = None
    total_payroll: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    advance_payment_summary: Decimal
    monthly_payroll_trend: list[MonthlyPayrollTrendItem]


class CategoryExpenseItem(BaseModel):
    category: str
    expense_count: int
    total_amount: Decimal
    percentage: float


class SiteExpenseItem(BaseModel):
    site_id: str
    site_code: str
    site_name: str
    expense_count: int
    total_amount: Decimal


class MonthlyExpenseTrendItem(BaseModel):
    label: str
    year: int
    month: int
    expense_count: int
    total_amount: Decimal


class ExpenseAnalyticsResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    site_id: Optional[str] = None
    category: Optional[str] = None
    total_expenses: Decimal
    highest_expense_category: Optional[str] = None
    highest_cost_site_id: Optional[str] = None
    highest_cost_site_name: Optional[str] = None
    highest_cost_site_amount: Decimal
    category_wise_expenses: list[CategoryExpenseItem]
    site_wise_expenses: list[SiteExpenseItem]
    monthly_expense_trend: list[MonthlyExpenseTrendItem]


class SiteProfitabilityItem(BaseModel):
    site_id: str
    site_code: str
    site_name: str
    client_name: Optional[str] = None
    status: str
    revenue: Decimal
    labour_cost: Decimal
    expense_cost: Decimal
    total_site_cost: Decimal
    net_margin: Decimal
    labour_percentage: float
    expense_percentage: float


class SiteProfitabilityResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_sites: int
    total_combined_cost: Decimal
    total_labour_cost: Decimal
    total_expense_cost: Decimal
    items: list[SiteProfitabilityItem]
