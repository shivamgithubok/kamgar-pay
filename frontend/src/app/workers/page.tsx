"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { FileText, Plus, RefreshCw, Save, Search, X } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { PersonAvatar } from "@/components/person-avatar";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError, createWorker, getSites, getWorkers, updateWorker, type SiteResponse, type WorkersListResponse } from "@/lib/api-client";

type WorkerItem = WorkersListResponse["items"][number];

type WorkerFormState = {
  worker_code: string;
  name: string;
  mobile: string;
  trade: string;
  daily_wage: string;
  pf_rate_percent: string;
  joining_date: string;
  assigned_site_id: string;
};

const emptyForm: WorkerFormState = {
  worker_code: "",
  name: "",
  mobile: "",
  trade: "",
  daily_wage: "",
  pf_rate_percent: "0",
  joining_date: new Date().toISOString().slice(0, 10),
  assigned_site_id: "",
};

export default function WorkersPage() {
  const [workers, setWorkers] = useState<WorkerItem[]>([]);
  const [sites, setSites] = useState<SiteResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<WorkerFormState>(emptyForm);
  const [editingWorkerId, setEditingWorkerId] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const loadWorkersData = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const [response, sitesResponse] = await Promise.all([getWorkers(), getSites()]);
        setWorkers(response.items);
        setSites(sitesResponse.items);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Workers could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void loadWorkersData();
  }, [refreshToken]);

  const filteredWorkers = workers.filter((w) => {
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    return (
      w.name.toLowerCase().includes(term) ||
      w.worker_code.toLowerCase().includes(term) ||
      (w.trade && w.trade.toLowerCase().includes(term)) ||
      (w.assigned_site_name && w.assigned_site_name.toLowerCase().includes(term))
    );
  });

  const submitForm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = {
        worker_code: form.worker_code,
        name: form.name,
        mobile: form.mobile || null,
        trade: form.trade || null,
        daily_wage: Number(form.daily_wage || 0),
        pf_rate_percent: Number(form.pf_rate_percent || 0),
        joining_date: form.joining_date,
        assigned_site_id: form.assigned_site_id || null,
      };
      if (editingWorkerId) {
        await updateWorker(editingWorkerId, payload);
      } else {
        await createWorker(payload);
      }
      setShowForm(false);
      setEditingWorkerId(null);
      setForm(emptyForm);
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Worker could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell activePath="/workers">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Workforce Directory"
          title="Workers"
          description="Manage construction workers, site assignments, trade skills, PF rate, and compliance document vault."
          action={showForm ? "Close form" : "Add worker"}
          onAction={() => {
            setShowForm((value) => !value);
            setEditingWorkerId(null);
            setForm(emptyForm);
            setFormError(null);
          }}
        />

        {showForm ? (
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader>
              <CardTitle>{editingWorkerId ? "Edit worker" : "Add worker"}</CardTitle>
              <CardDescription>Set daily wage and an owner-chosen PF percentage for this worker. Use 0 if PF does not apply.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="grid gap-4 lg:grid-cols-2" onSubmit={submitForm}>
                <Input required placeholder="Worker code" value={form.worker_code} onChange={(event) => setForm({ ...form, worker_code: event.target.value })} />
                <Input required placeholder="Full name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
                <Input placeholder="10-digit mobile" value={form.mobile} onChange={(event) => setForm({ ...form, mobile: event.target.value })} />
                <Input placeholder="Trade (Mason, Helper…)" value={form.trade} onChange={(event) => setForm({ ...form, trade: event.target.value })} />
                <Input required type="number" min="0" placeholder="Daily wage" value={form.daily_wage} onChange={(event) => setForm({ ...form, daily_wage: event.target.value })} />
                <Input required type="number" min="0" max="100" step="0.01" placeholder="PF rate %" value={form.pf_rate_percent} onChange={(event) => setForm({ ...form, pf_rate_percent: event.target.value })} />
                <Input required type="date" value={form.joining_date} onChange={(event) => setForm({ ...form, joining_date: event.target.value })} />
                <select
                  className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm lg:col-span-2"
                  value={form.assigned_site_id}
                  onChange={(event) => setForm({ ...form, assigned_site_id: event.target.value })}
                >
                  <option value="">Unassigned</option>
                  {sites.map((site) => (
                    <option key={site.id} value={site.id}>
                      {site.name}
                    </option>
                  ))}
                </select>
                <div className="flex flex-wrap gap-3 lg:col-span-2">
                  <Button disabled={saving} type="submit">
                    <Save className="h-4 w-4" />
                    {saving ? "Saving" : editingWorkerId ? "Save changes" : "Save worker"}
                  </Button>
                  <Button disabled={saving} type="button" variant="outline" onClick={() => setShowForm(false)}>
                    <X className="h-4 w-4" />
                    Cancel
                  </Button>
                </div>
                {formError ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 lg:col-span-2">{formError}</p> : null}
              </form>
            </CardContent>
          </Card>
        ) : null}

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Worker Master Roster</CardTitle>
            <CardDescription>Select any worker to manage identity, KYC, and compliance documents.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex flex-wrap gap-3">
              <div className="relative flex-1 min-w-[240px]">
                <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search worker by name, code, trade, site..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Button variant="ghost" onClick={() => setRefreshToken((v) => v + 1)}>
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button onClick={() => setShowForm(true)}>
                <Plus className="h-4 w-4" />
                Add worker
              </Button>
            </div>

            {loading ? (
              <div className="animate-pulse rounded-2xl border border-border bg-card/70 p-4 text-sm text-muted-foreground">
                Loading worker list...
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

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Worker Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Trade</TableHead>
                  <TableHead>Assigned Site</TableHead>
                  <TableHead>Daily Wage</TableHead>
                  <TableHead>PF %</TableHead>
                  <TableHead>Advances</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && filteredWorkers.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-28 text-center text-muted-foreground" colSpan={9}>
                      No workers found in directory.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredWorkers.map((worker) => (
                    <TableRow key={worker.id}>
                      <TableCell className="font-semibold">{worker.worker_code}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <PersonAvatar name={worker.name} />
                          <div>
                            <div className="font-semibold text-foreground">
                              <Link className="hover:underline" href={`/workers/${worker.id}`}>
                                {worker.name}
                              </Link>
                            </div>
                            <div className="text-xs text-muted-foreground">{worker.mobile || "No phone registered"}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{worker.trade || "General Worker"}</TableCell>
                      <TableCell>{worker.assigned_site_name || "Unassigned"}</TableCell>
                      <TableCell className="font-semibold">INR {worker.daily_wage}</TableCell>
                      <TableCell>{Number(worker.pf_rate_percent || 0)}%</TableCell>
                      <TableCell>
                        <Link className="font-semibold hover:underline" href={`/workers/${worker.id}`}>
                          INR {Number(worker.advance_total || 0)}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <StatusPill value={worker.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            type="button"
                            variant="ghost"
                            onClick={() => {
                              setEditingWorkerId(worker.id);
                              setShowForm(true);
                              setFormError(null);
                              setForm({
                                worker_code: worker.worker_code,
                                name: worker.name,
                                mobile: worker.mobile || "",
                                trade: worker.trade || "",
                                daily_wage: String(worker.daily_wage),
                                pf_rate_percent: String(worker.pf_rate_percent ?? "0"),
                                joining_date: worker.joining_date,
                                assigned_site_id: worker.assigned_site_id || "",
                              });
                            }}
                          >
                            Edit
                          </Button>
                          <Button asChild size="sm" variant="outline">
                          <Link href={`/workers/${worker.id}`}>
                            Ledger
                          </Link>
                        </Button>
                          <Button asChild size="sm" variant="outline">
                          <Link href={`/workers/${worker.id}/documents`}>
                            <FileText className="h-3.5 w-3.5" />
                            Documents
                          </Link>
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
      </div>
    </AppShell>
  );
}
