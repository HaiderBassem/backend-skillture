import { useQueries, useQueryClient } from "@tanstack/react-query";
import { ShoppingBag, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ProductArt } from "@/components/ProductArt";
import { QuantityStepper } from "@/components/QuantityStepper";
import { Button, IconButton, buttonClass } from "@/components/ui/Button";
import { EmptyState, PageHeader } from "@/components/ui/feedback";
import { useToast } from "@/components/ui/Toast";
import { useAuth } from "@/features/auth/AuthContext";
import { fetchProduct } from "@/features/catalog/api";
import { useCart } from "@/features/cart/CartContext";
import { usePlaceOrder } from "@/features/orders/api";
import { ApiError, errorMessage } from "@/lib/api";
import { formatMoney, orderRef, sumMoney } from "@/lib/format";
import type { Product } from "@/lib/types";

export function CartPage() {
  const { lines, subtotal, setQuantity, remove, clear, refresh } = useCart();
  const { account } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const placeOrder = usePlaceOrder();
  const [notice, setNotice] = useState<string | null>(null);

  // Check every line against the server: prices and stock may have changed since it was added.
  const checks = useQueries({
    queries: lines.map((line) => ({
      queryKey: ["product", line.productId],
      queryFn: ({ signal }: { signal: AbortSignal }) => fetchProduct(line.productId, signal),
      refetchOnMount: "always" as const,
      retry: false,
    })),
  });

  const live = new Map<number, Product>();
  const gone = new Set<number>();
  checks.forEach((check, i) => {
    const line = lines[i];
    if (!line) return;
    if (check.data) live.set(line.productId, check.data);
    if (check.error instanceof ApiError && check.error.status === 404) gone.add(line.productId);
  });
  const unavailable = (productId: number) => gone.has(productId) || live.get(productId)?.available === false;

  const signature = checks.map((c) => c.dataUpdatedAt).join(",");
  useEffect(() => {
    const changed = [...live.values()].filter((p) => {
      const line = lines.find((l) => l.productId === p.id);
      return line && (line.price !== p.price || line.stock !== p.stock_quantity || line.name !== p.name);
    });
    if (changed.length > 0) {
      refresh(changed);
      setNotice("Some prices or stock levels changed since you added items. The cart below is up to date.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only re-run when fresh data arrives
  }, [signature]);

  if (lines.length === 0) {
    return (
      <>
        <PageHeader title="Your cart" />
        <EmptyState
          icon={<ShoppingBag className="size-6" aria-hidden />}
          title="Your cart is empty"
          description="Add a few things you like and they'll wait for you here."
          action={
            <Link to="/" className={buttonClass("primary")}>
              Browse the shop
            </Link>
          }
        />
      </>
    );
  }

  const blocked = lines.some((l) => unavailable(l.productId));

  function submit() {
    placeOrder.mutate(
      lines.map((l) => ({ product_id: l.productId, quantity: l.quantity })),
      {
        onSuccess: (order) => {
          clear();
          toast.success(`Order ${orderRef(order.id)} placed`);
          navigate(`/orders/${order.id}`, { state: { placed: true } });
        },
        // Stock may be why it failed: re-check every line.
        onError: () => void queryClient.invalidateQueries({ queryKey: ["product"] }),
      },
    );
  }

  return (
    <>
      <PageHeader
        title="Your cart"
        actions={
          <Button variant="ghost" size="sm" onClick={clear}>
            Empty cart
          </Button>
        }
      />
      {notice && (
        <p role="status" className="mb-4 rounded-xl bg-warn-soft px-4 py-3 text-sm font-semibold text-warn-ink">
          {notice}
        </p>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <ul className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card">
          {lines.map((line) => {
            const out = unavailable(line.productId);
            return (
              <li key={line.productId} className="flex gap-4 border-b border-line p-4 last:border-b-0">
                <div className="hidden w-24 shrink-0 self-start overflow-hidden rounded-xl min-[420px]:block">
                  <ProductArt name={line.name} categoryId={line.categoryId} productId={line.productId} muted={out} />
                </div>
                <div className="flex min-w-0 flex-1 flex-col gap-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <Link to={`/products/${line.productId}`} className="font-semibold hover:underline">
                        {line.name}
                      </Link>
                      <p className="text-sm text-muted tnum">{formatMoney(line.price)} each</p>
                    </div>
                    <p className="font-bold tnum">{formatMoney(sumMoney([{ price: line.price, quantity: line.quantity }]))}</p>
                  </div>
                  {out ? (
                    <p role="alert" className="text-sm font-semibold text-danger-ink">
                      No longer available. Remove it to continue.
                    </p>
                  ) : (
                    <p className="text-[13px] text-muted">{line.stock <= 5 ? `Only ${line.stock} in stock` : "In stock"}</p>
                  )}
                  <div className="mt-auto flex items-center justify-between">
                    {!out ? (
                      <QuantityStepper
                        label={`Quantity of ${line.name}`}
                        value={line.quantity}
                        max={line.stock}
                        onChange={(q) => setQuantity(line.productId, q)}
                      />
                    ) : (
                      <span />
                    )}
                    <IconButton label={`Remove ${line.name}`} onClick={() => remove(line.productId)}>
                      <Trash2 className="size-[18px]" aria-hidden />
                    </IconButton>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>

        <aside className="flex flex-col gap-4 rounded-[var(--radius-card)] border border-line bg-surface p-5 shadow-card lg:sticky lg:top-28">
          <h2 className="text-xl">Summary</h2>
          <dl className="flex items-baseline justify-between">
            <dt className="text-muted">Subtotal</dt>
            <dd className="font-display text-2xl font-semibold tnum">{formatMoney(subtotal)}</dd>
          </dl>
          <p className="text-[13px] text-muted">The store confirms the final price when you place the order.</p>

          {placeOrder.isError && (
            <p role="alert" className="rounded-xl bg-danger-soft px-3.5 py-2.5 text-sm font-medium text-danger-ink">
              {errorMessage(placeOrder.error)}
            </p>
          )}

          {account ? (
            <Button size="lg" loading={placeOrder.isPending} disabled={blocked} onClick={submit}>
              Place order
            </Button>
          ) : (
            <Link to="/login" state={{ from: "/cart" }} className={buttonClass("primary", "lg")}>
              Sign in to place order
            </Link>
          )}
          {blocked && <p className="text-[13px] font-semibold text-danger-ink">Remove the unavailable items to continue.</p>}
        </aside>
      </div>
    </>
  );
}
