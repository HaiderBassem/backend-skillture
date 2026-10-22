import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ToastProvider } from "@/components/ui/Toast";
import { AuthProvider } from "@/features/auth/AuthContext";
import { getToken, setSession } from "@/features/auth/session";
import { CartProvider } from "@/features/cart/CartContext";
import { ApiError, configureApi } from "@/lib/api";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Retrying a 4xx never helps (not found, forbidden, ...); network blips deserve a retry.
      retry: (failures, error) => !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failures < 2,
    },
  },
});

// The API client reads the token from the session store and signs the user out when the
// server rejects it (expired or revoked). Route guards then send them to the login page.
configureApi({
  getToken,
  onUnauthorized: () => {
    setSession(null);
    queryClient.clear();
  },
});

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <CartProvider>{children}</CartProvider>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
