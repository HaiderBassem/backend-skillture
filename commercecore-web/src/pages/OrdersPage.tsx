import { ChevronRight, ReceiptText } from "lucide-react";
import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "@/components/ui/Badge";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { useMyOrders } from "@/features/orders/api";
import { formatDate, formatMoney, orderRef } from "@/lib/format";
import type { Order } from "@/lib/types";

function itemsSummary(order: Order): string {
  const names = order.items.map((i) => (i.quantity > 1 ? `${i.product_name} × ${i.quantity}` : i.product_name));
  return names.length <= 2 ? names.join(", ") : `${names.slice(0, 2).join(", ")} +${names.length - 2} more`;
}

export function OrdersPage() {
  const orders = useMyOrders();

  return (
    <>
      <PageHeader title="My orders" description="Everything you've ordered, newest first." />

      {orders.isPending ? (
        <div className="flex flex-col gap-3" aria-busy>
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-24 rounded-[var(--radius-card)]" />
          ))}
        </div>
      ) : orders.isError ? (
        <ErrorState error={orders.error} onRetry={() => void orders.refetch()} />
      ) : orders.data.length === 0 ? (
        <EmptyState
          icon={<ReceiptText className="size-6" aria-hidden />}
          title="No orders yet"
          description="When you place an order it shows up here, with its progress."
          action={
            <Link to="/" className={buttonClass("primary")}>
              Start shopping
            </Link>
          }
        />
      ) : (
        <ul className="stagger flex flex-col gap-3">
          {orders.data.map((order, index) => (
            <li key={order.id} style={{ "--i": index } as CSSProperties}>
              <Link
                to={`/orders/${order.id}`}
                className="flex items-center gap-4 rounded-[var(--radius-card)] border border-line bg-surface p-4 shadow-card transition-colors duration-150 hover:border-muted/50 sm:p-5"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="font-display text-lg font-semibold">{orderRef(order.id)}</span>
                    <StatusBadge status={order.status} />
                    <span className="text-sm text-muted">{formatDate(order.created_at)}</span>
                  </div>
                  <p className="truncate text-sm text-muted">{itemsSummary(order)}</p>
                </div>
                <span className="font-bold tnum">{formatMoney(order.total_amount)}</span>
                <ChevronRight className="size-5 shrink-0 text-muted" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
