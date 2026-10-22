import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { OrderActions, OrderDetail } from "@/components/OrderDetail";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { useAdminOrder } from "@/features/orders/api";
import { ApiError } from "@/lib/api";
import { formatDateTime, orderRef } from "@/lib/format";

export function AdminOrderPage() {
  const id = Number(useParams().id);
  const order = useAdminOrder(id);

  const back = (
    <Link to="/admin/orders" className="mb-4 inline-flex h-11 items-center gap-1.5 text-sm font-semibold text-muted hover:text-ink">
      <ArrowLeft className="size-4" aria-hidden />
      All orders
    </Link>
  );

  if (order.isPending) {
    return (
      <>
        {back}
        <Skeleton className="mb-6 h-10 w-64" />
        <Skeleton className="h-64 rounded-[var(--radius-card)]" />
      </>
    );
  }

  if (order.isError) {
    return (
      <>
        {back}
        {order.error instanceof ApiError && order.error.status === 404 ? (
          <EmptyState
            title="Order not found"
            action={
              <Link to="/admin/orders" className={buttonClass("primary")}>
                See all orders
              </Link>
            }
          />
        ) : (
          <ErrorState error={order.error} onRetry={() => void order.refetch()} />
        )}
      </>
    );
  }

  return (
    <div className="enter">
      {back}
      <PageHeader
        title={`Order ${orderRef(order.data.id)}`}
        description={`Placed ${formatDateTime(order.data.created_at)}`}
        actions={<OrderActions order={order.data} />}
      />
      <OrderDetail order={order.data} />
    </div>
  );
}
