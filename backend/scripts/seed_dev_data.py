"""Reset and seed the local demo organization with deterministic development data."""

from __future__ import annotations

import argparse
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select

from src.core.security import get_password_hash
from src.database.models import (
    AttendanceRecord,
    Document,
    DocumentLink,
    Expense,
    Notification,
    Organization,
    Payment,
    Payroll,
    PayrollPeriod,
    Role,
    Site,
    User,
    UserRole,
    Worker,
    WorkerSiteAssignment,
)
from src.db.session import SessionLocal, engine
from src.schemas.payroll import PayrollCalculateRequest
from src.services.payroll import calculate_monthly_payroll


ORGANIZATION_CODE = "demo"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "password123"
SUPERVISOR_EMAIL = "supervisor@example.com"
SUPERVISOR_PASSWORD = "password123"

SITE_DATA = (
    ("SITE-NORTH", "North Ridge Apartments", "Pune", "Maharashtra"),
    ("SITE-EAST", "East Market Complex", "Pune", "Maharashtra"),
    ("SITE-WEST", "West Valley Villas", "Pimpri-Chinchwad", "Maharashtra"),
)

FIRST_NAMES = (
    "Aarav", "Aditya", "Ajay", "Amit", "Anil", "Arjun", "Ashok", "Bhavesh", "Chandan", "Deepak",
    "Dinesh", "Ganesh", "Gaurav", "Hari", "Imran", "Javed", "Karan", "Kiran", "Mahesh", "Manoj",
    "Mohan", "Naveen", "Nikhil", "Omkar", "Pankaj", "Prakash", "Pravin", "Rahul", "Rajesh", "Rakesh",
    "Ramesh", "Ravi", "Rohit", "Sachin", "Sanjay", "Santosh", "Shankar", "Shivam", "Sohan", "Suresh",
    "Vijay", "Vikas", "Vinay", "Vishal", "Yash", "Yogesh", "Bharat", "Brijesh", "Dev", "Dharmendra",
    "Faisal", "Hemant", "Jitendra", "Kailash", "Lalit", "Mukesh", "Nitin", "Rajan", "Ranjit", "Roshan",
    "Sameer", "Sandeep", "Sanjiv", "Suraj", "Tarun", "Umesh", "Varun", "Vivek", "Wasim", "Anand",
    "Babu", "Bala", "Madhav", "Nilesh", "Sagar",
)

LAST_NAMES = (
    "Patil", "Sharma", "Jadhav", "Pawar", "Deshmukh", "Kulkarni", "Yadav", "More", "Shinde", "Chavan",
    "Kadam", "Gaikwad", "Joshi", "Mishra", "Khan",
)

