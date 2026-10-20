from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from src.database.models import AttendanceRecord, Expense, Payment, Payroll, PayrollPeriod, Site, Worker
from src.schemas.reports import (
    AttendanceSummaryReportItem,
    AttendanceSummaryReportResponse,
    MonthlyPayrollReportItem,
    MonthlyPayrollReportResponse,
    SiteExpenseReportItem,
    SiteExpenseReportResponse,
    WorkerPayrollReportItem,
    WorkerPayrollReportResponse,
)
from src.services.report_exports import ExportTable


def decimal_or_zero(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def join_worker_name(first_name: str, last_name: Optional[str]) -> str:
    return " ".join(part for part in [first_name, last_name] if part)


def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date",
        )


def payroll_payment_totals_subquery(organization_id: str):
    return (
        select(
            Payment.payroll_id.label("payroll_id"),
            func.sum(Payment.amount).label("paid_amount"),
        )
        .where(
            Payment.organization_id == organization_id,
            Payment.payment_type == "payroll",
            Payment.status == "completed",
            Payment.payroll_id.is_not(None),
        )
        .group_by(Payment.payroll_id)
        .subquery()
    )


def get_worker_wise_payroll_report(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    payroll_period_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    site_id: Optional[str] = None,
) -> WorkerPayrollReportResponse:
    validate_date_range(start_date, end_date)
    payment_totals = payroll_payment_totals_subquery(organization_id)
    paid_amount = func.coalesce(payment_totals.c.paid_amount, 0)

    query = (
        select(
            Worker.id.label("worker_id"),
            Worker.worker_code,
            Worker.first_name,
            Worker.last_name,
            func.count(Payroll.id).label("payroll_count"),
            func.sum(Payroll.attendance_days).label("attendance_days"),
            func.sum(Payroll.regular_hours).label("regular_hours"),
            func.sum(Payroll.overtime_hours).label("overtime_hours"),
            func.sum(Payroll.gross_amount).label("gross_amount"),
            func.sum(Payroll.deduction_amount).label("advance_amount"),
            func.sum(Payroll.pf_amount).label("pf_amount"),
            func.sum(Payroll.net_amount).label("net_amount"),
            func.sum(paid_amount).label("paid_amount"),
        )
        .join(Payroll, Payroll.worker_id == Worker.id)
        .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
        .outerjoin(payment_totals, payment_totals.c.payroll_id == Payroll.id)
        .where(Payroll.organization_id == organization_id)
        .group_by(Worker.id, Worker.worker_code, Worker.first_name, Worker.last_name)
    )
    if start_date is not None:
        query = query.where(PayrollPeriod.period_start >= start_date)
    if end_date is not None:
        query = query.where(PayrollPeriod.period_end <= end_date)
    if payroll_period_id is not None:
        query = query.where(Payroll.payroll_period_id == payroll_period_id)
    if worker_id is not None:
        query = query.where(Payroll.worker_id == worker_id)
    if site_id is not None:
        query = query.where(Payroll.site_id == site_id)

    items: list[WorkerPayrollReportItem] = []
    for row in db.execute(query.order_by(Worker.worker_code.asc())).all():
        net_amount = decimal_or_zero(row.net_amount)
        paid_total = decimal_or_zero(row.paid_amount)
        items.append(
            WorkerPayrollReportItem(
                worker_id=row.worker_id,
                worker_code=row.worker_code,
                worker_name=join_worker_name(row.first_name, row.last_name),
                payroll_count=row.payroll_count,
                attendance_days=decimal_or_zero(row.attendance_days),
                regular_hours=decimal_or_zero(row.regular_hours),
                overtime_hours=decimal_or_zero(row.overtime_hours),
                gross_amount=decimal_or_zero(row.gross_amount),
                advance_amount=decimal_or_zero(row.advance_amount),
                pf_amount=decimal_or_zero(row.pf_amount),
                net_amount=net_amount,
                paid_amount=paid_total,
                pending_amount=max(net_amount - paid_total, Decimal("0.00")),
            )
        )

    return WorkerPayrollReportResponse(
        start_date=start_date,
        end_date=end_date,
        payroll_period_id=payroll_period_id,
        worker_id=worker_id,
        site_id=site_id,
        total_workers=len(items),
        total_gross_amount=sum((item.gross_amount for item in items), Decimal("0.00")),
        total_advance_amount=sum((item.advance_amount for item in items), Decimal("0.00")),
        total_pf_amount=sum((item.pf_amount for item in items), Decimal("0.00")),
        total_net_amount=sum((item.net_amount for item in items), Decimal("0.00")),
        total_paid_amount=sum((item.paid_amount for item in items), Decimal("0.00")),
        total_pending_amount=sum((item.pending_amount for item in items), Decimal("0.00")),
        items=items,
    )


