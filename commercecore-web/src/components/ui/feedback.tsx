import { AlertTriangle, Inbox } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { errorMessage } from "@/lib/api";
import { Button } from "./Button";

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("skeleton rounded-lg", className)} />;
}

/** Tells the user what to do next instead of showing a blank area. */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="enter flex flex-col items-center gap-3 rounded-[var(--radius-card)] border border-dashed border-line px-6 py-14 text-center">
      <div className="grid size-12 place-items-center rounded-full bg-surface-2 text-muted">
        {icon ?? <Inbox className="size-6" aria-hidden />}
      </div>
      <h2 className="text-xl">{title}</h2>
      {description && <p className="max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

/** A failed request, with the server's message and a way to retry. */
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 rounded-[var(--radius-card)] bg-danger-soft px-6 py-10 text-center">
      <AlertTriangle className="size-7 text-danger-ink" aria-hidden />
      <p className="max-w-md text-sm font-medium text-danger-ink">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-3xl sm:text-4xl">{title}</h1>
        {description && <p className="mt-1.5 max-w-2xl text-[15px] text-muted">{description}</p>}
      </div>
      {actions}
    </div>
  );
}
