"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { BadgeIndianRupee, Building2, Edit3, Eye, Filter, MapPinned, Plus, RefreshCw, Save, UsersRound, X } from "lucide-react";

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
  createSite,
  getSites,
  updateSite,
  type SiteResponse,
  type SiteWritePayload,
} from "@/lib/api-client";

type SiteFormState = {
  site_code: string;
  name: string;
  client_name: string;
  project_name: string;
  city: string;
  state: string;
  status: string;
  start_date: string;
  end_date: string;
};

const emptyForm: SiteFormState = {
  site_code: "",
  name: "",
  client_name: "",
  project_name: "",
  city: "",
  state: "",
  status: "active",
  start_date: new Date().toISOString().slice(0, 10),
  end_date: "",
};

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function formatMoney(value: string | number) {
  return `INR ${moneyFormatter.format(Number(value || 0))}`;
}

function formFromSite(site: SiteResponse): SiteFormState {
  return {
    site_code: site.site_code,
    name: site.name,
    client_name: site.client_name ?? "",
    project_name: site.project_name ?? "",
    city: site.city ?? "",
    state: site.state ?? "",
    status: site.status,
    start_date: site.start_date,
    end_date: site.end_date ?? "",
  };
}

function toPayload(form: SiteFormState): SiteWritePayload {
  return {
    site_code: form.site_code,
    name: form.name,
    client_name: form.client_name || null,
    project_name: form.project_name || null,
    city: form.city || null,
    state: form.state || null,
    status: form.status,
    start_date: form.start_date,
    end_date: form.end_date || null,
    site_manager_user_id: null,
  };
}

