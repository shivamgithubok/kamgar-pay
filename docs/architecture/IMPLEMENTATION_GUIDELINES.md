# Implementation Guidelines

## 1. Purpose

This document defines technical guardrails for turning the architecture into a maintainable implementation while preserving domain boundaries.

## 2. Architecture Style

The recommended first implementation is a modular monolith with strong internal boundaries.

### Why this is the right starting point

- Attendance, payroll, and expenses share transactional dependencies
- The team can move faster with one deployment unit
- Reporting and documents can still scale through background jobs and storage separation
- Modules can later be extracted if scale, ownership, or integration demands it

## 3. Module Boundaries

## Auth and Access

Responsibilities:
- Authentication
- User sessions/tokens
- Role and permission evaluation
- Scoped access enforcement

Should not own:
- Worker HR rules
- Payroll logic

## Workers

Responsibilities:
- Worker profile lifecycle
- Employment details
- Bank and emergency contact records
- Assignment coordination with sites

Should not own:
- Attendance approval rules
- Payroll period logic

## Sites

Responsibilities:
- Site master lifecycle
- Site team structure
- Site-level operational views

Should not own:
- Worker master lifecycle
- Payroll calculation

## Attendance

Responsibilities:
- Attendance entry
- Attendance validation
- Adjustment workflow
- Approval and locking

Should not own:
- Payroll posting

## Payroll

Responsibilities:
- Payroll setup
- Payroll calculation engine
- Period and run lifecycle
- Payslip generation

Should not own:
- Raw attendance editing

## Expenses

Responsibilities:
- Expense capture
- Expense approval workflow
- Expense categorization

Should not own:
- General ledger accounting in phase 1

## Documents

Responsibilities:
- Upload, versioning, linking, search metadata
- Validity/expiry tracking

Should not own:
- Core business workflow approval logic

## Reports

Responsibilities:
- Read-optimized query models
- Exports
- Dashboards

Should not own:
- Business write operations

## Audit and Notifications

Responsibilities:
- Action logging
- Event-triggered notifications
- Operational alerts

## 4. Application Layer Rules

- Keep controllers thin
- Validate input at API boundary
- Place business rules inside domain services
- Keep repositories/data access isolated from controllers
- Use DTOs or request/response contracts explicitly
- Separate write flows from report query flows where possible

## 5. Data Management Rules

- PostgreSQL is the source of truth
- Use UUID primary keys
- Add `organization_id` to all organization-scoped tables
- Store audit timestamps on all major tables
- Use soft delete only when business recovery matters
- Use unique constraints for worker code, site code, and attendance uniqueness

## 6. Workflow Integrity Rules

- Attendance must be approved before payroll can consume it
- Payroll posting should create an immutable state transition
- Reopen actions must require a reason and elevated authority
- Expense approval state must remain traceable
- Bank detail changes should be auditable

## 7. API Standards

- Version APIs from day one
- Support pagination, filtering, and sorting on list endpoints
- Standardize error response structure
- Use idempotency for posting operations and imports
- Protect all document download endpoints with authorization checks

## 8. Background Job Candidates

- Payslip PDF generation
- Large report exports
- Bulk worker imports
- Document virus scan or metadata extraction if added later
- Notification dispatch
- Expiry reminder generation

## 9. Security Controls

- Hash passwords with a modern algorithm
- Limit sensitive data exposure by role
- Encrypt sensitive fields where appropriate
- Sign document access links or proxy downloads through authorized endpoints
- Audit create, update, approve, post, reopen, and export operations

## 10. Observability

- Structured application logs
- Request correlation IDs
- Audit logs for business actions
- Metrics for API latency, job failures, and payroll run duration
- Alerting for repeated payroll or export failures

## 11. Testing Strategy

### Unit Tests

- Payroll component calculations
- Attendance validation rules
- Expense approval rules
- Permission checks

### Integration Tests

- Worker onboarding to assignment flow
- Attendance approval to payroll generation flow
- Expense submission to approval flow
- Document linking behavior

### End-to-End Tests

- Admin setup
- Supervisor daily attendance
- Payroll manager processing a full period
- Finance expense review

## 12. Documentation Standards

- Maintain OpenAPI contract as a first-class artifact
- Record significant architecture decisions in ADR format
- Keep data dictionary updated when schema changes
- Keep report definitions versioned

## 13. Migration Strategy

- Start with clean schema creation scripts
- Prepare CSV/XLSX templates for workers, sites, and attendance
- Validate and stage imported data before final commit
- Preserve import audit trail with source file reference

## 14. Readiness Gate Before Coding

Coding should start only after:

- Approval matrix is confirmed
- Payroll rule catalog is signed off
- Required master data is listed
- Primary workflows are accepted
- Module boundaries are agreed
