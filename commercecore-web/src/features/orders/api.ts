import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { request } from "@/lib/api";
import type { AdminOrder, Order, OrderLineInput, OrderStatus } from "@/lib/types";

const LIST_LIMIT = 100; // the API's maximum per request

// ------------------------------------------------------------------- customer

export function useMyOrders() {
  return useQuery({
    queryKey: ["orders"],
    queryFn: ({ signal }) => request<Order[]>("/orders", { query: { limit: LIST_LIMIT }, signal }),
  });
}

export function useMyOrder(id: number) {
  return useQuery({
    queryKey: ["orders", id],
    queryFn: ({ signal }) => request<Order>(`/orders/${id}`, { signal }),
    enabled: Number.isInteger(id) && id > 0,
  });
}

/** Place an order. Sends only product ids and quantities: the server owns the prices. */
export function usePlaceOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (items: OrderLineInput[]) => request<Order>("/orders", { method: "POST", body: { items } }),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: ["orders"] }),
        // Stock changed, so every cached product list is now out of date.
        queryClient.invalidateQueries({ queryKey: ["products"] }),
        queryClient.invalidateQueries({ queryKey: ["product"] }),
        queryClient.invalidateQueries({ queryKey: ["admin"] }),
      ]),
  });
}

// ---------------------------------------------------------------------- admin

export function useAdminOrders(status?: OrderStatus) {
  return useQuery({
    queryKey: ["admin", "orders", { status }],
    queryFn: ({ signal }) =>
      request<AdminOrder[]>("/admin/orders", { query: { status, limit: LIST_LIMIT }, signal }),
  });
}

export function useAdminOrder(id: number) {
  return useQuery({
    queryKey: ["admin", "orders", id],
    queryFn: ({ signal }) => request<AdminOrder>(`/admin/orders/${id}`, { signal }),
    enabled: Number.isInteger(id) && id > 0,
  });
}

/** Confirm or cancel a pending order. Cancelling puts the stock back, so refresh products too. */
export function useDecideOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "confirm" | "cancel" }) =>
      request<AdminOrder>(`/admin/orders/${id}/${action}`, { method: "POST" }),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin"] }),
        queryClient.invalidateQueries({ queryKey: ["orders"] }),
        queryClient.invalidateQueries({ queryKey: ["products"] }),
        queryClient.invalidateQueries({ queryKey: ["product"] }),
      ]),
  });
}
