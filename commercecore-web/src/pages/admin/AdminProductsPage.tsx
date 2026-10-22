import { PackageSearch, Pencil, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ProductArt } from "@/components/ProductArt";
import { StockBadge } from "@/components/ProductCard";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton, buttonClass } from "@/components/ui/Button";
import { Chip } from "@/components/ui/Chip";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { SelectField, TextAreaField, TextField, controlClass } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { useAllAdminProducts, useCategories, useSaveProduct } from "@/features/catalog/api";
import { errorMessage, fieldError, formError } from "@/lib/api";
import { cn } from "@/lib/cn";
import { LOW_STOCK, formatMoney } from "@/lib/format";
import type { Category, Product, ProductCreateInput, ProductUpdateInput } from "@/lib/types";

type Filter = "all" | "onsale" | "low" | "out" | "hidden";
const FILTERS: Array<{ value: Filter; label: string }> = [
  { value: "all", label: "All" },
  { value: "onsale", label: "On sale" },
  { value: "low", label: "Low stock" },
  { value: "out", label: "Sold out" },
  { value: "hidden", label: "Hidden" },
];

const MATCH: Record<Filter, (p: Product) => boolean> = {
  all: () => true,
  onsale: (p) => p.available,
  low: (p) => p.is_active && p.stock_quantity > 0 && p.stock_quantity <= LOW_STOCK,
  out: (p) => p.is_active && p.stock_quantity === 0,
  hidden: (p) => !p.is_active,
};

const FORM_FIELDS = ["category_id", "name", "description", "price", "stock_quantity", "is_active"];

function ProductForm({ product, categories, onClose }: { product: Product | null; categories: Category[]; onClose: () => void }) {
  const save = useSaveProduct();
  const toast = useToast();
  const [form, setForm] = useState({
    category_id: String(product?.category_id ?? categories[0]?.id ?? ""),
    name: product?.name ?? "",
    description: product?.description ?? "",
    price: product?.price ?? "",
    stock_quantity: String(product?.stock_quantity ?? 0),
    is_active: product?.is_active ?? true,
  });
  const [problems, setProblems] = useState<Record<string, string>>({});
  const set = (key: keyof typeof form) => (event: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: event.target.value }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found: Record<string, string> = {};
    const price = form.price.trim();
    if (!form.name.trim()) found.name = "Give the product a name.";
    if (!form.category_id) found.category_id = "Pick a category.";
    if (!/^\d{1,10}(\.\d{1,2})?$/.test(price) || Number(price) <= 0) found.price = "Enter a price above 0, with at most 2 decimals.";
    if (!/^\d{1,9}$/.test(form.stock_quantity.trim())) found.stock_quantity = "Enter a whole number, 0 or more.";
    setProblems(found);
    if (Object.keys(found).length > 0) return;

    const next: ProductCreateInput = {
      category_id: Number(form.category_id),
      name: form.name.trim(),
      description: form.description,
      price,
      stock_quantity: Number(form.stock_quantity),
      is_active: form.is_active,
    };

    let input: ProductCreateInput | ProductUpdateInput = next;
    if (product) {
      // PATCH only what changed.
      const changed: ProductUpdateInput = {};
      if (next.category_id !== product.category_id) changed.category_id = next.category_id;
      if (next.name !== product.name) changed.name = next.name;
      if (next.description !== product.description) changed.description = next.description;
      if (Number(next.price) !== Number(product.price)) changed.price = next.price;
      if (next.stock_quantity !== product.stock_quantity) changed.stock_quantity = next.stock_quantity;
      if (next.is_active !== product.is_active) changed.is_active = next.is_active;
      if (Object.keys(changed).length === 0) return onClose();
      input = changed;
    }

    try {
      await save.mutateAsync({ id: product?.id, input });
      toast.success(product ? `Saved ${next.name}` : `Added ${next.name}`);
      onClose();
    } catch {
      // shown below via save.error
    }
  }

  const problem = (name: string) => problems[name] ?? fieldError(save.error, name);

  return (
    <Modal
      open
      onClose={onClose}
      title={product ? "Edit product" : "New product"}
      description={product ? "Orders already placed keep the old name and price." : undefined}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={save.isPending}>
            Cancel
          </Button>
          <Button type="submit" form="product-form" loading={save.isPending}>
            {product ? "Save changes" : "Add product"}
          </Button>
        </>
      }
    >
      <form id="product-form" onSubmit={submit} className="grid gap-4 sm:grid-cols-2" noValidate>
        {formError(save.error, FORM_FIELDS) && (
          <p role="alert" className="rounded-xl bg-danger-soft px-3.5 py-2.5 text-sm font-medium text-danger-ink sm:col-span-2">
            {formError(save.error, FORM_FIELDS)}
          </p>
        )}
        <TextField label="Name" required maxLength={150} value={form.name} onChange={set("name")} error={problem("name")} fieldClassName="sm:col-span-2" />
        <SelectField label="Category" required value={form.category_id} onChange={set("category_id")} error={problem("category_id")}>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </SelectField>
        <TextField label="Price" required inputMode="decimal" placeholder="0.00" value={form.price} onChange={set("price")} error={problem("price")} />
        <TextField
          label="Stock"
          required
          inputMode="numeric"
          value={form.stock_quantity}
          onChange={set("stock_quantity")}
          error={problem("stock_quantity")}
          hint={product ? "Set the new level: this is a stock correction." : undefined}
        />
        <label className="flex min-h-11 cursor-pointer items-center gap-2.5 self-end text-sm font-semibold">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            className="size-[18px] accent-[var(--accent)]"
          />
          On sale (visible to customers)
        </label>
        <TextAreaField label="Description" value={form.description} onChange={set("description")} error={problem("description")} fieldClassName="sm:col-span-2" />
      </form>
    </Modal>
  );
}

