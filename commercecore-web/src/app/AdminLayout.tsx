import { ClipboardList, LayoutDashboard, Package, Store, Tags } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAdminOrders } from "@/features/orders/api";
import { cn } from "@/lib/cn";

function AdminNavItem({
  to,
  end,
  icon: Icon,
  label,
  badge,
}: {
  to: string;
  end?: boolean;
  icon: LucideIcon;
  label: string;
  badge?: number;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex h-11 shrink-0 items-center gap-2.5 rounded-xl px-3.5 text-[15px] font-semibold transition-colors duration-150",
          isActive ? "bg-accent-soft text-accent-soft-ink" : "text-muted hover:bg-surface-2 hover:text-ink",
        )
      }
    >
      <Icon className="size-[18px]" aria-hidden />
      {label}
      {!!badge && (
        <span className="ml-auto rounded-full bg-warn-soft px-2 text-xs font-bold leading-5 text-warn-ink tnum">
          {badge >= 100 ? "99+" : badge}
          <span className="sr-only"> pending</span>
        </span>
      )}
    </NavLink>
  );
}

/** Sidebar on desktop, a scrollable tab strip on small screens. */
export function AdminLayout() {
  const pending = useAdminOrders("pending");

  return (
    <div className="grid gap-6 lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-10">
      <nav aria-label="Admin" className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-1 lg:sticky lg:top-24 lg:mx-0 lg:flex-col lg:self-start lg:overflow-visible lg:px-0">
        <AdminNavItem to="/admin" end icon={LayoutDashboard} label="Overview" />
        <AdminNavItem to="/admin/orders" icon={ClipboardList} label="Orders" badge={pending.data?.length} />
        <AdminNavItem to="/admin/products" icon={Package} label="Products" />
        <AdminNavItem to="/admin/categories" icon={Tags} label="Categories" />
        <div className="my-1 hidden border-t border-line lg:block" />
        <AdminNavItem to="/" icon={Store} label="View shop" />
      </nav>
      <div className="min-w-0">
        <Outlet />
      </div>
    </div>
  );
}
