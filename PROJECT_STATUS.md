# Labour ERP Project Status

## 1. Project Overview

This repository contains an early-stage Labour ERP implementation for construction contractor operations. The codebase includes both a backend API foundation and a frontend shell, with the main business focus on workers, attendance, payroll, and reporting.

This document reflects the current state of the repository as it exists today based on code inspection. No application code has been modified.

---

## 2. Current Folder Structure

```text
labour_v0/
├── backend/
│   ├── alembic/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   ├── deps.py
│   │   │   └── router.py
│   │   ├── core/
│   │   ├── database/
│   │   ├── db/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── main.py
│   │   └── __init__.py
│   ├── alembic.ini
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── package.json
│   └── README.md
├── docs/
├── SOFTWARE_ARCHITECTURE.md
└── PROJECT_STATUS.md
```

---

## 3. Frontend Framework and Components

### Frontend stack
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Component-based UI architecture

### Current frontend state
- A UI shell and reusable components are present.
- The frontend includes a sidebar, page header, metric cards, data cards, and UI primitives such as card, button, input, and table components.
- The app uses mock data from the frontend library layer rather than live API integration.
- There are no fully implemented domain pages yet for workers, attendance, payroll, or reports in the app router structure.

### What is implemented in the frontend
- Layout and shell structure
- Navigation sidebar
- Reusable UI components
- Static mock data for dashboard and summary views

### What is missing in the frontend
- Real page implementations for business workflows
- API client integration
- Authentication flow UI
- Forms for creating/editing workers, attendance, payroll, and expenses
- Data fetching from the backend

---

## 4. Backend Architecture

### Backend stack
- FastAPI
- SQLAlchemy 2 with declarative models
- Pydantic schemas
- JWT-based authentication
- SQLite configured by default
- Alembic scaffolding for migrations

### Backend structure
- API routes are organized by domain under the routes package.
- Business logic is separated into service modules.
- Database models are defined in a central models file.
- Security and configuration are isolated in core modules.
- Dependency injection is used for DB access and auth enforcement.

### Current backend state
The backend has a strong foundational architecture and a broad set of domain modules already implemented in code.

---

## 5. Database Models

The database layer includes a fairly comprehensive ERP-style domain model:

### Core entities
- Organization
- Role
- User
- UserRole
- Site
- Worker
- WorkerSiteAssignment

### Operational entities
- AttendanceRecord
- PayrollPeriod
- Payroll
- Payment
- Expense
- Document
- DocumentLink
- Notification

### Model quality
- The schema includes relationships, constraints, indexes, and status fields.
- The data model is designed for multi-organization scoping and role-based access.
- The design is much broader than the current API surface, which suggests the project is already intended to support more modules than are exposed today.

---

## 6. Existing APIs

The backend exposes a substantial set of REST endpoints under the API version prefix.

### Authentication APIs
- POST /api/v1/auth/register
- POST /api/v1/auth/login

### User APIs
- GET /api/v1/users/me
- GET /api/v1/users/
- GET /api/v1/users/{user_id}
- POST /api/v1/users/

### Worker APIs
- POST /api/v1/workers/
- GET /api/v1/workers/
- GET /api/v1/workers/{worker_id}
- PUT/PATCH /api/v1/workers/{worker_id}
- DELETE /api/v1/workers/{worker_id}

### Attendance APIs
- POST /api/v1/attendance/
- POST /api/v1/attendance/bulk
- GET /api/v1/attendance/report/monthly
- GET /api/v1/attendance/
- GET /api/v1/attendance/{attendance_id}
- PATCH /api/v1/attendance/{attendance_id}/overtime

### Payroll APIs
- POST /api/v1/payroll/periods
- GET /api/v1/payroll/periods
- GET /api/v1/payroll/periods/{payroll_period_id}
- POST /api/v1/payroll/periods/{payroll_period_id}/calculate
- GET /api/v1/payroll/periods/{payroll_period_id}/entries
- GET /api/v1/payroll/entries/{payroll_id}
- POST /api/v1/payroll/advances
- POST /api/v1/payroll/entries/{payroll_id}/payments
- GET /api/v1/payroll/payments/history

### Reporting APIs
- GET /api/v1/reports/worker-wise-payroll
- GET /api/v1/reports/worker-wise-payroll/export
- GET /api/v1/reports/site-wise-expense
- GET /api/v1/reports/site-wise-expense/export
- GET /api/v1/reports/attendance-summary
- GET /api/v1/reports/attendance-summary/export
- GET /api/v1/reports/monthly-payroll
- GET /api/v1/reports/monthly-payroll/export

### Health API
- GET /health

---

## 7. Authentication System

The authentication system is implemented and structured around JWT access tokens.

