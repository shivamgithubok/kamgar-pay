const DEFAULT_API_BASE = "/api/v1";

let inMemoryToken: string | null = null;

export type ApiErrorShape = {
  status: number;
  message: string;
  details?: unknown;
};

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function setAuthToken(token: string | null) {
  inMemoryToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      window.sessionStorage.setItem("labour_access_token", token);
    } else {
      window.sessionStorage.removeItem("labour_access_token");
    }
  }
}

export function getStoredAuthToken() {
  if (inMemoryToken) {
    return inMemoryToken;
  }

  if (typeof window === "undefined") {
    return null;
  }

  const token = window.sessionStorage.getItem("labour_access_token");
  if (token) {
    inMemoryToken = token;
  }
  return token;
}

export function clearAuthToken() {
  setAuthToken(null);
}

function buildUrl(path: string) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE;
  const normalizedBase = baseUrl.replace(/\/$/, "");
  const [pathname, query = ""] = path.split("?");
  const normalizedPath = (pathname.startsWith("/") ? pathname : `/${pathname}`).replace(/\/+$/, "") || "/";
  return `${normalizedBase}${normalizedPath}${query ? `?${query}` : ""}`;
}

function formatApiMessage(payload: unknown, fallback = "Request failed") {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          const loc = Array.isArray((item as { loc?: unknown }).loc) ? (item as { loc: Array<string | number> }).loc.filter((part) => part !== "body").join(".") : "";
          return loc ? `${loc}: ${String((item as { msg: string }).msg)}` : String((item as { msg: string }).msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getStoredAuthToken();
  const headers = new Headers(init.headers || {});
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path), {
    ...init,
    redirect: "follow",
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json().catch(() => null) : await response.text().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken();
    }
    throw new ApiError(response.status, formatApiMessage(payload), payload);
  }

  return payload as T;
}