/** A real on/off switch: role="switch", keyboard operable, state not conveyed by color alone. */
function ActiveSwitch({ product }: { product: Product }) {
  const save = useSaveProduct();
  const toast = useToast();
  const on = product.is_active;
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={`${product.name} is ${on ? "on sale" : "hidden"}`}
      disabled={save.isPending}
      onClick={() =>
        save.mutate(
          { id: product.id, input: { is_active: !on } },
          {
            onSuccess: () => toast.success(on ? `${product.name} hidden from the shop` : `${product.name} is on sale`),
            onError: (e) => toast.error(errorMessage(e)),
          },
        )
      }
      className="relative grid h-11 w-14 place-items-center disabled:opacity-60"
    >
      <span className={cn("h-6 w-11 rounded-full transition-colors duration-150", on ? "bg-accent" : "bg-line")} />
      <span
        className={cn(
          "absolute left-[calc(50%-1.25rem)] top-1/2 size-5 -translate-y-1/2 rounded-full bg-white shadow transition-transform duration-150",
          on && "translate-x-5",
        )}
      />
    </button>
  );
}

export function AdminProductsPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const categoryId = Number(params.get("category")) || undefined;
  const rawFilter = params.get("filter");
  const filter: Filter = FILTERS.some((f) => f.value === rawFilter) ? (rawFilter as Filter) : "all";

  const catalog = useAllAdminProducts();
  const categories = useCategories();
  const [editing, setEditing] = useState<Product | "new" | null>(null);

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

  const categoryName = useMemo(() => new Map((categories.data ?? []).map((c) => [c.id, c.name])), [categories.data]);

  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return catalog.products.filter(
      (p) =>
        MATCH[filter](p) &&
        (!categoryId || p.category_id === categoryId) &&
        (!needle || p.name.toLowerCase().includes(needle)),
    );
  }, [catalog.products, q, filter, categoryId]);

  const noCategories = categories.isSuccess && categories.data.length === 0;

  return (
    <>
      <PageHeader
        title="Products"
        description="Add products, correct stock, and take things off sale. Products are never deleted, so past orders stay accurate."
        actions={
          <Button icon={<Plus className="size-4" aria-hidden />} onClick={() => setEditing("new")} disabled={!categories.data?.length}>
            New product
          </Button>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-[18px] -translate-y-1/2 text-muted" aria-hidden />
          <input
            type="search"
            value={q}
            onChange={(e) => update({ q: e.target.value || null })}
            placeholder="Search by name"
            aria-label="Search products by name"
            className={cn(controlClass(), "pl-10")}
          />
        </div>
        <select
          value={categoryId ?? ""}
          onChange={(e) => update({ category: e.target.value || null })}
          aria-label="Filter by category"
          className={cn(controlClass(), "sm:w-56")}
        >
          <option value="">All categories</option>
          {(categories.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="mb-5 flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Filter by stock">
        {FILTERS.map((f) => (
          <Chip key={f.value} active={filter === f.value} onClick={() => update({ filter: f.value === "all" ? null : f.value })}>
            {f.label}
          </Chip>
        ))}
      </div>

      {noCategories ? (
        <EmptyState
          title="Create a category first"
          description="Every product belongs to a category."
          action={
            <Link to="/admin/categories" className={buttonClass("primary")}>
              Go to categories
            </Link>
          }
        />
      ) : catalog.isLoading ? (
        <div className="flex flex-col gap-3" aria-busy>
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-20 rounded-[var(--radius-card)]" />
          ))}
        </div>
      ) : catalog.error ? (
        <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} />
      ) : visible.length === 0 ? (
        <EmptyState
          icon={<PackageSearch className="size-6" aria-hidden />}
          title="No products match"
          description="Try a different search or filter."
          action={
            <Button variant="secondary" onClick={() => setParams({}, { replace: true })}>
              Clear filters
            </Button>
          }
        />
      ) : (
        <>
          <p aria-live="polite" className="mb-3 text-sm text-muted tnum">
            {visible.length} {visible.length === 1 ? "product" : "products"}
          </p>
          <ul className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card">
            {visible.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line px-4 py-3 last:border-b-0">
                <div className="hidden w-16 shrink-0 overflow-hidden rounded-lg min-[420px]:block">
                  <ProductArt name={p.name} categoryId={p.category_id} productId={p.id} muted={!p.is_active} />
                </div>
                <div className="min-w-0 flex-1 basis-48">
                  <p className="truncate font-semibold">{p.name}</p>
                  <p className="text-sm text-muted">{categoryName.get(p.category_id)}</p>
                </div>
                <div className="flex w-28 flex-col items-end gap-0.5 text-right">
                  <span className="font-bold tnum">{formatMoney(p.price)}</span>
                  <span className="text-sm text-muted tnum">{p.stock_quantity} in stock</span>
                </div>
                <div className="hidden w-28 md:block">
                  <StockBadge product={p} />
                  {p.available && p.stock_quantity > LOW_STOCK && <Badge tone="accent">On sale</Badge>}
                </div>
                <div className="ml-auto flex items-center">
                  <ActiveSwitch product={p} />
                  <IconButton label={`Edit ${p.name}`} onClick={() => setEditing(p)}>
                    <Pencil className="size-[18px]" aria-hidden />
                  </IconButton>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      {editing && categories.data && (
        <ProductForm
          key={editing === "new" ? "new" : editing.id}
          product={editing === "new" ? null : editing}
          categories={categories.data}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
