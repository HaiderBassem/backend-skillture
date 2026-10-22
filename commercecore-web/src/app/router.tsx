import { Loader2 } from "lucide-react";
import type { ComponentType } from "react";
import { createBrowserRouter } from "react-router-dom";
import { GuestOnly, RequireAdmin, RequireAuth } from "@/features/auth/guards";
import { NotFoundPage, RouteErrorBoundary } from "@/pages/RouteError";
import { AdminLayout } from "./AdminLayout";
import { Layout } from "./Layout";

// Every page is its own chunk, so the shop never downloads admin code.
function page<T extends Record<string, unknown>>(load: () => Promise<T>, name: keyof T) {
  return async () => ({ Component: (await load())[name] as ComponentType });
}

function Loading() {
  return (
    <div className="grid min-h-dvh place-items-center text-muted" role="status" aria-label="Loading">
      <Loader2 className="size-6 animate-spin" aria-hidden />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    HydrateFallback: Loading,
    ErrorBoundary: RouteErrorBoundary,
    children: [
      { index: true, lazy: page(() => import("@/pages/ShopPage"), "ShopPage") },
      { path: "products/:id", lazy: page(() => import("@/pages/ProductPage"), "ProductPage") },
      { path: "cart", lazy: page(() => import("@/pages/CartPage"), "CartPage") },
      {
        Component: GuestOnly,
        children: [
          { path: "login", lazy: page(() => import("@/pages/LoginPage"), "LoginPage") },
          { path: "register", lazy: page(() => import("@/pages/RegisterPage"), "RegisterPage") },
        ],
      },
      {
        Component: RequireAuth,
        children: [
          { path: "orders", lazy: page(() => import("@/pages/OrdersPage"), "OrdersPage") },
          { path: "orders/:id", lazy: page(() => import("@/pages/OrderPage"), "OrderPage") },
        ],
      },
      {
        path: "admin",
        Component: RequireAdmin,
        children: [
          {
            Component: AdminLayout,
            children: [
              { index: true, lazy: page(() => import("@/pages/admin/DashboardPage"), "DashboardPage") },
              { path: "orders", lazy: page(() => import("@/pages/admin/AdminOrdersPage"), "AdminOrdersPage") },
              { path: "orders/:id", lazy: page(() => import("@/pages/admin/AdminOrderPage"), "AdminOrderPage") },
              { path: "products", lazy: page(() => import("@/pages/admin/AdminProductsPage"), "AdminProductsPage") },
              { path: "categories", lazy: page(() => import("@/pages/admin/AdminCategoriesPage"), "AdminCategoriesPage") },
            ],
          },
        ],
      },
      { path: "*", Component: NotFoundPage },
    ],
  },
]);
