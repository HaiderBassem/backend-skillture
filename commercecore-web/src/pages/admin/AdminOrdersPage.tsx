import { ClipboardList } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { OrderActions } from "@/components/OrderDetail";
import { StatusBadge } from "@/components/ui/Badge";
import { Chip } from "@/components/ui/Chip";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { useAdminOrders } from "@/features/orders/api";
import { formatDateTime, formatMoney, orderRef } from "@/lib/format";
import type { OrderStatus } from "@/lib/types";

const FILTERS: Array<{ value: OrderStatus | ""; label: string }> = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "confirmed", label: "Confirmed" },
  { value: "cancelled", label: "Cancelled" },
];

export function AdminOrdersPage() {
  const [params, setParams] = useSearchParams();
  const raw = params.get("status");
  const status = FILTERS.find((f) => f.value && f.value === raw)?.value || undefined;
  const orders = useAdminOrders(status as OrderStatus | undefined);

  return (
    <>
      <PageHeader title="Orders" description="Confirm or cancel what customers have placed." />

      <div className="mb-5 flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Filter by status">
        {FILTERS.map((f) => (
          <Chip
            key={f.label}
            active={(status ?? "") === f.value}
            onClick={() => setParams(f.value ? { status: f.value } : {}, { replace: true })}
          >
            {f.label}
          </Chip>
        ))}
      </div>

      {orders.isPending ? (
        <div className="flex flex-col gap-3" aria-busy>
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-20 rounded-[var(--radius-card)]" />
          ))}
        </div>
      ) : orders.isError ? (
        <ErrorState error={orders.error} onRetry={() => void orders.refetch()} />
      ) : orders.data.length === 0 ? (
        <EmptyState
          icon={<ClipboardList className="size-6" aria-hidden />}
          title={status ? `No ${status} orders` : "No orders yet"}
          description="New orders will appear here as customers place them."
        />
      ) : (
        <>
          <ul className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card">
            {orders.data.map((order) => (
              <li key={order.id} className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b border-line px-5 py-4 last:border-b-0">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <Link to={`/admin/orders/${order.id}`} className="font-display text-lg font-semibold hover:underline">
                      {orderRef(order.id)}
                    </Link>
                    <StatusBadge status={order.status} />
                  </div>
                  <p className="text-sm text-muted tnum">
                    Customer #{order.user_id} · {formatDateTime(order.created_at)} · {order.items.length}{" "}
                    {order.items.length === 1 ? "item" : "items"}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-bold tnum">{formatMoney(order.total_amount)}</span>
                  <OrderActions order={order} size="sm" />
                </div>
              </li>
            ))}
          </ul>
          {orders.data.length === 100 && (
            <p className="mt-3 text-center text-sm text-muted">Showing the 100 most recent orders. Use the filters to narrow down.</p>
          )}
        </>
      )}
    </>
  );
}
