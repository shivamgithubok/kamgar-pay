"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  BadgeIndianRupee,
  Building2,
  CheckCircle2,
  Clock,
  Edit3,
  FileText,
  Filter,
  Plus,
  ReceiptText,
  RefreshCw,
  Save,
  Trash2,
  Upload,
  X,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ApiError,
  createExpense,
  deleteExpense,
  getExpenseMetricsSummary,
  getExpenses,
  getSites,
  updateExpense,
  type ExpenseMetricsSummaryResponse,
  type ExpenseResponse,
  type ExpenseWritePayload,
  type SiteResponse,
} from "@/lib/api-client";

type ExpenseFormState = {
  site_id: string;
  category: string;
  amount: string;
  expense_date: string;
  payment_mode: string;
  vendor_name: string;
  description: string;
  receipt_required: boolean;
  status?: string;
};

const emptyForm: ExpenseFormState = {
  site_id: "",
  category: "Material",
  amount: "",
  expense_date: new Date().toISOString().slice(0, 10),
  payment_mode: "cash",
  vendor_name: "",
  description: "",
  receipt_required: true,
  status: "draft",
};

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });

function formatMoney(value: string | number) {
  return `INR ${moneyFormatter.format(Number(value || 0))}`;
}

const CATEGORIES = [
  "Material",
  "Labour",
  "Transport",
  "Tools",
  "Safety",
  "Utilities",
  "Subcontractor",
  "Other",
];

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [sites, setSites] = useState<SiteResponse[]>([]);
  const [metrics, setMetrics] = useState<ExpenseMetricsSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState<ExpenseResponse | null>(null);
  const [form, setForm] = useState<ExpenseFormState>(emptyForm);

  const [filters, setFilters] = useState({
    search: "",
    site_id: "",
    category: "",
    status: "",
    start_date: "",
    end_date: "",
  });
  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [refreshToken, setRefreshToken] = useState(0);

  // Load sites for site selection dropdown
  useEffect(() => {
    const loadSitesList = async () => {
      try {
        const response = await getSites({ page: 1, page_size: 200 });
        setSites(response.items);
      } catch (err) {
        console.error("Could not load sites list for expense dropdown:", err);
      }
    };
    void loadSitesList();
  }, []);

  // Load expenses and metrics
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const [expensesRes, summaryRes] = await Promise.all([
          getExpenses({
            page: 1,
            page_size: 100,
            search: appliedFilters.search,
            site_id: appliedFilters.site_id,
            category: appliedFilters.category,
            status: appliedFilters.status,
            start_date: appliedFilters.start_date,
            end_date: appliedFilters.end_date,
          }),
          getExpenseMetricsSummary().catch(() => null),
        ]);
        setExpenses(expensesRes.items);
        setMetrics(summaryRes);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Expenses could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void loadData();
  }, [appliedFilters, refreshToken]);

  const dashboardCards = useMemo(() => {
    const totalExp = metrics?.total_expenses ?? expenses.reduce((sum, e) => sum + Number(e.amount), 0);
    const thisMonthExp = metrics?.this_month_expenses ?? "0";
    const highestSite = metrics?.highest_expense_site_name ?? "None";
    const highestAmount = metrics?.highest_expense_site_amount ?? "0";
    const pendingCount = metrics?.pending_approvals_count ?? expenses.filter((e) => e.status === "draft" || e.status === "review").length;

    return [
      {
        label: "Total Expenses",
        value: formatMoney(totalExp),
        delta: loading ? "Loading" : `${metrics?.total_count ?? expenses.length} transactions recorded`,
        icon: BadgeIndianRupee,
        tone: "clay" as const,
      },
      {
        label: "This Month Expense",
        value: formatMoney(thisMonthExp),
        delta: loading ? "Loading" : "Current calendar month",
        icon: ReceiptText,
        tone: "amber" as const,
      },
      {
        label: "Highest Expense Site",
        value: highestSite !== "None" ? highestSite : "N/A",
        delta: loading ? "Loading" : highestSite !== "None" ? formatMoney(highestAmount) : "No expenses yet",
        icon: Building2,
        tone: "mint" as const,
      },
      {
        label: "Pending Approvals",
        value: String(pendingCount),
        delta: loading ? "Loading" : "Draft / pending review",
        icon: Clock,
        tone: "ink" as const,
      },
    ];
  }, [loading, metrics, expenses]);

  const openCreateForm = () => {
    setEditingExpense(null);
    setForm({
      ...emptyForm,
      site_id: sites.length > 0 ? sites[0].id : "",
    });
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (expense: ExpenseResponse) => {
    setEditingExpense(expense);
    setForm({
      site_id: expense.site_id,
      category: expense.category,
      amount: String(expense.amount),
      expense_date: expense.expense_date,
      payment_mode: expense.payment_mode,
      vendor_name: expense.vendor_name ?? "",
      description: expense.description ?? "",
      receipt_required: expense.receipt_required,
      status: expense.status,
    });
    setFormError(null);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingExpense(null);
    setFormError(null);
    setForm(emptyForm);
  };

  const submitForm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.site_id) {
      setFormError("Please select a site.");
      return;
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setFormError("Please enter a valid amount greater than 0.");
      return;
    }

    setSaving(true);
    setFormError(null);
    try {
      const payload: ExpenseWritePayload & { status?: string } = {
        site_id: form.site_id,
        category: form.category,
        amount: Number(form.amount),
        expense_date: form.expense_date,
        payment_mode: form.payment_mode,
        vendor_name: form.vendor_name.trim() || null,
        description: form.description.trim() || null,
        receipt_required: form.receipt_required,
        ...(form.status ? { status: form.status } : {}),
      };

      if (editingExpense) {
        await updateExpense(editingExpense.id, payload);
      } else {
        await createExpense(payload);
      }
      closeForm();
      setRefreshToken((val) => val + 1);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Expense could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this expense record?")) return;
    setDeletingId(id);
    try {
      await deleteExpense(id);
      setRefreshToken((val) => val + 1);
    } catch (error) {
      alert(error instanceof ApiError ? error.message : "Could not delete expense.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleStatusChange = async (expense: ExpenseResponse, newStatus: string) => {
    try {
      await updateExpense(expense.id, { status: newStatus });
      setRefreshToken((val) => val + 1);
    } catch (error) {
      alert(error instanceof ApiError ? error.message : "Status update failed.");
    }
  };

  return (
    <AppShell activePath="/expenses">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Financial control"
          title="Expenses"
          description="Track site-level expenses, material, transport, and operational costs across all construction sites."
          action={showForm ? "Close form" : "Create expense"}
          onAction={showForm ? closeForm : openCreateForm}
        />

        {/* Dashboard Metric Cards */}
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {dashboardCards.map((card) => (
            <MetricCard key={card.label} {...card} />
          ))}
        </div>

        {/* Form Modal / Card */}
        {showForm ? (
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader>
              <CardTitle>{editingExpense ? "Edit expense" : "Record new expense"}</CardTitle>
              <CardDescription>
                {editingExpense
                  ? `Editing expense record for ${editingExpense.site_name}`
                  : "Log site expenditures including material, transport, equipment, or petty cash."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="grid gap-4 lg:grid-cols-2" onSubmit={submitForm}>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Site *</label>
                  <select
                    required
                    className="h-10 w-full rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.site_id}
                    onChange={(e) => setForm({ ...form, site_id: e.target.value })}
                  >
                    <option value="" disabled>
                      Select construction site...
                    </option>
                    {sites.map((site) => (
                      <option key={site.id} value={site.id}>
                        {site.name} ({site.site_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Category *</label>
                  <select
                    required
                    className="h-10 w-full rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Amount (INR) *</label>
                  <Input
                    required
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="e.g. 50000"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Expense Date *</label>
                  <Input
                    required
                    type="date"
                    value={form.expense_date}
                    onChange={(e) => setForm({ ...form, expense_date: e.target.value })}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Payment Mode</label>
                  <select
                    className="h-10 w-full rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.payment_mode}
                    onChange={(e) => setForm({ ...form, payment_mode: e.target.value })}
                  >
                    <option value="cash">Cash</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="upi">UPI</option>
                    <option value="card">Card / Cheque</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Vendor / Supplier Name</label>
                  <Input
                    placeholder="e.g. ACC Cement Traders"
                    value={form.vendor_name}
                    onChange={(e) => setForm({ ...form, vendor_name: e.target.value })}
                  />
                </div>

                {editingExpense ? (
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-muted-foreground">Approval Status</label>
                    <select
                      className="h-10 w-full rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value })}
                    >
                      <option value="draft">Draft</option>
                      <option value="approved">Approved</option>
                      <option value="paid">Paid</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                ) : null}

                <div className="lg:col-span-2">
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Description / Notes</label>
                  <textarea
                    rows={3}
                    className="w-full rounded-xl border border-input bg-background p-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="Add itemized details, invoice numbers, or site supervisor notes..."
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>

                {/* Attachment Upload Placeholder */}
                <div className="rounded-2xl border border-dashed border-border bg-card/50 p-4 text-center text-xs text-muted-foreground lg:col-span-2">
                  <div className="flex items-center justify-center gap-2 font-semibold">
                    <Upload className="h-4 w-4 text-muted-foreground" />
                    Receipt Attachment Placeholder
                  </div>
                  <p className="mt-1 text-[11px]">Supports PDF, PNG, JPG (up to 10MB). Document link will attach on submit.</p>
                </div>

                <div className="flex flex-wrap gap-3 lg:col-span-2">
                  <Button disabled={saving} type="submit">
                    <Save className="h-4 w-4" />
                    {saving ? "Saving..." : editingExpense ? "Update Expense" : "Save Expense"}
                  </Button>
                  <Button disabled={saving} type="button" variant="outline" onClick={closeForm}>
                    <X className="h-4 w-4" />
                    Cancel
                  </Button>
                </div>

                {formError ? (
                  <p className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 lg:col-span-2">
                    {formError}
                  </p>
                ) : null}
              </form>
            </CardContent>
          </Card>
        ) : null}

        {/* Expenses Table Card */}
        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Expense Register</CardTitle>
            <CardDescription>Filter site costs by category, status, site, or date range.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Filter Bar */}
            <div className="grid gap-3 md:grid-cols-6">
              <Input
                className="md:col-span-2"
                placeholder="Search description, vendor..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              />
              <select
                className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.site_id}
                onChange={(e) => setFilters({ ...filters, site_id: e.target.value })}
              >
                <option value="">All Sites</option>
                {sites.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <select
                className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <select
                className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="approved">Approved</option>
                <option value="paid">Paid</option>
                <option value="rejected">Rejected</option>
              </select>
              <Input
                type="date"
                placeholder="Start Date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => setAppliedFilters(filters)}>
                <Filter className="h-4 w-4" />
                Apply Filters
              </Button>
              <Button variant="ghost" onClick={() => setRefreshToken((v) => v + 1)}>
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  const resetFilters = { search: "", site_id: "", category: "", status: "", start_date: "", end_date: "" };
                  setFilters(resetFilters);
                  setAppliedFilters(resetFilters);
                }}
              >
                Clear
              </Button>
            </div>

            {loading ? (
              <div className="animate-pulse rounded-2xl border border-border bg-card/70 p-4 text-sm text-muted-foreground">
                Loading expenses...
              </div>
            ) : null}

            {errorMessage ? (
              <div className="flex flex-col gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
                <span>{errorMessage}</span>
                <button
                  className="font-bold underline underline-offset-4"
                  onClick={() => setRefreshToken((v) => v + 1)}
                  type="button"
                >
                  Try again
                </button>
              </div>
            ) : null}

            {/* Table */}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Site</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Vendor / Details</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Created By</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && expenses.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-28 text-center text-muted-foreground" colSpan={8}>
                      No expenses match the current criteria.
                    </TableCell>
                  </TableRow>
                ) : (
                  expenses.map((expense) => (
                    <TableRow key={expense.id}>
                      <TableCell className="font-semibold text-muted-foreground whitespace-nowrap">
                        {expense.expense_date}
                      </TableCell>
                      <TableCell>
                        <div className="font-semibold text-foreground">{expense.site_name}</div>
                        <div className="text-xs text-muted-foreground">Mode: {expense.payment_mode}</div>
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center rounded-full bg-secondary/80 px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
                          {expense.category}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium text-foreground">{expense.vendor_name || "General Vendor"}</div>
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {expense.description || "No description provided"}
                        </div>
                      </TableCell>
                      <TableCell className="font-bold text-foreground whitespace-nowrap">
                        {formatMoney(expense.amount)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {expense.submitted_by_name}
                      </TableCell>
                      <TableCell>
                        <StatusPill value={expense.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {expense.status === "draft" ? (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                              title="Approve Expense"
                              onClick={() => handleStatusChange(expense, "approved")}
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" />
                            </Button>
                          ) : null}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8"
                            onClick={() => openEditForm(expense)}
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                            disabled={deletingId === expense.id}
                            onClick={() => handleDelete(expense.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {!showForm && !loading && !errorMessage && expenses.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-card/60 p-8 text-center text-sm text-muted-foreground">
            No expense records found. Click below to add your first site expense.
            <div className="mt-4">
              <Button onClick={openCreateForm}>
                <Plus className="h-4 w-4" />
                Create Expense
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
