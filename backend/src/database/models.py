from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, utcnow


def new_id() -> str:
    return str(uuid4())


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Calcutta", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    workers: Mapped[list["Worker"]] = relationship(back_populates="organization")
    sites: Mapped[list["Site"]] = relationship(back_populates="organization")
    payroll_periods: Mapped[list["PayrollPeriod"]] = relationship(back_populates="organization")
    payrolls: Mapped[list["Payroll"]] = relationship(back_populates="organization")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="organization")
    documents: Mapped[list["Document"]] = relationship(back_populates="organization")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="organization")
    payments: Mapped[list["Payment"]] = relationship(back_populates="organization")

    __table_args__ = (
        UniqueConstraint("code", name="uq_organizations_code"),
        Index("ix_organizations_status_name", "status", "name"),
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped[Optional["Organization"]] = relationship()
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_roles_organization_code"),
        Index("ix_roles_organization_name", "organization_id", "name"),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="users")
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    managed_sites: Mapped[list["Site"]] = relationship(
        back_populates="site_manager",
        foreign_keys="Site.site_manager_user_id",
    )
    created_attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="captured_by_user",
        foreign_keys="AttendanceRecord.captured_by_user_id",
    )
    approved_attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="approved_by_user",
        foreign_keys="AttendanceRecord.approved_by_user_id",
    )
    submitted_expenses: Mapped[list["Expense"]] = relationship(
        back_populates="submitted_by_user",
        foreign_keys="Expense.submitted_by_user_id",
    )
    approved_expenses: Mapped[list["Expense"]] = relationship(
        back_populates="approved_by_user",
        foreign_keys="Expense.approved_by_user_id",
    )
    uploaded_documents: Mapped[list["Document"]] = relationship(back_populates="uploaded_by_user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    initiated_payroll_periods: Mapped[list["PayrollPeriod"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="PayrollPeriod.created_by_user_id",
    )
    payments_processed: Mapped[list["Payment"]] = relationship(
        back_populates="processed_by_user",
        foreign_keys="Payment.processed_by_user_id",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_organization_email"),
        UniqueConstraint("organization_id", "phone", name="uq_users_organization_phone"),
        Index("ix_users_organization_status", "organization_id", "status"),
        Index("ix_users_organization_name", "organization_id", "full_name"),
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("ix_user_roles_role_id", "role_id"),
    )


class Site(TimestampMixin, Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_manager_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    site_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    project_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="sites")
    site_manager: Mapped[Optional["User"]] = relationship(
        back_populates="managed_sites",
        foreign_keys=[site_manager_user_id],
    )
    worker_assignments: Mapped[list["WorkerSiteAssignment"]] = relationship(
        back_populates="site",
        cascade="all, delete-orphan",
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="site")
    payrolls: Mapped[list["Payroll"]] = relationship(back_populates="site")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="site")
    documents: Mapped[list["DocumentLink"]] = relationship(back_populates="site")
    payments: Mapped[list["Payment"]] = relationship(back_populates="site")
    assigned_workers: Mapped[list["Worker"]] = relationship(
        back_populates="assigned_site",
        foreign_keys="Worker.assigned_site_id",
    )

    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="site_dates_valid"),
        UniqueConstraint("organization_id", "site_code", name="uq_sites_organization_site_code"),
        Index("ix_sites_organization_status", "organization_id", "status"),
        Index("ix_sites_organization_name", "organization_id", "name"),
    )


class Worker(TimestampMixin, Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_site_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"),
        nullable=True,
    )
    worker_code: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    trade: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(30), default="daily_wage", nullable=False)
    wage_type: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)
    default_wage_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    pf_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    bank_account_holder_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(34), nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bank_account_masked: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    id_document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    joined_on: Mapped[date] = mapped_column(Date, nullable=False)
    exited_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="workers")
    assigned_site: Mapped[Optional["Site"]] = relationship(
        back_populates="assigned_workers",
        foreign_keys=[assigned_site_id],
    )
    assignments: Mapped[list["WorkerSiteAssignment"]] = relationship(
        back_populates="worker",
        cascade="all, delete-orphan",
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="worker")
    payrolls: Mapped[list["Payroll"]] = relationship(back_populates="worker")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="worker")
    documents: Mapped[list["DocumentLink"]] = relationship(back_populates="worker")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="worker")
    payments: Mapped[list["Payment"]] = relationship(back_populates="worker")

    __table_args__ = (
        CheckConstraint("default_wage_rate >= 0", name="worker_default_wage_rate_non_negative"),
        CheckConstraint("overtime_rate >= 0", name="worker_overtime_rate_non_negative"),
        CheckConstraint("pf_rate_percent >= 0 AND pf_rate_percent <= 100", name="worker_pf_rate_percent_valid"),
        CheckConstraint("exited_on IS NULL OR exited_on >= joined_on", name="worker_dates_valid"),
        UniqueConstraint("organization_id", "worker_code", name="uq_workers_organization_worker_code"),
        UniqueConstraint("organization_id", "aadhaar_number", name="uq_workers_organization_aadhaar_number"),
        UniqueConstraint("organization_id", "id_document_number", name="uq_workers_organization_id_document"),
        Index("ix_workers_organization_status", "organization_id", "status"),
        Index("ix_workers_organization_phone", "organization_id", "phone"),
        Index("ix_workers_organization_name", "organization_id", "first_name", "last_name"),
        Index("ix_workers_organization_assigned_site", "organization_id", "assigned_site_id"),
        Index("ix_workers_organization_trade", "organization_id", "trade"),
    )


