"use client";

import { useEffect, useMemo, useState } from "react";
import { BadgeIndianRupee, Building2, ClipboardCheck, Filter, Search, UsersRound } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { PersonAvatar } from "@/components/person-avatar";
import { SiteBoard } from "@/components/site-board";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/contexts/auth-context";
import {
  ApiError,
  getMonthlyAttendanceReport,
  getMonthlyPayrollReport,
  getSiteExpenseReport,
  getSites,
  getWorkers,
  type MonthlyAttendanceReportResponse,
  type MonthlyPayrollReportResponse,
  type SiteExpenseReportResponse,
  type SiteResponse,
  type WorkersListResponse,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function localDateKey(value: Date) {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

const FEED_TABS = [
  { id: "sites", label: "Sites" },
  { id: "attendance", label: "Attendance" },
  { id: "workforce", label: "Workforce" },
  { id: "payroll", label: "Payroll" },
  { id: "categories", label: "Worker categories" },
] as const;

type FeedTab = (typeof FEED_TABS)[number]["id"];

export default function DashboardPage() {
  const { user } = useAuth();
  const [workersResponse, setWorkersResponse] = useState<WorkersListResponse | null>(null);
  const [attendanceReport, setAttendanceReport] = useState<MonthlyAttendanceReportResponse | null>(null);
  const [payrollReport, setPayrollReport] = useState<MonthlyPayrollReportResponse | null>(null);
  const [expenseReport, setExpenseReport] = useState<SiteExpenseReportResponse | null>(null);
  const [sites, setSites] = useState<SiteResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);
  const [feedTab, setFeedTab] = useState<FeedTab>("sites");
  const [search, setSearch] = useState("");
  const [showFeed, setShowFeed] = useState(false);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setErrorMessage(null);
      const now = new Date();
      try {
        const results = await Promise.allSettled([
          getWorkers(),
          getMonthlyAttendanceReport(now.getFullYear(), now.getMonth() + 1),
          getMonthlyPayrollReport(now.getFullYear(), now.getMonth() + 1),
          getSiteExpenseReport(),
          getSites(),
        ]);
        const [workersResult, attendanceResult, payrollResult, expenseResult, sitesResult] = results;
        setWorkersResponse(workersResult.status === "fulfilled" ? workersResult.value : null);
        setAttendanceReport(attendanceResult.status === "fulfilled" ? attendanceResult.value : null);
        setPayrollReport(payrollResult.status === "fulfilled" ? payrollResult.value : null);
        setExpenseReport(expenseResult.status === "fulfilled" ? expenseResult.value : null);
        setSites(sitesResult.status === "fulfilled" ? sitesResult.value.items : []);
        const failed = results.find((result) => result.status === "rejected");
        if (failed && failed.status === "rejected") {
          setErrorMessage(failed.reason instanceof ApiError ? failed.reason.message : "Some dashboard data could not be loaded.");
        }
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Dashboard data could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void loadDashboard();
  }, [refreshToken]);

  useEffect(() => {
    setShowFeed(false);
    const timer = window.setTimeout(() => setShowFeed(true), 700);
    return () => window.clearTimeout(timer);
  }, [loading, sites.length]);

  const workers = workersResponse?.items ?? [];
  const attendanceWorkers = attendanceReport?.workers ?? [];
  const payrollItems = payrollReport?.items ?? [];
  const expenseItems = expenseReport?.items ?? [];

  const presentToday = useMemo(() => {
    const today = localDateKey(new Date());
    return attendanceWorkers.reduce(
      (count, worker) => count + worker.days.filter((day) => day.attendance_date === today && day.status === "present").length,
      0,
    );
  }, [attendanceWorkers]);

  const presentRows = useMemo(() => {
    const today = localDateKey(new Date());
    return attendanceWorkers.map((worker) => {
      const todayRecord = worker.days.find((day) => day.attendance_date === today);
      return {
        name: worker.worker_name,
        code: worker.worker_code,
        status: todayRecord?.status ?? "not marked",
        site: todayRecord?.site_name ?? "—",
        present: worker.present_days,
        ot: worker.ot_hours,
      };
    });
  }, [attendanceWorkers]);

  const workerCategories = useMemo(() => {
    const counts = new Map<string, number>();
    workers.forEach((worker) => {
      const category = worker.trade || "Uncategorized";
      counts.set(category, (counts.get(category) ?? 0) + 1);
    });
    return [...counts.entries()].sort(([, left], [, right]) => right - left).map(([label, value]) => ({ label, value }));
  }, [workers]);

  const matchesSearch = (value: string) => value.toLowerCase().includes(search.trim().toLowerCase());

  const feedRows = useMemo(() => {
    if (feedTab === "sites") {
      return sites
        .filter((site) => !search || matchesSearch(`${site.name} ${site.site_code} ${site.city ?? ""} ${site.status}`))
        .map((site) => ({
          id: site.id,
          name: site.name,
          meta: site.site_code,
          col2: [site.city, site.state].filter(Boolean).join(", ") || "Unspecified",
          col3: String(site.active_worker_count),
          col4: `₹${moneyFormatter.format(Number(site.total_expense_amount || 0))}`,
          status: site.status,
        }));
    }
    if (feedTab === "attendance") {
      return presentRows
        .filter((row) => !search || matchesSearch(`${row.name} ${row.code} ${row.status} ${row.site}`))
        .map((row) => ({
          id: row.code,
          name: row.name,
          meta: row.code,
          col2: row.site,
          col3: String(row.present),
          col4: String(row.ot),
          status: row.status,
        }));
    }
    if (feedTab === "workforce") {
      return workers
        .filter((worker) => !search || matchesSearch(`${worker.name} ${worker.worker_code} ${worker.trade ?? ""} ${worker.assigned_site_name ?? ""}`))
        .slice(0, 12)
        .map((worker) => ({
          id: worker.id,
          name: worker.name,
          meta: worker.worker_code,
          col2: worker.trade || "General",
          col3: worker.assigned_site_name ?? "Unassigned",
          col4: `₹${worker.daily_wage}`,
          status: worker.status,
        }));
    }
    if (feedTab === "payroll") {
      return payrollItems
        .filter((item) => !search || matchesSearch(`${item.period_name}`))
        .map((item) => ({
          id: item.payroll_period_id,
          name: item.period_name,
          meta: `${item.payroll_count} payrolls`,
          col2: String(item.worker_count),
          col3: `₹${moneyFormatter.format(Number(item.gross_amount))}`,
          col4: `₹${moneyFormatter.format(Number(item.pending_amount))}`,
          status: Number(item.pending_amount) > 0 ? "pending" : "paid",
        }));
    }
    return workerCategories
      .filter((item) => !search || matchesSearch(item.label))
      .map((item) => ({
        id: item.label,
        name: item.label,
        meta: "Trade",
        col2: String(item.value),
        col3: `${workers.length ? Math.round((item.value / workers.length) * 100) : 0}%`,
        col4: "Roster share",
        status: "active",
      }));
  }, [feedTab, presentRows, payrollItems, search, sites, workerCategories, workers]);

  const columns = {
    sites: ["Site", "Location", "Workers", "Expenses", "Status"],
    attendance: ["Worker", "Site", "Present days", "OT hours", "Today"],
    workforce: ["Worker", "Trade", "Site", "Daily wage", "Status"],
    payroll: ["Period", "Workers", "Gross", "Pending", "Status"],
    categories: ["Category", "Workers", "Share", "Note", "Status"],
  }[feedTab];

  const activeSiteCount = sites.filter((site) => site.status === "active").length;

  return (
    <AppShell activePath="/">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Overview"
          title={`Welcome back, ${user?.full_name ?? "operator"}`}
          description="Site activity first, then choose attendance, workforce, payroll, or categories."
          action={loading ? "Refreshing" : "Refresh"}
          onAction={() => setRefreshToken((value) => value + 1)}
        />

        {loading ? <div className="animate-pulse rounded-3xl bg-card p-4 text-sm text-muted-foreground shadow-card">Loading operations overview…</div> : null}
        {errorMessage ? (
          <div className="flex flex-col gap-3 rounded-3xl bg-red-50 p-5 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
            <span>{errorMessage}</span>
            <button className="font-bold underline underline-offset-4" onClick={() => setRefreshToken((value) => value + 1)} type="button">
              Try again
            </button>
          </div>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Workers" value={workersResponse ? String(workersResponse.total) : "—"} delta="Live roster" icon={UsersRound} tone="mint" />
          <MetricCard label="Present today" value={attendanceReport ? String(presentToday) : "—"} delta="Marked present" icon={ClipboardCheck} tone="amber" />
          <MetricCard label="Active sites" value={String(activeSiteCount || expenseItems.length)} delta="Operational sites" icon={Building2} tone="ink" />
          <MetricCard label="Monthly payroll" value={payrollReport ? `₹${moneyFormatter.format(Number(payrollReport.total_gross_amount))}` : "—"} delta={`${payrollReport?.total_payrolls ?? 0} payrolls`} icon={BadgeIndianRupee} tone="clay" />
        </div>

        <SiteBoard sites={sites} />

        {showFeed ? (
          <Card className="animate-feed-in overflow-hidden">
            <CardContent className="space-y-4 p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-labour-ink">Live operations feed</h3>
                  <p className="text-sm text-muted-foreground">Default view is sites. Switch to attendance, workforce, payroll, or categories.</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input className="w-56 pl-9" placeholder="Search this view..." value={search} onChange={(event) => setSearch(event.target.value)} />
                  </div>
                  <Button variant="outline" size="sm" type="button">
                    <Filter className="h-4 w-4" />
                    Filter
                  </Button>
                </div>
              </div>

              <div className="flex gap-2 overflow-x-auto pb-1">
                {FEED_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    className={cn(
                      "whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted",
                      feedTab === tab.id && "bg-primary text-white shadow-glow hover:bg-primary",
                    )}
                    onClick={() => setFeedTab(tab.id)}
                    type="button"
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    {columns.map((column) => (
                      <TableHead key={column}>{column}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {feedRows.length === 0 ? (
                    <TableRow>
                      <TableCell className="h-24 text-center text-muted-foreground" colSpan={5}>
                        Nothing to show in this view yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    feedRows.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <PersonAvatar name={row.name} />
                            <div>
                              <div className="font-medium">{row.name}</div>
                              <div className="text-xs text-muted-foreground">{row.meta}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{row.col2}</TableCell>
                        <TableCell>{row.col3}</TableCell>
                        <TableCell>{row.col4}</TableCell>
                        <TableCell>
                          <StatusPill value={row.status} />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        ) : (
          <div className="rounded-3xl bg-card p-6 text-sm text-muted-foreground shadow-card">Preparing live feed…</div>
        )}
      </div>
    </AppShell>
  );
}
