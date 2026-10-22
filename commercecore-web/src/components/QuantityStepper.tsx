import { Minus, Plus } from "lucide-react";
import { IconButton } from "./ui/Button";

/** − 2 +  : never goes below 1 or above `max` (the stock). Removing is a separate action. */
export function QuantityStepper({
  value,
  max,
  onChange,
  label,
}: {
  value: number;
  max: number;
  onChange: (value: number) => void;
  label: string;
}) {
  return (
    <div role="group" aria-label={label} className="inline-flex items-center rounded-xl border border-line bg-surface">
      <IconButton label="Decrease quantity" disabled={value <= 1} onClick={() => onChange(value - 1)}>
        <Minus className="size-4" aria-hidden />
      </IconButton>
      <output aria-live="polite" className="min-w-8 text-center font-bold tnum">
        {value}
      </output>
      <IconButton label="Increase quantity" disabled={value >= max} onClick={() => onChange(value + 1)}>
        <Plus className="size-4" aria-hidden />
      </IconButton>
    </div>
  );
}