def get_site_wise_expense_report(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    site_id: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> SiteExpenseReportResponse:
    validate_date_range(start_date, end_date)
    query = (
        select(
            Site.id.label("site_id"),
            Site.site_code,
            Site.name.label("site_name"),
            func.count(Expense.id).label("expense_count"),
            func.sum(Expense.amount).label("total_amount"),
            func.sum(case((Expense.status == "draft", Expense.amount), else_=0)).label("draft_amount"),
            func.sum(case((Expense.status == "approved", Expense.amount), else_=0)).label("approved_amount"),
            func.sum(case((Expense.status == "paid", Expense.amount), else_=0)).label("paid_amount"),
            func.sum(case((Expense.status == "rejected", Expense.amount), else_=0)).label("rejected_amount"),
        )
        .join(Expense, Expense.site_id == Site.id)
        .where(Expense.organization_id == organization_id)
        .group_by(Site.id, Site.site_code, Site.name)
    )
    if start_date is not None:
        query = query.where(Expense.expense_date >= start_date)
    if end_date is not None:
        query = query.where(Expense.expense_date <= end_date)
    if site_id is not None:
        query = query.where(Expense.site_id == site_id)
    if category is not None:
        query = query.where(Expense.category == category.strip())
    if status_filter is not None:
        query = query.where(Expense.status == status_filter.strip().lower())

    items = [
        SiteExpenseReportItem(
            site_id=row.site_id,
            site_code=row.site_code,
            site_name=row.site_name,
            expense_count=row.expense_count,
            total_amount=decimal_or_zero(row.total_amount),
            draft_amount=decimal_or_zero(row.draft_amount),
            approved_amount=decimal_or_zero(row.approved_amount),
            paid_amount=decimal_or_zero(row.paid_amount),
            rejected_amount=decimal_or_zero(row.rejected_amount),
        )
        for row in db.execute(query.order_by(Site.name.asc())).all()
    ]
    return SiteExpenseReportResponse(
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        category=category,
        status=status_filter,
        total_sites=len(items),
        total_expenses=sum(item.expense_count for item in items),
        total_amount=sum((item.total_amount for item in items), Decimal("0.00")),
        items=items,
    )


def get_attendance_summary_report(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    site_id: Optional[str] = None,
    worker_id: Optional[str] = None,
) -> AttendanceSummaryReportResponse:
    validate_date_range(start_date, end_date)
    query = (
        select(
            Site.id.label("site_id"),
            Site.site_code,
            Site.name.label("site_name"),
            func.count(AttendanceRecord.id).label("total_records"),
            func.sum(case((AttendanceRecord.status == "present", 1), else_=0)).label("present_days"),
            func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("absent_days"),
            func.sum(case((AttendanceRecord.status == "half_day", 1), else_=0)).label("half_days"),
            func.sum(case((AttendanceRecord.status == "leave", 1), else_=0)).label("leave_days"),
            func.sum(case((AttendanceRecord.status == "weekly_off", 1), else_=0)).label("weekly_off_days"),
            func.sum(
                case(
                    (AttendanceRecord.status == "present", 1),
                    (AttendanceRecord.status == "half_day", 0.5),
                    else_=0,
                )
            ).label("paid_days"),
            func.sum(AttendanceRecord.regular_hours).label("regular_hours"),
            func.sum(AttendanceRecord.overtime_hours).label("overtime_hours"),
        )
        .join(AttendanceRecord, AttendanceRecord.site_id == Site.id)
        .where(AttendanceRecord.organization_id == organization_id)
        .group_by(Site.id, Site.site_code, Site.name)
    )
    if start_date is not None:
        query = query.where(AttendanceRecord.attendance_date >= start_date)
    if end_date is not None:
        query = query.where(AttendanceRecord.attendance_date <= end_date)
    if site_id is not None:
        query = query.where(AttendanceRecord.site_id == site_id)
    if worker_id is not None:
        query = query.where(AttendanceRecord.worker_id == worker_id)

    items = [
        AttendanceSummaryReportItem(
            site_id=row.site_id,
            site_code=row.site_code,
            site_name=row.site_name,
            total_records=row.total_records,
            present_days=decimal_or_zero(row.present_days),
            absent_days=int(row.absent_days or 0),
            half_days=int(row.half_days or 0),
            leave_days=int(row.leave_days or 0),
            weekly_off_days=int(row.weekly_off_days or 0),
            paid_days=decimal_or_zero(row.paid_days),
            regular_hours=decimal_or_zero(row.regular_hours),
            overtime_hours=decimal_or_zero(row.overtime_hours),
        )
        for row in db.execute(query.order_by(Site.name.asc())).all()
    ]
    return AttendanceSummaryReportResponse(
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        worker_id=worker_id,
        total_sites=len(items),
        total_records=sum(item.total_records for item in items),
        total_paid_days=sum((item.paid_days for item in items), Decimal("0.00")),
        total_regular_hours=sum((item.regular_hours for item in items), Decimal("0.00")),
        total_overtime_hours=sum((item.overtime_hours for item in items), Decimal("0.00")),
        items=items,
    )


def get_monthly_payroll_report(
    db: Session,
    *,
    organization_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    payroll_period_id: Optional[str] = None,
) -> MonthlyPayrollReportResponse:
    if month is not None and year is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year is required when month is provided",
        )
    payment_totals = payroll_payment_totals_subquery(organization_id)
    paid_amount = func.coalesce(payment_totals.c.paid_amount, 0)
    query = (
        select(
            PayrollPeriod.id.label("payroll_period_id"),
            PayrollPeriod.name.label("period_name"),
            PayrollPeriod.period_start,
            PayrollPeriod.period_end,
            func.count(Payroll.id).label("payroll_count"),
            func.count(distinct(Payroll.worker_id)).label("worker_count"),
            func.sum(Payroll.attendance_days).label("attendance_days"),
            func.sum(Payroll.regular_hours).label("regular_hours"),
            func.sum(Payroll.overtime_hours).label("overtime_hours"),
            func.sum(Payroll.gross_amount).label("gross_amount"),
            func.sum(Payroll.deduction_amount).label("advance_amount"),
            func.sum(Payroll.pf_amount).label("pf_amount"),
            func.sum(Payroll.net_amount).label("net_amount"),
            func.sum(paid_amount).label("paid_amount"),
        )
        .join(Payroll, Payroll.payroll_period_id == PayrollPeriod.id)
        .outerjoin(payment_totals, payment_totals.c.payroll_id == Payroll.id)
        .where(PayrollPeriod.organization_id == organization_id)
        .group_by(PayrollPeriod.id, PayrollPeriod.name, PayrollPeriod.period_start, PayrollPeriod.period_end)
    )
    if payroll_period_id is not None:
        query = query.where(PayrollPeriod.id == payroll_period_id)
    if year is not None:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        query = query.where(PayrollPeriod.period_start >= year_start, PayrollPeriod.period_end <= year_end)
    if month is not None and year is not None:
        month_start = date(year, month, 1)
        next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        query = query.where(PayrollPeriod.period_start >= month_start, PayrollPeriod.period_start < next_month)

    items: list[MonthlyPayrollReportItem] = []
    for row in db.execute(query.order_by(PayrollPeriod.period_start.desc())).all():
        net_amount = decimal_or_zero(row.net_amount)
        paid_total = decimal_or_zero(row.paid_amount)
        items.append(
            MonthlyPayrollReportItem(
                payroll_period_id=row.payroll_period_id,
                period_name=row.period_name,
                period_start=row.period_start,
                period_end=row.period_end,
                payroll_count=row.payroll_count,
                worker_count=row.worker_count,
                attendance_days=decimal_or_zero(row.attendance_days),
                regular_hours=decimal_or_zero(row.regular_hours),
                overtime_hours=decimal_or_zero(row.overtime_hours),
                gross_amount=decimal_or_zero(row.gross_amount),
                advance_amount=decimal_or_zero(row.advance_amount),
                pf_amount=decimal_or_zero(row.pf_amount),
                net_amount=net_amount,
                paid_amount=paid_total,
                pending_amount=max(net_amount - paid_total, Decimal("0.00")),
            )
        )

    return MonthlyPayrollReportResponse(
        year=year,
        month=month,
        payroll_period_id=payroll_period_id,
        total_periods=len(items),
        total_payrolls=sum(item.payroll_count for item in items),
        total_gross_amount=sum((item.gross_amount for item in items), Decimal("0.00")),
        total_advance_amount=sum((item.advance_amount for item in items), Decimal("0.00")),
        total_pf_amount=sum((item.pf_amount for item in items), Decimal("0.00")),
        total_net_amount=sum((item.net_amount for item in items), Decimal("0.00")),
        total_paid_amount=sum((item.paid_amount for item in items), Decimal("0.00")),
        total_pending_amount=sum((item.pending_amount for item in items), Decimal("0.00")),
        items=items,
    )


