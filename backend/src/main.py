from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text

from src.api.router import api_router
from src.core.config import settings
from src.database.base import Base
from src.database.models import Organization
from src.db.session import SessionLocal, engine
from src.schemas.auth import RegisterRequest
from src.services.auth import register_organization_admin


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


def ensure_sqlite_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    statements: list[str] = []
    if "workers" in table_names:
        worker_columns = {column["name"] for column in inspector.get_columns("workers")}
        if "pf_rate_percent" not in worker_columns:
            statements.append(
                "ALTER TABLE workers ADD COLUMN pf_rate_percent NUMERIC(5, 2) DEFAULT 0 NOT NULL"
            )
    if "payrolls" in table_names:
        payroll_columns = {column["name"] for column in inspector.get_columns("payrolls")}
        if "pf_amount" not in payroll_columns:
            statements.append("ALTER TABLE payrolls ADD COLUMN pf_amount NUMERIC(14, 2) DEFAULT 0 NOT NULL")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def run_migrations() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()


def seed_demo_account() -> None:
    db = SessionLocal()
    try:
        existing_organization = db.execute(select(Organization)).scalar_one_or_none()
        if existing_organization is not None:
            return

        register_organization_admin(
            db,
            RegisterRequest(
                organization_name="Demo Organization",
                organization_code="demo",
                full_name="Demo Admin",
                email="admin@example.com",
                password="password123",
            ),
        )
    finally:
        db.close()


@app.on_event("startup")
def startup_event() -> None:
    run_migrations()
    seed_demo_account()


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
