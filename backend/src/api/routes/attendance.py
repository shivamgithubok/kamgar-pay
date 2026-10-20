from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.attendance import (
    AttendanceResponse,
    BulkAttendanceRequest,
    BulkAttendanceResponse,
    MarkAttendanceRequest,
    MonthlyAttendanceReportResponse,
    OvertimeUpdateRequest,
)
from src.services.attendance import (
    bulk_mark_attendance,
    get_attendance_by_id,
    get_monthly_attendance_report,
    list_attendance,
    mark_daily_attendance,
    mark_overtime_hours,
    to_attendance_response,
)


router = APIRouter()


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def mark_daily_attendance_route(
    payload: MarkAttendanceRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> AttendanceResponse:
    attendance, created = mark_daily_attendance(
        db,
        organization_id=current_user.organization_id,
        captured_by_user_id=current_user.id,
        payload=payload,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return to_attendance_response(attendance)


@router.post("/bulk", response_model=BulkAttendanceResponse)
def bulk_attendance_entry_route(
    payload: BulkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> BulkAttendanceResponse:
    return bulk_mark_attendance(
        db,
        organization_id=current_user.organization_id,
        captured_by_user_id=current_user.id,
        payload=payload,
    )


@router.get("/report/monthly", response_model=MonthlyAttendanceReportResponse)
def monthly_attendance_report_route(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    site_id: Optional[str] = Query(default=None),
    worker_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> MonthlyAttendanceReportResponse:
    return get_monthly_attendance_report(
        db,
        organization_id=current_user.organization_id,
        year=year,
        month=month,
        site_id=site_id,
        worker_id=worker_id,
    )


@router.get("", response_model=list[AttendanceResponse])
@router.get("/", response_model=list[AttendanceResponse], include_in_schema=False)
def list_attendance_route(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    site_id: Optional[str] = Query(default=None),
    worker_id: Optional[str] = Query(default=None),
    approval_status: Optional[str] = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> list[AttendanceResponse]:
    records = list_attendance(
        db,
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        worker_id=worker_id,
        approval_status=approval_status,
    )
    return [to_attendance_response(record) for record in records]


@router.get("/{attendance_id}", response_model=AttendanceResponse)
def get_attendance_route(
    attendance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> AttendanceResponse:
    attendance = get_attendance_by_id(
        db,
        organization_id=current_user.organization_id,
        attendance_id=attendance_id,
        required=True,
    )
    return to_attendance_response(attendance)


@router.patch("/{attendance_id}/overtime", response_model=AttendanceResponse)
def mark_overtime_hours_route(
    attendance_id: str,
    payload: OvertimeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> AttendanceResponse:
    attendance = mark_overtime_hours(
        db,
        organization_id=current_user.organization_id,
        attendance_id=attendance_id,
        payload=payload,
    )
    return to_attendance_response(attendance)
