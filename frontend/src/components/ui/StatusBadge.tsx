import { cn } from "../../lib/cn";

type StatusBadgeProps = {
  status: "OK" | "WARNING" | "ERROR" | "running" | "stopped" | "idle" | "error" | string;
  label?: string;
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const normalized = status.toLowerCase();
  const tone =
    normalized === "ok" || normalized === "running"
      ? "good"
      : normalized === "error"
        ? "bad"
        : "warn";

  return <span className={cn("status-badge", `status-${tone}`)}>{label || status}</span>;
}
