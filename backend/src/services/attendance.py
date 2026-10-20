from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.database.models import AttendanceRecord, Site, Worker
from src.schemas.attendance import (
    AttendanceResponse,
    BulkAttendanceRequest,
    BulkAttendanceResponse,
    MarkAttendanceRequest,
    MonthlyAttendanceDay,
    MonthlyAttendanceReportResponse,
    MonthlyAttendanceWorkerReport,
    OvertimeUpdateRequest,
)
from src.services.workers import join_name


REGULAR_HOURS_BY_STATUS = {
    "present": Decimal("8.00"),
    "half_day": Decimal("4.00"),
    "absent": Decimal("0.00"),
    "leave": Decimal("0.00"),
    "weekly_off": Decimal("0.00"),
}
PAID_DAYS_BY_STATUS = {
    "present": Decimal("1.00"),
    "half_day": Decimal("0.50"),
    "absent": Decimal("0.00"),
    "leave": Decimal("0.00"),
    "weekly_off": Decimal("0.00"),
}


def base_attendance_query() -> Select[tuple[AttendanceRecord]]:
    return select(AttendanceRecord).options(
        selectinload(AttendanceRecord.worker),
        selectinload(AttendanceRecord.site),
    )


def get_attendance_by_id(
    db: Session,
    *,
    organization_id: str,
    attendance_id: str,
    required: bool = False,
) -> AttendanceRecord | None:
    attendance = db.execute(
        base_attendance_query().where(
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.id == attendance_id,
        )
    ).scalar_one_or_none()
    if attendance is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    return attendance


def get_existing_attendance(
    db: Session,
    *,
    organization_id: str,
    worker_id: str,
    attendance_date: date,
) -> AttendanceRecord | None:
    return db.execute(
        base_attendance_query().where(
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.worker_id == worker_id,
            AttendanceRecord.attendance_date == attendance_date,
        )
    ).scalar_one_or_none()


def validate_worker_and_site(
    db: Session,
    *,
    organization_id: str,
    worker_id: str,
    site_id: str,
    attendance_date: date,
) -> tuple[Worker, Site]:
    worker = db.execute(
        select(Worker).where(
            Worker.organization_id == organization_id,
            Worker.id == worker_id,
        )
    ).scalar_one_or_none()
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    if worker.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Worker is not active")
    if attendance_date < worker.joined_on:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance date cannot be before worker joining date",
        )
    if worker.exited_on is not None and attendance_date > worker.exited_on:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance date cannot be after worker exit date",
        )

    site = db.execute(
        select(Site).where(
            Site.organization_id == organization_id,
            Site.id == site_id,
        )
    ).scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if site.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site is not active")
    if attendance_date < site.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance date cannot be before site start date",
        )
    if site.end_date is not None and attendance_date > site.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance date cannot be after site end date",
        )

    return worker, site


def ensure_attendance_editable(attendance: AttendanceRecord) -> None:
    if attendance.payroll_locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance record is locked by payroll and cannot be edited",
        )


def apply_attendance_fields(
    attendance: AttendanceRecord,
    *,
    payload: MarkAttendanceRequest,
    captured_by_user_id: str,
) -> None:
    attendance.worker_id = payload.worker_id
    attendance.site_id = payload.site_id
    attendance.attendance_date = payload.attendance_date
    attendance.status = payload.status
    attendance.regular_hours = REGULAR_HOURS_BY_STATUS[payload.status]
    attendance.overtime_hours = payload.ot_hours
    attendance.remarks = payload.remarks
    attendance.captured_by_user_id = captured_by_user_id
    attendance.approved_by_user_id = None
    attendance.approval_status = "draft"


