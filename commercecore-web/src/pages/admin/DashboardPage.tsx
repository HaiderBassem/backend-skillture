import { ArrowRight } from "lucide-react";
import { useMemo } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { OrderActions } from "@/components/OrderDetail";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { useAuth } from "@/features/auth/AuthContext";
import { useAllAdminProducts, useCategories } from "@/features/catalog/api";
import { useAdminOrders } from "@/features/orders/api";
import { cn } from "@/lib/cn";
import { LOW_STOCK, formatDate, formatMoney, orderRef } from "@/lib/format";

function StatTile({
  label,
  value,
  hint,
  to,
  tone,
  loading,
}: {
  label: string;
  value: number;
  hint: string;
  to: string;
  tone?: "warn";
  loading: boolean;
}) {
  return (
    <Link
      to={to}
      className={cn(
        "group flex flex-col gap-1 rounded-[var(--radius-card)] border p-5 shadow-card transition-colors duration-150",
        tone === "warn" && value > 0
          ? "border-transparent bg-warn-soft text-warn-ink"
          : "border-line bg-surface hover:border-muted/50",
      )}
    >
      <span className="text-sm font-semibold">{label}</span>
      {loading ? (
        <Skeleton className="my-1 h-10 w-16" />
      ) : (
        <span className="font-display text-4xl font-semibold leading-tight tnum">{value}</span>
      )}
      <span className="flex items-center justify-between text-[13px] opacity-80">
        {hint}
        <ArrowRight className="size-4 transition-transform duration-150 group-hover:translate-x-0.5" aria-hidden />
      </span>
    </Link>
  );
}

function Panel({ title, to, linkLabel, children }: { title: string; to: string; linkLabel: string; children: ReactNode }) {
  return (
    <section className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card">
      <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
        <h2 className="text-xl">{title}</h2>
        <Link to={to} className="inline-flex h-11 items-center text-sm font-semibold text-accent underline-offset-4 hover:underline">
          {linkLabel}
        </Link>
      </header>
      {children}
    </section>
  );
}

export function DashboardPage() {
  const { account } = useAuth();
  const pending = useAdminOrders("pending");
  const catalog = useAllAdminProducts();
  const categories = useCategories();

  const stats = useMemo(() => {
    const list = catalog.products;
    const lowStock = list
      .filter((p) => p.is_active && p.stock_quantity > 0 && p.stock_quantity <= LOW_STOCK)
      .sort((a, b) => a.stock_quantity - b.stock_quantity);
    return {
      onSale: list.filter((p) => p.available).length,
      lowStock,
      soldOut: list.filter((p) => p.is_active && p.stock_quantity === 0),
    };
  }, [catalog.products]);

  const categoryName = (id: number) => categories.data?.find((c) => c.id === id)?.name;
  const firstName = account?.full_name.split(" ")[0] ?? "";

  return (
    <>
      <PageHeader title={`Hello, ${firstName}`} description="What needs your attention in the store today." />

      <div className="mb-8 grid grid-cols-1 gap-4 min-[520px]:grid-cols-2 xl:grid-cols-4">
        <StatTile
          label="Orders to decide"
          value={pending.data?.length ?? 0}
          hint="Pending confirmation"
          to="/admin/orders?status=pending"
          tone="warn"
          loading={pending.isPending}
        />
        <StatTile label="On sale" value={stats.onSale} hint="Products customers can buy" to="/admin/products?filter=onsale" loading={catalog.isLoading} />
        <StatTile label="Running low" value={stats.lowStock.length} hint={`${LOW_STOCK} or fewer left`} to="/admin/products?filter=low" tone="warn" loading={catalog.isLoading} />
        <StatTile label="Sold out" value={stats.soldOut.length} hint="Active but no stock" to="/admin/products?filter=out" loading={catalog.isLoading} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Needs a decision" to="/admin/orders?status=pending" linkLabel="All pending">
          {pending.isPending ? (
            <div className="p-5">
              <Skeleton className="h-16" />
            </div>
          ) : pending.isError ? (
            <div className="p-5">
              <ErrorState error={pending.error} onRetry={() => void pending.refetch()} />
            </div>
          ) : pending.data.length === 0 ? (
            <div className="p-5">
              <EmptyState title="All caught up" description="There are no orders waiting for a decision." />
            </div>
          ) : (
            <ul className="divide-y divide-line">
              {pending.data.slice(0, 5).map((order) => (
                <li key={order.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                  <div className="min-w-0">
                    <Link to={`/admin/orders/${order.id}`} className="font-display text-lg font-semibold hover:underline">
                      {orderRef(order.id)}
                    </Link>
                    <p className="text-sm text-muted tnum">
                      Customer #{order.user_id} · {formatDate(order.created_at)} · {formatMoney(order.total_amount)}
                    </p>
                  </div>
                  <OrderActions order={order} size="sm" />
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Running low" to="/admin/products?filter=low" linkLabel="All low stock">
          {catalog.isLoading ? (
            <div className="p-5">
              <Skeleton className="h-16" />
            </div>
          ) : catalog.error ? (
            <div className="p-5">
              <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} />
            </div>
          ) : stats.lowStock.length + stats.soldOut.length === 0 ? (
            <div className="p-5">
              <EmptyState title="Stock looks healthy" description="Nothing is running low right now." />
            </div>
          ) : (
            <ul className="divide-y divide-line">
              {[...stats.soldOut, ...stats.lowStock].slice(0, 6).map((p) => (
                <li key={p.id} className="flex items-center justify-between gap-3 px-5 py-3.5">
                  <div className="min-w-0">
                    <Link to={`/admin/products?q=${encodeURIComponent(p.name)}`} className="font-semibold hover:underline">
                      {p.name}
                    </Link>
                    <p className="text-sm text-muted">{categoryName(p.category_id)}</p>
                  </div>
                  {p.stock_quantity === 0 ? <Badge tone="danger">Sold out</Badge> : <Badge tone="warn">{p.stock_quantity} left</Badge>}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </>
  );
}
