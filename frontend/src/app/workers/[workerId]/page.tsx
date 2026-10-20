"use client";

import Link from "next/link";
import { type FormEvent, use, useEffect, useState } from "react";
import { ArrowLeft, FileText, Save } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ApiError,
  createAdvancePayment,
  getPaymentHistory,
  getWorker,
  type PaymentResponse,
  type WorkerDetailResponse,
} from "@/lib/api-client";

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function formatMoney(value: string | number | null | undefined) {
  return `INR ${moneyFormatter.format(Number(value || 0))}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

export default function WorkerProfilePage({ params }: { params: Promise<{ workerId: string }> }) {
  const { workerId } = use(params);
  const [worker, setWorker] = useState<WorkerDetailResponse | null>(null);
  const [advances, setAdvances] = useState<PaymentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);
  const [form, setForm] = useState({
    amount: "",
    payment_date: todayKey(),
    reason: "",
  });

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const [workerResponse, payments] = await Promise.all([
          getWorker(workerId),
          getPaymentHistory({ worker_id: workerId, payment_type: "advance" }),
        ]);
        setWorker(workerResponse);
        setAdvances(payments);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Worker advances could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [refreshToken, workerId]);

  const submitAdvance = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createAdvancePayment({
        worker_id: workerId,
        amount: Number(form.amount),
        payment_date: form.payment_date,
        reason: form.reason || "Worker advance",
        notes: form.reason || "Worker advance",
      });
      setForm({ amount: "", payment_date: todayKey(), reason: "" });
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Advance could not be recorded.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell activePath="/workers">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button asChild size="sm" variant="outline">
            <Link href="/workers">
              <ArrowLeft className="h-4 w-4" />
              Back to Workers
            </Link>
          </Button>
          <Button asChild size="sm" variant="ghost">
            <Link href={`/workers/${workerId}/documents`}>
              <FileText className="h-4 w-4" />
              Documents
            </Link>
          </Button>
        </div>

        <PageHeader
          eyebrow="Worker ledger"
          title={worker?.name || "Worker"}
          description="Every advance for this person is kept as a dated record with the reason it was given."
        />

        {loading ? <p className="text-sm text-muted-foreground">Loading worker ledger…</p> : null}
        {errorMessage ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{errorMessage}</p> : null}

        {worker ? (
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="p-5">
                <p className="text-sm text-muted-foreground">Code</p>
                <p className="mt-2 text-xl font-semibold">{worker.worker_code}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-sm text-muted-foreground">PF rate</p>
                <p className="mt-2 text-xl font-semibold">{Number(worker.pf_rate_percent || 0)}%</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-sm text-muted-foreground">Advances taken</p>
                <p className="mt-2 text-xl font-semibold">{worker.advance_count ?? advances.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-sm text-muted-foreground">Advance total</p>
                <p className="mt-2 text-xl font-semibold">{formatMoney(worker.advance_total)}</p>
              </CardContent>
            </Card>
          </div>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Give advance</CardTitle>
            <CardDescription>Record amount, date, and reason. This stays on the worker’s ledger and is deducted when payroll is calculated.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3 md:grid-cols-4" onSubmit={submitAdvance}>
              <Input
                min="0"
                placeholder="Amount"
                required
                type="number"
                value={form.amount}
                onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))}
              />
              <Input
                required
                type="date"
                value={form.payment_date}
                onChange={(event) => setForm((current) => ({ ...current, payment_date: event.target.value }))}
              />
              <Input
                className="md:col-span-1"
                placeholder="Reason (festival, medical, travel…)"
                required
                value={form.reason}
                onChange={(event) => setForm((current) => ({ ...current, reason: event.target.value }))}
              />
              <Button disabled={saving} type="submit">
                <Save className="h-4 w-4" />
                {saving ? "Saving" : "Save advance"}
              </Button>
            </form>
            {formError ? <p className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{formError}</p> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Advance history</CardTitle>
            <CardDescription>Date given, time recorded, reason, and amount for this worker only.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date given</TableHead>
                  <TableHead>Recorded at</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && advances.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-24 text-center text-muted-foreground" colSpan={6}>
                      No advances recorded for this worker yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  advances.map((advance) => (
                    <TableRow key={advance.id}>
                      <TableCell className="font-semibold">{formatDate(advance.payment_date)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{formatDateTime(advance.created_at)}</TableCell>
                      <TableCell className="font-semibold">{formatMoney(advance.amount)}</TableCell>
                      <TableCell>{advance.reason || advance.notes || "—"}</TableCell>
                      <TableCell className="capitalize">{advance.payment_method.replaceAll("_", " ")}</TableCell>
                      <TableCell>
                        <StatusPill value={advance.status} />
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
