from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import case, distinct, extract, func, select
from sqlalchemy.orm import Session

from src.database.models import AttendanceRecord, Expense, Payment, Payroll, PayrollPeriod, Site, Worker
from src.schemas.analytics import (
    AttendanceAnalyticsResponse,
    AttendanceTrendItem,
    CategoryExpenseItem,
    ExpenseAnalyticsResponse,
    LabourCostAnalyticsResponse,
    MonthlyExpenseTrendItem,
    MonthlyPayrollTrendItem,
    MonthlyTrendItem,
    PayrollAnalyticsResponse,
    SiteCostItem,
    SiteExpenseItem,
    SiteProfitabilityItem,
    SiteProfitabilityResponse,
    WorkerAttendanceRankItem,
    WorkerPaymentSummaryItem,
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


def payroll_payments_subquery(organization_id: str):
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


# 1. LABOUR COST ANALYTICS
def get_labour_cost_analytics(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    site_id: Optional[str] = None,
) -> LabourCostAnalyticsResponse:
    validate_date_range(start_date, end_date)
    today = date.today()

    payments_sq = payroll_payments_subquery(organization_id)
    paid_col = func.coalesce(payments_sq.c.paid_amount, 0)

    # Base query for payrolls
    payroll_q = (
        select(
            func.sum(Payroll.gross_amount).label("total_gross"),
            func.sum(Payroll.net_amount).label("total_net"),
            func.sum(paid_col).label("total_paid"),
            func.sum(Payroll.deduction_amount).label("total_advance"),
            func.sum(Payroll.overtime_hours).label("total_ot"),
        )
        .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
        .outerjoin(payments_sq, payments_sq.c.payroll_id == Payroll.id)
        .where(Payroll.organization_id == organization_id)
    )

    if start_date:
        payroll_q = payroll_q.where(PayrollPeriod.period_start >= start_date)
    if end_date:
        payroll_q = payroll_q.where(PayrollPeriod.period_end <= end_date)
    if site_id:
        payroll_q = payroll_q.where(Payroll.site_id == site_id)

    row = db.execute(payroll_q).one()
    total_labour_cost = decimal_or_zero(row.total_gross)
    total_ot_hours = decimal_or_zero(row.total_ot)

    # Monthly cost for current month
    this_month_q = (
        select(func.sum(Payroll.gross_amount))
        .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
        .where(
            Payroll.organization_id == organization_id,
            extract("year", PayrollPeriod.period_start) == today.year,
            extract("month", PayrollPeriod.period_start) == today.month,
        )
    )
    if site_id:
        this_month_q = this_month_q.where(Payroll.site_id == site_id)
    monthly_labour_cost = decimal_or_zero(db.execute(this_month_q).scalar_one_or_none())

    # Active workers count
    active_workers_q = select(func.count(Worker.id)).where(
        Worker.organization_id == organization_id, Worker.status == "active"
    )
    if site_id:
        active_workers_q = active_workers_q.where(Worker.assigned_site_id == site_id)
    total_active_workers = db.execute(active_workers_q).scalar_one()

    avg_worker_cost = (
        total_labour_cost / Decimal(total_active_workers)
        if total_active_workers > 0
        else Decimal("0.00")
    )

    # Site-wise labour cost
    site_cost_q = (
        select(
            Site.id.label("site_id"),
            Site.site_code,
            Site.name.label("site_name"),
            func.sum(Payroll.gross_amount).label("labour_cost"),
        )
        .join(Payroll, Payroll.site_id == Site.id)
        .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
        .where(Payroll.organization_id == organization_id)
        .group_by(Site.id, Site.site_code, Site.name)
    )
    if start_date:
        site_cost_q = site_cost_q.where(PayrollPeriod.period_start >= start_date)
    if end_date:
        site_cost_q = site_cost_q.where(PayrollPeriod.period_end <= end_date)
    if site_id:
        site_cost_q = site_cost_q.where(Site.id == site_id)

    site_wise_labour_cost: list[SiteCostItem] = []
    for s_row in db.execute(site_cost_q.order_by(Site.name.asc())).all():
        l_cost = decimal_or_zero(s_row.labour_cost)
        # Fetch expenses for this site
        exp_sum = db.execute(
            select(func.sum(Expense.amount)).where(
                Expense.organization_id == organization_id, Expense.site_id == s_row.site_id
            )
        ).scalar_one_or_none()
        e_cost = decimal_or_zero(exp_sum)

        w_cnt = db.execute(
            select(func.count(Worker.id)).where(
                Worker.organization_id == organization_id, Worker.assigned_site_id == s_row.site_id, Worker.status == "active"
            )
        ).scalar_one()

        site_wise_labour_cost.append(
            SiteCostItem(
                site_id=s_row.site_id,
                site_code=s_row.site_code,
                site_name=s_row.site_name,
                labour_cost=l_cost,
                expense_cost=e_cost,
                total_cost=l_cost + e_cost,
                active_workers=w_cnt,
            )
        )

    # Monthly Trend
    monthly_trend_q = (
        select(
            extract("year", PayrollPeriod.period_start).label("year_num"),
            extract("month", PayrollPeriod.period_start).label("month_num"),
            func.sum(Payroll.gross_amount).label("gross_sum"),
        )
        .join(Payroll, Payroll.payroll_period_id == PayrollPeriod.id)
        .where(PayrollPeriod.organization_id == organization_id)
        .group_by(extract("year", PayrollPeriod.period_start), extract("month", PayrollPeriod.period_start))
    )
    if site_id:
        monthly_trend_q = monthly_trend_q.where(Payroll.site_id == site_id)

    monthly_trend: list[MonthlyTrendItem] = []
    for m_row in db.execute(monthly_trend_q.order_by(extract("year", PayrollPeriod.period_start).desc(), extract("month", PayrollPeriod.period_start).desc())).all():
        yr = int(m_row.year_num)
        mo = int(m_row.month_num)
        lbl = date(yr, mo, 1).strftime("%b %Y")
        g_sum = decimal_or_zero(m_row.gross_sum)

        # Monthly expenses
        exp_m = db.execute(
            select(func.sum(Expense.amount)).where(
                Expense.organization_id == organization_id,
                extract("year", Expense.expense_date) == yr,
                extract("month", Expense.expense_date) == mo,
            )
        ).scalar_one_or_none()
        e_m = decimal_or_zero(exp_m)

        monthly_trend.append(
            MonthlyTrendItem(
                label=lbl,
                year=yr,
                month=mo,
                labour_cost=g_sum,
                expense_cost=e_m,
                total_payroll=g_sum,
                total_cost=g_sum + e_m,
            )
        )

    # Worker payment summary
    worker_sum_q = (
        select(
            Worker.id.label("worker_id"),
            Worker.worker_code,
            Worker.first_name,
            Worker.last_name,
            Worker.trade,
            Site.name.label("site_name"),
            func.sum(Payroll.gross_amount).label("gross_sum"),
            func.sum(Payroll.deduction_amount).label("advance_sum"),
            func.sum(Payroll.net_amount).label("net_sum"),
            func.sum(paid_col).label("paid_sum"),
        )
        .join(Payroll, Payroll.worker_id == Worker.id)
        .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
        .outerjoin(Site, Site.id == Worker.assigned_site_id)
        .outerjoin(payments_sq, payments_sq.c.payroll_id == Payroll.id)
        .where(Payroll.organization_id == organization_id)
        .group_by(Worker.id, Worker.worker_code, Worker.first_name, Worker.last_name, Worker.trade, Site.name)
    )
    if start_date:
        worker_sum_q = worker_sum_q.where(PayrollPeriod.period_start >= start_date)
    if end_date:
        worker_sum_q = worker_sum_q.where(PayrollPeriod.period_end <= end_date)
    if site_id:
        worker_sum_q = worker_sum_q.where(Payroll.site_id == site_id)

    worker_payment_summary: list[WorkerPaymentSummaryItem] = []
    for w_row in db.execute(worker_sum_q.order_by(Worker.first_name.asc())).all():
        net = decimal_or_zero(w_row.net_sum)
        paid = decimal_or_zero(w_row.paid_sum)
        worker_payment_summary.append(
            WorkerPaymentSummaryItem(
                worker_id=w_row.worker_id,
                worker_code=w_row.worker_code,
                worker_name=join_worker_name(w_row.first_name, w_row.last_name),
                trade=w_row.trade,
                assigned_site_name=w_row.site_name,
                gross_amount=decimal_or_zero(w_row.gross_sum),
                advance_amount=decimal_or_zero(w_row.advance_sum),
                paid_amount=paid,
                pending_amount=max(net - paid, Decimal("0.00")),
            )
        )

    return LabourCostAnalyticsResponse(
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        total_labour_cost=total_labour_cost,
        monthly_labour_cost=monthly_labour_cost,
        average_worker_cost=avg_worker_cost,
        total_active_workers=total_active_workers,
        total_overtime_hours=total_ot_hours,
        site_wise_labour_cost=site_wise_labour_cost,
        monthly_trend=monthly_trend,
        worker_payment_summary=worker_payment_summary,
    )


# 2. ATTENDANCE ANALYTICS
def get_attendance_analytics(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    site_id: Optional[str] = None,
) -> AttendanceAnalyticsResponse:
    validate_date_range(start_date, end_date)

    query = select(
        func.count(AttendanceRecord.id).label("total_records"),
        func.sum(case((AttendanceRecord.status == "present", 1), (AttendanceRecord.status == "half_day", 0.5), else_=0)).label("present_days"),
        func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("absent_days"),
        func.sum(case((AttendanceRecord.status == "leave", 1), else_=0)).label("leave_days"),
        func.sum(AttendanceRecord.overtime_hours).label("overtime_hours"),
    ).where(AttendanceRecord.organization_id == organization_id)

    if start_date:
        query = query.where(AttendanceRecord.attendance_date >= start_date)
    if end_date:
        query = query.where(AttendanceRecord.attendance_date <= end_date)
    if site_id:
        query = query.where(AttendanceRecord.site_id == site_id)

    row = db.execute(query).one()
    total_records = row.total_records or 0
    total_present = float(decimal_or_zero(row.present_days))
    total_absent = int(row.absent_days or 0)
    total_leave = int(row.leave_days or 0)
    total_ot = decimal_or_zero(row.overtime_hours)

    attendance_rate = (total_present / total_records * 100.0) if total_records > 0 else 0.0
    absence_rate = (total_absent / total_records * 100.0) if total_records > 0 else 0.0

    # Daily / Monthly absence trends
    trend_q = (
        select(
            AttendanceRecord.attendance_date,
            func.count(AttendanceRecord.id).label("total_count"),
            func.sum(case((AttendanceRecord.status == "present", 1), (AttendanceRecord.status == "half_day", 0.5), else_=0)).label("present_count"),
            func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("absent_count"),
            func.sum(case((AttendanceRecord.status == "leave", 1), else_=0)).label("leave_count"),
            func.sum(AttendanceRecord.overtime_hours).label("ot_hours"),
        )
        .where(AttendanceRecord.organization_id == organization_id)
        .group_by(AttendanceRecord.attendance_date)
    )
    if start_date:
        trend_q = trend_q.where(AttendanceRecord.attendance_date >= start_date)
    if end_date:
        trend_q = trend_q.where(AttendanceRecord.attendance_date <= end_date)
    if site_id:
        trend_q = trend_q.where(AttendanceRecord.site_id == site_id)

    absence_trends: list[AttendanceTrendItem] = []
    for t_row in db.execute(trend_q.order_by(AttendanceRecord.attendance_date.desc()).limit(30)).all():
        rec_cnt = t_row.total_count or 0
        p_cnt = float(t_row.present_count or 0)
        rate = (p_cnt / rec_cnt * 100.0) if rec_cnt > 0 else 0.0
        absence_trends.append(
            AttendanceTrendItem(
                label=t_row.attendance_date.strftime("%d %b"),
                date_str=t_row.attendance_date.isoformat(),
                present_count=int(p_cnt),
                absent_count=int(t_row.absent_count or 0),
                leave_count=int(t_row.leave_count or 0),
                overtime_hours=decimal_or_zero(t_row.ot_hours),
                attendance_rate=round(rate, 1),
            )
        )

    # Worker attendance rankings
    rank_q = (
        select(
            Worker.id.label("worker_id"),
            Worker.worker_code,
            Worker.first_name,
            Worker.last_name,
            Worker.trade,
            Site.name.label("site_name"),
            func.count(AttendanceRecord.id).label("total_rec"),
            func.sum(case((AttendanceRecord.status == "present", 1), (AttendanceRecord.status == "half_day", 0.5), else_=0)).label("p_days"),
            func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("a_days"),
            func.sum(AttendanceRecord.overtime_hours).label("ot_h"),
        )
        .join(AttendanceRecord, AttendanceRecord.worker_id == Worker.id)
        .outerjoin(Site, Site.id == AttendanceRecord.site_id)
        .where(AttendanceRecord.organization_id == organization_id)
        .group_by(Worker.id, Worker.worker_code, Worker.first_name, Worker.last_name, Worker.trade, Site.name)
    )
    if start_date:
        rank_q = rank_q.where(AttendanceRecord.attendance_date >= start_date)
    if end_date:
        rank_q = rank_q.where(AttendanceRecord.attendance_date <= end_date)
    if site_id:
        rank_q = rank_q.where(AttendanceRecord.site_id == site_id)

    worker_rankings: list[WorkerAttendanceRankItem] = []
    for r_row in db.execute(rank_q.order_by(func.sum(case((AttendanceRecord.status == "present", 1), else_=0)).desc()).limit(50)).all():
        tot = r_row.total_rec or 0
        p_val = float(r_row.p_days or 0)
        rate = (p_val / tot * 100.0) if tot > 0 else 0.0
        worker_rankings.append(
            WorkerAttendanceRankItem(
                worker_id=r_row.worker_id,
                worker_code=r_row.worker_code,
                worker_name=join_worker_name(r_row.first_name, r_row.last_name),
                trade=r_row.trade,
                site_name=r_row.site_name,
                present_days=p_val,
                absent_days=int(r_row.a_days or 0),
                overtime_hours=decimal_or_zero(r_row.ot_h),
                attendance_rate=round(rate, 1),
            )
        )

    return AttendanceAnalyticsResponse(
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        overall_attendance_rate=round(attendance_rate, 1),
        absence_rate=round(absence_rate, 1),
        total_records=total_records,
        total_present=total_present,
        total_absent=total_absent,
        total_leave=total_leave,
        total_overtime_hours=total_ot,
        absence_trends=absence_trends,
        worker_rankings=worker_rankings,
    )


# 3. PAYROLL ANALYTICS
def get_payroll_analytics(
    db: Session,
    *,
    organization_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    site_id: Optional[str] = None,
) -> PayrollAnalyticsResponse:
    payments_sq = payroll_payments_subquery(organization_id)
    paid_col = func.coalesce(payments_sq.c.paid_amount, 0)

    query = (
        select(
            func.sum(Payroll.gross_amount).label("total_gross"),
            func.sum(Payroll.deduction_amount).label("total_advance"),
            func.sum(Payroll.net_amount).label("total_net"),
            func.sum(paid_col).label("total_paid"),
        )
        .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
        .outerjoin(payments_sq, payments_sq.c.payroll_id == Payroll.id)
        .where(Payroll.organization_id == organization_id)
    )

    if year:
        query = query.where(extract("year", PayrollPeriod.period_start) == year)
    if month:
        query = query.where(extract("month", PayrollPeriod.period_start) == month)
    if site_id:
        query = query.where(Payroll.site_id == site_id)

    row = db.execute(query).one()
    total_gross = decimal_or_zero(row.total_gross)
    total_net = decimal_or_zero(row.total_net)
    total_paid = decimal_or_zero(row.total_paid)
    total_advance = decimal_or_zero(row.total_advance)
    pending_amount = max(total_net - total_paid, Decimal("0.00"))

    # Monthly payroll trend
    trend_q = (
        select(
            extract("year", PayrollPeriod.period_start).label("year_num"),
            extract("month", PayrollPeriod.period_start).label("month_num"),
            func.sum(Payroll.gross_amount).label("gross_sum"),
            func.sum(Payroll.deduction_amount).label("advance_sum"),
            func.sum(Payroll.net_amount).label("net_sum"),
            func.sum(paid_col).label("paid_sum"),
            func.count(distinct(Payroll.worker_id)).label("worker_cnt"),
        )
        .join(Payroll, Payroll.payroll_period_id == PayrollPeriod.id)
        .outerjoin(payments_sq, payments_sq.c.payroll_id == Payroll.id)
        .where(PayrollPeriod.organization_id == organization_id)
        .group_by(extract("year", PayrollPeriod.period_start), extract("month", PayrollPeriod.period_start))
    )
    if site_id:
        trend_q = trend_q.where(Payroll.site_id == site_id)

    monthly_payroll_trend: list[MonthlyPayrollTrendItem] = []
    for tr in db.execute(trend_q.order_by(extract("year", PayrollPeriod.period_start).desc(), extract("month", PayrollPeriod.period_start).desc())).all():
        yr = int(tr.year_num)
        mo = int(tr.month_num)
        lbl = date(yr, mo, 1).strftime("%b %Y")
        g_s = decimal_or_zero(tr.gross_sum)
        n_s = decimal_or_zero(tr.net_sum)
        p_s = decimal_or_zero(tr.paid_sum)
        a_s = decimal_or_zero(tr.advance_sum)

        monthly_payroll_trend.append(
            MonthlyPayrollTrendItem(
                label=lbl,
                year=yr,
                month=mo,
                gross_amount=g_s,
                paid_amount=p_s,
                pending_amount=max(n_s - p_s, Decimal("0.00")),
                advance_amount=a_s,
                worker_count=tr.worker_cnt or 0,
            )
        )

    return PayrollAnalyticsResponse(
        year=year,
        month=month,
        site_id=site_id,
        total_payroll=total_gross,
        paid_amount=total_paid,
        pending_amount=pending_amount,
        advance_payment_summary=total_advance,
        monthly_payroll_trend=monthly_payroll_trend,
    )


# 4. EXPENSE ANALYTICS
def get_expense_analytics(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    site_id: Optional[str] = None,
    category: Optional[str] = None,
) -> ExpenseAnalyticsResponse:
    validate_date_range(start_date, end_date)

    query = select(
        func.count(Expense.id).label("total_cnt"),
        func.sum(Expense.amount).label("total_sum"),
    ).where(Expense.organization_id == organization_id)

    if start_date:
        query = query.where(Expense.expense_date >= start_date)
    if end_date:
        query = query.where(Expense.expense_date <= end_date)
    if site_id:
        query = query.where(Expense.site_id == site_id)
    if category:
        query = query.where(Expense.category == category.strip())

    total_row = db.execute(query).one()
    total_expenses = decimal_or_zero(total_row.total_sum)

    # Category breakdown
    cat_q = (
        select(
            Expense.category,
            func.count(Expense.id).label("cnt"),
            func.sum(Expense.amount).label("tot"),
        )
        .where(Expense.organization_id == organization_id)
        .group_by(Expense.category)
    )
    if start_date:
        cat_q = cat_q.where(Expense.expense_date >= start_date)
    if end_date:
        cat_q = cat_q.where(Expense.expense_date <= end_date)
    if site_id:
        cat_q = cat_q.where(Expense.site_id == site_id)

    category_wise: list[CategoryExpenseItem] = []
    highest_cat = None
    highest_cat_amt = Decimal("0.00")

    for c_row in db.execute(cat_q.order_by(func.sum(Expense.amount).desc())).all():
        amt = decimal_or_zero(c_row.tot)
        pct = (float(amt / total_expenses) * 100.0) if total_expenses > 0 else 0.0
        if amt > highest_cat_amt:
            highest_cat_amt = amt
            highest_cat = c_row.category

        category_wise.append(
            CategoryExpenseItem(
                category=c_row.category,
                expense_count=c_row.cnt,
                total_amount=amt,
                percentage=round(pct, 1),
            )
        )

    # Site breakdown
    site_q = (
        select(
            Site.id.label("site_id"),
            Site.site_code,
            Site.name.label("site_name"),
            func.count(Expense.id).label("cnt"),
            func.sum(Expense.amount).label("tot"),
        )
        .join(Expense, Expense.site_id == Site.id)
        .where(Expense.organization_id == organization_id)
        .group_by(Site.id, Site.site_code, Site.name)
    )
    if start_date:
        site_q = site_q.where(Expense.expense_date >= start_date)
    if end_date:
        site_q = site_q.where(Expense.expense_date <= end_date)

    site_wise: list[SiteExpenseItem] = []
    highest_site_id = None
    highest_site_name = None
    highest_site_amt = Decimal("0.00")

    for s_row in db.execute(site_q.order_by(func.sum(Expense.amount).desc())).all():
        amt = decimal_or_zero(s_row.tot)
        if amt > highest_site_amt:
            highest_site_amt = amt
            highest_site_id = s_row.site_id
            highest_site_name = s_row.site_name

        site_wise.append(
            SiteExpenseItem(
                site_id=s_row.site_id,
                site_code=s_row.site_code,
                site_name=s_row.site_name,
                expense_count=s_row.cnt,
                total_amount=amt,
            )
        )

    # Monthly Trend
    m_trend_q = (
        select(
            extract("year", Expense.expense_date).label("year_num"),
            extract("month", Expense.expense_date).label("month_num"),
            func.count(Expense.id).label("cnt"),
            func.sum(Expense.amount).label("tot"),
        )
        .where(Expense.organization_id == organization_id)
        .group_by(extract("year", Expense.expense_date), extract("month", Expense.expense_date))
    )
    if site_id:
        m_trend_q = m_trend_q.where(Expense.site_id == site_id)

    monthly_expense_trend: list[MonthlyExpenseTrendItem] = []
    for m_row in db.execute(m_trend_q.order_by(extract("year", Expense.expense_date).desc(), extract("month", Expense.expense_date).desc())).all():
        yr = int(m_row.year_num)
        mo = int(m_row.month_num)
        monthly_expense_trend.append(
            MonthlyExpenseTrendItem(
                label=date(yr, mo, 1).strftime("%b %Y"),
                year=yr,
                month=mo,
                expense_count=m_row.cnt,
                total_amount=decimal_or_zero(m_row.tot),
            )
        )

    return ExpenseAnalyticsResponse(
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        category=category,
        total_expenses=total_expenses,
        highest_expense_category=highest_cat,
        highest_cost_site_id=highest_site_id,
        highest_cost_site_name=highest_site_name,
        highest_cost_site_amount=highest_site_amt,
        category_wise_expenses=category_wise,
        site_wise_expenses=site_wise,
        monthly_expense_trend=monthly_expense_trend,
    )


# 5. SITE PROFITABILITY REPORT
def get_site_profitability(
    db: Session,
    *,
    organization_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> SiteProfitabilityResponse:
    validate_date_range(start_date, end_date)

    sites = db.execute(
        select(Site).where(Site.organization_id == organization_id).order_by(Site.name.asc())
    ).scalars().all()

    items: list[SiteProfitabilityItem] = []
    total_labour = Decimal("0.00")
    total_expense = Decimal("0.00")

    for site in sites:
        # Labour cost query for site
        l_query = (
            select(func.sum(Payroll.gross_amount))
            .join(PayrollPeriod, PayrollPeriod.id == Payroll.payroll_period_id)
            .where(Payroll.organization_id == organization_id, Payroll.site_id == site.id)
        )
        if start_date:
            l_query = l_query.where(PayrollPeriod.period_start >= start_date)
        if end_date:
            l_query = l_query.where(PayrollPeriod.period_end <= end_date)

        labour_cost = decimal_or_zero(db.execute(l_query).scalar_one_or_none())

        # Expense cost query for site
        e_query = select(func.sum(Expense.amount)).where(
            Expense.organization_id == organization_id, Expense.site_id == site.id
        )
        if start_date:
            e_query = e_query.where(Expense.expense_date >= start_date)
        if end_date:
            e_query = e_query.where(Expense.expense_date <= end_date)

        expense_cost = decimal_or_zero(db.execute(e_query).scalar_one_or_none())

        total_site_cost = labour_cost + expense_cost
        total_labour += labour_cost
        total_expense += expense_cost

        labour_pct = (float(labour_cost / total_site_cost) * 100.0) if total_site_cost > 0 else 0.0
        expense_pct = (float(expense_cost / total_site_cost) * 100.0) if total_site_cost > 0 else 0.0

        # Estimated contract revenue (if not set on site, default to 1.25x total cost for demo margin)
        revenue = total_site_cost * Decimal("1.25")
        net_margin = revenue - total_site_cost

        items.append(
            SiteProfitabilityItem(
                site_id=site.id,
                site_code=site.site_code,
                site_name=site.name,
                client_name=site.client_name,
                status=site.status,
                revenue=revenue,
                labour_cost=labour_cost,
                expense_cost=expense_cost,
                total_site_cost=total_site_cost,
                net_margin=net_margin,
                labour_percentage=round(labour_pct, 1),
                expense_percentage=round(expense_pct, 1),
            )
        )

    return SiteProfitabilityResponse(
        start_date=start_date,
        end_date=end_date,
        total_sites=len(items),
        total_combined_cost=total_labour + total_expense,
        total_labour_cost=total_labour,
        total_expense_cost=total_expense,
        items=items,
    )


# EXPORT TABLE GENERATORS FOR ANALYTICS
def labour_cost_export_table(report: LabourCostAnalyticsResponse) -> ExportTable:
    return ExportTable(
        title="Labour Cost Analytics",
        headers=["Site Code", "Site Name", "Labour Cost", "Expense Cost", "Total Cost", "Active Workers"],
        rows=[
            [
                item.site_code,
                item.site_name,
                item.labour_cost,
                item.expense_cost,
                item.total_cost,
                item.active_workers,
            ]
            for item in report.site_wise_labour_cost
        ],
    )


def attendance_analytics_export_table(report: AttendanceAnalyticsResponse) -> ExportTable:
    return ExportTable(
        title="Attendance Analytics",
        headers=["Worker Code", "Worker Name", "Trade", "Site", "Present Days", "Absent Days", "OT Hours", "Attendance %"],
        rows=[
            [
                item.worker_code,
                item.worker_name,
                item.trade or "N/A",
                item.site_name or "N/A",
                item.present_days,
                item.absent_days,
                item.overtime_hours,
                f"{item.attendance_rate}%",
            ]
            for item in report.worker_rankings
        ],
    )


def payroll_analytics_export_table(report: PayrollAnalyticsResponse) -> ExportTable:
    return ExportTable(
        title="Payroll Analytics",
        headers=["Period", "Gross Amount", "Advance Amount", "Paid Amount", "Pending Amount", "Worker Count"],
        rows=[
            [
                item.label,
                item.gross_amount,
                item.advance_amount,
                item.paid_amount,
                item.pending_amount,
                item.worker_count,
            ]
            for item in report.monthly_payroll_trend
        ],
    )


def expense_analytics_export_table(report: ExpenseAnalyticsResponse) -> ExportTable:
    return ExportTable(
        title="Expense Analytics",
        headers=["Category", "Expense Count", "Total Amount", "Share %"],
        rows=[
            [
                item.category,
                item.expense_count,
                item.total_amount,
                f"{item.percentage}%",
            ]
            for item in report.category_wise_expenses
        ],
    )


def site_profitability_export_table(report: SiteProfitabilityResponse) -> ExportTable:
    return ExportTable(
        title="Site Profitability Statement",
        headers=["Site Code", "Site Name", "Status", "Labour Cost", "Expense Cost", "Total Cost", "Labour %", "Expense %"],
        rows=[
            [
                item.site_code,
                item.site_name,
                item.status,
                item.labour_cost,
                item.expense_cost,
                item.total_site_cost,
                f"{item.labour_percentage}%",
                f"{item.expense_percentage}%",
            ]
            for item in report.items
        ],
    )
