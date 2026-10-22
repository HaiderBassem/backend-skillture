import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** A toggle-style filter pill. `aria-pressed` tells screen readers which one is on. */
export function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "h-11 shrink-0 rounded-full border px-4 text-sm font-semibold transition-colors duration-150",
        active ? "border-accent bg-accent text-accent-ink" : "border-line bg-surface text-ink hover:bg-surface-2",
      )}
    >
      {children}
    </button>
  );
}
