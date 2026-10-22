export function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect width="32" height="32" rx="8" className="fill-accent" />
      <path
        d="M21.5 11.2A7 7 0 1 0 21.5 20.8"
        fill="none"
        strokeWidth="3"
        strokeLinecap="round"
        className="stroke-accent-ink"
      />
    </svg>
  );
}