class WorkerSiteAssignment(TimestampMixin, Base):
    __tablename__ = "worker_site_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    assigned_from: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    worker: Mapped["Worker"] = relationship(back_populates="assignments")
    site: Mapped["Site"] = relationship(back_populates="worker_assignments")

    __table_args__ = (
        CheckConstraint("assigned_to IS NULL OR assigned_to >= assigned_from", name="assignment_dates_valid"),
        UniqueConstraint(
            "worker_id",
            "site_id",
            "assigned_from",
            name="uq_worker_site_assignments_worker_site_from",
        ),
        Index("ix_worker_site_assignments_site_status", "site_id", "status"),
        Index("ix_worker_site_assignments_worker_status", "worker_id", "status"),
        Index("ix_worker_site_assignments_organization_primary", "organization_id", "is_primary"),
    )


class AttendanceRecord(TimestampMixin, Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    captured_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    check_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    check_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    payroll_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    worker: Mapped["Worker"] = relationship(back_populates="attendance_records")
    site: Mapped["Site"] = relationship(back_populates="attendance_records")
    captured_by_user: Mapped["User"] = relationship(
        back_populates="created_attendance_records",
        foreign_keys=[captured_by_user_id],
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="approved_attendance_records",
        foreign_keys=[approved_by_user_id],
    )

    __table_args__ = (
        CheckConstraint("regular_hours >= 0", name="attendance_regular_hours_non_negative"),
        CheckConstraint("overtime_hours >= 0", name="attendance_overtime_hours_non_negative"),
        UniqueConstraint(
            "organization_id",
            "worker_id",
            "attendance_date",
            name="uq_attendance_records_organization_worker_date",
        ),
        Index("ix_attendance_records_site_date", "site_id", "attendance_date"),
        Index("ix_attendance_records_organization_approval_date", "organization_id", "approval_status", "attendance_date"),
        Index("ix_attendance_records_organization_payroll_locked", "organization_id", "payroll_locked", "attendance_date"),
        Index("ix_attendance_records_worker_date", "worker_id", "attendance_date"),
    )


class PayrollPeriod(TimestampMixin, Base):
    __tablename__ = "payroll_periods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    pay_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="payroll_periods")
    created_by_user: Mapped["User"] = relationship(
        back_populates="initiated_payroll_periods",
        foreign_keys=[created_by_user_id],
    )
    payrolls: Mapped[list["Payroll"]] = relationship(back_populates="payroll_period")

    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="payroll_period_dates_valid"),
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_payroll_periods_organization_name",
        ),
        Index("ix_payroll_periods_organization_status", "organization_id", "status"),
        Index("ix_payroll_periods_organization_dates", "organization_id", "period_start", "period_end"),
    )


