import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Logo } from "./Logo";
import { Field, controlClass } from "./ui/Field";

export function AuthCard({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="enter mx-auto flex max-w-md flex-col gap-6 pt-2 sm:pt-8">
      <div className="flex flex-col items-center gap-3 text-center">
        <Logo className="size-10" />
        <h1 className="text-3xl">{title}</h1>
        <p className="text-[15px] text-muted">{description}</p>
      </div>
      <div className="rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-card">{children}</div>
      <p className="text-center text-[15px] text-muted">{footer}</p>
    </div>
  );
}

/** A password input with a show/hide button. */
export function PasswordField({
  label,
  error,
  hint,
  ...rest
}: { label: string; error?: string | null; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  const [shown, setShown] = useState(false);
  return (
    <Field label={label} error={error} hint={hint} required={rest.required}>
      {(a11y) => (
        <div className="relative">
          <input {...a11y} {...rest} type={shown ? "text" : "password"} className={cn(controlClass(!!error), "pr-12")} />
          <button
            type="button"
            onClick={() => setShown((s) => !s)}
            aria-label={shown ? "Hide password" : "Show password"}
            aria-pressed={shown}
            className="absolute right-0 top-0 grid size-11 place-items-center rounded-xl text-muted hover:text-ink"
          >
            {shown ? <EyeOff className="size-[18px]" aria-hidden /> : <Eye className="size-[18px]" aria-hidden />}
          </button>
        </div>
      )}
    </Field>
  );
}

export function FormAlert({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-xl bg-danger-soft px-3.5 py-2.5 text-sm font-medium text-danger-ink">
      {message}
    </p>
  );
}
