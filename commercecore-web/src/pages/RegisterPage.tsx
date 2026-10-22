import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { AuthCard, FormAlert, PasswordField } from "@/components/AuthCard";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { useAuth } from "@/features/auth/AuthContext";
import { fieldError, formError } from "@/lib/api";

const FIELDS = ["full_name", "email", "password", "international_id"];

export function RegisterPage() {
  const { register } = useAuth();
  const location = useLocation();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", international_id: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});

  const set = (key: keyof typeof form) => (event: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: event.target.value }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    const problems: Record<string, string> = {};
    const idText = form.international_id.trim();
    if (idText && !/^[1-9]\d{0,17}$/.test(idText)) problems.international_id = "Enter a whole number, or leave it empty.";
    if (form.password.length < 8) problems.password = "Use at least 8 characters.";
    setLocalErrors(problems);
    if (Object.keys(problems).length > 0) return;

    setBusy(true);
    setError(null);
    try {
      await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        ...(idText ? { international_id: Number(idText) } : {}),
      });
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  }

  const fieldProblem = (name: string) => localErrors[name] ?? fieldError(error, name);

  return (
    <AuthCard
      title="Create your account"
      description="It takes a minute, and you can start ordering right away."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" state={location.state} className="font-semibold text-accent underline underline-offset-4">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <FormAlert message={formError(error, FIELDS)} />
        <TextField
          label="Full name"
          autoComplete="name"
          required
          maxLength={100}
          value={form.full_name}
          onChange={set("full_name")}
          error={fieldProblem("full_name")}
        />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          inputMode="email"
          required
          value={form.email}
          onChange={set("email")}
          error={fieldProblem("email")}
        />
        <PasswordField
          label="Password"
          autoComplete="new-password"
          required
          minLength={8}
          value={form.password}
          onChange={set("password")}
          hint="At least 8 characters."
          error={fieldProblem("password")}
        />
        <TextField
          label="National / international ID (optional)"
          inputMode="numeric"
          value={form.international_id}
          onChange={set("international_id")}
          error={fieldProblem("international_id")}
        />
        <Button type="submit" size="lg" loading={busy} disabled={!form.full_name || !form.email || !form.password}>
          Create account
        </Button>
      </form>
    </AuthCard>
  );
}
