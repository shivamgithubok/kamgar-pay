"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { MapPinned } from "lucide-react";

import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { SiteResponse } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const PIN_LAYOUT = [
  { top: "18%", left: "16%" },
  { top: "28%", left: "46%" },
  { top: "22%", left: "74%" },
  { top: "58%", left: "24%" },
  { top: "62%", left: "58%" },
  { top: "48%", left: "82%" },
  { top: "78%", left: "40%" },
  { top: "36%", left: "32%" },
];

const moneyFormatter = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

type SiteBoardProps = {
  sites: SiteResponse[];
};

export function SiteBoard({ sites }: SiteBoardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedId && sites[0]?.id) {
      setSelectedId(sites[0].id);
    }
  }, [selectedId, sites]);
  const selected = useMemo(() => sites.find((site) => site.id === selectedId) ?? sites[0] ?? null, [selectedId, sites]);

  return (
    <Card className="animate-fade-up overflow-hidden">
      <CardContent className="p-0">
        <div className="relative min-h-[320px] overflow-hidden bg-[linear-gradient(180deg,#eef2ff_0%,#f8fafc_55%,#e2e8f0_100%)]">
          <div
            className="absolute inset-0 opacity-50"
            style={{
              backgroundImage:
                "linear-gradient(rgba(148,163,184,0.28) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.28) 1px, transparent 1px)",
              backgroundSize: "42px 42px",
            }}
          />
          <div className="absolute left-8 top-10 h-24 w-40 rounded-[2rem] bg-white/50" />
          <div className="absolute right-16 top-16 h-28 w-48 rounded-[2.2rem] bg-white/40" />
          <div className="absolute bottom-12 left-1/4 h-20 w-56 rounded-[2rem] bg-white/45" />
          <div className="absolute bottom-16 right-24 h-24 w-36 rounded-[1.8rem] bg-white/40" />

          {sites.slice(0, PIN_LAYOUT.length).map((site, index) => {
            const layout = PIN_LAYOUT[index];
            const isSelected = selected?.id === site.id;
            const isQuiet = site.status !== "active" || site.active_worker_count === 0;
            return (
              <button
                key={site.id}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{ top: layout.top, left: layout.left, animationDelay: `${index * 90}ms` }}
                onClick={() => setSelectedId(site.id)}
                type="button"
                aria-label={site.name}
              >
                <span className={cn("block h-3.5 w-3.5 rounded-full ring-4", isQuiet ? "bg-amber-500 ring-amber-200 animate-pin-pulse" : "bg-emerald-500 ring-emerald-200 animate-pin-pulse", isSelected && "h-4 w-4 bg-rose-500 ring-rose-200")} />
              </button>
            );
          })}

          {selected ? (
            <div className="absolute left-1/2 top-1/2 w-[min(100%-2rem,340px)] -translate-x-1/2 -translate-y-1/2 animate-fade-up rounded-3xl bg-white p-4 shadow-card-hover">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-rose-500">{selected.site_code}</p>
                  <h3 className="mt-1 text-lg font-semibold text-labour-ink">{selected.name}</h3>
                  <p className="text-sm text-muted-foreground">{[selected.city, selected.state].filter(Boolean).join(", ") || "Location not set"}</p>
                </div>
                <StatusPill value={selected.status} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                <div className="rounded-2xl bg-muted p-3">
                  <p className="text-xs text-muted-foreground">Workers</p>
                  <p className="mt-1 font-semibold">{selected.active_worker_count}</p>
                </div>
                <div className="rounded-2xl bg-muted p-3">
                  <p className="text-xs text-muted-foreground">Expenses</p>
                  <p className="mt-1 font-semibold">₹{moneyFormatter.format(Number(selected.total_expense_amount || 0))}</p>
                </div>
              </div>
              <Button asChild className="mt-4 w-full" size="sm">
                <Link href={`/sites/${selected.id}`}>
                  <MapPinned className="h-4 w-4" />
                  View site
                </Link>
              </Button>
            </div>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">No sites to preview yet.</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
