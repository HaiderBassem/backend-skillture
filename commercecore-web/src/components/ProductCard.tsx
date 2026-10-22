import { Plus } from "lucide-react";
import type { CSSProperties } from "react";
import { Link } from "react-router-dom";
import { useCart } from "@/features/cart/CartContext";
import { cn } from "@/lib/cn";
import { LOW_STOCK, formatMoney } from "@/lib/format";
import type { Product } from "@/lib/types";
import { ProductArt } from "./ProductArt";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { useToast } from "./ui/Toast";

export function StockBadge({ product }: { product: Product }) {
  if (!product.is_active) return <Badge tone="neutral">Not for sale</Badge>;
  if (product.stock_quantity === 0) return <Badge tone="neutral">Sold out</Badge>;
  if (product.stock_quantity <= LOW_STOCK) return <Badge tone="warn">Only {product.stock_quantity} left</Badge>;
  return null;
}

export function ProductCard({ product, categoryName, index }: { product: Product; categoryName?: string; index: number }) {
  const { lines, add } = useCart();
  const toast = useToast();
  const inCart = lines.find((l) => l.productId === product.id)?.quantity ?? 0;
  const atLimit = inCart >= product.stock_quantity;

  return (
    <article
      style={{ "--i": index } as CSSProperties}
      className="relative flex flex-col overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card transition-colors duration-150 hover:border-muted/50"
    >
      <ProductArt
        name={product.name}
        categoryId={product.category_id}
        productId={product.id}
        muted={!product.available}
      />
      <div className="flex flex-1 flex-col gap-1.5 p-4">
        {categoryName && <p className="text-xs font-bold uppercase tracking-wider text-muted">{categoryName}</p>}
        <h3 className="text-lg leading-snug">
          {/* The whole card is clickable: this link stretches over it. */}
          <Link to={`/products/${product.id}`} className="after:absolute after:inset-0 after:content-['']">
            {product.name}
          </Link>
        </h3>
        <div className="min-h-6">
          <StockBadge product={product} />
        </div>
        <div className="mt-auto flex items-center justify-between gap-3 pt-3">
          <span className="text-lg font-bold tnum">{formatMoney(product.price)}</span>
          <Button
            size="sm"
            variant={inCart > 0 ? "secondary" : "primary"}
            className={cn("relative z-10")}
            disabled={!product.available || atLimit}
            aria-label={`Add ${product.name} to cart`}
            icon={<Plus className="size-4" aria-hidden />}
            onClick={() => {
              add(product);
              toast.success(`Added ${product.name}`);
            }}
          >
            {inCart > 0 ? `In cart · ${inCart}` : "Add"}
          </Button>
        </div>
      </div>
    </article>
  );
}
