# Product Requirements Document

## 1. Product Vision

Build a Labour ERP platform for construction contractors that centralizes labour operations across workers, sites, attendance, payroll, expenses, documents, and reporting.

The platform should reduce manual work, improve payroll accuracy, strengthen compliance, and give management daily operational visibility.

## 2. Product Objectives

- Maintain a single source of truth for workers and site assignments
- Capture accurate daily attendance with approvals and corrections
- Generate payroll from approved attendance with full traceability
- Track site expenses with evidence and approvals
- Manage worker and site documents with expiry monitoring
- Provide operational and financial reports for management decisions

## 3. Success Criteria

- Worker onboarding time reduced by at least 50 percent versus manual process
- Attendance submission completed daily for all active sites
- Payroll disputes caused by attendance mismatch reduced materially
- Site expense entries always include category and supporting proof where required
- All critical actions are auditable by organization and user

## 4. Business Users

- Contractor owners and management
- HR team
- Site operations team
- Payroll and accounts teams
- Compliance and audit users
- Supervisors at site level
- Workers in a later self-service phase

## 5. Scope Definition

### In Scope for Initial Product

- Worker master and employment profile
- Worker site assignment
- Daily attendance and approval
- Payroll calculation and payslip generation
- Site master and teams
- Expense capture and approvals
- Document upload and linking
- Operational and management reports

### Out of Scope for Initial Product

- Material inventory
- Purchase orders and procurement
- Client billing and receivables
- General ledger
- Full vendor management lifecycle
- Native biometric integration in first release

## 6. Functional Requirements by Module

## 6.1 Worker Management

### Features

- Create and maintain worker profiles
- Capture personal, contact, and emergency details
- Capture employment type, trade, skill level, and wage structure
- Maintain bank/payment details
- Track status changes such as active, inactive, exited
- Assign workers to sites and teams with date ranges
- Upload and link worker-related documents

### Business Rules

- Worker code must be unique within an organization
- A worker may have many site assignments over time
- Only one active primary assignment is allowed at a time unless configured otherwise
- Exited workers cannot receive new attendance or payroll unless reopened
- Sensitive financial fields should be restricted to authorized roles

### Acceptance Direction

- HR can onboard a worker end-to-end with mandatory fields validated
- Site manager can view active workers assigned to their site
- System prevents duplicate active worker code creation

## 6.2 Attendance Management

### Features

- Daily site-wise attendance entry
- Bulk attendance marking for site workforce
- Shift support
- Hours and overtime capture
- Check-in/check-out optional mode
- Leave, holiday, absent, half-day, and present statuses
- Attendance adjustment workflow
- Approval workflow and lock control

### Business Rules

- Attendance should be unique per worker, site, and day
- Supervisor can submit attendance but not finalize locked periods
- Manager approval is required before payroll consumption
- Attendance used by payroll should be snapshotted or period-locked
- Retroactive edits require authorization and audit logging

### Acceptance Direction

- Supervisor can mark attendance for a full team in one operation
- Manager can approve a day sheet or reject for correction
- Locked attendance cannot be edited by normal users

## 6.3 Payroll Management

### Features

- Payroll groups and cycles
- Payroll period creation
- Earnings components and deduction components
- Attendance-based payroll generation
- Advances and deductions handling
- Review, approval, posting, and payslip issue
- Payroll register and wage sheet

### Business Rules

- Payroll must be generated only from approved attendance
- Final posted payroll should be immutable except through controlled reversal/reopen flow
- Each payroll run should preserve calculation inputs and outputs
- Net pay cannot be negative without authorized override
- Multiple payroll runs for one period should be versioned or numbered

### Acceptance Direction

- Payroll manager can generate payroll for a selected period
- Accounts can review component-level breakdown per worker
- Posted payroll produces payslips and export-ready reports

## 6.4 Site Management

### Features

- Create and manage sites
- Assign site manager and supervisors
- Define teams or gangs
- View assigned workers
- View site-level attendance and expense summaries

### Business Rules

- Site code must be unique per organization
- Closed sites should not accept new assignments without reopen action
- Only authorized site users can manage their site workforce

### Acceptance Direction

- Organization admin can create sites and assign managers
- Site manager can see operational dashboard for their site

## 6.5 Expense Tracking

### Features

- Record site expenses
- Categorize expenses
- Attach bills and receipts
- Submit for approval
- Approve or reject with comments
- Report by site, date, and category

### Business Rules

- Expense category is mandatory
- Supporting document requirement can vary by category or amount threshold
- Rejected expenses remain traceable and editable for resubmission
- Approved expenses become read-only except for finance-authorized actions

### Acceptance Direction

- Site staff can submit expense with attachment
- Approver can review amount, category, and proof before action
- Finance can export site expense summary

## 6.6 Reports

### Features

- Worker headcount
- Site labour utilization
- Attendance summary
- Overtime summary
- Payroll register
- Wage sheet
- Expense summary
- Site cost report
- Document expiry report

### Business Rules

- Report visibility follows user scope permissions
- Large report exports should run asynchronously
- Finalized payroll reports must remain reproducible

### Acceptance Direction

- Manager can filter report by site and date
- Exported reports match on-screen totals

## 6.7 Document Management

### Features

- Upload, version, tag, and search documents
- Link documents to workers, sites, expenses, and payroll records
- Track validity dates and expiry
- Download based on role permission

### Business Rules

- Files must store metadata and uploader details
- Multiple versions must remain traceable
- Expired compliance documents should surface in reports/alerts

### Acceptance Direction

- HR can upload worker KYC files
- Accounts can attach bills to expenses
- Auditor can view document history without editing

## 7. Non-Functional Requirements

## Security

- Role-based access with scoped permissions
- Audit logs for sensitive actions
- Secure document access
- Encrypted storage for sensitive financial data where required

## Availability

- Designed for business-hour operational continuity
- Backup and restore procedures defined before production launch

## Performance

- Bulk attendance handling should remain practical for large sites
- Payroll calculation should complete in business-acceptable batch windows
- Search and dashboards should remain responsive for normal workloads

## Maintainability

- Modular domain structure
- Clear API contracts
- Test coverage for calculation and workflow rules

## 8. Dependencies

- Master data setup before operational use
- Defined payroll component catalog
- Defined approval matrix by role
- Import templates for worker onboarding and initial data migration

## 9. Open Design Decisions

- Whether worker self-service is included in release 1 or phase 2
- Whether attendance uses check-in/check-out, muster-only, or hybrid model by default
- Whether statutory payroll rules are configurable or deferred to later phase
- Whether multi-language UI support is required in phase 1

## 10. Release Recommendation

Release functional slices in this order:

1. Foundation and security
2. Worker and site management
3. Attendance
4. Payroll
5. Expenses
6. Reports and compliance views
