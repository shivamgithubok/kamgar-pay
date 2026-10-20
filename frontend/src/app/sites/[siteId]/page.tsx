"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { ArrowLeft, BadgeIndianRupee, CalendarDays, Link2, RefreshCw, Trash2, UsersRound } from "lucide-react";

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
  assignWorkerToSite,
  getSite,
  getSiteExpenseSummary,
  getSiteStats,
  getSiteWorkers,
  getWorkers,
  unassignWorkerFromSite,
  type SiteExpenseSummaryResponse,
  type SiteResponse,
  type SiteStatsResponse,
  type SiteWorkerResponse,
  type WorkersListResponse,
} from "@/lib/api-client";

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function formatMoney(value: string | number) {
  return `INR ${moneyFormatter.format(Number(value || 0))}`;
}

function formatDate(value?: string | null) {
  if (!value) {
    return "Open";
  }
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`));
}

export default function SiteDetailsPage() {
  const params = useParams<{ siteId: string }>();
  const siteId = params.siteId;
  const [site, setSite] = useState<SiteResponse | null>(null);
  const [stats, setStats] = useState<SiteStatsResponse | null>(null);
  const [expenseSummary, setExpenseSummary] = useState<SiteExpenseSummaryResponse | null>(null);
  const [siteWorkers, setSiteWorkers] = useState<SiteWorkerResponse[]>([]);
  const [workersResponse, setWorkersResponse] = useState<WorkersListResponse | null>(null);
  const [selectedWorkerId, setSelectedWorkerId] = useState("");
  const [assignedFrom, setAssignedFrom] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const loadSiteDetails = async () => {
      setLoading(true);
      setErrorMessage(null);
      setActionError(null);
      try {
        const [siteResponse, statsResponse, expenseResponse, workerResponse, allWorkersResponse] = await Promise.all([
          getSite(siteId),
          getSiteStats(siteId),
          getSiteExpenseSummary(siteId),
          getSiteWorkers(siteId),
          getWorkers(),
        ]);
        setSite(siteResponse);
        setStats(statsResponse);
        setExpenseSummary(expenseResponse);
        setSiteWorkers(workerResponse);
        setWorkersResponse(allWorkersResponse);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Site details could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    if (siteId) {
      void loadSiteDetails();
    }
  }, [siteId, refreshToken]);

  const assignedWorkerIds = useMemo(() => new Set(siteWorkers.map((worker) => worker.id)), [siteWorkers]);
  const assignableWorkers = useMemo(
    () => (workersResponse?.items ?? []).filter((worker) => !assignedWorkerIds.has(worker.id) && worker.status === "active"),
    [assignedWorkerIds, workersResponse],
  );

  const metrics = useMemo(() => [
    {
      label: "Active workers",
      value: stats ? String(stats.active_worker_count) : "-",
      delta: loading ? "Loading" : `${stats?.total_worker_assignments ?? 0} assignment records`,
      icon: UsersRound,
      tone: "mint" as const,
    },
    {
      label: "Attendance",
      value: stats ? String(stats.attendance_records) : "-",
      delta: loading ? "Loading" : `${stats?.paid_days ?? 0} paid days`,
      icon: CalendarDays,
      tone: "amber" as const,
    },
    {
      label: "Payroll",
      value: stats ? formatMoney(stats.gross_payroll) : "-",
      delta: loading ? "Loading" : `${stats?.payroll_count ?? 0} payroll entries`,
      icon: BadgeIndianRupee,
      tone: "clay" as const,
    },
    {
      label: "Expenses",
      value: stats ? formatMoney(stats.total_expenses) : "-",
      delta: loading ? "Loading" : `${stats?.expense_count ?? 0} expense entries`,
      icon: BadgeIndianRupee,
      tone: "ink" as const,
    },
  ], [loading, stats]);

  const assignWorker = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedWorkerId) {
      setActionError("Choose a worker to assign.");
      return;
    }
    setAssigning(true);
    setActionError(null);
    try {
      await assignWorkerToSite(siteId, {
        worker_id: selectedWorkerId,
        assigned_from: assignedFrom,
        is_primary: true,
      });
      setSelectedWorkerId("");
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : "Worker could not be assigned.");
    } finally {
      setAssigning(false);
    }
  };

  const removeWorker = async (workerId: string) => {
    setAssigning(true);
    setActionError(null);
    try {
      await unassignWorkerFromSite(siteId, workerId);
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : "Worker could not be unassigned.");
    } finally {
      setAssigning(false);
    }
  };

  return (
    <AppShell activePath="/sites">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Site details"
          title={site?.name ?? "Site"}
          description={site ? `${site.site_code} / ${[site.city, site.state].filter(Boolean).join(", ") || "Location pending"}` : "Loading site profile and operational summary."}
          action="Refresh"
          onAction={() => setRefreshToken((value) => value + 1)}
        />

        <Button asChild variant="ghost">
          <Link href="/sites">
            <ArrowLeft className="h-4 w-4" />
            Back to sites
          </Link>
        </Button>

        {loading ? (
          <div className="animate-pulse rounded-2xl border border-border bg-card/70 p-4 text-sm text-muted-foreground">Loading site profile...</div>
        ) : null}

        {errorMessage ? (
          <div className="flex flex-col gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
            <span>{errorMessage}</span>
            <button className="font-bold underline underline-offset-4" onClick={() => setRefreshToken((value) => value + 1)} type="button">Try again</button>
          </div>
        ) : null}

        {site ? (
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader>
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <CardTitle>{site.name}</CardTitle>
                  <CardDescription>{site.client_name ?? "No client recorded"}</CardDescription>
                </div>
                <StatusPill value={site.status.replace("_", " ")} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 text-sm md:grid-cols-2 xl:grid-cols-4">
                <div>
                  <p className="font-semibold text-muted-foreground">Project</p>
                  <p className="mt-1 font-semibold">{site.project_name ?? "Not set"}</p>
                </div>
                <div>
                  <p className="font-semibold text-muted-foreground">Manager</p>
                  <p className="mt-1 font-semibold">{site.site_manager_name ?? "Unassigned"}</p>
                </div>
                <div>
                  <p className="font-semibold text-muted-foreground">Start</p>
                  <p className="mt-1 font-semibold">{formatDate(site.start_date)}</p>
                </div>
                <div>
                  <p className="font-semibold text-muted-foreground">End</p>
                  <p className="mt-1 font-semibold">{formatDate(site.end_date)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </div>

        <div className="grid gap-5 xl:grid-cols-[1.4fr_0.9fr]">
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader>
              <CardTitle>Assigned workers</CardTitle>
              <CardDescription>Current active worker allocation for this site.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <form className="grid gap-3 md:grid-cols-[1fr_170px_auto]" onSubmit={assignWorker}>
                <select
                  className="h-10 min-w-0 rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={selectedWorkerId}
                  onChange={(event) => setSelectedWorkerId(event.target.value)}
                >
                  <option value="">Choose worker</option>
                  {assignableWorkers.map((worker) => (
                    <option key={worker.id} value={worker.id}>
                      {worker.worker_code} - {worker.name}
                    </option>
                  ))}
                </select>
                <Input type="date" value={assignedFrom} onChange={(event) => setAssignedFrom(event.target.value)} />
                <Button disabled={assigning || assignableWorkers.length === 0} type="submit">
                  <Link2 className="h-4 w-4" />
                  Assign
                </Button>
              </form>

              {assignableWorkers.length === 0 && !loading ? (
                <p className="rounded-2xl border border-dashed border-border bg-card/60 p-3 text-sm text-muted-foreground">No active unassigned workers are available from the current roster.</p>
              ) : null}

              {actionError ? <p className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{actionError}</p> : null}

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Worker</TableHead>
                    <TableHead>Trade</TableHead>
                    <TableHead>Mobile</TableHead>
                    <TableHead>Assigned</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!loading && siteWorkers.length === 0 ? (
                    <TableRow>
                      <TableCell className="h-24 text-center text-muted-foreground" colSpan={6}>
                        No workers are assigned to this site yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    siteWorkers.map((worker) => (
                      <TableRow key={worker.id}>
                        <TableCell>
                          <div className="font-semibold">{worker.name}</div>
                          <div className="text-xs text-muted-foreground">{worker.worker_code}</div>
                        </TableCell>
                        <TableCell>{worker.trade ?? "Uncategorized"}</TableCell>
                        <TableCell>{worker.mobile ?? "Not recorded"}</TableCell>
                        <TableCell>{formatDate(worker.assigned_from)}</TableCell>
                        <TableCell><StatusPill value={worker.status} /></TableCell>
                        <TableCell>
                          <Button disabled={assigning} size="sm" variant="ghost" onClick={() => void removeWorker(worker.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                            Unassign
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card className="animate-fade-up overflow-hidden">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle>Expense summary</CardTitle>
                  <CardDescription>Spend by status and category.</CardDescription>
                </div>
                <Button size="icon" variant="outline" onClick={() => setRefreshToken((value) => value + 1)} aria-label="Refresh expense summary">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-2xl border border-border bg-card/70 p-4">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-muted-foreground">Total</p>
                <p className="mt-2 text-3xl font-black text-labour-ink">{formatMoney(expenseSummary?.total_expenses ?? 0)}</p>
                <p className="mt-1 text-sm text-muted-foreground">{expenseSummary?.expense_count ?? 0} expense entries</p>
              </div>

              <div>
                <h3 className="text-sm font-bold uppercase tracking-[0.16em] text-muted-foreground">By status</h3>
                <div className="mt-3 space-y-2">
                  {(expenseSummary?.by_status ?? []).length === 0 ? (
                    <p className="rounded-2xl border border-dashed border-border bg-card/60 p-3 text-sm text-muted-foreground">No expenses recorded for this site.</p>
                  ) : (
                    expenseSummary?.by_status.map((item) => (
                      <div key={item.key} className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-card/70 p-3 text-sm">
                        <StatusPill value={item.key} />
                        <span className="font-semibold">{formatMoney(item.total_amount)}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold uppercase tracking-[0.16em] text-muted-foreground">By category</h3>
                <div className="mt-3 space-y-2">
                  {(expenseSummary?.by_category ?? []).length === 0 ? (
                    <p className="rounded-2xl border border-dashed border-border bg-card/60 p-3 text-sm text-muted-foreground">Category totals will appear after expenses are logged.</p>
                  ) : (
                    expenseSummary?.by_category.map((item) => (
                      <div key={item.key} className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-card/70 p-3 text-sm">
                        <span className="font-semibold capitalize">{item.key}</span>
                        <span>{formatMoney(item.total_amount)}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
