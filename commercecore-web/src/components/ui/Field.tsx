import { useId } from "react";
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

const CONTROL =
  "w-full min-h-11 rounded-xl border bg-surface px-3.5 text-[15px] text-ink placeholder:text-muted/80 " +
  "transition-colors duration-150 disabled:opacity-60 focus-visible:outline-2";

export function controlClass(invalid?: boolean) {
  return cn(CONTROL, invalid ? "border-danger" : "border-line hover:border-muted/60");
}

interface FieldShellProps {
  label: string;
  error?: string | null;
  hint?: string;
  required?: boolean;
  className?: string;
  children: (props: { id: string; "aria-describedby"?: string; "aria-invalid"?: true }) => ReactNode;
}

/** A visible label, the control, a hint, and the error right below the control. */
export function Field({ label, error, hint, required, className, children }: FieldShellProps) {
  const id = useId();
  const describedBy = [error ? `${id}-err` : null, hint ? `${id}-hint` : null].filter(Boolean).join(" ");
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-sm font-semibold">
        {label}
        {required && (
          <span aria-hidden className="ml-0.5 text-danger">
            *
          </span>
        )}
      </label>
      {children({
        id,
        "aria-describedby": describedBy || undefined,
        "aria-invalid": error ? true : undefined,
      })}
      {hint && !error && (
        <p id={`${id}-hint`} className="text-[13px] text-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} role="alert" className="text-[13px] font-medium text-danger-ink">
          {error}
        </p>
      )}
    </div>
  );
}

type Shared = { label: string; error?: string | null; hint?: string; fieldClassName?: string };

export function TextField({
  label,
  error,
  hint,
  fieldClassName,
  required,
  className,
  ...rest
}: Shared & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <Field label={label} error={error} hint={hint} required={required} className={fieldClassName}>
      {(a11y) => <input {...a11y} required={required} {...rest} className={cn(controlClass(!!error), className)} />}
    </Field>
  );
}

export function TextAreaField({
  label,
  error,
  hint,
  fieldClassName,
  required,
  className,
  ...rest
}: Shared & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <Field label={label} error={error} hint={hint} required={required} className={fieldClassName}>
      {(a11y) => (
        <textarea
          rows={4}
          {...a11y}
          required={required}
          {...rest}
          className={cn(controlClass(!!error), "py-2.5", className)}
        />
      )}
    </Field>
  );
}

export function SelectField({
  label,
  error,
  hint,
  fieldClassName,
  required,
  className,
  children,
  ...rest
}: Shared & SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <Field label={label} error={error} hint={hint} required={required} className={fieldClassName}>
      {(a11y) => (
        <select {...a11y} required={required} {...rest} className={cn(controlClass(!!error), className)}>
          {children}
        </select>
      )}
    </Field>
  );
}
