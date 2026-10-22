import { ShieldAlert } from "lucide-react";
import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/feedback";
import { useAuth } from "./AuthContext";

function loginRedirect(from: string) {
  return <Navigate to="/login" replace state={{ from }} />;
}

/** Customer pages: signed-out visitors are sent to log in, then brought back. */
export function RequireAuth() {
  const { account } = useAuth();
  const location = useLocation();
  if (!account) return loginRedirect(location.pathname + location.search);
  return <Outlet />;
}

/** Admin pages. The API enforces this too (403); this just gives a friendly screen. */
export function RequireAdmin() {
  const { account, isAdmin } = useAuth();
  const location = useLocation();
  if (!account) return loginRedirect(location.pathname + location.search);
  if (!isAdmin) {
    return (
      <EmptyState
        icon={<ShieldAlert className="size-6" aria-hidden />}
        title="Administrators only"
        description="Your account doesn't have access to the admin console."
        action={
          <Link to="/" className={buttonClass("secondary")}>
            Back to the shop
          </Link>
        }
      />
    );
  }
  return <Outlet />;
}

/** Login and register: signed-in users are sent on to where they were heading. */
export function GuestOnly() {
  const { account, isAdmin } = useAuth();
  const location = useLocation();
  if (account) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from ?? (isAdmin ? "/admin" : "/")} replace />;
  }
  return <Outlet />;
}