export async function login(payload: { organization_code: string; email: string; password: string }) {
  return request<{ access_token: string; token_type: string; expires_in: number; user: UserResponse }>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function getCurrentUser() {
  return request<UserResponse>("/users/me");
}

export async function getWorkers(params: { page?: number; page_size?: number; search?: string; trade?: string; status?: string; site_id?: string } = {}) {
  return request<WorkersListResponse>(`/workers${toQueryString({ page: 1, page_size: 100, ...params })}`);
}

export async function createWorker(payload: WorkerWritePayload) {
  return request<WorkersListResponse["items"][number]>("/workers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateWorker(workerId: string, payload: Partial<WorkerWritePayload>) {
  return request<WorkersListResponse["items"][number]>(`/workers/${workerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

function toQueryString(params: Record<string, string | number | undefined | null>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function getSites(params: SiteListParams = {}) {
  return request<SiteListResponse>(`/sites${toQueryString({ page: 1, page_size: 100, ...params })}`);
}

export async function getSite(siteId: string) {
  return request<SiteResponse>(`/sites/${siteId}`);
}

export async function createSite(payload: SiteWritePayload) {
  return request<SiteResponse>("/sites", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateSite(siteId: string, payload: Partial<SiteWritePayload>) {
  return request<SiteResponse>(`/sites/${siteId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getSiteWorkers(siteId: string) {
  return request<SiteWorkerResponse[]>(`/sites/${siteId}/workers`);
}

export async function assignWorkerToSite(siteId: string, payload: SiteWorkerAssignmentPayload) {
  return request<SiteAssignmentResponse>(`/sites/${siteId}/workers/assign`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function unassignWorkerFromSite(siteId: string, workerId: string) {
  return request<void>(`/sites/${siteId}/workers/${workerId}`, {
    method: "DELETE",
  });
}

export async function getSiteStats(siteId: string) {
  return request<SiteStatsResponse>(`/sites/${siteId}/stats`);
}

export async function getSiteExpenseSummary(siteId: string) {
  return request<SiteExpenseSummaryResponse>(`/sites/${siteId}/expense-summary`);
}

export async function getMonthlyAttendanceReport(year: number, month: number, params: { site_id?: string; worker_id?: string } = {}) {
  return request<MonthlyAttendanceReportResponse>(`/attendance/report/monthly${toQueryString({ year, month, ...params })}`);
}

export async function getAttendance(params: { start_date?: string; end_date?: string; site_id?: string; worker_id?: string; approval_status?: string } = {}) {
  return request<AttendanceResponse[]>(`/attendance${toQueryString(params)}`);
}

export async function markAttendance(payload: MarkAttendancePayload) {
  return request<AttendanceResponse>("/attendance", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function bulkMarkAttendance(payload: { entries: MarkAttendancePayload[] }) {
  return request<BulkAttendanceResponse>("/attendance/bulk", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPayrollPeriods(params: { status?: string } = {}) {
  return request<PayrollPeriodResponse[]>(`/payroll/periods${toQueryString(params)}`);
}

export async function createPayrollPeriod(payload: { year: number; month: number; name?: string; pay_date?: string | null }) {
  return request<PayrollPeriodResponse>("/payroll/periods", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function calculatePayroll(periodId: string, payload: { site_id?: string | null; worker_ids?: string[]; recalculate_existing?: boolean } = {}) {
  return request<PayrollCalculationSummaryResponse>(`/payroll/periods/${periodId}/calculate`, {
    method: "POST",
    body: JSON.stringify({ worker_ids: [], recalculate_existing: true, ...payload }),
  });
}

export async function getPayrollEntries(periodId: string) {
  return request<PayrollEntryResponse[]>(`/payroll/periods/${periodId}/entries`);
}

export async function recordPayrollPayment(payrollId: string, payload: { amount: number | string; payment_date: string; payment_method?: string; status?: string; notes?: string | null }) {
  return request<PaymentResponse>(`/payroll/entries/${payrollId}/payments`, {
    method: "POST",
    body: JSON.stringify({ payment_method: "cash", status: "completed", ...payload }),
  });
}

export async function createAdvancePayment(payload: {
  worker_id: string;
  site_id?: string | null;
  amount: number | string;
  payment_date: string;
  payment_method?: string;
  notes?: string | null;
  reason?: string | null;
}) {
  return request<PaymentResponse>("/payroll/advances", {
    method: "POST",
    body: JSON.stringify({ payment_method: "cash", status: "completed", ...payload }),
  });
}

export async function getPaymentHistory(params: {
  worker_id?: string;
  payroll_id?: string;
  payment_type?: string;
  start_date?: string;
  end_date?: string;
} = {}) {
  return request<PaymentResponse[]>(`/payroll/payments/history${toQueryString(params)}`);
}

export async function getMonthlyPayrollReport(year: number, month: number) {
  return request<MonthlyPayrollReportResponse>(`/reports/monthly-payroll?year=${year}&month=${month}`);
}

export async function getAttendanceSummaryReport() {
  const now = new Date();
  return request<AttendanceSummaryReportResponse>(`/reports/attendance-summary?start_date=${now.getFullYear()}-01-01&end_date=${now.getFullYear()}-12-31`);
}

export async function getSiteExpenseReport() {
  const now = new Date();
  return request<SiteExpenseReportResponse>(`/reports/site-wise-expense?start_date=${now.getFullYear()}-01-01&end_date=${now.getFullYear()}-12-31`);
}

export async function getExpenses(params: ExpenseListParams = {}) {
  return request<ExpenseListResponse>(`/expenses${toQueryString({ page: 1, page_size: 100, ...params })}`);
}

export async function getExpense(expenseId: string) {
  return request<ExpenseResponse>(`/expenses/${expenseId}`);
}

export async function createExpense(payload: ExpenseWritePayload) {
  return request<ExpenseResponse>("/expenses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateExpense(expenseId: string, payload: Partial<ExpenseWritePayload> & { status?: string }) {
  return request<ExpenseResponse>(`/expenses/${expenseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteExpense(expenseId: string) {
  return request<void>(`/expenses/${expenseId}`, {
    method: "DELETE",
  });
}

export async function getExpenseMetricsSummary() {
  return request<ExpenseMetricsSummaryResponse>("/expenses/summary");
}

export type UserResponse = {
  id: string;
  organization_id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  status: string;
  is_locked: boolean;
  last_login_at?: string | null;
  role_codes: string[];
  created_at: string;
  updated_at: string;
};

export type WorkersListResponse = {
  items: Array<{
    id: string;
    organization_id: string;
    worker_code: string;
    name: string;
    mobile?: string | null;
    aadhaar?: string | null;
    address: {
      line1?: string | null;
      line2?: string | null;
      city?: string | null;
      state?: string | null;
      postal_code?: string | null;
    };
    trade?: string | null;
    daily_wage: string;
    pf_rate_percent: string;
    joining_date: string;
    assigned_site_id?: string | null;
    assigned_site_name?: string | null;
    bank_details: {
      account_holder_name?: string | null;
      bank_name?: string | null;
      account_number?: string | null;
      ifsc_code?: string | null;
    };
    status: string;
    advance_count: number;
    advance_total: string;
    last_advance_date?: string | null;
    last_advance_reason?: string | null;
    created_at: string;
    updated_at: string;
  }>;
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type WorkerWritePayload = {
  worker_code: string;
  name: string;
  mobile?: string | null;
  aadhaar?: string | null;
  trade?: string | null;
  daily_wage: number | string;
  pf_rate_percent?: number | string;
  joining_date: string;
  assigned_site_id?: string | null;
};

export type SiteListParams = {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  city?: string;
  state?: string;
  site_manager_user_id?: string;
};

export type SiteWritePayload = {
  site_code: string;
  name: string;
  client_name?: string | null;
  project_name?: string | null;
  city?: string | null;
  state?: string | null;
  status?: string;
  start_date: string;
  end_date?: string | null;
  site_manager_user_id?: string | null;
};

export type SiteResponse = {
  id: string;
  organization_id: string;
  site_code: string;
  name: string;
  client_name?: string | null;
  project_name?: string | null;
  city?: string | null;
  state?: string | null;
  status: string;
  start_date: string;
  end_date?: string | null;
  site_manager_user_id?: string | null;
  site_manager_name?: string | null;
  active_worker_count: number;
  total_expense_amount: string;
  created_at: string;
  updated_at: string;
};

export type SiteListResponse = {
  items: SiteResponse[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type SiteWorkerResponse = {
  id: string;
  worker_code: string;
  name: string;
  mobile?: string | null;
  trade?: string | null;
  daily_wage: string;
  status: string;
  assigned_from?: string | null;
  assignment_id?: string | null;
};

export type SiteWorkerAssignmentPayload = {
  worker_id: string;
  assigned_from?: string | null;
  is_primary?: boolean;
};

export type SiteAssignmentResponse = {
  id: string;
  organization_id: string;
  worker_id: string;
  site_id: string;
  is_primary: boolean;
  status: string;
  assigned_from: string;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
};

export type SiteStatsResponse = {
  site_id: string;
  active_worker_count: number;
  total_worker_assignments: number;
  attendance_records: number;
  present_days: string;
  absent_days: number;
  paid_days: string;
  regular_hours: string;
  overtime_hours: string;
  payroll_count: number;
  gross_payroll: string;
  net_payroll: string;
  expense_count: number;
  total_expenses: string;
};

export type SiteExpenseSummaryResponse = {
  site_id: string;
  total_expenses: string;
  expense_count: number;
  by_status: Array<{
    key: string;
    expense_count: number;
    total_amount: string;
  }>;
  by_category: Array<{
    key: string;
    expense_count: number;
    total_amount: string;
  }>;
};

export type MonthlyAttendanceReportResponse = {
  year: number;
  month: number;
  start_date: string;
  end_date: string;
  site_id?: string | null;
  worker_id?: string | null;
  total_workers: number;
  total_records: number;
  total_paid_days: string;
  total_regular_hours: string;
  total_ot_hours: string;
  workers: Array<{
    worker_id: string;
    worker_code: string;
    worker_name: string;
    present_days: string;
    absent_days: number;
    half_days: number;
    leave_days: number;
    weekly_off_days: number;
    paid_days: string;
    regular_hours: string;
    ot_hours: string;
    total_records: number;
    days: Array<{
      attendance_id: string;
      attendance_date: string;
      site_id: string;
      site_name: string;
      status: string;
      regular_hours: string;
      ot_hours: string;
      approval_status: string;
      payroll_locked: boolean;
    }>;
  }>;
};

export type MarkAttendancePayload = {
  worker_id: string;
  site_id: string;
  attendance_date: string;
  status: string;
  ot_hours?: number | string;
  remarks?: string | null;
};

export type AttendanceResponse = {
  id: string;
  organization_id: string;
  worker_id: string;
  worker_code: string;
  worker_name: string;
  site_id: string;
  site_name: string;
  attendance_date: string;
  status: string;
  regular_hours: string;
  ot_hours: string;
  approval_status: string;
  payroll_locked: boolean;
  remarks?: string | null;
  captured_by_user_id: string;
  approved_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type BulkAttendanceResponse = {
  created_count: number;
  updated_count: number;
  items: AttendanceResponse[];
};

export type PayrollPeriodResponse = {
  id: string;
  organization_id: string;
  name: string;
  period_start: string;
  period_end: string;
  pay_date?: string | null;
  status: string;
  payroll_count: number;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type PayrollEntryResponse = {
  id: string;
  organization_id: string;
  payroll_period_id: string;
  worker_id: string;
  worker_code: string;
  worker_name: string;
  site_id?: string | null;
  site_name?: string | null;
  daily_wage: string;
  overtime_rate: string;
  attendance_days: string;
  regular_hours: string;
  overtime_hours: string;
  overtime_amount: string;
  gross_amount: string;
  advance_amount: string;
  pf_rate_percent: string;
  pf_amount: string;
  net_amount: string;
  paid_amount: string;
  pending_amount: string;
  status: string;
  remarks?: string | null;
  posted_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type PayrollCalculationSummaryResponse = {
  payroll_period: PayrollPeriodResponse;
  generated_count: number;
  updated_count: number;
  skipped_count: number;
  total_gross_amount: string;
  total_advance_amount: string;
  total_pf_amount: string;
  total_net_amount: string;
  total_paid_amount: string;
  total_pending_amount: string;
  items: PayrollEntryResponse[];
};

export type PaymentResponse = {
  id: string;
  organization_id: string;
  payroll_id?: string | null;
  worker_id?: string | null;
  worker_code?: string | null;
  worker_name?: string | null;
  site_id?: string | null;
  site_name?: string | null;
  processed_by_user_id?: string | null;
  payment_type: string;
  payment_method: string;
  amount: string;
  payment_date: string;
  status: string;
  external_reference?: string | null;
  notes?: string | null;
  reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type MonthlyPayrollReportResponse = {
  year?: number | null;
  month?: number | null;
  payroll_period_id?: string | null;
  total_periods: number;
  total_payrolls: number;
  total_gross_amount: string;
  total_advance_amount: string;
  total_pf_amount: string;
  total_net_amount: string;
  total_paid_amount: string;
  total_pending_amount: string;
  items: Array<{
    payroll_period_id: string;
    period_name: string;
    period_start: string;
    period_end: string;
    payroll_count: number;
    worker_count: number;
    attendance_days: string;
    regular_hours: string;
    overtime_hours: string;
    gross_amount: string;
    advance_amount: string;
    pf_amount: string;
    net_amount: string;
    paid_amount: string;
    pending_amount: string;
  }>;
};

export type AttendanceSummaryReportResponse = {
  start_date?: string | null;
  end_date?: string | null;
  site_id?: string | null;
  worker_id?: string | null;
  total_sites: number;
  total_records: number;
  total_paid_days: string;
  total_regular_hours: string;
  total_overtime_hours: string;
  items: Array<{
    site_id: string;
    site_code: string;
    site_name: string;
    total_records: number;
    present_days: string;
    absent_days: number;
    half_days: number;
    leave_days: number;
    weekly_off_days: number;
    paid_days: string;
    regular_hours: string;
    overtime_hours: string;
  }>;
};

export type SiteExpenseReportResponse = {
  start_date?: string | null;
  end_date?: string | null;
  site_id?: string | null;
  category?: string | null;
  status?: string | null;
  total_sites: number;
  total_expenses: number;
  total_amount: string;
  items: Array<{
    site_id: string;
    site_code: string;
    site_name: string;
    expense_count: number;
    total_amount: string;
    draft_amount: string;
    approved_amount: string;
    paid_amount: string;
    rejected_amount: string;
  }>;
};

export type ExpenseListParams = {
  page?: number;
  page_size?: number;
  site_id?: string;
  category?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
};

export type ExpenseWritePayload = {
  site_id: string;
  category: string;
  amount: number | string;
  expense_date: string;
  payment_mode?: string;
  vendor_name?: string | null;
  description?: string | null;
  worker_id?: string | null;
  receipt_required?: boolean;
};

export type ExpenseResponse = {
  id: string;
  organization_id: string;
  site_id: string;
  site_name: string;
  worker_id?: string | null;
  worker_name?: string | null;
  submitted_by_user_id: string;
  submitted_by_name: string;
  approved_by_user_id?: string | null;
  approved_by_name?: string | null;
  category: string;
  expense_date: string;
  amount: string;
  payment_mode: string;
  vendor_name?: string | null;
  description?: string | null;
  status: string;
  receipt_required: boolean;
  created_at: string;
  updated_at: string;
};

export type ExpenseListResponse = {
  items: ExpenseResponse[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type ExpenseMetricsSummaryResponse = {
  total_expenses: string;
  this_month_expenses: string;
  highest_expense_site_id?: string | null;
  highest_expense_site_name?: string | null;
  highest_expense_site_amount: string;
  pending_approvals_count: number;
  total_count: number;
};

export type DocumentResponse = {
  id: string;
  organization_id: string;
  worker_id?: string | null;
  document_type: string;
  file_name: string;
  original_file_name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  uploaded_by: string;
  uploaded_by_name: string;
  created_at: string;
};

export type DocumentListResponse = {
  items: DocumentResponse[];
  total: number;
};

export type WorkerDetailResponse = {
  id: string;
  organization_id: string;
  worker_code: string;
  first_name?: string;
  last_name?: string | null;
  name: string;
  phone?: string | null;
  mobile?: string | null;
  trade?: string | null;
  default_wage_rate?: string;
  daily_wage?: string;
  pf_rate_percent?: string;
  status: string;
  assigned_site_id?: string | null;
  assigned_site_name?: string | null;
  joined_on?: string;
  joining_date?: string;
  advance_count?: number;
  advance_total?: string;
  last_advance_date?: string | null;
  last_advance_reason?: string | null;
};

export async function uploadWorkerDocument(workerId: string, documentType: string, file: File) {
  const formData = new FormData();
  formData.append("worker_id", workerId);
  formData.append("document_type", documentType);
  formData.append("file", file);

  const token = getStoredAuthToken();
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE;
  const url = `${baseUrl.replace(/\/$/, "")}/documents/upload`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "detail" in payload ? String((payload as { detail?: unknown }).detail) : "Upload failed";
    throw new ApiError(response.status, message, payload);
  }
  return payload as DocumentResponse;
}

export async function getWorkerDocuments(workerId: string) {
  return request<DocumentListResponse>(`/workers/${workerId}/documents`);
}

export async function getWorker(workerId: string) {
  return request<WorkerDetailResponse>(`/workers/${workerId}`);
}

export async function deleteDocument(documentId: string) {
  return request<void>(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function getDocumentDownloadUrl(documentId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE;
  return `${baseUrl.replace(/\/$/, "")}/documents/${documentId}/file`;
}

export async function getLabourCostAnalytics(params: { start_date?: string; end_date?: string; site_id?: string } = {}) {
  return request<LabourCostAnalyticsResponse>(`/reports/labour-cost${toQueryString(params)}`);
}

export async function getAttendanceAnalytics(params: { start_date?: string; end_date?: string; site_id?: string } = {}) {
  return request<AttendanceAnalyticsResponse>(`/reports/attendance-analytics${toQueryString(params)}`);
}

export async function getPayrollAnalytics(params: { year?: number; month?: number; site_id?: string } = {}) {
  return request<PayrollAnalyticsResponse>(`/reports/payroll-analytics${toQueryString(params)}`);
}

export async function getExpenseAnalytics(params: { start_date?: string; end_date?: string; site_id?: string; category?: string } = {}) {
  return request<ExpenseAnalyticsResponse>(`/reports/expense-analytics${toQueryString(params)}`);
}

export async function getSiteProfitability(params: { start_date?: string; end_date?: string } = {}) {
  return request<SiteProfitabilityResponse>(`/reports/site-profitability${toQueryString(params)}`);
}

export function getReportExportUrl(reportType: string, params: Record<string, string | number | undefined | null>, format: "pdf" | "excel" = "excel") {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE;
  const token = getStoredAuthToken();
  const query = toQueryString({ ...params, format });
  return `${baseUrl.replace(/\/$/, "")}/reports/${reportType}/export${query}`;
}

export type LabourCostAnalyticsResponse = {
  start_date?: string | null;
  end_date?: string | null;
  site_id?: string | null;
  total_labour_cost: string;
  monthly_labour_cost: string;
  average_worker_cost: string;
  total_active_workers: number;
  total_overtime_hours: string;
  site_wise_labour_cost: Array<{
    site_id: string;
    site_code: string;
    site_name: string;
    labour_cost: string;
    expense_cost: string;
    total_cost: string;
    active_workers: number;
  }>;
  monthly_trend: Array<{
    label: string;
    year: number;
    month: number;
    labour_cost: string;
    expense_cost: string;
    total_payroll: string;
    total_cost: string;
  }>;
  worker_payment_summary: Array<{
    worker_id: string;
    worker_code: string;
    worker_name: string;
    trade?: string | null;
    assigned_site_name?: string | null;
    gross_amount: string;
    paid_amount: string;
    pending_amount: string;
    advance_amount: string;
  }>;
};

export type AttendanceAnalyticsResponse = {
  start_date?: string | null;
  end_date?: string | null;
  site_id?: string | null;
  overall_attendance_rate: number;
  absence_rate: number;
  total_records: number;
  total_present: number;
  total_absent: number;
  total_leave: number;
  total_overtime_hours: string;
  absence_trends: Array<{
    label: string;
    date_str: string;
    present_count: number;
    absent_count: number;
    leave_count: number;
    overtime_hours: string;
    attendance_rate: number;
  }>;
  worker_rankings: Array<{
    worker_id: string;
    worker_code: string;
    worker_name: string;
    trade?: string | null;
    site_name?: string | null;
    present_days: number;
    absent_days: number;
    overtime_hours: string;
    attendance_rate: number;
  }>;
};

export type PayrollAnalyticsResponse = {
  year?: number | null;
  month?: number | null;
  site_id?: string | null;
  total_payroll: string;
  paid_amount: string;
  pending_amount: string;
  advance_payment_summary: string;
  monthly_payroll_trend: Array<{
    label: string;
    year: number;
    month: number;
    gross_amount: string;
    paid_amount: string;
    pending_amount: string;
    advance_amount: string;
    worker_count: number;
  }>;
};

export type ExpenseAnalyticsResponse = {
  start_date?: string | null;
  end_date?: string | null;
  site_id?: string | null;
  category?: string | null;
  total_expenses: string;
  highest_expense_category?: string | null;
  highest_cost_site_id?: string | null;
  highest_cost_site_name?: string | null;
  highest_cost_site_amount: string;
  category_wise_expenses: Array<{
    category: string;
    expense_count: number;
    total_amount: string;
    percentage: number;
  }>;
  site_wise_expenses: Array<{
    site_id: string;
    site_code: string;
    site_name: string;
    expense_count: number;
    total_amount: string;
  }>;
  monthly_expense_trend: Array<{
    label: string;
    year: number;
    month: number;
    expense_count: number;
    total_amount: string;
  }>;
};

export type SiteProfitabilityResponse = {
  start_date?: string | null;
  end_date?: string | null;
  total_sites: number;
  total_combined_cost: string;
  total_labour_cost: string;
  total_expense_cost: string;
  items: Array<{
    site_id: string;
    site_code: string;
    site_name: string;
    client_name?: string | null;
    status: string;
    revenue: string;
    labour_cost: string;
    expense_cost: string;
    total_site_cost: string;
    net_margin: string;
    labour_percentage: number;
    expense_percentage: number;
  }>;
};


