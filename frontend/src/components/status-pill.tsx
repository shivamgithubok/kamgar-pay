import { Badge } from "@/components/ui/badge";

type StatusPillProps = {
  value: string;
};

export function StatusPill({ value }: StatusPillProps) {
  const normalized = value.toLowerCase();
  const variant = normalized.includes("active") || normalized.includes("approved") || normalized.includes("paid") || normalized.includes("present") || normalized.includes("checked")
    ? "success"
    : normalized.includes("review") || normalized.includes("leave") || normalized.includes("pending") || normalized.includes("half")
      ? "warning"
      : normalized.includes("absent") || normalized.includes("rejected") || normalized.includes("inactive")
        ? "danger"
        : normalized.includes("draft")
          ? "muted"
          : "clay";

  return <Badge variant={variant}>{value.replaceAll("_", " ")}</Badge>;
}