def mark_daily_attendance(
    db: Session,
    *,
    organization_id: str,
    captured_by_user_id: str,
    payload: MarkAttendanceRequest,
    commit: bool = True,
) -> tuple[AttendanceRecord, bool]:
    validate_worker_and_site(
        db,
        organization_id=organization_id,
        worker_id=payload.worker_id,
        site_id=payload.site_id,
        attendance_date=payload.attendance_date,
    )

    attendance = get_existing_attendance(
        db,
        organization_id=organization_id,
        worker_id=payload.worker_id,
        attendance_date=payload.attendance_date,
    )
    created = attendance is None

    if attendance is None:
        attendance = AttendanceRecord(
            organization_id=organization_id,
            captured_by_user_id=captured_by_user_id,
            worker_id=payload.worker_id,
            site_id=payload.site_id,
            attendance_date=payload.attendance_date,
            status=payload.status,
        )
    else:
        ensure_attendance_editable(attendance)

    apply_attendance_fields(attendance, payload=payload, captured_by_user_id=captured_by_user_id)

    try:
        db.add(attendance)
        db.flush()
        if commit:
            db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance could not be saved because a record already exists for this worker and date",
        ) from exc

    if commit:
        attendance = get_attendance_by_id(
            db,
            organization_id=organization_id,
            attendance_id=attendance.id,
            required=True,
        )
    return attendance, created


def mark_overtime_hours(
    db: Session,
    *,
    organization_id: str,
    attendance_id: str,
    payload: OvertimeUpdateRequest,
) -> AttendanceRecord:
    attendance = get_attendance_by_id(
        db,
        organization_id=organization_id,
        attendance_id=attendance_id,
        required=True,
    )
    ensure_attendance_editable(attendance)
    attendance.overtime_hours = payload.ot_hours
    if "remarks" in payload.model_fields_set:
        attendance.remarks = payload.remarks
    attendance.approved_by_user_id = None
    attendance.approval_status = "draft"

    db.add(attendance)
    db.commit()
    return get_attendance_by_id(
        db,
        organization_id=organization_id,
        attendance_id=attendance.id,
        required=True,
    )


def bulk_mark_attendance(
    db: Session,
    *,
    organization_id: str,
    captured_by_user_id: str,
    payload: BulkAttendanceRequest,
) -> BulkAttendanceResponse:
    seen_keys: set[tuple[str, date]] = set()
    for entry in payload.entries:
        key = (entry.worker_id, entry.attendance_date)
        if key in seen_keys:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Bulk payload contains duplicate worker/date entries",
            )
        seen_keys.add(key)

    created_count = 0
    updated_count = 0
    records: list[AttendanceRecord] = []

    try:
        for entry in payload.entries:
            attendance, created = mark_daily_attendance(
                db,
                organization_id=organization_id,
                captured_by_user_id=captured_by_user_id,
                payload=entry,
                commit=False,
            )
            records.append(attendance)
            if created:
                created_count += 1
            else:
                updated_count += 1
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bulk attendance could not be saved because one or more records conflict",
        ) from exc

    refreshed_records = [
        get_attendance_by_id(
            db,
            organization_id=organization_id,
            attendance_id=record.id,
            required=True,
        )
        for record in records
    ]
    return BulkAttendanceResponse(
        created_count=created_count,
        updated_count=updated_count,
        items=[to_attendance_response(record) for record in refreshed_records],
    )


def list_attendance(
    db: Session,
    *,
    organization_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    site_id: str | None = None,
    worker_id: str | None = None,
    approval_status: str | None = None,
) -> list[AttendanceRecord]:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date",
        )

    query = base_attendance_query().where(AttendanceRecord.organization_id == organization_id)
    if start_date is not None:
        query = query.where(AttendanceRecord.attendance_date >= start_date)
    if end_date is not None:
        query = query.where(AttendanceRecord.attendance_date <= end_date)
    if site_id is not None:
        query = query.where(AttendanceRecord.site_id == site_id)
    if worker_id is not None:
        query = query.where(AttendanceRecord.worker_id == worker_id)
    if approval_status is not None:
        query = query.where(AttendanceRecord.approval_status == approval_status.strip().lower())

    return list(
        db.execute(
            query.order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.created_at.desc())
        ).scalars().all()
    )