CATEGORIES = (
    ("Mason", Decimal("950.00"), Decimal("120.00")),
    ("Helper", Decimal("700.00"), Decimal("90.00")),
    ("Carpenter", Decimal("1000.00"), Decimal("130.00")),
    ("Electrician", Decimal("1100.00"), Decimal("150.00")),
    ("Plumber", Decimal("1050.00"), Decimal("140.00")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        default=None,
        help="Optional SQLite path. Defaults to the configured database.",
    )
    return parser.parse_args()


def reset_demo_organization(db) -> None:
    organization = db.execute(
        select(Organization).where(Organization.code == ORGANIZATION_CODE)
    ).scalar_one_or_none()
    if organization is None:
        return

    organization_id = organization.id
    demo_user_ids = select(User.id).where(User.organization_id == organization_id)
    db.execute(delete(UserRole).where(UserRole.user_id.in_(demo_user_ids)))
    for model in (
        DocumentLink,
        Notification,
        Payment,
        Payroll,
        PayrollPeriod,
        AttendanceRecord,
        Expense,
        WorkerSiteAssignment,
        Document,
        Worker,
        Site,
        Role,
        User,
    ):
        db.execute(delete(model).where(model.organization_id == organization_id))
    db.execute(delete(Organization).where(Organization.id == organization_id))
    db.commit()


def create_users(db, organization: Organization) -> tuple[User, User]:
    admin_role = Role(
        organization_id=organization.id,
        name="Organization Admin",
        code="organization_admin",
        description="Full access for the development organization.",
    )
    supervisor_role = Role(
        organization_id=organization.id,
        name="Supervisor",
        code="staff",
        description="Site attendance and operations access.",
    )
    db.add_all([admin_role, supervisor_role])
    db.flush()

    admin = User(
        organization_id=organization.id,
        full_name="Neha Kulkarni",
        email=ADMIN_EMAIL,
        password_hash=get_password_hash(ADMIN_PASSWORD),
        status="active",
    )
    supervisor = User(
        organization_id=organization.id,
        full_name="Sanjay Patil",
        email=SUPERVISOR_EMAIL,
        password_hash=get_password_hash(SUPERVISOR_PASSWORD),
        status="active",
    )
    db.add_all([admin, supervisor])
    db.flush()
    db.add_all([
        UserRole(user_id=admin.id, role_id=admin_role.id),
        UserRole(user_id=supervisor.id, role_id=supervisor_role.id),
    ])
    db.flush()
    return admin, supervisor


def create_sites(db, organization: Organization, supervisor: User) -> list[Site]:
    sites = [
        Site(
            organization_id=organization.id,
            site_manager_user_id=supervisor.id,
            site_code=code,
            name=name,
            client_name=("Sahyadri Developers" if index == 0 else "Pioneer Buildworks"),
            project_name=name,
            city=city,
            state=state,
            status="active",
            start_date=date.today() - timedelta(days=180),
        )
        for index, (code, name, city, state) in enumerate(SITE_DATA)
    ]
    db.add_all(sites)
    db.flush()
    return sites


def create_workers(db, organization: Organization, sites: list[Site]) -> list[Worker]:
    workers: list[Worker] = []
    joined_on = date.today() - timedelta(days=120)
    for index in range(75):
        category_index = index % len(CATEGORIES)
        category, daily_wage, overtime_rate = CATEGORIES[category_index]
        worker = Worker(
            organization_id=organization.id,
            assigned_site_id=sites[index % len(sites)].id,
            worker_code=f"WRK-{index + 1:03d}",
            first_name=FIRST_NAMES[index],
            last_name=LAST_NAMES[index % len(LAST_NAMES)],
            phone=f"98{index + 1:08d}",
            trade=category,
            employment_type="daily_wage",
            wage_type="daily",
            default_wage_rate=daily_wage,
            overtime_rate=overtime_rate,
            pf_rate_percent=Decimal("0.00") if category == "Helper" else Decimal("12.00"),
            status="active",
            joined_on=joined_on,
        )
        workers.append(worker)
    db.add_all(workers)
    db.flush()
    db.add_all(
        WorkerSiteAssignment(
            organization_id=organization.id,
            worker_id=worker.id,
            site_id=worker.assigned_site_id,
            is_primary=True,
            status="active",
            assigned_from=worker.joined_on,
        )
        for worker in workers
    )
    db.flush()
    return workers


def create_attendance(db, organization: Organization, supervisor: User, sites: list[Site], workers: list[Worker]) -> None:
    start_date = date.today() - timedelta(days=29)
    records: list[AttendanceRecord] = []
    for day_offset in range(30):
        attendance_date = start_date + timedelta(days=day_offset)
        for index, worker in enumerate(workers):
            if attendance_date.weekday() == 6:
                status = "weekly_off"
            else:
                outcome = (index * 19 + day_offset * 23) % 100
                status = "present" if outcome < 86 else "absent" if outcome < 91 else "half_day" if outcome < 95 else "leave"
            records.append(
                AttendanceRecord(
                    organization_id=organization.id,
                    worker_id=worker.id,
                    site_id=sites[index % len(sites)].id,
                    captured_by_user_id=supervisor.id,
                    attendance_date=attendance_date,
                    status=status,
                    regular_hours={"present": Decimal("8.00"), "half_day": Decimal("4.00")}.get(status, Decimal("0.00")),
                    overtime_hours=Decimal("2.00") if status == "present" and (index + day_offset) % 11 == 0 else Decimal("0.00"),
                    approval_status="approved" if day_offset < 27 else "draft",
                    payroll_locked=False,
                )
            )
    db.add_all(records)
    db.flush()


def create_expenses(db, organization: Organization, admin: User, sites: list[Site]) -> None:
    expense_specs = (
        ("labour", Decimal("18500.00"), "Weekly labour support and site helpers"),
        ("material", Decimal("42600.00"), "Cement, sand, aggregate, and reinforcement steel"),
        ("site", Decimal("9800.00"), "Temporary fencing, water, power, and site safety supplies"),
    )
    expenses = [
        Expense(
            organization_id=organization.id,
            site_id=sites[index % len(sites)].id,
            submitted_by_user_id=admin.id,
            category=category,
            expense_date=date.today() - timedelta(days=index * 3 + 1),
            amount=amount + Decimal(index * 725),
            payment_mode="bank_transfer" if category == "material" else "cash",
            vendor_name=("Shree Materials" if category == "material" else "Site Operations Cash Desk"),
            description=description,
            status=("approved" if index % 3 == 0 else "paid" if index % 3 == 1 else "draft"),
            receipt_required=category != "labour",
        )
        for index, (category, amount, description) in enumerate(expense_specs * 4)
    ]
    db.add_all(expenses)
    db.flush()


def create_payroll(db, organization: Organization, admin: User, workers: list[Worker]) -> None:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today.replace(day=monthrange(today.year, today.month)[1])
    period = PayrollPeriod(
        organization_id=organization.id,
        created_by_user_id=admin.id,
        name=f"{today.strftime('%B')} {today.year}",
        period_start=period_start,
        period_end=period_end,
        pay_date=period_end + timedelta(days=5),
        status="processing",
    )
    db.add(period)
    db.flush()

    for index, worker in enumerate(workers[::3]):
        db.add(
            Payment(
                organization_id=organization.id,
                worker_id=worker.id,
                site_id=worker.assigned_site_id,
                processed_by_user_id=admin.id,
                payment_type="advance",
                payment_method="upi",
                amount=Decimal("3500.00") + Decimal(index * 250),
                payment_date=period_start + timedelta(days=min(index + 2, 20)),
                status="completed",
                external_reference=f"ADV-DEMO-{index + 1:03d}",
                notes="Development advance payment",
            )
        )
    db.flush()

    result = calculate_monthly_payroll(
        db,
        organization_id=organization.id,
        payroll_period_id=period.id,
        payload=PayrollCalculateRequest(worker_ids=[worker.id for worker in workers]),
    )
    for index, payroll_item in enumerate(result.items):
        if index % 3 == 0 and payroll_item.net_amount > 0:
            db.add(
                Payment(
                    organization_id=organization.id,
                    payroll_id=payroll_item.id,
                    worker_id=payroll_item.worker_id,
                    site_id=payroll_item.site_id,
                    processed_by_user_id=admin.id,
                    payment_type="payroll",
                    payment_method="bank_transfer",
                    amount=(payroll_item.net_amount * Decimal("0.60")).quantize(Decimal("0.01")),
                    payment_date=period_end,
                    status="completed",
                    external_reference=f"PAY-DEMO-{index + 1:03d}",
                    notes="Partial development payroll payment",
                )
            )
        elif payroll_item.net_amount > 0:
            db.add(
                Payment(
                    organization_id=organization.id,
                    payroll_id=payroll_item.id,
                    worker_id=payroll_item.worker_id,
                    site_id=payroll_item.site_id,
                    processed_by_user_id=admin.id,
                    payment_type="payroll",
                    payment_method="bank_transfer",
                    amount=payroll_item.net_amount,
                    payment_date=period_end,
                    status="pending",
                    external_reference=f"PENDING-DEMO-{index + 1:03d}",
                    notes="Pending development payroll payment",
                )
            )
    db.commit()


def seed() -> None:
    db = SessionLocal()
    try:
        reset_demo_organization(db)
        organization = Organization(name="Demo Construction Company", code=ORGANIZATION_CODE, status="active")
        db.add(organization)
        db.flush()
        admin, supervisor = create_users(db, organization)
        sites = create_sites(db, organization, supervisor)
        workers = create_workers(db, organization, sites)
        create_attendance(db, organization, supervisor, sites, workers)
        create_expenses(db, organization, admin, sites)
        db.commit()
        create_payroll(db, organization, admin, workers)
        print(f"Seeded {organization.name}: 2 users, 3 sites, {len(workers)} workers, 30 days of attendance, payroll, payments, and expenses.")
        print(f"Admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"Supervisor login: {SUPERVISOR_EMAIL} / {SUPERVISOR_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.database:
        raise SystemExit("Custom database selection is not supported yet; set DATABASE_URL in backend/.env instead.")
    if not str(engine.url).startswith("sqlite"):
        raise SystemExit("This development seed script only supports SQLite.")
    seed()