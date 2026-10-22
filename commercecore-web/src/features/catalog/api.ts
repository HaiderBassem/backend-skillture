import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { request } from "@/lib/api";
import type {
  Category,
  CategoryInput,
  Product,
  ProductCreateInput,
  ProductUpdateInput,
} from "@/lib/types";

export const SHOP_PAGE_SIZE = 48;
export const ADMIN_PAGE_SIZE = 100; // the API's maximum

// ----------------------------------------------------------------------- reading

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: ({ signal }) => request<Category[]>("/categories", { signal }),
    staleTime: 5 * 60_000,
  });
}

function useProductPages(scope: "shop" | "admin", categoryId?: number) {
  const size = scope === "admin" ? ADMIN_PAGE_SIZE : SHOP_PAGE_SIZE;
  return useInfiniteQuery({
    queryKey: scope === "admin" ? ["admin", "products", { categoryId }] : ["products", { categoryId }],
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      request<Product[]>(scope === "admin" ? "/admin/products" : "/products", {
        query: { category_id: categoryId, limit: size, offset: pageParam },
        signal,
      }),
    getNextPageParam: (last, all) => (last.length === size ? all.length * size : undefined),
    select: (data) => ({ ...data, products: data.pages.flat() }),
  });
}

/** Products customers can see, one page at a time. */
export const useProducts = (categoryId?: number) => useProductPages("shop", categoryId);

/** Every product including inactive ones (administrators). */
export const useAdminProducts = (categoryId?: number) => useProductPages("admin", categoryId);

export const fetchProduct = (id: number, signal?: AbortSignal) => request<Product>(`/products/${id}`, { signal });

export function useProduct(id: number) {
  return useQuery({
    queryKey: ["product", id],
    queryFn: ({ signal }) => fetchProduct(id, signal),
    enabled: Number.isInteger(id) && id > 0,
  });
}

/** Every product for the admin overview and category counts: keeps fetching pages until done. */
export function useAllAdminProducts() {
  const query = useAdminProducts();
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = query;
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) void fetchNextPage();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);
  return {
    products: query.data?.products ?? [],
    isLoading: query.isLoading || !!hasNextPage,
    error: query.error,
    refetch: query.refetch,
  };
}

// --------------------------------------------------------------------- admin writes

function useInvalidateCatalog() {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ["categories"] }),
      queryClient.invalidateQueries({ queryKey: ["products"] }),
      queryClient.invalidateQueries({ queryKey: ["product"] }),
      queryClient.invalidateQueries({ queryKey: ["admin", "products"] }),
    ]);
}

/** Create a category, or replace an existing one when `id` is given. */
export function useSaveCategory() {
  const invalidate = useInvalidateCatalog();
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: CategoryInput }) =>
      id
        ? request<Category>(`/admin/categories/${id}`, { method: "PUT", body: input })
        : request<Category>("/admin/categories", { method: "POST", body: input }),
    onSuccess: invalidate,
  });
}

export function useDeleteCategory() {
  const invalidate = useInvalidateCatalog();
  return useMutation({
    mutationFn: (id: number) => request<void>(`/admin/categories/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });
}

/** Create a product, or update only the changed fields when `id` is given. */
export function useSaveProduct() {
  const invalidate = useInvalidateCatalog();
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: ProductCreateInput | ProductUpdateInput }) =>
      id
        ? request<Product>(`/admin/products/${id}`, { method: "PATCH", body: input })
        : request<Product>("/admin/products", { method: "POST", body: input }),
    onSuccess: invalidate,
  });
}
