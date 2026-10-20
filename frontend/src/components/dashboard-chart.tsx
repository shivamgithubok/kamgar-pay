import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ChartPoint = {
  label: string;
  value: number;
  secondaryValue?: number;
};

type BarChartProps = {
  title: string;
  description: string;
  points: ChartPoint[];
  valueLabel?: string;
  secondaryLabel?: string;
};

export function BarChart({ title, description, points, valueLabel = "Value", secondaryLabel }: BarChartProps) {
  const maximum = Math.max(...points.flatMap((point) => [point.value, point.secondaryValue ?? 0]), 1);

  return (
    <Card className="animate-fade-up overflow-hidden">
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" />{valueLabel}</span>
          {secondaryLabel ? <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-indigo-200" />{secondaryLabel}</span> : null}
        </div>
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <div className="flex h-44 items-center justify-center rounded-3xl bg-muted text-sm text-muted-foreground">No chart data available yet.</div>
        ) : (
          <div className="space-y-3">
            <div className="flex h-48 items-end gap-2 px-1">
              {points.map((point) => (
                <div className="group flex min-w-0 flex-1 items-end justify-center gap-0.5" key={point.label} title={`${point.label}: ${point.value}`}>
                  <div className="w-full rounded-t-2xl bg-primary/85 transition-all group-hover:bg-primary" style={{ height: `${Math.max((point.value / maximum) * 100, 8)}%` }} />
                  {secondaryLabel ? <div className="w-full rounded-t-2xl bg-indigo-200" style={{ height: `${Math.max(((point.secondaryValue ?? 0) / maximum) * 100, 6)}%` }} /> : null}
                </div>
              ))}
            </div>
            <div className="flex gap-2 text-[10px] text-muted-foreground">
              {points.map((point) => (
                <span className="min-w-0 flex-1 truncate text-center" key={`${point.label}-axis`}>
                  {point.label}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

type DistributionChartProps = {
  title: string;
  description: string;
  points: ChartPoint[];
  colors: string[];
};

export function DistributionChart({ title, description, points, colors }: DistributionChartProps) {
  const total = points.reduce((sum, point) => sum + point.value, 0);
  let accumulated = 0;
  const gradient = points
    .map((point, index) => {
      const start = total ? (accumulated / total) * 100 : 0;
      accumulated += point.value;
      const end = total ? (accumulated / total) * 100 : 0;
      return `${colors[index % colors.length]} ${start}% ${end}%`;
    })
    .join(", ");

  return (
    <Card className="animate-fade-up overflow-hidden">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {points.length === 0 || total === 0 ? (
          <div className="flex h-40 items-center justify-center rounded-3xl bg-muted text-sm text-muted-foreground">No chart data available yet.</div>
        ) : (
          <div className="flex items-center gap-6">
            <div className="relative h-36 w-36 shrink-0 rounded-full" style={{ background: `conic-gradient(${gradient})` }}>
              <div className="absolute inset-5 flex items-center justify-center rounded-full bg-card text-center text-xs font-semibold text-muted-foreground">
                {total.toLocaleString()}
                <br />
                total
              </div>
            </div>
            <div className="min-w-0 space-y-2">
              {points.map((point, index) => (
                <div className="flex items-center justify-between gap-4 text-sm" key={point.label}>
                  <span className="flex min-w-0 items-center gap-2 truncate">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: colors[index % colors.length] }} />
                    {point.label}
                  </span>
                  <span className="font-semibold text-labour-ink">{point.value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
