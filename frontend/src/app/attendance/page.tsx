"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { ClipboardCheck, RefreshCw, Save } from "lucide-react";

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
  bulkMarkAttendance,
  getAttendance,
  getSites,
  getSiteWorkers,
  type AttendanceResponse,
  type SiteResponse,
  type SiteWorkerResponse,
} from "@/lib/api-client";

const STATUSES = ["present", "absent", "half_day", "leave", "weekly_off"];

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendancePage() {
  const [sites, setSites] = useState<SiteResponse[]>([]);
  const [workers, setWorkers] = useState<SiteWorkerResponse[]>([]);
  const [records, setRecords] = useState<AttendanceResponse[]>([]);
  const [siteId, setSiteId] = useState("");
  const [attendanceDate, setAttendanceDate] = useState(todayKey());
  const [draft, setDraft] = useState<Record<string, { status: string; ot_hours: string }>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const sitesResponse = await getSites();
        setSites(sitesResponse.items);
        const preferredSite = sitesResponse.items.find((site) => site.active_worker_count > 0) ?? sitesResponse.items[0];
        const nextSiteId = siteId || preferredSite?.id || "";
        if (!siteId && nextSiteId) {
          setSiteId(nextSiteId);
        }
        const activeSiteId = siteId || nextSiteId;
        if (!activeSiteId) {
          setWorkers([]);
          setRecords([]);
          return;
        }
        const [siteWorkers, attendance] = await Promise.all([
          getSiteWorkers(activeSiteId),
          getAttendance({ site_id: activeSiteId, start_date: attendanceDate, end_date: attendanceDate }),
        ]);
        setWorkers(siteWorkers);
        setRecords(attendance);
        const nextDraft: Record<string, { status: string; ot_hours: string }> = {};
        siteWorkers.forEach((worker) => {
          const existing = attendance.find((item) => item.worker_id === worker.id);
          nextDraft[worker.id] = {
            status: existing?.status || "present",
            ot_hours: existing ? String(existing.ot_hours) : "0",
          };
        });
        setDraft(nextDraft);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Attendance could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [attendanceDate, refreshToken, siteId]);

  const metrics = useMemo(() => {
    const values = Object.values(draft);
    const present = values.filter((item) => item.status === "present").length;
    const absent = values.filter((item) => item.status === "absent").length;
    return [
      { label: "Assigned workers", value: String(workers.length), delta: "On selected site", icon: ClipboardCheck, tone: "ink" as const },
      { label: "Marked present", value: String(present), delta: loading ? "Loading" : "Current sheet", icon: ClipboardCheck, tone: "mint" as const },
      { label: "Marked absent", value: String(absent), delta: loading ? "Loading" : "Current sheet", icon: ClipboardCheck, tone: "clay" as const },
      { label: "Saved records", value: String(records.length), delta: "Already stored for this date", icon: ClipboardCheck, tone: "amber" as const },
    ];
  }, [draft, loading, records.length, workers.length]);

  const saveSheet = async (event: FormEvent) => {
    event.preventDefault();
    if (!siteId) {
      setErrorMessage("Create a site first, then mark attendance.");
      return;
    }
    setSaving(true);
    setErrorMessage(null);
    try {
      await bulkMarkAttendance({
        entries: workers.map((worker) => ({
          worker_id: worker.id,
          site_id: siteId,
          attendance_date: attendanceDate,
          status: draft[worker.id]?.status || "present",
          ot_hours: Number(draft[worker.id]?.ot_hours || 0),
        })),
      });
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Attendance could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell activePath="/attendance">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Daily capture"
          title="Attendance"
          description="Mark present, absent, leave, and overtime for workers assigned to a site."
          action="Refresh"
          onAction={() => setRefreshToken((value) => value + 1)}
        />

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </div>

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Attendance sheet</CardTitle>
            <CardDescription>Choose a site and date, then save the roster in one bulk request.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={saveSheet}>
              <div className="grid gap-3 md:grid-cols-3">
                <select
                  className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm"
                  value={siteId}
                  onChange={(event) => setSiteId(event.target.value)}
                >
                  {sites.length === 0 ? <option value="">No sites yet</option> : null}
                  {sites.map((site) => (
                    <option key={site.id} value={site.id}>
                      {site.name}
                    </option>
                  ))}
                </select>
                <Input type="date" value={attendanceDate} onChange={(event) => setAttendanceDate(event.target.value)} />
                <Button type="button" variant="outline" onClick={() => setRefreshToken((value) => value + 1)}>
                  <RefreshCw className="h-4 w-4" />
                  Reload sheet
                </Button>
              </div>

              {errorMessage ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{errorMessage}</p> : null}
              {loading ? <p className="text-sm text-muted-foreground">Loading attendance sheet…</p> : null}

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Worker</TableHead>
                    <TableHead>Trade</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>OT hours</TableHead>
                    <TableHead>Saved</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!loading && workers.length === 0 ? (
                    <TableRow>
                      <TableCell className="h-24 text-center text-muted-foreground" colSpan={5}>
                        Assign workers to this site before capturing attendance.
                      </TableCell>
                    </TableRow>
                  ) : (
                    workers.map((worker) => {
                      const saved = records.find((item) => item.worker_id === worker.id);
                      return (
                        <TableRow key={worker.id}>
                          <TableCell>
                            <div className="font-semibold">{worker.name}</div>
                            <div className="text-xs text-muted-foreground">{worker.worker_code}</div>
                          </TableCell>
                          <TableCell>{worker.trade || "General"}</TableCell>
                          <TableCell>
                            <select
                              className="h-10 rounded-xl border border-input bg-background px-3 text-sm"
                              value={draft[worker.id]?.status || "present"}
                              onChange={(event) =>
                                setDraft((current) => ({
                                  ...current,
                                  [worker.id]: { ...(current[worker.id] || { ot_hours: "0" }), status: event.target.value },
                                }))
                              }
                            >
                              {STATUSES.map((status) => (
                                <option key={status} value={status}>
                                  {status.replace("_", " ")}
                                </option>
                              ))}
                            </select>
                          </TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              min="0"
                              step="0.5"
                              value={draft[worker.id]?.ot_hours || "0"}
                              onChange={(event) =>
                                setDraft((current) => ({
                                  ...current,
                                  [worker.id]: { ...(current[worker.id] || { status: "present" }), ot_hours: event.target.value },
                                }))
                              }
                            />
                          </TableCell>
                          <TableCell>{saved ? <StatusPill value={saved.approval_status} /> : "Not saved"}</TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>

              <Button disabled={saving || workers.length === 0} type="submit">
                <Save className="h-4 w-4" />
                {saving ? "Saving" : "Save attendance"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
