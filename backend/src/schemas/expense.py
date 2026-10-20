from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    site_id: str = Field(..., description="ID of the site where expense was incurred")
    category: str = Field(..., min_length=1, max_length=50, description="Category of expense")
    amount: Decimal = Field(..., gt=0, description="Amount spent")
    expense_date: date = Field(..., description="Date of expense")
    payment_mode: str = Field(default="cash", max_length=20, description="Payment mode (cash, bank_transfer, upi, card)")
    vendor_name: Optional[str] = Field(default=None, max_length=150, description="Vendor or supplier name")
    description: Optional[str] = Field(default=None, description="Detailed description")
    worker_id: Optional[str] = Field(default=None, description="Optional worker associated with expense")
    receipt_required: bool = Field(default=True, description="Whether receipt is required")


class ExpenseUpdateRequest(BaseModel):
    site_id: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    amount: Optional[Decimal] = Field(default=None, gt=0)
    expense_date: Optional[date] = Field(default=None)
    payment_mode: Optional[str] = Field(default=None, max_length=20)
    vendor_name: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = Field(default=None)
    worker_id: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None, max_length=20)
    receipt_required: Optional[bool] = Field(default=None)


class ExpenseResponse(BaseModel):
    id: str
    organization_id: str
    site_id: str
    site_name: str
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    submitted_by_user_id: str
    submitted_by_name: str
    approved_by_user_id: Optional[str] = None
    approved_by_name: Optional[str] = None
    category: str
    expense_date: date
    amount: Decimal
    payment_mode: str
    vendor_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    receipt_required: bool
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class ExpenseMetricsSummaryResponse(BaseModel):
    total_expenses: Decimal
    this_month_expenses: Decimal
    highest_expense_site_id: Optional[str] = None
    highest_expense_site_name: Optional[str] = None
    highest_expense_site_amount: Decimal
    pending_approvals_count: int
    total_count: int


class MonthlyExpenseSummaryItem(BaseModel):
    year: int
    month: int
    expense_count: int
    total_amount: Decimal


class MonthlyExpenseSummaryResponse(BaseModel):
    year: Optional[int] = None
    total_expenses: Decimal
    total_count: int
    items: list[MonthlyExpenseSummaryItem]
