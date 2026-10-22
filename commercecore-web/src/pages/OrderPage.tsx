import { ArrowLeft, PartyPopper } from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";
import { OrderDetail } from "@/components/OrderDetail";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { useMyOrder } from "@/features/orders/api";
import { ApiError } from "@/lib/api";
import { formatDateTime, orderRef } from "@/lib/format";

export function OrderPage() {
  const id = Number(useParams().id);
  const order = useMyOrder(id);
  const justPlaced = (useLocation().state as { placed?: boolean } | null)?.placed === true;

  const back = (
    <Link to="/orders" className="mb-4 inline-flex h-11 items-center gap-1.5 text-sm font-semibold text-muted hover:text-ink">
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
            description="It doesn't exist, or it belongs to a different account."
            action={
              <Link to="/orders" className={buttonClass("primary")}>
                See my orders
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
      {justPlaced && (
        <div role="status" className="mb-6 flex items-center gap-3 rounded-[var(--radius-card)] bg-accent-soft px-5 py-4 text-accent-soft-ink">
          <PartyPopper className="size-6 shrink-0" aria-hidden />
          <p className="font-semibold">Thank you! Your order is placed. The store will confirm it shortly.</p>
        </div>
      )}
      <PageHeader title={`Order ${orderRef(order.data.id)}`} description={`Placed ${formatDateTime(order.data.created_at)}`} />
      <OrderDetail order={order.data} />
    </div>
  );
}
