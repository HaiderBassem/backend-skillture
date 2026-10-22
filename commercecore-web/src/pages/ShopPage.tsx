import { PackageSearch, Search } from "lucide-react";
import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { ProductCard } from "@/components/ProductCard";
import { Button } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { controlClass } from "@/components/ui/Field";
import { useCategories, useProducts } from "@/features/catalog/api";
import { cn } from "@/lib/cn";

type Sort = "default" | "price-asc" | "price-desc" | "name";
const SORTS: Array<{ value: Sort; label: string }> = [
  { value: "default", label: "Featured" },
  { value: "price-asc", label: "Price: low to high" },
  { value: "price-desc", label: "Price: high to low" },
  { value: "name", label: "Name: A to Z" },
];

export function ShopPage() {
  // Filters live in the URL, so a filtered view can be shared or bookmarked and Back works.
  const [params, setParams] = useSearchParams();
  const categoryId = Number(params.get("category")) || undefined;
  const q = params.get("q") ?? "";
  const sortParam = params.get("sort");
  const sort: Sort = SORTS.some((s) => s.value === sortParam) ? (sortParam as Sort) : "default";
  const inStockOnly = params.get("instock") === "1";

  const categories = useCategories();
  const products = useProducts(categoryId);
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = products;
  const searching = q.trim() !== "";

  // The API has no text search, so while searching, load the remaining pages to search them all.
  useEffect(() => {
    if (searching && hasNextPage && !isFetchingNextPage) void fetchNextPage();
  }, [searching, hasNextPage, isFetchingNextPage, fetchNextPage]);

  function update(changes: Record<string, string | null>) {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        for (const [key, value] of Object.entries(changes)) {
          if (value) next.set(key, value);
          else next.delete(key);
        }
        return next;
      },
      { replace: true },
    );
  }

  const categoryName = useMemo(
    () => new Map((categories.data ?? []).map((c) => [c.id, c.name])),
    [categories.data],
  );

  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let list = (products.data?.products ?? []).filter(
      (p) =>
        (!needle || p.name.toLowerCase().includes(needle) || p.description.toLowerCase().includes(needle)) &&
        (!inStockOnly || p.available),
    );
    if (sort === "price-asc") list = [...list].sort((a, b) => Number(a.price) - Number(b.price));
    if (sort === "price-desc") list = [...list].sort((a, b) => Number(b.price) - Number(a.price));
    if (sort === "name") list = [...list].sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [products.data, q, sort, inStockOnly]);

  const filtered = searching || inStockOnly;

  return (
    <>
      <PageHeader title="Shop" description="Everything in stock, ready to order." />

      <div className="mb-6 flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 size-[18px] -translate-y-1/2 text-muted" aria-hidden />
            <input
              type="search"
              value={q}
              onChange={(event) => update({ q: event.target.value || null })}
              placeholder="Search products"
              aria-label="Search products"
              className={cn(controlClass(), "pl-10")}
            />
          </div>
          <select
            value={sort}
            onChange={(event) => update({ sort: event.target.value === "default" ? null : event.target.value })}
            aria-label="Sort products"
            className={cn(controlClass(), "sm:w-52")}
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0" role="group" aria-label="Categories">
          <Chip active={!categoryId} onClick={() => update({ category: null })}>
            All
          </Chip>
          {(categories.data ?? []).map((c) => (
            <Chip key={c.id} active={categoryId === c.id} onClick={() => update({ category: String(c.id) })}>
              {c.name}
            </Chip>
          ))}
        </div>

        <label className="inline-flex min-h-11 w-fit cursor-pointer items-center gap-2.5 text-sm font-semibold">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(event) => update({ instock: event.target.checked ? "1" : null })}
            className="size-[18px] accent-[var(--accent)]"
          />
          Hide sold-out items
        </label>
      </div>

      {products.isPending ? (
        <div className="grid grid-cols-1 gap-4 min-[520px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4" aria-busy>
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton key={i} className="h-72 rounded-[var(--radius-card)]" />
          ))}
        </div>
      ) : products.isError ? (
        <ErrorState error={products.error} onRetry={() => void products.refetch()} />
      ) : visible.length === 0 ? (
        <EmptyState
          icon={<PackageSearch className="size-6" aria-hidden />}
          title={filtered ? "Nothing matches your search" : "No products here yet"}
          description={filtered ? "Try a different word, or clear the filters." : "Check back soon, or try another category."}
          action={
            filtered || categoryId ? (
              <Button variant="secondary" onClick={() => setParams({}, { replace: true })}>
                Clear filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <p aria-live="polite" className="mb-3 text-sm text-muted tnum">
            {visible.length} {visible.length === 1 ? "product" : "products"}
          </p>
          <div className="stagger grid grid-cols-1 gap-4 min-[520px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {visible.map((product, index) => (
              <ProductCard
                key={product.id}
                product={product}
                index={index}
                categoryName={categoryName.get(product.category_id)}
              />
            ))}
          </div>
          {hasNextPage && !searching && (
            <div className="mt-8 flex justify-center">
              <Button variant="secondary" loading={isFetchingNextPage} onClick={() => void fetchNextPage()}>
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </>
  );
}