class Payroll(TimestampMixin, Base):
    __tablename__ = "payrolls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    payroll_period_id: Mapped[str] = mapped_column(
        ForeignKey("payroll_periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[Optional[str]] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    attendance_days: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0, nullable=False)
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0, nullable=False)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0, nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    deduction_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    pf_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="payrolls")
    payroll_period: Mapped["PayrollPeriod"] = relationship(back_populates="payrolls")
    worker: Mapped["Worker"] = relationship(back_populates="payrolls")
    site: Mapped[Optional["Site"]] = relationship(back_populates="payrolls")
    payments: Mapped[list["Payment"]] = relationship(back_populates="payroll")

    __table_args__ = (
        CheckConstraint("attendance_days >= 0", name="payroll_attendance_days_non_negative"),
        CheckConstraint("regular_hours >= 0", name="payroll_regular_hours_non_negative"),
        CheckConstraint("overtime_hours >= 0", name="payroll_overtime_hours_non_negative"),
        CheckConstraint("gross_amount >= 0", name="payroll_gross_amount_non_negative"),
        CheckConstraint("deduction_amount >= 0", name="payroll_deduction_amount_non_negative"),
        CheckConstraint("pf_amount >= 0", name="payroll_pf_amount_non_negative"),
        CheckConstraint("net_amount >= 0", name="payroll_net_amount_non_negative"),
        UniqueConstraint(
            "organization_id",
            "payroll_period_id",
            "worker_id",
            name="uq_payrolls_organization_period_worker",
        ),
        Index("ix_payrolls_period_status", "payroll_period_id", "status"),
        Index("ix_payrolls_organization_worker", "organization_id", "worker_id"),
        Index("ix_payrolls_organization_site", "organization_id", "site_id"),
    )


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    payroll_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("payrolls.id", ondelete="SET NULL"),
        nullable=True,
    )
    worker_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
    )
    site_id: Mapped[Optional[str]] = mapped_column(ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    processed_by_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_type: Mapped[str] = mapped_column(String(30), default="payroll", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), default="bank_transfer", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="payments")
    payroll: Mapped[Optional["Payroll"]] = relationship(back_populates="payments")
    worker: Mapped[Optional["Worker"]] = relationship(back_populates="payments")
    site: Mapped[Optional["Site"]] = relationship(back_populates="payments")
    processed_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="payments_processed",
        foreign_keys=[processed_by_user_id],
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="payment_amount_non_negative"),
        UniqueConstraint(
            "organization_id",
            "external_reference",
            name="uq_payments_organization_external_reference",
        ),
        Index("ix_payments_organization_status_date", "organization_id", "status", "payment_date"),
        Index("ix_payments_payroll_id", "payroll_id"),
        Index("ix_payments_worker_date", "worker_id", "payment_date"),
    )


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    worker_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(20), default="cash", nullable=False)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    receipt_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="expenses")
    site: Mapped["Site"] = relationship(back_populates="expenses")
    worker: Mapped[Optional["Worker"]] = relationship(back_populates="expenses")
    submitted_by_user: Mapped["User"] = relationship(
        back_populates="submitted_expenses",
        foreign_keys=[submitted_by_user_id],
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="approved_expenses",
        foreign_keys=[approved_by_user_id],
    )
    documents: Mapped[list["DocumentLink"]] = relationship(back_populates="expense")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="expense_amount_non_negative"),
        Index("ix_expenses_site_date", "site_id", "expense_date"),
        Index("ix_expenses_organization_status_date", "organization_id", "status", "expense_date"),
        Index("ix_expenses_organization_category_date", "organization_id", "category", "expense_date"),
    )


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="documents")
    uploaded_by_user: Mapped["User"] = relationship(back_populates="uploaded_documents")
    links: Mapped[list["DocumentLink"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="document_file_size_non_negative"),
        CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="document_validity_dates"),
        Index("ix_documents_organization_category", "organization_id", "category"),
        Index("ix_documents_organization_valid_to", "organization_id", "valid_to"),
        Index("ix_documents_checksum", "checksum"),
    )


class DocumentLink(TimestampMixin, Base):
    __tablename__ = "document_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    worker_id: Mapped[Optional[str]] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), nullable=True)
    site_id: Mapped[Optional[str]] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    expense_id: Mapped[Optional[str]] = mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"), nullable=True)
    payroll_id: Mapped[Optional[str]] = mapped_column(ForeignKey("payrolls.id", ondelete="CASCADE"), nullable=True)
    tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="links")
    worker: Mapped[Optional["Worker"]] = relationship(back_populates="documents")
    site: Mapped[Optional["Site"]] = relationship(back_populates="documents")
    expense: Mapped[Optional["Expense"]] = relationship(back_populates="documents")
    payroll: Mapped[Optional["Payroll"]] = relationship()

    __table_args__ = (
        CheckConstraint(
            "(worker_id IS NOT NULL) + (site_id IS NOT NULL) + (expense_id IS NOT NULL) + (payroll_id IS NOT NULL) >= 1",
            name="document_link_has_target",
        ),
        Index("ix_document_links_document_id", "document_id"),
        Index("ix_document_links_worker_id", "worker_id"),
        Index("ix_document_links_site_id", "site_id"),
        Index("ix_document_links_expense_id", "expense_id"),
        Index("ix_document_links_payroll_id", "payroll_id"),
    )


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    worker_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="notifications")
    user: Mapped["User"] = relationship(back_populates="notifications")
    worker: Mapped[Optional["Worker"]] = relationship(back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_unread_created", "user_id", "is_read", "created_at"),
        Index("ix_notifications_organization_status", "organization_id", "status"),
    )
