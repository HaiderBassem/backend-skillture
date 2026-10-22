import { useId } from "react";
import { cn } from "@/lib/cn";

// The API has no product photos, so every product gets a deterministic "paper tile":
// a duotone palette picked by its category, a pattern picked by its id, and its initials.
const PALETTES = [
  { bg: "#cfe8e1", fg: "#0d6b5e" },
  { bg: "#f0d9c8", fg: "#9a4a22" },
  { bg: "#ece3c8", fg: "#7a6416" },
  { bg: "#d6e0ee", fg: "#2f4a75" },
  { bg: "#dfe6c8", fg: "#4d5e1c" },
  { bg: "#f3d6d6", fg: "#9a3030" },
  { bg: "#dedad2", fg: "#38342c" },
  { bg: "#f5e0b8", fg: "#8a5a00" },
];

function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const letters = words.length > 1 ? (words[0]?.[0] ?? "") + (words[1]?.[0] ?? "") : name.slice(0, 2);
  return letters.toUpperCase();
}

export function ProductArt({
  name,
  categoryId,
  productId,
  className,
  muted,
}: {
  name: string;
  categoryId: number;
  productId: number;
  className?: string;
  muted?: boolean;
}) {
  const uid = useId().replace(/:/g, "");
  const palette = PALETTES[categoryId % PALETTES.length] ?? PALETTES[0]!;
  const variant = productId % 3;

  return (
    <div
      aria-hidden
      className={cn(
        "relative aspect-[4/3] w-full overflow-hidden [container-type:inline-size]",
        muted && "grayscale-[0.7] opacity-70",
        className,
      )}
      style={{ background: palette.bg, color: palette.fg }}
    >
      <svg className="absolute inset-0 size-full" preserveAspectRatio="xMidYMid slice" viewBox="0 0 120 90">
        <defs>
          <pattern id={uid} width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(32)">
            {variant === 0 && <circle cx="6" cy="6" r="1.3" fill="currentColor" opacity="0.22" />}
            {variant === 1 && <rect width="12" height="1.4" y="5" fill="currentColor" opacity="0.18" />}
            {variant === 2 && <path d="M0 12 L12 0" stroke="currentColor" strokeWidth="1" opacity="0.2" />}
          </pattern>
        </defs>
        <rect width="120" height="90" fill={`url(#${uid})`} />
        <circle cx="96" cy="14" r="30" fill="currentColor" opacity="0.1" />
      </svg>
      <span
        // cqw = 1% of the tile's width, so the lettering scales from a thumbnail to the product page.
        className="absolute bottom-[4cqw] left-[5cqw] font-display text-[20cqw] font-semibold leading-none tracking-tight opacity-90"
        style={{ fontVariationSettings: '"SOFT" 100, "WONK" 1' }}
      >
        {initials(name)}
      </span>
    </div>
  );
}
