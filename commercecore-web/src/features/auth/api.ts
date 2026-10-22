import { request } from "@/lib/api";
import type { Account, RegisterInput, TokenResponse } from "@/lib/types";

export const authApi = {
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", { method: "POST", body: { email, password } }),
  register: (input: RegisterInput) => request<Account>("/auth/register", { method: "POST", body: input }),
};
