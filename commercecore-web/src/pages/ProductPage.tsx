import { ChevronRight, ShoppingBag } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ProductArt } from "@/components/ProductArt";
import { StockBadge } from "@/components/ProductCard";
import { QuantityStepper } from "@/components/QuantityStepper";
import { Button, buttonClass } from "@/components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/feedback";
import { useToast } from "@/components/ui/Toast";
import { useCategories, useProduct } from "@/features/catalog/api";
import { useCart } from "@/features/cart/CartContext";
import { ApiError } from "@/lib/api";
import { formatMoney } from "@/lib/format";

export function ProductPage() {
  const id = Number(useParams().id);
  const product = useProduct(id);
  const categories = useCategories();
  const { lines, add } = useCart();
  const toast = useToast();
  const [quantity, setQuantity] = useState(1);

  if (product.isPending) {
    return (
      <div className="grid gap-8 md:grid-cols-2" aria-busy>
        <Skeleton className="aspect-[4/3] rounded-[var(--radius-card)]" />
        <div className="flex flex-col gap-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    );
  }

  if (product.isError) {
    if (product.error instanceof ApiError && product.error.status === 404) {
      return (
        <EmptyState
          title="This product isn't available"
          description="It may have been taken off sale."
          action={
            <Link to="/" className={buttonClass("primary")}>
              Back to the shop
            </Link>
          }
        />
      );
    }
    return <ErrorState error={product.error} onRetry={() => void product.refetch()} />;
  }

  const p = product.data;
  const category = categories.data?.find((c) => c.id === p.category_id);
  const inCart = lines.find((l) => l.productId === p.id)?.quantity ?? 0;
  const room = Math.max(p.stock_quantity - inCart, 0);
  const shown = Math.min(quantity, Math.max(room, 1));

  return (
    <div className="enter">
      <nav aria-label="Breadcrumb" className="mb-6 flex flex-wrap items-center gap-1 text-sm text-muted">
        <Link to="/" className="hover:text-ink">
          Shop
        </Link>
        {category && (
          <>
            <ChevronRight className="size-4" aria-hidden />
            <Link to={`/?category=${category.id}`} className="hover:text-ink">
              {category.name}
            </Link>
          </>
        )}
        <ChevronRight className="size-4" aria-hidden />
        <span aria-current="page" className="font-semibold text-ink">
          {p.name}
        </span>
      </nav>

      <div className="grid gap-8 md:grid-cols-2 md:gap-12">
        <ProductArt
          name={p.name}
          categoryId={p.category_id}
          productId={p.id}
          muted={!p.available}
          className="rounded-[var(--radius-card)] border border-line"
        />

        <div className="flex flex-col gap-5">
          <div>
            {category && <p className="mb-1 text-xs font-bold uppercase tracking-wider text-muted">{category.name}</p>}
            <h1 className="text-3xl sm:text-4xl">{p.name}</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <p className="font-display text-3xl font-semibold tnum">{formatMoney(p.price)}</p>
            <StockBadge product={p} />
          </div>
          {p.description && <p className="max-w-prose whitespace-pre-line text-[15px] leading-relaxed text-muted">{p.description}</p>}

          {p.available ? (
            <div className="mt-2 flex flex-col gap-3 border-t border-line pt-5">
              {room > 0 ? (
                <div className="flex flex-wrap items-center gap-3">
                  <QuantityStepper label={`Quantity of ${p.name}`} value={shown} max={room} onChange={setQuantity} />
                  <Button
                    size="lg"
                    icon={<ShoppingBag className="size-[18px]" aria-hidden />}
                    onClick={() => {
                      add(p, shown);
                      setQuantity(1);
                      toast.success(`Added ${shown} × ${p.name}`);
                    }}
                  >
                    Add to cart
                  </Button>
                </div>
              ) : (
                <p className="text-sm font-semibold text-muted">All {p.stock_quantity} available are already in your cart.</p>
              )}
              {inCart > 0 && (
                <Link to="/cart" className="w-fit text-sm font-semibold text-accent underline underline-offset-4">
                  {inCart} in your cart · View cart
                </Link>
              )}
            </div>
          ) : (
            <p className="mt-2 rounded-xl bg-surface-2 px-4 py-3 text-sm font-semibold text-muted">
              This product can't be ordered right now.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
