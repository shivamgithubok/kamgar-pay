"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BadgeIndianRupee,
  BarChart3,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  HardHat,
  MapPinned,
  PieChart as PieChartIcon,
  ReceiptText,
  RefreshCw,
  UsersRound,
  Wallet,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { DonutChart, LineChart } from "@/components/charts";
import { BarChart } from "@/components/dashboard-chart";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ApiError,
  getAttendanceAnalytics,
  getExpenseAnalytics,
  getLabourCostAnalytics,
  getPayrollAnalytics,
  getReportExportUrl,
  getSiteProfitability,
  getSites,
  type AttendanceAnalyticsResponse,
  type ExpenseAnalyticsResponse,
  type LabourCostAnalyticsResponse,
  type PayrollAnalyticsResponse,
  type SiteProfitabilityResponse,
  type SiteResponse,
} from "@/lib/api-client";

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function formatMoney(value: string | number) {
  return `INR ${moneyFormatter.format(Number(value || 0))}`;
}

export default function ReportsPage() {
  const [sites, setSites] = useState<SiteResponse[]>([]);
  const [labourData, setLabourData] = useState<LabourCostAnalyticsResponse | null>(null);
  const [attendanceData, setAttendanceData] = useState<AttendanceAnalyticsResponse | null>(null);
  const [payrollData, setPayrollData] = useState<PayrollAnalyticsResponse | null>(null);
  const [expenseData, setExpenseData] = useState<ExpenseAnalyticsResponse | null>(null);
  const [profitabilityData, setProfitabilityData] = useState<SiteProfitabilityResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    start_date: "",
    end_date: "",
    site_id: "",
  });
  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [refreshToken, setRefreshToken] = useState(0);

  // Load sites for filter dropdown
  useEffect(() => {
    const loadSitesList = async () => {
      try {
        const response = await getSites({ page: 1, page_size: 200 });
        setSites(response.items);
      } catch (err) {
        console.error("Could not load sites for report filters:", err);
      }
    };
    void loadSitesList();
  }, []);

  // Fetch all analytics datasets concurrently
  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const params = {
          start_date: appliedFilters.start_date || undefined,
          end_date: appliedFilters.end_date || undefined,
          site_id: appliedFilters.site_id || undefined,
        };

        const [labourRes, attendanceRes, payrollRes, expenseRes, profitRes] = await Promise.all([
          getLabourCostAnalytics(params),
          getAttendanceAnalytics(params),
          getPayrollAnalytics({ site_id: params.site_id }),
          getExpenseAnalytics(params),
          getSiteProfitability({ start_date: params.start_date, end_date: params.end_date }),
        ]);

        setLabourData(labourRes);
        setAttendanceData(attendanceRes);
        setPayrollData(payrollRes);
        setExpenseData(expenseRes);
        setProfitabilityData(profitRes);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Analytics data could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void loadAnalytics();
  }, [appliedFilters, refreshToken]);

  // Labour Metric Cards
  const labourCards = useMemo(() => {
    return [
      {
        label: "Total Labour Cost",
        value: formatMoney(labourData?.total_labour_cost ?? 0),
        delta: loading ? "Loading" : `${labourData?.monthly_trend.length ?? 0} active periods`,
        icon: BadgeIndianRupee,
        tone: "clay" as const,
      },
      {
        label: "Average Worker Cost",
        value: formatMoney(labourData?.average_worker_cost ?? 0),
        delta: loading ? "Loading" : "Per active worker",
        icon: UsersRound,
        tone: "amber" as const,
      },
      {
        label: "Total Active Workers",
        value: String(labourData?.total_active_workers ?? 0),
        delta: loading ? "Loading" : "Active headcount",
        icon: HardHat,
        tone: "mint" as const,
      },
      {
        label: "Overtime Hours",
        value: `${Number(labourData?.total_overtime_hours ?? 0).toFixed(0)} hrs`,
        delta: loading ? "Loading" : "Logged overtime",
        icon: Clock,
        tone: "ink" as const,
      },
    ];
  }, [loading, labourData]);

  // Payroll Metric Cards
  const payrollCards = useMemo(() => {
    return [
      {
        label: "Total Payroll",
        value: formatMoney(payrollData?.total_payroll ?? 0),
        delta: loading ? "Loading" : "Gross accrued payroll",
        icon: Wallet,
        tone: "clay" as const,
      },
      {
        label: "Paid Amount",
        value: formatMoney(payrollData?.paid_amount ?? 0),
        delta: loading ? "Loading" : "Disbursed to workers",
        icon: CheckCircle2,
        tone: "mint" as const,
      },
      {
        label: "Pending Amount",
        value: formatMoney(payrollData?.pending_amount ?? 0),
        delta: loading ? "Loading" : "Awaiting payment",
        icon: Clock,
        tone: "amber" as const,
      },
      {
        label: "Advances Logged",
        value: formatMoney(payrollData?.advance_payment_summary ?? 0),
        delta: loading ? "Loading" : "Worker advance payments",
        icon: BadgeIndianRupee,
        tone: "ink" as const,
      },
    ];
  }, [loading, payrollData]);

  // Expense Metric Cards
  const expenseCards = useMemo(() => {
    return [
      {
        label: "Total Expense",
        value: formatMoney(expenseData?.total_expenses ?? 0),
        delta: loading ? "Loading" : `${expenseData?.category_wise_expenses.length ?? 0} expense categories`,
        icon: ReceiptText,
        tone: "clay" as const,
      },
      {
        label: "Highest Expense Category",
        value: expenseData?.highest_expense_category || "N/A",
        delta: loading ? "Loading" : "Primary expense driver",
        icon: BarChart3,
        tone: "amber" as const,
      },
      {
        label: "Highest Cost Site",
        value: expenseData?.highest_cost_site_name || "N/A",
        delta: loading ? "Loading" : formatMoney(expenseData?.highest_cost_site_amount ?? 0),
        icon: Building2,
        tone: "mint" as const,
      },
      {
        label: "Attendance Rate",
        value: `${attendanceData?.overall_attendance_rate ?? 0}%`,
        delta: loading ? "Loading" : `${attendanceData?.total_records ?? 0} total muster logs`,
        icon: Activity,
        tone: "ink" as const,
      },
    ];
  }, [loading, expenseData, attendanceData]);

  // Visual Chart Data points
  const payrollTrendPoints = useMemo(() => {
    if (!payrollData) return [];
    return [...payrollData.monthly_payroll_trend].reverse().map((item) => ({
      label: item.label,
      value: Number(item.gross_amount),
      secondaryValue: Number(item.paid_amount),
    }));
  }, [payrollData]);

  const attendanceTrendPoints = useMemo(() => {
    if (!attendanceData) return [];
    return [...attendanceData.absence_trends].reverse().map((item) => ({
      label: item.label,
      value: item.present_count,
      secondaryValue: item.absent_count,
    }));
  }, [attendanceData]);

  const expenseDistributionPoints = useMemo(() => {
    if (!expenseData) return [];
    return expenseData.category_wise_expenses.map((cat) => ({
      label: cat.category,
      value: Number(cat.total_amount),
    }));
  }, [expenseData]);

  const siteCostComparisonPoints = useMemo(() => {
    if (!profitabilityData) return [];
    return profitabilityData.items.map((site) => ({
      label: site.site_code,
      value: Number(site.labour_cost),
      secondaryValue: Number(site.expense_cost),
    }));
  }, [profitabilityData]);

  const triggerExport = (reportType: string, format: "pdf" | "excel") => {
    const url = getReportExportUrl(
      reportType,
      {
        start_date: appliedFilters.start_date || undefined,
        end_date: appliedFilters.end_date || undefined,
        site_id: appliedFilters.site_id || undefined,
      },
      format
    );
    window.open(url, "_blank");
  };

  return (
    <AppShell activePath="/reports">
      <div className="space-y-8">
        <PageHeader
          eyebrow="Enterprise Reporting"
          title="Advanced Reports & Analytics"
          description="Comprehensive intelligence on labour costs, site expenses, payroll trends, worker attendance, and site profitability statements."
        />

        {/* Global Filter & Export Controls */}
        <Card className="animate-fade-up overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  Analytics Controls & Exports
                </CardTitle>
                <CardDescription>Apply global filters and download standard accounting reports.</CardDescription>
              </div>

              {/* Export Trigger Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => triggerExport("labour-cost", "pdf")}>
                  <FileText className="h-3.5 w-3.5 text-rose-600" />
                  Labour PDF
                </Button>
                <Button size="sm" variant="outline" onClick={() => triggerExport("payroll-analytics", "excel")}>
                  <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
                  Payroll Excel
                </Button>
                <Button size="sm" variant="outline" onClick={() => triggerExport("expense-analytics", "pdf")}>
                  <FileText className="h-3.5 w-3.5 text-rose-600" />
                  Expenses PDF
                </Button>
                <Button size="sm" variant="outline" onClick={() => triggerExport("site-profitability", "excel")}>
                  <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
                  Profitability Excel
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-xs font-semibold text-muted-foreground">Start Date</label>
                <Input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-muted-foreground">End Date</label>
                <Input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-muted-foreground">Project Site</label>
                <select
                  className="h-10 w-full rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={filters.site_id}
                  onChange={(e) => setFilters({ ...filters, site_id: e.target.value })}
                >
                  <option value="">All Sites</option>
                  {sites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.site_code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end gap-2">
                <Button className="w-full" variant="outline" onClick={() => setAppliedFilters(filters)}>
                  <Filter className="h-4 w-4" />
                  Apply Filters
                </Button>
                <Button variant="ghost" onClick={() => setRefreshToken((v) => v + 1)}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="animate-pulse rounded-2xl border border-border bg-card/70 p-6 text-center text-sm text-muted-foreground">
            Loading analytics dashboard engine...
          </div>
        ) : null}

        {errorMessage ? (
          <div className="flex items-center justify-between rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <span>{errorMessage}</span>
            <button className="font-bold underline" onClick={() => setRefreshToken((v) => v + 1)}>
              Retry
            </button>
          </div>
        ) : null}

        {/* 1. LABOUR OVERVIEW */}
        <section className="space-y-4">
          <h3 className="text-lg font-black text-foreground flex items-center gap-2">
            <UsersRound className="h-5 w-5 text-labour-amber" />
            Labour Cost Overview
          </h3>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {labourCards.map((card) => (
              <MetricCard key={card.label} {...card} />
            ))}
          </div>
        </section>

        {/* 2. PAYROLL OVERVIEW */}
        <section className="space-y-4">
          <h3 className="text-lg font-black text-foreground flex items-center gap-2">
            <Wallet className="h-5 w-5 text-emerald-600" />
            Payroll Overview
          </h3>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {payrollCards.map((card) => (
              <MetricCard key={card.label} {...card} />
            ))}
          </div>
        </section>

        {/* 3. EXPENSE OVERVIEW */}
        <section className="space-y-4">
          <h3 className="text-lg font-black text-foreground flex items-center gap-2">
            <ReceiptText className="h-5 w-5 text-sky-600" />
            Expense & Site Operational Overview
          </h3>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {expenseCards.map((card) => (
              <MetricCard key={card.label} {...card} />
            ))}
          </div>
        </section>

        {/* 4. VISUAL CHARTS GRID */}
        <section className="space-y-4">
          <h3 className="text-lg font-black text-foreground flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-indigo-600" />
            Visual Intelligence Charts
          </h3>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Monthly Payroll Trend Line Chart */}
            <LineChart
              title="Monthly Payroll Trend"
              description="Gross accrued payroll vs Disbursed paid amount over time."
              points={payrollTrendPoints}
              valueLabel="Gross Payroll (INR)"
              secondaryLabel="Paid Amount (INR)"
              valueFormatter={formatMoney}
            />

            {/* Attendance Trend Line Chart */}
            <LineChart
              title="Daily Attendance Trend"
              description="Present worker muster count vs Absent state count."
              points={attendanceTrendPoints}
              valueLabel="Present Workers"
              secondaryLabel="Absent Workers"
            />

            {/* Expense Distribution Donut Chart */}
            <DonutChart
              title="Category-wise Expense Distribution"
              description="Itemized breakdown of site operational costs by category."
              points={expenseDistributionPoints}
              totalFormatter={formatMoney}
            />

            {/* Site Cost Comparison Bar Chart */}
            <BarChart
              title="Site Cost Comparison"
              description="Labour costs (dark) vs Operational site expenses (amber)."
              points={siteCostComparisonPoints}
              valueLabel="Labour Cost"
              secondaryLabel="Site Expenses"
            />
          </div>
        </section>

        {/* 5. SITE PROFITABILITY & STATEMENT TABLE */}
        <section className="space-y-4">
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold">Site Profitability & Cost Statement</CardTitle>
                <CardDescription>Comparison of site labour expenditure, site expenses, total cost, and labour share.</CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={() => triggerExport("site-profitability", "pdf")}>
                <Download className="h-4 w-4" />
                Export Statement
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Site Code</TableHead>
                    <TableHead>Site Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Labour Cost</TableHead>
                    <TableHead>Site Expenses</TableHead>
                    <TableHead>Total Site Cost</TableHead>
                    <TableHead>Labour %</TableHead>
                    <TableHead>Expense %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!loading && profitabilityData?.items.length === 0 ? (
                    <TableRow>
                      <TableCell className="h-24 text-center text-muted-foreground" colSpan={8}>
                        No site cost records found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    profitabilityData?.items.map((item) => (
                      <TableRow key={item.site_id}>
                        <TableCell className="font-semibold">{item.site_code}</TableCell>
                        <TableCell>
                          <div className="font-semibold text-foreground">{item.site_name}</div>
                          <div className="text-xs text-muted-foreground">{item.client_name || "Internal Site"}</div>
                        </TableCell>
                        <TableCell>
                          <StatusPill value={item.status} />
                        </TableCell>
                        <TableCell className="font-semibold text-foreground whitespace-nowrap">
                          {formatMoney(item.labour_cost)}
                        </TableCell>
                        <TableCell className="font-semibold text-foreground whitespace-nowrap">
                          {formatMoney(item.expense_cost)}
                        </TableCell>
                        <TableCell className="font-bold text-foreground whitespace-nowrap">
                          {formatMoney(item.total_site_cost)}
                        </TableCell>
                        <TableCell className="text-xs font-semibold">
                          <span className="rounded-md bg-primary/10 px-2 py-0.5 text-primary">
                            {item.labour_percentage}%
                          </span>
                        </TableCell>
                        <TableCell className="text-xs font-semibold">
                          <span className="rounded-md bg-amber-500/10 px-2 py-0.5 text-amber-600">
                            {item.expense_percentage}%
                          </span>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </section>

        {/* 6. TOP WORKER ATTENDANCE RANKING TABLE */}
        <section className="space-y-4">
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold">Worker Attendance & Overtime Rankings</CardTitle>
                <CardDescription>Top workers ranked by attendance consistency and logged overtime hours.</CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={() => triggerExport("attendance-analytics", "excel")}>
                <Download className="h-4 w-4" />
                Export Rankings
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Worker Code</TableHead>
                    <TableHead>Worker Name</TableHead>
                    <TableHead>Trade</TableHead>
                    <TableHead>Site</TableHead>
                    <TableHead>Present Days</TableHead>
                    <TableHead>Absent Days</TableHead>
                    <TableHead>OT Hours</TableHead>
                    <TableHead>Attendance Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!loading && attendanceData?.worker_rankings.length === 0 ? (
                    <TableRow>
                      <TableCell className="h-24 text-center text-muted-foreground" colSpan={8}>
                        No attendance ranking data available.
                      </TableCell>
                    </TableRow>
                  ) : (
                    attendanceData?.worker_rankings.slice(0, 15).map((w) => (
                      <TableRow key={w.worker_id}>
                        <TableCell className="font-semibold">{w.worker_code}</TableCell>
                        <TableCell className="font-semibold text-foreground">{w.worker_name}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{w.trade || "General"}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{w.site_name || "Unassigned"}</TableCell>
                        <TableCell className="font-semibold text-emerald-600">{w.present_days}</TableCell>
                        <TableCell className="font-semibold text-rose-500">{w.absent_days}</TableCell>
                        <TableCell className="font-semibold">{w.overtime_hours} hrs</TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-bold ${
                              w.attendance_rate >= 80
                                ? "bg-emerald-100 text-emerald-800"
                                : w.attendance_rate >= 50
                                ? "bg-amber-100 text-amber-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {w.attendance_rate}%
                          </span>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </section>
      </div>
    </AppShell>
  );
}
