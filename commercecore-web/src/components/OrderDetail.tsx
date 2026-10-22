import { CheckCircle2, CircleDot, XCircle } from "lucide-react";
import { useState } from "react";
import { useDecideOrder } from "@/features/orders/api";
import { cn } from "@/lib/cn";
import { formatDateTime, formatMoney, orderRef } from "@/lib/format";
import type { AdminOrder, Order } from "@/lib/types";
import { StatusBadge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { ConfirmDialog } from "./ui/Modal";
import { useToast } from "./ui/Toast";

function Timeline({ order }: { order: Order }) {
  const decided = order.decided_at ? formatDateTime(order.decided_at) : null;
  const steps = [
    { icon: CheckCircle2, tone: "text-accent", title: "Order placed", when: formatDateTime(order.created_at) },
    order.status === "pending"
      ? { icon: CircleDot, tone: "text-warn-ink", title: "Waiting for the store to confirm", when: null }
      : order.status === "confirmed"
        ? { icon: CheckCircle2, tone: "text-accent", title: "Confirmed by the store", when: decided }
        : { icon: XCircle, tone: "text-danger-ink", title: "Cancelled", when: decided },
  ];
  return (
    <ol className="flex flex-col gap-3" aria-label="Order progress">
      {steps.map((step) => (
        <li key={step.title} className="flex items-start gap-3">
          <step.icon className={cn("mt-0.5 size-5 shrink-0", step.tone)} aria-hidden />
          <div>
            <p className="text-[15px] font-semibold">{step.title}</p>
            {step.when && <p className="text-sm text-muted">{step.when}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** One order in full: lines, total and progress. Admin orders also show who ordered. */
export function OrderDetail({ order }: { order: Order | AdminOrder }) {
  const admin = "user_id" in order ? order : null;
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
      <section aria-labelledby="items-title" className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card">
        <h2 id="items-title" className="border-b border-line px-5 py-4 text-xl">
          Items
        </h2>
        <ul className="divide-y divide-line">
          {order.items.map((item) => (
            <li key={item.product_id} className="flex items-start justify-between gap-4 px-5 py-4">
              <div className="min-w-0">
                <p className="font-semibold">{item.product_name}</p>
                <p className="text-sm text-muted tnum">
                  {formatMoney(item.unit_price)} × {item.quantity}
                </p>
              </div>
              <p className="font-bold tnum">{formatMoney(item.line_total)}</p>
            </li>
          ))}
        </ul>
        <div className="flex items-center justify-between border-t border-line bg-surface-2 px-5 py-4">
          <span className="font-semibold">Total</span>
          <span className="font-display text-2xl font-semibold tnum">{formatMoney(order.total_amount)}</span>
        </div>
      </section>

      <aside className="flex flex-col gap-6">
        <section className="rounded-[var(--radius-card)] border border-line bg-surface p-5 shadow-card">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-xl">{orderRef(order.id)}</h2>
            <StatusBadge status={order.status} />
          </div>
          <Timeline order={order} />
        </section>
        {admin && (
          <section className="rounded-[var(--radius-card)] border border-line bg-surface p-5 text-sm shadow-card">
            <h2 className="mb-3 text-xl">Customer</h2>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5">
              <dt className="text-muted">Account</dt>
              <dd className="font-semibold tnum">#{admin.user_id}</dd>
              {admin.decided_by !== null && (
                <>
                  <dt className="text-muted">Decided by</dt>
                  <dd className="font-semibold tnum">Admin #{admin.decided_by}</dd>
                </>
              )}
            </dl>
          </section>
        )}
      </aside>
    </div>
  );
}

/** Confirm / Cancel for a pending order. Each asks first: neither can be undone. */
export function OrderActions({ order, size = "md" }: { order: Order; size?: "sm" | "md" }) {
  const decide = useDecideOrder();
  const toast = useToast();
  const [action, setAction] = useState<"confirm" | "cancel" | null>(null);

  if (order.status !== "pending") return null;

  const cancelling = action === "cancel";
  return (
    <>
      <div className="flex gap-2">
        <Button size={size} variant="secondary" onClick={() => setAction("cancel")}>
          Cancel order
        </Button>
        <Button size={size} onClick={() => setAction("confirm")}>
          Confirm
        </Button>
      </div>
      <ConfirmDialog
        open={action !== null}
        tone={cancelling ? "danger" : "primary"}
        title={cancelling ? `Cancel order ${orderRef(order.id)}?` : `Confirm order ${orderRef(order.id)}?`}
        description={
          cancelling
            ? "The stock for these items goes back on the shelf. This can't be undone."
            : "The customer's order is accepted. This can't be undone."
        }
        confirmLabel={cancelling ? "Cancel order" : "Confirm order"}
        onClose={() => setAction(null)}
        onConfirm={async () => {
          if (!action) return;
          await decide.mutateAsync({ id: order.id, action });
          toast.success(action === "confirm" ? `Order ${orderRef(order.id)} confirmed` : `Order ${orderRef(order.id)} cancelled`);
        }}
      />
    </>
  );
}
