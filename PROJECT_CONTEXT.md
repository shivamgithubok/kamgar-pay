# Labour ERP Project Context & Status

## Overview
Labour ERP is a system for construction contractors to manage workers, project sites, daily attendance, payroll runs, site expenses, documents, and operational reports.

---

## Completed Modules

✅ **1. Authentication & Identity Access**
- Organization-scoped JWT access tokens
- Admin and staff role-based route permissions (`organization_admin`, `staff`)

✅ **2. Worker Management**
- Worker CRUD APIs and service layer
- Worker site assignments and status history
- Worker master roster page (`/workers`)

✅ **3. Site Management**
- Site CRUD APIs, worker allocations, and statistics
- Site directory page (`/sites`) with KPI metric cards and modals

✅ **4. Attendance Management**
- Daily muster roll and bulk attendance entry
- Shift management, overtime calculations, and monthly reports

✅ **5. Payroll Management**
- Payroll periods, automated calculation engine, advance deductions, and payment records

✅ **6. Expense Management**
- Site expense tracking by category (Material, Labour, Transport, Tools, Safety, Utilities, Subcontractor, Other)
- API endpoints: `/api/v1/expenses`, `/api/v1/expenses/summary`, `/api/v1/expenses/site-summary`
- Next.js expense dashboard page (`/expenses`) with metric cards and filterable register

✅ **7. Document Management System**
- Local storage provider (`backend/uploads/workers/{worker_id}/`) with pluggable abstraction for S3/Blob storage
- File format validation (PDF, JPG, PNG) and max file size enforcement (10MB)
- API endpoints:
  - `POST /api/v1/documents/upload`
  - `GET /api/v1/documents`
  - `GET /api/v1/documents/{id}`
  - `GET /api/v1/documents/{id}/file` (secure file streaming)
  - `GET /api/v1/workers/{worker_id}/documents`
  - `DELETE /api/v1/documents/{id}`
- Next.js Worker Documents Vault page (`/workers/[workerId]/documents`) with upload modal, preview, download, and delete actions

✅ **8. Advanced Reports & Analytics Module**
- 5 new analytics API endpoints:
  - `GET /api/v1/reports/labour-cost` (+ `/export`)
  - `GET /api/v1/reports/attendance-analytics` (+ `/export`)
  - `GET /api/v1/reports/payroll-analytics` (+ `/export`)
  - `GET /api/v1/reports/expense-analytics` (+ `/export`)
  - `GET /api/v1/reports/site-profitability` (+ `/export`)
- Instant PDF and Excel report generation (`/export?format=pdf` & `/export?format=excel`)
- Next.js Analytics & Reports Dashboard (`/reports`) featuring Labour, Payroll, and Expense overview cards, global date/site/category filters, PDF/Excel export controls, interactive visual charts (Monthly Payroll Trend Line Chart, Daily Attendance Trend Line Chart, Expense Distribution Donut Chart, Site Cost Comparison Bar Chart), Site Profitability statements, and Worker Attendance Rankings table.

---

## Current Architecture
- **Backend**: FastAPI, SQLAlchemy 2 ORM, Pydantic v2, SQLite/PostgreSQL
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide icons
