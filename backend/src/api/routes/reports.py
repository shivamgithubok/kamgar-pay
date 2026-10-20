from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.reports import (
    AttendanceSummaryReportResponse,
    MonthlyPayrollReportResponse,
    SiteExpenseReportResponse,
    WorkerPayrollReportResponse,
)
from src.services.report_exports import ExportTable, export_table
from src.services.reports import (
    attendance_summary_export_table,
    get_attendance_summary_report,
    get_monthly_payroll_report,
    get_site_wise_expense_report,
    get_worker_wise_payroll_report,
    monthly_payroll_export_table,
    site_expense_export_table,
    worker_payroll_export_table,
)


router = APIRouter()


def build_export_response(table: ExportTable, file_format: str) -> Response:
    try:
        content, media_type, filename = export_table(table, file_format)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/worker-wise-payroll", response_model=WorkerPayrollReportResponse)
def worker_wise_payroll_report_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    payroll_period_id: Optional[str] = Query(default=None),
    worker_id: Optional[str] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> WorkerPayrollReportResponse:
    return get_worker_wise_payroll_report(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        payroll_period_id=payroll_period_id,
        worker_id=worker_id,
        site_id=site_id,
    )


@router.get("/worker-wise-payroll/export")
def export_worker_wise_payroll_report_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    payroll_period_id: Optional[str] = Query(default=None),
    worker_id: Optional[str] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_worker_wise_payroll_report(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        payroll_period_id=payroll_period_id,
        worker_id=worker_id,
        site_id=site_id,
    )
    return build_export_response(worker_payroll_export_table(report), file_format)


@router.get("/site-wise-expense", response_model=SiteExpenseReportResponse)
def site_wise_expense_report_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None, max_length=50),
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteExpenseReportResponse:
    return get_site_wise_expense_report(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        category=category,
        status_filter=status_filter,
    )


@router.get("/site-wise-expense/export")
def export_site_wise_expense_report_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None, max_length=50),
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_site_wise_expense_report(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        category=category,
        status_filter=status_filter,
    )
    return build_export_response(site_expense_export_table(report), file_format)


@router.get("/attendance-summary", response_model=AttendanceSummaryReportResponse)
def attendance_summary_report_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    worker_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> AttendanceSummaryReportResponse:
    return get_attendance_summary_report(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        worker_id=worker_id,
    )


@router.get("/attendance-summary/export")
def export_attendance_summary_report_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    worker_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_attendance_summary_report(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        worker_id=worker_id,
    )
    return build_export_response(attendance_summary_export_table(report), file_format)


@router.get("/monthly-payroll", response_model=MonthlyPayrollReportResponse)
def monthly_payroll_report_route(
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    payroll_period_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> MonthlyPayrollReportResponse:
    return get_monthly_payroll_report(
        db,
        organization_id=current_user.organization_id,
        year=year,
        month=month,
        payroll_period_id=payroll_period_id,
    )


@router.get("/monthly-payroll/export")
def export_monthly_payroll_report_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    payroll_period_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_monthly_payroll_report(
        db,
        organization_id=current_user.organization_id,
        year=year,
        month=month,
        payroll_period_id=payroll_period_id,
    )
    return build_export_response(monthly_payroll_export_table(report), file_format)


# ---------------------------------------------------------
# ADVANCED ANALYTICS ENDPOINTS
# ---------------------------------------------------------

from src.schemas.analytics import (
    AttendanceAnalyticsResponse,
    ExpenseAnalyticsResponse,
    LabourCostAnalyticsResponse,
    PayrollAnalyticsResponse,
    SiteProfitabilityResponse,
)
from src.services.analytics import (
    attendance_analytics_export_table,
    expense_analytics_export_table,
    get_attendance_analytics,
    get_expense_analytics,
    get_labour_cost_analytics,
    get_payroll_analytics,
    get_site_profitability,
    labour_cost_export_table,
    payroll_analytics_export_table,
    site_profitability_export_table,
)


@router.get("/labour-cost", response_model=LabourCostAnalyticsResponse)
def labour_cost_analytics_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> LabourCostAnalyticsResponse:
    return get_labour_cost_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
    )


@router.get("/labour-cost/export")
def export_labour_cost_analytics_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_labour_cost_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
    )
    return build_export_response(labour_cost_export_table(report), file_format)


@router.get("/attendance-analytics", response_model=AttendanceAnalyticsResponse)
def attendance_analytics_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> AttendanceAnalyticsResponse:
    return get_attendance_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
    )


@router.get("/attendance-analytics/export")
def export_attendance_analytics_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_attendance_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
    )
    return build_export_response(attendance_analytics_export_table(report), file_format)


@router.get("/payroll-analytics", response_model=PayrollAnalyticsResponse)
def payroll_analytics_route(
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> PayrollAnalyticsResponse:
    return get_payroll_analytics(
        db,
        organization_id=current_user.organization_id,
        year=year,
        month=month,
        site_id=site_id,
    )


@router.get("/payroll-analytics/export")
def export_payroll_analytics_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_payroll_analytics(
        db,
        organization_id=current_user.organization_id,
        year=year,
        month=month,
        site_id=site_id,
    )
    return build_export_response(payroll_analytics_export_table(report), file_format)


@router.get("/expense-analytics", response_model=ExpenseAnalyticsResponse)
def expense_analytics_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> ExpenseAnalyticsResponse:
    return get_expense_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        category=category,
    )


@router.get("/expense-analytics/export")
def export_expense_analytics_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_expense_analytics(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        category=category,
    )
    return build_export_response(expense_analytics_export_table(report), file_format)


@router.get("/site-profitability", response_model=SiteProfitabilityResponse)
def site_profitability_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteProfitabilityResponse:
    return get_site_profitability(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/site-profitability/export")
def export_site_profitability_route(
    file_format: str = Query(default="excel", alias="format", pattern="^(pdf|excel|xls)$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    report = get_site_profitability(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    return build_export_response(site_profitability_export_table(report), file_format)

