import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation } from "react-router-dom";
import { AuthCard, FormAlert, PasswordField } from "@/components/AuthCard";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { useAuth } from "@/features/auth/AuthContext";
import { fieldError, formError } from "@/lib/api";

// Handy while developing: the accounts created by `make seed` (all use password123).
const DEMO_ACCOUNTS = [
  { label: "Customer", email: "sara@example.com" },
  { label: "Administrator", email: "admin@commercecore.dev" },
];

export function LoginPage() {
  const { login } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password); // the router then sends you on (GuestOnly)
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      description="Sign in to place orders and follow them."
      footer={
        <>
          New here?{" "}
          <Link to="/register" state={location.state} className="font-semibold text-accent underline underline-offset-4">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <FormAlert message={formError(error, ["email", "password"])} />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          inputMode="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={fieldError(error, "email")}
        />
        <PasswordField
          label="Password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={fieldError(error, "password")}
        />
        <Button type="submit" size="lg" loading={busy} disabled={!email || !password}>
          Sign in
        </Button>
      </form>

      {import.meta.env.DEV && (
        <div className="mt-5 border-t border-line pt-4">
          <p className="mb-2 text-[13px] text-muted">Development only: fill in a seeded demo account</p>
          <div className="flex flex-wrap gap-2">
            {DEMO_ACCOUNTS.map((account) => (
              <Button
                key={account.email}
                size="sm"
                variant="secondary"
                onClick={() => {
                  setEmail(account.email);
                  setPassword("password123");
                }}
              >
                {account.label}
              </Button>
            ))}
          </div>
        </div>
      )}
    </AuthCard>
  );
}
