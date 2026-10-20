# Development Roadmap

## 1. Objective

Deliver the Labour ERP in controlled phases so business risk stays low and each release creates usable value.

## 2. Delivery Principles

- Build by business dependency order
- Release usable slices rather than isolated technical layers
- Lock down payroll correctness before advanced analytics
- Keep documentation and API contracts updated as features evolve

## 3. Suggested Team Shape

- Product owner/business analyst
- Solution architect
- Backend engineer
- Frontend engineer
- QA engineer
- UI/UX designer
- DevOps support part-time

## 4. Phase Plan

## Phase 0: Discovery and Validation

Goals:
- Validate real workflows with contractor stakeholders
- Freeze core scope for release 1

Outputs:
- Approved architecture blueprint
- Product requirements
- Workflow sign-off
- Role and permission sign-off
- Payroll rules baseline
- Import templates

Exit criteria:
- No open ambiguity on attendance or payroll approval ownership

## Phase 1: Platform Foundation

Goals:
- Establish technical base and access model

Scope:
- Authentication
- RBAC
- Organization setup
- Master data
- Audit framework
- Document storage base

Outputs:
- Secure admin-ready foundation

Exit criteria:
- Admin can log in, manage users, roles, and masters

## Phase 2: Worker and Site Operations

Goals:
- Enable worker onboarding and site allocation

Scope:
- Worker profiles
- Employment details
- Bank details
- Site master
- Teams
- Site assignments
- Worker and site documents

Outputs:
- Operational workforce registry

Exit criteria:
- Workers can be created and assigned to sites with documents attached

## Phase 3: Attendance Operations

Goals:
- Enable reliable day-to-day labour tracking

Scope:
- Daily attendance
- Bulk entry
- Approval flow
- Adjustment requests
- Period lock
- Attendance summaries

Outputs:
- Supervisor-to-manager attendance workflow

Exit criteria:
- Approved attendance available for payroll input

## Phase 4: Payroll Engine

Goals:
- Deliver end-to-end payroll processing

Scope:
- Payroll groups
- Payroll periods
- Payroll components
- Advances and deductions
- Payroll run generation
- Review, approval, and posting
- Payslips

Outputs:
- Attendance-driven payroll capability

Exit criteria:
- Posted payroll with reproducible reports and payslips

## Phase 5: Expense Control

Goals:
- Control site-level operational spending

Scope:
- Expense capture
- Approval queue
- Receipt attachments
- Expense reporting

Outputs:
- Structured site expense process

Exit criteria:
- Approved site expenses available in reports

## Phase 6: Reporting and Compliance

Goals:
- Provide management visibility and compliance monitoring

Scope:
- Management dashboards
- Attendance and payroll reports
- Site cost reports
- Expense analytics
- Document expiry reports
- Export jobs

Outputs:
- Decision-support reporting pack

Exit criteria:
- Stakeholders can self-serve core operational reports

## Phase 7: Hardening and Production Readiness

Goals:
- Prepare for stable production rollout

Scope:
- Performance tuning
- Security review
- Backup and restore drills
- Observability
- Role refinement
- Data migration rehearsal
- UAT and training support

Outputs:
- Production-ready release candidate

Exit criteria:
- Successful UAT and operational sign-off

## 5. Milestone Dependencies

- Worker and site modules must complete before attendance can be fully tested
- Attendance must stabilize before payroll goes live
- Payroll and expense data should exist before full reporting pack is validated
- Document expiry reporting depends on document metadata discipline

## 6. Key Project Risks

### Payroll rule ambiguity

Risk:
- Delays or rework in payroll implementation

Mitigation:
- Collect real sample payroll sheets and validate formulas early

### Attendance process mismatch

Risk:
- Low user adoption at site level

Mitigation:
- Prototype attendance screen flows with supervisors before development lock

### Poor master data quality

Risk:
- Reporting inaccuracies and duplicate worker records

Mitigation:
- Define import validation and mandatory data standards

### Approval bottlenecks

Risk:
- Stuck operational transactions

Mitigation:
- Define substitute approver strategy and SLA expectations

## 7. Suggested Project Artifacts Per Phase

### Before Phase 1

- Approved documents in this design pack
- Initial backlog
- Wireframes for key screens

### Before Phase 3

- Attendance business scenarios
- Site supervisor usability review

### Before Phase 4

- Payroll formula catalog
- Sample payroll validation workbook

### Before Go-Live

- Migration plan
- Admin guide
- User training guide
- Support handoff checklist

## 8. Recommended Immediate Next Steps

1. Review and approve the new design documents
2. Convert workflows into wireframes
3. Freeze the approval matrix
4. Define payroll components and calculation rules
5. Break phase 1 and phase 2 into implementation backlog items
