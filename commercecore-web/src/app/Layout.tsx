import { LogOut, ShoppingBag } from "lucide-react";
import { useEffect, useRef } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { IconButton, buttonClass } from "@/components/ui/Button";
import { useAuth } from "@/features/auth/AuthContext";
import { useCart } from "@/features/cart/CartContext";
import { cn } from "@/lib/cn";

function NavItem({ to, end, children }: { to: string; end?: boolean; children: string }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "inline-flex h-11 items-center rounded-xl px-3.5 text-[15px] font-semibold transition-colors duration-150",
          isActive ? "bg-surface-2 text-ink" : "text-muted hover:bg-surface-2 hover:text-ink",
        )
      }
    >
      {children}
    </NavLink>
  );
}

export function Layout() {
  const { account, isAdmin, logout } = useAuth();
  const { count } = useCart();
  const { pathname } = useLocation();
  const main = useRef<HTMLElement>(null);
  const first = useRef(true);

  // After navigating, move focus to the page so keyboard and screen-reader users start at the top.
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    main.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }, [pathname]);

  return (
    <div className="flex min-h-dvh flex-col">
      <a
        href="#main"
        className="sr-only z-50 rounded-xl bg-accent px-4 py-2 font-semibold text-accent-ink focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-0 px-4 py-2 sm:px-6">
          <Link to="/" className="flex h-11 items-center gap-2.5 font-display text-xl font-semibold tracking-tight">
            <Logo className="size-7" />
            CommerceCore
          </Link>

          <nav aria-label="Main" className="order-3 -mx-1 flex w-full gap-1 pb-1 sm:order-none sm:mx-0 sm:w-auto sm:pb-0">
            <NavItem to="/" end>
              Shop
            </NavItem>
            {account && <NavItem to="/orders">My orders</NavItem>}
            {isAdmin && <NavItem to="/admin">Admin</NavItem>}
          </nav>

          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Link
              to="/cart"
              aria-label={`Cart, ${count} ${count === 1 ? "item" : "items"}`}
              className="relative inline-flex size-11 items-center justify-center rounded-xl transition-colors duration-150 hover:bg-surface-2"
            >
              <ShoppingBag className="size-5" aria-hidden />
              {count > 0 && (
                <span className="absolute right-0.5 top-0.5 grid min-w-5 place-items-center rounded-full bg-accent px-1 text-[11px] font-bold leading-5 text-accent-ink tnum">
                  {count}
                </span>
              )}
            </Link>

            {account ? (
              <>
                <span className="ml-1 hidden max-w-36 truncate text-sm font-semibold md:block" title={account.email}>
                  {account.full_name}
                </span>
                <IconButton label="Sign out" onClick={logout}>
                  <LogOut className="size-5" aria-hidden />
                </IconButton>
              </>
            ) : (
              <>
                <Link to="/login" className={buttonClass("ghost", "md", "ml-1")}>
                  Sign in
                </Link>
                <Link to="/register" className={buttonClass("primary", "md", "hidden sm:inline-flex")}>
                  Create account
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main id="main" ref={main} tabIndex={-1} className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 outline-none sm:px-6 sm:py-10">
        <Outlet />
      </main>

      <footer className="border-t border-line py-6 text-center text-sm text-muted">
        CommerceCore · a small online store
      </footer>
    </div>
  );
}
