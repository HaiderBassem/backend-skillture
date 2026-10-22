import { useQueryClient } from "@tanstack/react-query";
import { createContext, use, useCallback, useMemo, useSyncExternalStore } from "react";
import type { ReactNode } from "react";
import type { Account, RegisterInput } from "@/lib/types";
import { authApi } from "./api";
import { getSession, setSession, subscribeSession } from "./session";

interface AuthValue {
  account: Account | null;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const session = useSyncExternalStore(subscribeSession, getSession);
  const queryClient = useQueryClient();

  const login = useCallback(async (email: string, password: string) => {
    const result = await authApi.login(email.trim(), password);
    setSession({
      token: result.access_token,
      expiresAt: Date.now() + result.expires_in * 1000,
      account: result.account,
    });
  }, []);

  const register = useCallback(
    async (input: RegisterInput) => {
      await authApi.register(input);
      await login(input.email, input.password); // registering also signs you in
    },
    [login],
  );

  const logout = useCallback(() => {
    setSession(null);
    queryClient.clear(); // nothing from this account may linger in memory
  }, [queryClient]);

  const value = useMemo<AuthValue>(
    () => ({
      account: session?.account ?? null,
      isAdmin: session?.account.role === "admin",
      login,
      register,
      logout,
    }),
    [session, login, register, logout],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthValue {
  const ctx = use(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
