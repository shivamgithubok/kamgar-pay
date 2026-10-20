from fastapi import APIRouter

from src.api.routes import attendance, auth, documents, expenses, payroll, reports, sites, users, workers


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workers.router, prefix="/workers", tags=["workers"])
api_router.include_router(documents.worker_documents_router, prefix="/workers", tags=["workers"])
api_router.include_router(sites.router, prefix="/sites", tags=["sites"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(payroll.router, prefix="/payroll", tags=["payroll"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])