export default function SitesPage() {
  const [sites, setSites] = useState<SiteResponse[]>([]);
  const [totalSites, setTotalSites] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingSite, setEditingSite] = useState<SiteResponse | null>(null);
  const [form, setForm] = useState<SiteFormState>(emptyForm);
  const [filters, setFilters] = useState({ search: "", status: "", city: "", state: "" });
  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const loadSites = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const response = await getSites({
          page: 1,
          page_size: 100,
          search: appliedFilters.search,
          status: appliedFilters.status,
          city: appliedFilters.city,
          state: appliedFilters.state,
        });
        setSites(response.items);
        setTotalSites(response.total);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Sites could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void loadSites();
  }, [appliedFilters, refreshToken]);

  const metrics = useMemo(() => {
    const activeSites = sites.filter((site) => site.status === "active").length;
    const workerCount = sites.reduce((sum, site) => sum + site.active_worker_count, 0);
    const expenses = sites.reduce((sum, site) => sum + Number(site.total_expense_amount), 0);
    return [
      { label: "Total sites", value: String(totalSites), delta: loading ? "Loading" : "Filtered portfolio", icon: Building2, tone: "ink" as const },
      { label: "Active sites", value: String(activeSites), delta: loading ? "Loading" : "Operational sites", icon: MapPinned, tone: "mint" as const },
      { label: "Assigned workers", value: String(workerCount), delta: loading ? "Loading" : "Current primary assignments", icon: UsersRound, tone: "amber" as const },
      { label: "Site expenses", value: formatMoney(expenses), delta: loading ? "Loading" : "All listed sites", icon: BadgeIndianRupee, tone: "clay" as const },
    ];
  }, [loading, sites, totalSites]);

  const openCreateForm = () => {
    setEditingSite(null);
    setForm(emptyForm);
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (site: SiteResponse) => {
    setEditingSite(site);
    setForm(formFromSite(site));
    setFormError(null);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingSite(null);
    setFormError(null);
    setForm(emptyForm);
  };

  const submitForm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      if (editingSite) {
        await updateSite(editingSite.id, toPayload(form));
      } else {
        await createSite(toPayload(form));
      }
      closeForm();
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Site could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell activePath="/sites">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Site management"
          title="Sites"
          description="Create, update, filter, and inspect project sites connected to workers, expenses, payroll, and attendance."
          action={showForm ? "Close form" : "Create site"}
          onAction={showForm ? closeForm : openCreateForm}
        />

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </div>

        {showForm ? (
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader>
              <CardTitle>{editingSite ? "Edit site" : "Create site"}</CardTitle>
              <CardDescription>{editingSite ? editingSite.site_code : "Add a project site for worker allocation and reporting."}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="grid gap-4 lg:grid-cols-2" onSubmit={submitForm}>
                <Input required placeholder="Site code" value={form.site_code} onChange={(event) => setForm({ ...form, site_code: event.target.value })} />
                <Input required placeholder="Site name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
                <Input placeholder="Client name" value={form.client_name} onChange={(event) => setForm({ ...form, client_name: event.target.value })} />
                <Input placeholder="Project name" value={form.project_name} onChange={(event) => setForm({ ...form, project_name: event.target.value })} />
                <Input placeholder="City" value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} />
                <Input placeholder="State" value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })} />
                <select
                  className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={form.status}
                  onChange={(event) => setForm({ ...form, status: event.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="on_hold">On hold</option>
                  <option value="completed">Completed</option>
                  <option value="inactive">Inactive</option>
                </select>
                <Input required type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} />
                <Input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} />
                <div className="flex flex-wrap gap-3 lg:col-span-2">
                  <Button disabled={saving} type="submit">
                    <Save className="h-4 w-4" />
                    {saving ? "Saving" : "Save site"}
                  </Button>
                  <Button disabled={saving} type="button" variant="outline" onClick={closeForm}>
                    <X className="h-4 w-4" />
                    Cancel
                  </Button>
                </div>
                {formError ? <p className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 lg:col-span-2">{formError}</p> : null}
              </form>
            </CardContent>
          </Card>
        ) : null}

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Site directory</CardTitle>
            <CardDescription>Filter by location, status, or project identifiers.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-3 md:grid-cols-5">
              <Input className="md:col-span-2" placeholder="Search sites" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
              <select
                className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.status}
                onChange={(event) => setFilters({ ...filters, status: event.target.value })}
              >
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="on_hold">On hold</option>
                <option value="completed">Completed</option>
                <option value="inactive">Inactive</option>
              </select>
              <Input placeholder="City" value={filters.city} onChange={(event) => setFilters({ ...filters, city: event.target.value })} />
              <Input placeholder="State" value={filters.state} onChange={(event) => setFilters({ ...filters, state: event.target.value })} />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => setAppliedFilters(filters)}>
                <Filter className="h-4 w-4" />
                Apply filters
              </Button>
              <Button variant="ghost" onClick={() => setRefreshToken((value) => value + 1)}>
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button variant="ghost" onClick={() => {
                const nextFilters = { search: "", status: "", city: "", state: "" };
                setFilters(nextFilters);
                setAppliedFilters(nextFilters);
              }}>
                Clear
              </Button>
            </div>

            {loading ? (
              <div className="animate-pulse rounded-2xl border border-border bg-card/70 p-4 text-sm text-muted-foreground">Loading sites...</div>
            ) : null}

            {errorMessage ? (
              <div className="flex flex-col gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
                <span>{errorMessage}</span>
                <button className="font-bold underline underline-offset-4" onClick={() => setRefreshToken((value) => value + 1)} type="button">Try again</button>
              </div>
            ) : null}

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Site</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Manager</TableHead>
                  <TableHead>Workers</TableHead>
                  <TableHead>Expenses</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && sites.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-24 text-center text-muted-foreground" colSpan={8}>
                      No sites match the current filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  sites.map((site) => (
                    <TableRow key={site.id}>
                      <TableCell className="font-semibold">{site.site_code}</TableCell>
                      <TableCell>
                        <div className="font-semibold text-foreground">{site.name}</div>
                        <div className="text-xs text-muted-foreground">{site.project_name ?? site.client_name ?? "No project reference"}</div>
                      </TableCell>
                      <TableCell>{[site.city, site.state].filter(Boolean).join(", ") || "Unspecified"}</TableCell>
                      <TableCell>{site.site_manager_name ?? "Unassigned"}</TableCell>
                      <TableCell>{site.active_worker_count}</TableCell>
                      <TableCell>{formatMoney(site.total_expense_amount)}</TableCell>
                      <TableCell><StatusPill value={site.status.replace("_", " ")} /></TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button asChild size="sm" variant="outline">
                            <Link href={`/sites/${site.id}`}>
                              <Eye className="h-3.5 w-3.5" />
                              Details
                            </Link>
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => openEditForm(site)}>
                            <Edit3 className="h-3.5 w-3.5" />
                            Edit
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

        {!showForm && !loading && !errorMessage && sites.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-card/60 p-8 text-center text-sm text-muted-foreground">
            Create the first site to begin assigning workers and tracking expenses by location.
            <div className="mt-4">
              <Button onClick={openCreateForm}>
                <Plus className="h-4 w-4" />
                Create site
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