def get_monthly_attendance_report(
    db: Session,
    *,
    organization_id: str,
    year: int,
    month: int,
    site_id: str | None = None,
    worker_id: str | None = None,
) -> MonthlyAttendanceReportResponse:
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    records = list_attendance(
        db,
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        worker_id=worker_id,
    )

    grouped: dict[str, list[AttendanceRecord]] = {}
    for record in records:
        grouped.setdefault(record.worker_id, []).append(record)

    worker_reports: list[MonthlyAttendanceWorkerReport] = []
    total_paid_days = Decimal("0.00")
    total_regular_hours = Decimal("0.00")
    total_ot_hours = Decimal("0.00")

    for worker_records in grouped.values():
        worker_records.sort(key=lambda item: item.attendance_date)
        first_record = worker_records[0]
        status_counts = {
            "present": 0,
            "absent": 0,
            "half_day": 0,
            "leave": 0,
            "weekly_off": 0,
        }
        paid_days = Decimal("0.00")
        regular_hours = Decimal("0.00")
        ot_hours = Decimal("0.00")
        days: list[MonthlyAttendanceDay] = []

        for record in worker_records:
            status_counts[record.status] = status_counts.get(record.status, 0) + 1
            paid_days += PAID_DAYS_BY_STATUS.get(record.status, Decimal("0.00"))
            regular_hours += record.regular_hours
            ot_hours += record.overtime_hours
            days.append(
                MonthlyAttendanceDay(
                    attendance_id=record.id,
                    attendance_date=record.attendance_date,
                    site_id=record.site_id,
                    site_name=record.site.name,
                    status=record.status,
                    regular_hours=record.regular_hours,
                    ot_hours=record.overtime_hours,
                    approval_status=record.approval_status,
                    payroll_locked=record.payroll_locked,
                )
            )

        total_paid_days += paid_days
        total_regular_hours += regular_hours
        total_ot_hours += ot_hours
        worker_reports.append(
            MonthlyAttendanceWorkerReport(
                worker_id=first_record.worker_id,
                worker_code=first_record.worker.worker_code,
                worker_name=join_name(first_record.worker),
                present_days=Decimal(status_counts["present"]),
                absent_days=status_counts["absent"],
                half_days=status_counts["half_day"],
                leave_days=status_counts["leave"],
                weekly_off_days=status_counts["weekly_off"],
                paid_days=paid_days,
                regular_hours=regular_hours,
                ot_hours=ot_hours,
                total_records=len(worker_records),
                days=days,
            )
        )

    worker_reports.sort(key=lambda item: item.worker_name.lower())
    return MonthlyAttendanceReportResponse(
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        site_id=site_id,
        worker_id=worker_id,
        total_workers=len(worker_reports),
        total_records=len(records),
        total_paid_days=total_paid_days,
        total_regular_hours=total_regular_hours,
        total_ot_hours=total_ot_hours,
        workers=worker_reports,
    )


def to_attendance_response(attendance: AttendanceRecord) -> AttendanceResponse:
    return AttendanceResponse(
        id=attendance.id,
        organization_id=attendance.organization_id,
        worker_id=attendance.worker_id,
        worker_code=attendance.worker.worker_code,
        worker_name=join_name(attendance.worker),
        site_id=attendance.site_id,
        site_name=attendance.site.name,
        attendance_date=attendance.attendance_date,
        status=attendance.status,
        regular_hours=attendance.regular_hours,
        ot_hours=attendance.overtime_hours,
        approval_status=attendance.approval_status,
        payroll_locked=attendance.payroll_locked,
        remarks=attendance.remarks,
        captured_by_user_id=attendance.captured_by_user_id,
        approved_by_user_id=attendance.approved_by_user_id,
        created_at=attendance.created_at,
        updated_at=attendance.updated_at,
    )