def worker_payroll_export_table(report: WorkerPayrollReportResponse) -> ExportTable:
    return ExportTable(
        title="Worker Wise Payroll",
        headers=[
            "Worker Code",
            "Worker Name",
            "Payrolls",
            "Attendance Days",
            "OT Hours",
            "Gross",
            "Advance",
            "PF",
            "Net",
            "Paid",
            "Pending",
        ],
        rows=[
            [
                item.worker_code,
                item.worker_name,
                item.payroll_count,
                item.attendance_days,
                item.overtime_hours,
                item.gross_amount,
                item.advance_amount,
                item.pf_amount,
                item.net_amount,
                item.paid_amount,
                item.pending_amount,
            ]
            for item in report.items
        ],
    )


def site_expense_export_table(report: SiteExpenseReportResponse) -> ExportTable:
    return ExportTable(
        title="Site Wise Expense",
        headers=["Site Code", "Site Name", "Expenses", "Total", "Draft", "Approved", "Paid", "Rejected"],
        rows=[
            [
                item.site_code,
                item.site_name,
                item.expense_count,
                item.total_amount,
                item.draft_amount,
                item.approved_amount,
                item.paid_amount,
                item.rejected_amount,
            ]
            for item in report.items
        ],
    )


def attendance_summary_export_table(report: AttendanceSummaryReportResponse) -> ExportTable:
    return ExportTable(
        title="Attendance Summary",
        headers=[
            "Site Code",
            "Site Name",
            "Records",
            "Present",
            "Half Days",
            "Absent",
            "Leave",
            "Weekly Off",
            "Paid Days",
            "Regular Hours",
            "OT Hours",
        ],
        rows=[
            [
                item.site_code,
                item.site_name,
                item.total_records,
                item.present_days,
                item.half_days,
                item.absent_days,
                item.leave_days,
                item.weekly_off_days,
                item.paid_days,
                item.regular_hours,
                item.overtime_hours,
            ]
            for item in report.items
        ],
    )


def monthly_payroll_export_table(report: MonthlyPayrollReportResponse) -> ExportTable:
    return ExportTable(
        title="Monthly Payroll",
        headers=[
            "Period",
            "Start",
            "End",
            "Payrolls",
            "Workers",
            "Attendance Days",
            "Gross",
            "Advance",
            "PF",
            "Net",
            "Paid",
            "Pending",
        ],
        rows=[
            [
                item.period_name,
                item.period_start,
                item.period_end,
                item.payroll_count,
                item.worker_count,
                item.attendance_days,
                item.gross_amount,
                item.advance_amount,
                item.pf_amount,
                item.net_amount,
                item.paid_amount,
                item.pending_amount,
            ]
            for item in report.items
        ],
    )
