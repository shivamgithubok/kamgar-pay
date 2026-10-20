# Workflows and Screen Inventory

## 1. Purpose

This document translates the architecture into operational workflows and a practical screen map for UI planning before development starts.

## 2. Primary User Journeys

### Journey A: Worker Onboarding

Actors:
- HR Manager
- Document Controller

Flow:
1. HR creates worker profile
2. HR enters employment details and wage settings
3. HR adds bank details and emergency contact
4. HR uploads KYC and compliance documents
5. HR assigns worker to site or leaves unassigned pool
6. Worker becomes active after validation

System checks:
- Duplicate worker code detection
- Required field validation
- Restricted access to financial data
- Audit trail for creation and status activation

### Journey B: Worker Assignment to Site

Actors:
- HR Manager
- Site Manager

Flow:
1. HR or admin opens assignment screen
2. User selects worker and target site/team
3. System checks worker status and overlapping assignments
4. Assignment effective dates are saved
5. Site manager sees worker in active roster

System checks:
- Active worker required
- Conflict validation for overlapping primary assignments

### Journey C: Daily Attendance Capture

Actors:
- Site Supervisor
- Site Manager

Flow:
1. Supervisor opens daily attendance sheet for site
2. System loads active assigned workers
3. Supervisor marks present, absent, half-day, leave, holiday, hours, and overtime
4. Supervisor saves draft or submits
5. Site manager reviews and approves or rejects
6. Approved attendance becomes payroll-eligible

System checks:
- No duplicate attendance lines
- Attendance date must belong to open period
- Locked records block edits

### Journey D: Attendance Correction

Actors:
- Site Supervisor
- Site Manager
- Organization Admin

Flow:
1. User requests adjustment for an existing attendance record
2. Reason and changed values are captured
3. Approver reviews old and new values
4. Approved adjustment updates record if period is open
5. If locked, authorized reopen is required before correction

System checks:
- Mandatory reason
- Full audit log of before and after values

### Journey E: Payroll Processing

Actors:
- Payroll Manager
- Finance Officer

Flow:
1. Payroll manager selects payroll period
2. System validates approved and locked attendance
3. Payroll run is generated
4. Components, advances, deductions, and overtime are calculated
5. Payroll manager reviews exceptions
6. Finance or payroll approver approves run
7. Authorized user posts payroll
8. Payslips and reports become available

System checks:
- Attendance snapshot integrity
- Non-negative validation or controlled override
- Immutable final posting behavior

### Journey F: Expense Submission and Approval

Actors:
- Supervisor or Site Staff
- Site Manager
- Finance Officer

Flow:
1. User creates expense entry
2. User adds category, amount, date, and description
3. Receipt is attached if required
4. Expense is submitted
5. Approver reviews and approves or rejects
6. Approved expense appears in cost reports

System checks:
- Category required
- Attachment rules based on policy
- Approval comments captured

### Journey G: Document Compliance Tracking

Actors:
- HR Manager
- Document Controller
- Auditor

Flow:
1. User uploads and tags document
2. Document is linked to worker, site, payroll, or expense
3. Validity period is set where applicable
4. System surfaces upcoming expiries in reports
5. New versions replace prior active version while keeping history

System checks:
- File type and size restrictions
- Version traceability
- Secure download authorization

## 3. Screen Inventory

## 3.1 Core Navigation

- Login
- Forgot password
- Dashboard
- Notifications
- User profile

## 3.2 Admin Screens

- Organization setup
- User management
- Role and permissions management
- Master data management
  Trades
  Skill levels
  Shifts
  Expense categories
  Payroll components

## 3.3 Worker Management Screens

- Worker list
- Worker create/edit form
- Worker profile summary
- Worker employment tab
- Worker bank details tab
- Worker documents tab
- Worker assignment history tab
- Worker status change dialog

## 3.4 Site Management Screens

- Site list
- Site create/edit form
- Site profile/dashboard
- Site team management
- Site active workers roster

## 3.5 Attendance Screens

- Attendance daily sheet
- Bulk attendance marking view
- Attendance approval queue
- Attendance adjustment request screen
- Attendance period management
- Attendance summary report screen

## 3.6 Payroll Screens

- Payroll group setup
- Payroll period list
- Payroll run creation wizard
- Payroll run summary
- Worker payroll detail view
- Payroll approval screen
- Payslip list and detail
- Advances and deductions management

## 3.7 Expense Screens

- Expense list
- Expense create/edit form
- Expense approval queue
- Expense detail with attachment preview
- Expense summary report screen

## 3.8 Document Screens

- Document library/search
- Document upload modal/page
- Document detail and versions
- Entity-linked document tab
- Document expiry report

## 3.9 Reporting Screens

- Management dashboard
- Headcount report
- Site labour utilization report
- Attendance summary report
- Payroll register report
- Wage sheet report
- Expense summary report
- Site cost report
- Audit log viewer

## 4. Dashboard Recommendations

### Organization Dashboard

- Active workers
- Active sites
- Today attendance submitted sites
- Pending attendance approvals
- Pending payroll actions
- Pending expense approvals
- Documents expiring in next 30 days

### Site Dashboard

- Site headcount
- Present vs absent today
- Overtime hours today
- Pending expenses
- Labour cost trend

### Payroll Dashboard

- Open payroll periods
- Payroll exceptions
- Advances pending recovery
- Posted payroll totals by period

## 5. UX Design Notes

- Attendance entry should optimize for speed and bulk actions
- Mobile/responsive layout is mandatory for supervisor attendance screens
- Payroll and expense approvals should emphasize review clarity and audit evidence
- Document pages should support preview, tags, validity dates, and history

## 6. Recommended Release of Screens

### Release 1

- Login
- Dashboard
- User and master setup
- Worker management
- Site management

### Release 2

- Attendance capture and approval
- Attendance reporting

### Release 3

- Payroll setup and payroll run flow
- Payslips

### Release 4

- Expense submission and approvals
- Cost and expense reporting

### Release 5

- Document library
- Compliance and expiry reporting
- Expanded dashboards
