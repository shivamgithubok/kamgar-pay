"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { BadgeIndianRupee, Calculator, Plus, Wallet } from "lucide-react";

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
  calculatePayroll,
  createAdvancePayment,
  createPayrollPeriod,
  getPaymentHistory,
  getPayrollEntries,
  getPayrollPeriods,
  getWorkers,
  recordPayrollPayment,
  type PaymentResponse,
  type PayrollEntryResponse,
  type PayrollPeriodResponse,
  type WorkersListResponse,
} from "@/lib/api-client";

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

function formatMoney(value: string | number) {
  return `INR ${moneyFormatter.format(Number(value || 0))}`;
}

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

export default function PayrollPage() {
  const now = new Date();
  const [periods, setPeriods] = useState<PayrollPeriodResponse[]>([]);
  const [entries, setEntries] = useState<PayrollEntryResponse[]>([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState("");
  const [year, setYear] = useState(String(now.getFullYear()));
  const [month, setMonth] = useState(String(now.getMonth() + 1));
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [paymentAmounts, setPaymentAmounts] = useState<Record<string, string>>({});
  const [workers, setWorkers] = useState<WorkersListResponse["items"]>([]);
  const [advanceForm, setAdvanceForm] = useState({
    worker_id: "",
    amount: "",
    payment_date: todayKey(),
    reason: "",
  });
  const [advances, setAdvances] = useState<PaymentResponse[]>([]);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const [periodList, workersResponse] = await Promise.all([getPayrollPeriods(), getWorkers()]);
        setPeriods(periodList);
        setWorkers(workersResponse.items);
        const nextPeriodId = selectedPeriodId || periodList[0]?.id || "";
        if (!selectedPeriodId && nextPeriodId) {
          setSelectedPeriodId(nextPeriodId);
        }
        const activePeriodId = selectedPeriodId || nextPeriodId;
        const activePeriod = periodList.find((period) => period.id === activePeriodId);
        if (activePeriodId) {
          const [payrolls, periodAdvances] = await Promise.all([
            getPayrollEntries(activePeriodId),
            getPaymentHistory({
              payment_type: "advance",
              start_date: activePeriod?.period_start,
              end_date: activePeriod?.period_end,
            }),
          ]);
          setEntries(payrolls);
          setAdvances(periodAdvances);
        } else {
          setEntries([]);
          setAdvances([]);
        }
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Payroll could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [refreshToken, selectedPeriodId]);

  const totals = useMemo(() => {
    return {
      gross: entries.reduce((sum, item) => sum + Number(item.gross_amount), 0),
      advance: entries.reduce((sum, item) => sum + Number(item.advance_amount), 0),
      pf: entries.reduce((sum, item) => sum + Number(item.pf_amount), 0),
      pending: entries.reduce((sum, item) => sum + Number(item.pending_amount), 0),
      paid: entries.reduce((sum, item) => sum + Number(item.paid_amount), 0),
    };
  }, [entries]);

  const createPeriod = async (event: FormEvent) => {
    event.preventDefault();
    setWorking(true);
    setErrorMessage(null);
    try {
      const period = await createPayrollPeriod({ year: Number(year), month: Number(month) });
      setSelectedPeriodId(period.id);
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Payroll period could not be created.");
    } finally {
      setWorking(false);
    }
  };

  const runCalculate = async () => {
    if (!selectedPeriodId) {
      setErrorMessage("Create or select a payroll period first.");
      return;
    }
    setWorking(true);
    setErrorMessage(null);
    try {
      await calculatePayroll(selectedPeriodId, { recalculate_existing: true });
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Payroll calculation failed.");
    } finally {
      setWorking(false);
    }
  };

  const recordAdvance = async (event: FormEvent) => {
    event.preventDefault();
    if (!advanceForm.worker_id || !advanceForm.amount) {
      setErrorMessage("Select a worker and enter an advance amount.");
      return;
    }
    setWorking(true);
    setErrorMessage(null);
    try {
      await createAdvancePayment({
        worker_id: advanceForm.worker_id,
        amount: Number(advanceForm.amount),
        payment_date: advanceForm.payment_date,
        reason: advanceForm.reason || "Worker advance",
        notes: advanceForm.reason || "Worker advance",
      });
      if (selectedPeriodId) {
        await calculatePayroll(selectedPeriodId, { recalculate_existing: true });
      }
      setAdvanceForm((current) => ({ ...current, amount: "", reason: "" }));
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Advance could not be recorded.");
    } finally {
      setWorking(false);
    }
  };

  const payEntry = async (entry: PayrollEntryResponse) => {
    const amount = Number(paymentAmounts[entry.id] || entry.pending_amount);
    if (!amount) return;
    setWorking(true);
    setErrorMessage(null);
    try {
      await recordPayrollPayment(entry.id, { amount, payment_date: todayKey() });
      setRefreshToken((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Payment could not be recorded.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <AppShell activePath="/payroll">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Wages and payouts"
          title="Payroll"
          description="Create a monthly period, record worker advances, apply each worker’s PF rate, and pay the remaining net."
          action="Refresh"
          onAction={() => setRefreshToken((value) => value + 1)}
        />

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard label="Periods" value={String(periods.length)} delta="Available payroll cycles" icon={Wallet} tone="ink" />
          <MetricCard label="Payroll entries" value={String(entries.length)} delta={loading ? "Loading" : "Selected period"} icon={Calculator} tone="mint" />
          <MetricCard label="Gross amount" value={formatMoney(totals.gross)} delta="Calculated wages" icon={BadgeIndianRupee} tone="amber" />
          <MetricCard label="Advances + PF" value={formatMoney(totals.advance + totals.pf)} delta={`${formatMoney(totals.advance)} advances`} icon={BadgeIndianRupee} tone="clay" />
          <MetricCard label="Pending amount" value={formatMoney(totals.pending)} delta="Still unpaid" icon={BadgeIndianRupee} tone="clay" />
        </div>

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Payroll period</CardTitle>
            <CardDescription>Create a month, then calculate wages from saved attendance.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form className="grid gap-3 md:grid-cols-4" onSubmit={createPeriod}>
              <Input type="number" min="2000" value={year} onChange={(event) => setYear(event.target.value)} />
              <Input type="number" min="1" max="12" value={month} onChange={(event) => setMonth(event.target.value)} />
              <select
                className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm"
                value={selectedPeriodId}
                onChange={(event) => setSelectedPeriodId(event.target.value)}
              >
                {periods.length === 0 ? <option value="">No periods yet</option> : null}
                {periods.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.name}
                  </option>
                ))}
              </select>
              <div className="flex gap-2">
                <Button disabled={working} type="submit">
                  <Plus className="h-4 w-4" />
                  Create period
                </Button>
                <Button disabled={working} type="button" variant="outline" onClick={runCalculate}>
                  <Calculator className="h-4 w-4" />
                  Calculate
                </Button>
              </div>
            </form>
            {errorMessage ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{errorMessage}</p> : null}
          </CardContent>
        </Card>

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Record advance</CardTitle>
            <CardDescription>
              Advances are stored as payroll payments for the worker. Recalculation deducts them from that month’s net, along with PF from the worker master.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3 md:grid-cols-6" onSubmit={recordAdvance}>
              <select
                className="h-10 rounded-xl border border-input bg-background px-3.5 text-sm md:col-span-2"
                value={advanceForm.worker_id}
                onChange={(event) => setAdvanceForm((current) => ({ ...current, worker_id: event.target.value }))}
              >
                <option value="">Select worker</option>
                {workers.map((worker) => (
                  <option key={worker.id} value={worker.id}>
                    {worker.name} ({worker.worker_code}) · PF {Number(worker.pf_rate_percent || 0)}%
                  </option>
                ))}
              </select>
              <Input
                min="0"
                placeholder="Amount"
                required
                type="number"
                value={advanceForm.amount}
                onChange={(event) => setAdvanceForm((current) => ({ ...current, amount: event.target.value }))}
              />
              <Input
                required
                type="date"
                value={advanceForm.payment_date}
                onChange={(event) => setAdvanceForm((current) => ({ ...current, payment_date: event.target.value }))}
              />
              <Input
                placeholder="Reason"
                required
                value={advanceForm.reason}
                onChange={(event) => setAdvanceForm((current) => ({ ...current, reason: event.target.value }))}
              />
              <Button disabled={working} type="submit">
                Save advance
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Who took advance</CardTitle>
            <CardDescription>Advances dated in the selected payroll period. Open a worker ledger for the full history.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Worker</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Recorded at</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && advances.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-24 text-center text-muted-foreground" colSpan={5}>
                      No advances in this period yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  advances.map((advance) => (
                    <TableRow key={advance.id}>
                      <TableCell>
                        {advance.worker_id ? (
                          <Link className="font-semibold hover:underline" href={`/workers/${advance.worker_id}`}>
                            {advance.worker_name || "Worker"}
                          </Link>
                        ) : (
                          <span className="font-semibold">{advance.worker_name || "Worker"}</span>
                        )}
                        <div className="text-xs text-muted-foreground">{advance.worker_code}</div>
                      </TableCell>
                      <TableCell>{advance.payment_date}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(advance.created_at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </TableCell>
                      <TableCell className="font-semibold">{formatMoney(advance.amount)}</TableCell>
                      <TableCell>{advance.reason || advance.notes || "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="animate-fade-up overflow-hidden">
          <CardHeader>
            <CardTitle>Payroll entries</CardTitle>
            <CardDescription>Net = gross − advance − PF. PF uses the percentage saved on the worker.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? <p className="mb-4 text-sm text-muted-foreground">Loading payroll…</p> : null}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Worker</TableHead>
                  <TableHead>Days</TableHead>
                  <TableHead>Gross</TableHead>
                  <TableHead>Advance</TableHead>
                  <TableHead>PF</TableHead>
                  <TableHead>Pending</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Pay now</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && entries.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-24 text-center text-muted-foreground" colSpan={8}>
                      Create a period and calculate payroll to see wage entries.
                    </TableCell>
                  </TableRow>
                ) : (
                  entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>
                        <div className="font-semibold">{entry.worker_name}</div>
                        <div className="text-xs text-muted-foreground">{entry.worker_code}</div>
                      </TableCell>
                      <TableCell>{entry.attendance_days}</TableCell>
                      <TableCell>{formatMoney(entry.gross_amount)}</TableCell>
                      <TableCell>{formatMoney(entry.advance_amount)}</TableCell>
                      <TableCell>
                        <div>{formatMoney(entry.pf_amount)}</div>
                        <div className="text-xs text-muted-foreground">{Number(entry.pf_rate_percent || 0)}%</div>
                      </TableCell>
                      <TableCell>{formatMoney(entry.pending_amount)}</TableCell>
                      <TableCell>
                        <StatusPill value={entry.status} />
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Input
                            className="w-28"
                            type="number"
                            min="0"
                            value={paymentAmounts[entry.id] ?? entry.pending_amount}
                            onChange={(event) => setPaymentAmounts((current) => ({ ...current, [entry.id]: event.target.value }))}
                          />
                          <Button disabled={working || Number(entry.pending_amount) <= 0} size="sm" type="button" onClick={() => void payEntry(entry)}>
                            Pay
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
