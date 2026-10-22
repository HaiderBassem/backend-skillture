import { CheckCircle2, Clock3, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { STATUS_LABEL } from "@/lib/format";
import type { OrderStatus } from "@/lib/types";

export type Tone = "neutral" | "accent" | "warn" | "danger";

const TONE: Record<Tone, string> = {
  neutral: "bg-surface-2 text-muted",
  accent: "bg-accent-soft text-accent-soft-ink",
  warn: "bg-warn-soft text-warn-ink",
  danger: "bg-danger-soft text-danger-ink",
};

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold tracking-wide",
        TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

const STATUS: Record<OrderStatus, { tone: Tone; icon: typeof Clock3 }> = {
  pending: { tone: "warn", icon: Clock3 },
  confirmed: { tone: "accent", icon: CheckCircle2 },
  cancelled: { tone: "danger", icon: XCircle },
};

/** Status is always icon + text, never color alone. */
export function StatusBadge({ status }: { status: OrderStatus }) {
  const { tone, icon: Icon } = STATUS[status];
  return (
    <Badge tone={tone}>
      <Icon className="size-3.5" aria-hidden />
      {STATUS_LABEL[status]}
    </Badge>
  );
}
