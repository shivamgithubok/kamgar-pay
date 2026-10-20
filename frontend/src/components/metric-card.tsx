import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const toneClass = {
  mint: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
  clay: "bg-indigo-50 text-indigo-600",
  ink: "bg-slate-900 text-white",
};

type MetricCardProps = {
  label: string;
  value: string;
  delta: string;
  icon: LucideIcon;
  tone: keyof typeof toneClass;
};

export function MetricCard({ label, value, delta, icon: Icon, tone }: MetricCardProps) {
  return (
    <Card className="animate-fade-up">
      <CardContent className="p-5">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <div className={cn("flex h-9 w-9 items-center justify-center rounded-full", toneClass[tone])}>
            <Icon className="h-4 w-4" />
          </div>
        </div>
        <p className="mt-4 truncate text-3xl font-semibold tracking-tight text-labour-ink">{value}</p>
        <p className="mt-2 text-xs font-medium text-emerald-600">{delta}</p>
      </CardContent>
    </Card>
  );
}
