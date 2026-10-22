import { Pencil, Plus, Tags, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui/feedback";
import { TextAreaField, TextField } from "@/components/ui/Field";
import { ConfirmDialog, Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";
import { useAllAdminProducts, useCategories, useDeleteCategory, useSaveCategory } from "@/features/catalog/api";
import { fieldError, formError } from "@/lib/api";
import type { Category } from "@/lib/types";

function CategoryForm({ category, onClose }: { category: Category | null; onClose: () => void }) {
  const save = useSaveCategory();
  const toast = useToast();
  const [name, setName] = useState(category?.name ?? "");
  const [description, setDescription] = useState(category?.description ?? "");
  const [nameProblem, setNameProblem] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return setNameProblem("Give the category a name.");
    setNameProblem(null);
    try {
      await save.mutateAsync({
        id: category?.id,
        input: { name: name.trim(), description: description.trim() || null },
      });
      toast.success(category ? `Saved ${name.trim()}` : `Added ${name.trim()}`);
      onClose();
    } catch {
      // shown below via save.error
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={category ? "Edit category" : "New category"}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={save.isPending}>
            Cancel
          </Button>
          <Button type="submit" form="category-form" loading={save.isPending}>
            {category ? "Save changes" : "Add category"}
          </Button>
        </>
      }
    >
      <form id="category-form" onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {formError(save.error, ["name", "description"]) && (
          <p role="alert" className="rounded-xl bg-danger-soft px-3.5 py-2.5 text-sm font-medium text-danger-ink">
            {formError(save.error, ["name", "description"])}
          </p>
        )}
        <TextField
          label="Name"
          required
          maxLength={100}
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={nameProblem ?? fieldError(save.error, "name")}
        />
        <TextAreaField
          label="Description"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          error={fieldError(save.error, "description")}
        />
      </form>
    </Modal>
  );
}

export function AdminCategoriesPage() {
  const categories = useCategories();
  const catalog = useAllAdminProducts();
  const remove = useDeleteCategory();
  const toast = useToast();
  const [editing, setEditing] = useState<Category | "new" | null>(null);
  const [deleting, setDeleting] = useState<Category | null>(null);

  const counts = useMemo(() => {
    const map = new Map<number, number>();
    for (const p of catalog.products) map.set(p.category_id, (map.get(p.category_id) ?? 0) + 1);
    return map;
  }, [catalog.products]);

  return (
    <>
      <PageHeader
        title="Categories"
        description="Group products so customers can find them. A category can only be deleted once it has no products."
        actions={
          <Button icon={<Plus className="size-4" aria-hidden />} onClick={() => setEditing("new")}>
            New category
          </Button>
        }
      />

      {categories.isPending ? (
        <div className="flex flex-col gap-3" aria-busy>
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-20 rounded-[var(--radius-card)]" />
          ))}
        </div>
      ) : categories.isError ? (
        <ErrorState error={categories.error} onRetry={() => void categories.refetch()} />
      ) : categories.data.length === 0 ? (
        <EmptyState
          icon={<Tags className="size-6" aria-hidden />}
          title="No categories yet"
          description="Create your first category, then add products to it."
          action={<Button onClick={() => setEditing("new")}>New category</Button>}
        />
      ) : (
        <ul className="overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-card">
          {categories.data.map((c) => {
            const count = counts.get(c.id) ?? 0;
            const canDelete = !catalog.isLoading && count === 0;
            return (
              <li key={c.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line px-5 py-4 last:border-b-0">
                <div className="min-w-0 flex-1 basis-56">
                  <p className="font-semibold">{c.name}</p>
                  {c.description && <p className="text-sm text-muted">{c.description}</p>}
                </div>
                <Badge tone={count === 0 ? "neutral" : "accent"}>
                  {catalog.isLoading ? "…" : `${count} ${count === 1 ? "product" : "products"}`}
                </Badge>
                <div className="flex">
                  <IconButton label={`Edit ${c.name}`} onClick={() => setEditing(c)}>
                    <Pencil className="size-[18px]" aria-hidden />
                  </IconButton>
                  <IconButton
                    label={canDelete ? `Delete ${c.name}` : `${c.name} can't be deleted while it has products`}
                    disabled={!canDelete}
                    onClick={() => setDeleting(c)}
                  >
                    <Trash2 className="size-[18px]" aria-hidden />
                  </IconButton>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {editing && (
        <CategoryForm
          key={editing === "new" ? "new" : editing.id}
          category={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}

      <ConfirmDialog
        open={deleting !== null}
        title={`Delete ${deleting?.name ?? "category"}?`}
        description="This can't be undone."
        confirmLabel="Delete category"
        onClose={() => setDeleting(null)}
        onConfirm={async () => {
          if (!deleting) return;
          await remove.mutateAsync(deleting.id);
          toast.success(`Deleted ${deleting.name}`);
        }}
      />
    </>
  );
}