### Current behavior
- Organization registration creates an organization, default roles, and an initial organization admin user.
- Login validates organization code, email, and password.
- Access tokens include the user ID, organization ID, and role list.
- Route-level authorization uses dependency functions that enforce required roles.

### Strengths
- Organization-scoped access is built into the auth flow.
- Role-based route protection is already in place.
- The auth service is integrated with the user and role model.

### Gaps
- No refresh token flow is implemented.
- No password reset or email verification flow is present.
- No MFA or advanced security policies are implemented.
- No explicit audit trail for auth events beyond the model structure.

---

## 8. Completed Modules

The following areas appear to be implemented in code:

### Foundation
- FastAPI application bootstrap
- Settings and configuration management
- Database session management
- Alembic scaffolding

### Identity and access
- Organization registration
- User login
- JWT token generation
- User profile retrieval
- Role-based authorization
- User creation by organization admins

### Worker management
- Worker CRUD routes and service logic
- Worker assignment handling
- Worker list filtering and pagination
- Basic worker response mapping

### Attendance management
- Daily attendance capture
- Bulk attendance entry
- Attendance listing and retrieval
- Monthly attendance reporting
- Overtime update route

### Payroll management
- Payroll period creation
- Payroll calculation engine
- Payroll entry generation
- Advance payment recording
- Payroll payment recording
- Payment history viewing

### Expense management
- Expense creation, update, deletion, listing and site/category/date filtering
- Expense metrics summary and site-wise expense summary
- Next.js /expenses dashboard page with metric cards, directory table, and forms

### Document management
- Storage provider abstraction (`LocalStorageProvider` saving files under `backend/uploads/workers/{worker_id}/`)
- Document upload validation (PDF, JPG, PNG up to 10MB limit)
- Document CRUD APIs (`/api/v1/documents/upload`, `/api/v1/documents`, `/api/v1/documents/{id}/file`, `/api/v1/workers/{worker_id}/documents`)
- Next.js `/workers/[workerId]/documents` page with document vault, preview link, download, and delete actions

### Advanced reports & analytics
- 5 Analytics API endpoints (`/reports/labour-cost`, `/reports/attendance-analytics`, `/reports/payroll-analytics`, `/reports/expense-analytics`, `/reports/site-profitability`)
- Instant PDF and Excel export engine for all analytics reports
- Next.js /reports dashboard with interactive Line, Donut, and Bar charts, KPI overview cards, global date/site/category filters, and data export buttons

### Reporting
- Worker-wise payroll report
- Site-wise expense report
- Attendance summary report
- Monthly payroll report
- Export table generation for Excel/PDF-style output

---

## 9. What Is Working

Based on the current repository contents, the following appear to be in place:

- The backend architecture is coherent and modular.
- The core business domains are represented in code and routed through service layers.
- JWT-based auth and organization-scoped access are implemented.
- Worker, attendance, payroll, and reporting flows are coded with schemas and service logic.
- The frontend has a structured shell and reusable UI components.
- The project has a documented architecture and roadmap that align with the implemented modules.

---

## 10. What Is Incomplete or Not Yet Fully Realized

The following areas remain incomplete or only partially built:

### Frontend completeness
- The UI is mostly a visual shell and mock-data demo, not a fully connected business application.
- No real domain pages or forms are implemented yet.
- No live backend integration layer is present.

### Site management
- The database model supports sites, but there are no dedicated site CRUD APIs or frontend screens yet.

### Expense management
- Expense entities exist in the data model and reporting layer, but dedicated expense APIs and screens are not present.

### Document management
- Document and document-link models exist, but document upload and attachment workflows are not implemented.

### Workflow maturity
- Approval workflows are partially represented through status fields and flags, but not implemented as full business processes.
- Payroll posting and approval logic is lightweight compared to the full ERP vision.

### Production readiness
- Migrations and database initialization are not clearly surfaced as a complete workflow.
- There is no evidence of automated tests.
- There are no deployment, environment, or observability setups described in the codebase.

---

## 11. What Should Be Built Next

The next implementation priority should be to move from scaffold and domain logic to a connected, usable application.

### Recommended next steps
1. Build the missing site management API and UI.
2. Implement expense capture, approval, and reporting flows.
3. Connect the frontend to the backend using real API calls.
4. Add authentication UI and protected routes.
5. Implement document upload and attachment handling.
6. Add form screens for worker, attendance, and payroll entry.
7. Add migration and database initialization steps for local development.
8. Introduce automated tests for auth, worker, attendance, and payroll flows.
9. Harden the system with production-ready configuration and deployment guidance.

### Best immediate focus
The most valuable next milestone is to complete the end-to-end experience for one full workflow:
- create a user
- create workers
- capture attendance
- calculate payroll
- review reports

That would turn the current codebase from a strong foundation into a usable ERP slice.
