# User Roles and Permissions

## 1. Access Control Model

The Labour ERP should use a layered authorization model:

- Authentication verifies user identity
- RBAC grants baseline permissions by role
- Scope rules restrict data visibility to organization, assigned sites, or self
- Approval authority controls who can approve operational and financial actions

## 2. Role Catalog

## Super Admin

Purpose:
- Platform-level administration across organizations

Typical permissions:
- Manage organizations
- Create top-level admins
- View system-wide audit information
- Configure global master settings

Restrictions:
- Should not usually participate in daily operational transactions

## Organization Admin

Purpose:
- Full business administration for one contractor organization

Typical permissions:
- Manage users and roles
- Configure sites, shifts, payroll groups, expense categories, trades, skill levels
- View all organization data
- Reopen locked business periods where policy permits

Restrictions:
- High-risk actions should be audited and optionally require MFA

## HR Manager

Purpose:
- Manage worker lifecycle

Typical permissions:
- Create and update workers
- Manage worker documents
- View worker assignment history
- Change worker employment status

Restrictions:
- No payroll posting authority by default
- No organization-level security configuration

## Site Manager

Purpose:
- Own operational control for assigned sites

Typical permissions:
- View assigned site dashboard
- Review worker assignment lists
- Approve attendance for assigned sites
- Approve site expenses within limits

Restrictions:
- Cannot access payroll across the organization unless separately granted

## Site Supervisor

Purpose:
- Execute daily site attendance and operational submissions

Typical permissions:
- Mark attendance
- Submit attendance sheets
- Create expense requests if allowed
- View assigned team members

Restrictions:
- Cannot approve own submissions unless explicitly allowed by policy

## Payroll Manager

Purpose:
- Own payroll calculation and finalization

Typical permissions:
- Configure payroll periods and payroll groups
- Generate payroll runs
- Review components and adjustments
- Approve or post payroll
- Issue payslips

Restrictions:
- Cannot alter attendance after payroll lock unless granted reopen rights

## Accounts/Finance Officer

Purpose:
- Manage expense verification and financial review

Typical permissions:
- Review expenses
- Approve or reject within authority
- View payroll summaries and exports
- Access finance-oriented reports

Restrictions:
- No worker HR edits by default

## Document Controller

Purpose:
- Govern document quality and compliance tracking

Typical permissions:
- Upload and tag documents
- Replace document versions
- Monitor document expiry

Restrictions:
- Cannot change core worker or payroll data

## Auditor/Compliance Officer

Purpose:
- Independent review of business actions

Typical permissions:
- Read-only access to attendance, payroll, expenses, documents, and audit logs
- Export compliance reports

Restrictions:
- No create, update, approve, or delete permissions

## Worker

Purpose:
- Limited self-service in later phase

Typical permissions:
- View own attendance
- View own payslips
- View own profile and documents

Restrictions:
- Self-only access

## 3. Permission Matrix

Legend:
- `C` Create
- `R` Read
- `U` Update
- `A` Approve
- `P` Post/Lock
- `E` Export

| Module | Super Admin | Org Admin | HR Manager | Site Manager | Supervisor | Payroll Manager | Finance | Doc Controller | Auditor | Worker |
|---|---|---|---|---|---|---|---|---|---|---|
| Organizations | CRU | R | - | - | - | - | - | - | R | - |
| Users/Roles | CRU | CRU | R | - | - | - | - | - | R | - |
| Workers | R | CRU | CRU | R | R | R | R | R | R | Self-R |
| Worker Documents | R | CRU | CRU | R | R | R | R | CRU | R | Self-R |
| Sites | R | CRU | R | CRU-scope | R-scope | R | R | R | R | - |
| Assignments | R | CRU | CRU | U-scope | R-scope | R | R | - | R | - |
| Attendance | R | CRUAP | R | RA-scope | CRU-scope | R | R | - | R | Self-R |
| Payroll | R | R | R | R-scope | - | CRUAP | R/E | - | R/E | Self-R |
| Expenses | R | CRUAP | R | RA-scope | CU-scope | R | CRUAP | R-docs | R/E | - |
| Documents | R | CRU | CRU | R-scope | U-scope limited | R | R | CRU | R | Self-R limited |
| Reports | R/E | R/E | R/E worker reports | R/E-scope | R-scope | R/E payroll | R/E finance | R expiry | R/E | Self-R limited |
| Audit Logs | R | R | - | - | - | - | - | - | R/E | - |

## 4. Scope Rules

### Organization Scope

- Every transactional record belongs to one organization
- Users should never cross organization boundaries unless they are platform super admins

### Site Scope

- Site managers and supervisors see only assigned sites by default
- Expense and attendance actions should be limited to assigned site scope

### Self Scope

- Worker access is strictly limited to own records
- Any self-service requests should be isolated from admin functions

## 5. Approval Ownership

### Attendance

- Created by Site Supervisor
- Approved by Site Manager or authorized delegate
- Reopened by Organization Admin or privileged manager

### Payroll

- Generated by Payroll Manager
- Approved by Payroll Manager or Finance approver depending on company policy
- Posted and locked by authorized payroll/finance role

### Expenses

- Created by site-level user or finance user
- Approved by Site Manager or Finance based on amount and policy
- Multi-level approvals can be enabled later

### Documents

- Uploaded by HR, supervisor, finance, or document controller
- Sensitive documents may require verification flag by HR or compliance

## 6. Recommended Control Policies

- No user should approve their own sensitive financial transaction by default
- Payroll post should require elevated permission and strong audit logging
- Locked periods should require explicit reopen action and reason
- Bank detail changes should be captured in audit history and optionally require secondary approval

## 7. Future Enhancements

- Policy-driven dynamic permission engine
- Approval matrix based on amount threshold and site hierarchy
- Temporary delegated access for leave coverage
