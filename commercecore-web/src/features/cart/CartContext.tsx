import { createContext, use, useCallback, useEffect, useMemo, useReducer } from "react";
import type { ReactNode } from "react";
import type { Product } from "@/lib/types";
import { cartCount, cartReducer, cartSubtotal, loadCart, saveCart } from "./cart";
import type { CartLine } from "./cart";

interface CartValue {
  lines: CartLine[];
  count: number;
  subtotal: string;
  add: (product: Product, quantity?: number) => void;
  setQuantity: (productId: number, quantity: number) => void;
  remove: (productId: number) => void;
  refresh: (products: Product[]) => void;
  clear: () => void;
}

const CartContext = createContext<CartValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, dispatch] = useReducer(cartReducer, undefined, loadCart);

  useEffect(() => saveCart(lines), [lines]);

  const add = useCallback(
    (product: Product, quantity = 1) =>
      dispatch({
        type: "add",
        quantity,
        item: {
          productId: product.id,
          categoryId: product.category_id,
          name: product.name,
          price: product.price,
          stock: product.stock_quantity,
        },
      }),
    [],
  );
  const setQuantity = useCallback((productId: number, quantity: number) => dispatch({ type: "set", productId, quantity }), []);
  const remove = useCallback((productId: number) => dispatch({ type: "remove", productId }), []);
  const refresh = useCallback((products: Product[]) => dispatch({ type: "refresh", products }), []);
  const clear = useCallback(() => dispatch({ type: "clear" }), []);

  const value = useMemo<CartValue>(
    () => ({ lines, count: cartCount(lines), subtotal: cartSubtotal(lines), add, setQuantity, remove, refresh, clear }),
    [lines, add, setQuantity, remove, refresh, clear],
  );

  return <CartContext value={value}>{children}</CartContext>;
}

export function useCart(): CartValue {
  const ctx = use(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>");
  return ctx;
}
