// Pure cart logic (no React): easy to test. The API has no cart, so it lives in the browser;
// only {product_id, quantity} is ever sent when ordering, and the server decides the price.

import { sumMoney } from "@/lib/format";
import type { Product } from "@/lib/types";

export interface CartLine {
  productId: number;
  categoryId: number;
  name: string;
  price: string;
  stock: number;
  quantity: number;
}

export type CartSnapshot = Pick<CartLine, "productId" | "categoryId" | "name" | "price" | "stock">;

export type CartAction =
  | { type: "add"; item: CartSnapshot; quantity: number }
  | { type: "set"; productId: number; quantity: number }
  | { type: "remove"; productId: number }
  | { type: "refresh"; products: Product[] }
  | { type: "clear" };

const clamp = (quantity: number, stock: number) => Math.max(1, Math.min(quantity, Math.max(stock, 1)));

export function cartReducer(lines: CartLine[], action: CartAction): CartLine[] {
  switch (action.type) {
    case "add": {
      const { item, quantity } = action;
      if (item.stock < 1) return lines;
      const existing = lines.find((l) => l.productId === item.productId);
      if (!existing) return [...lines, { ...item, quantity: clamp(quantity, item.stock) }];
      return lines.map((l) =>
        l.productId === item.productId ? { ...l, ...item, quantity: clamp(l.quantity + quantity, item.stock) } : l,
      );
    }
    case "set":
      if (action.quantity < 1) return lines.filter((l) => l.productId !== action.productId);
      return lines.map((l) =>
        l.productId === action.productId ? { ...l, quantity: clamp(action.quantity, l.stock) } : l,
      );
    case "remove":
      return lines.filter((l) => l.productId !== action.productId);
    case "refresh":
      // Bring name, price and stock up to date with the server. Quantities only shrink to fit stock.
      return lines.map((l) => {
        const fresh = action.products.find((p) => p.id === l.productId);
        if (!fresh) return l;
        return {
          ...l,
          name: fresh.name,
          price: fresh.price,
          stock: fresh.stock_quantity,
          quantity: fresh.stock_quantity > 0 ? clamp(l.quantity, fresh.stock_quantity) : l.quantity,
        };
      });
    case "clear":
      return [];
  }
}

export const cartCount = (lines: CartLine[]) => lines.reduce((n, l) => n + l.quantity, 0);

export const cartSubtotal = (lines: CartLine[]) => sumMoney(lines);

const KEY = "cc.cart";

export function loadCart(): CartLine[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]") as CartLine[];
    return Array.isArray(parsed) ? parsed.filter((l) => l.productId > 0 && l.quantity > 0) : [];
  } catch {
    return [];
  }
}

export function saveCart(lines: CartLine[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(lines));
  } catch {
    // Storage blocked: the cart simply won't survive a reload.
  }
}
