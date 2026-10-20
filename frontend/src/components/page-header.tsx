import { Button } from "@/components/ui/button";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  action?: string;
  onAction?: () => void;
};

export function PageHeader({ eyebrow, title, description, action = "New entry", onAction }: PageHeaderProps) {
  return (
    <header className="mb-6 animate-fade-up">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary/80">{eyebrow}</p>
          <h2 className="text-3xl font-semibold tracking-tight text-labour-ink">{title}</h2>
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{description}</p>
        </div>
        <Button onClick={onAction}>{action}</Button>
      </div>
    </header>
  );
}
