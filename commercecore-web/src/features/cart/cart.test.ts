import { describe, expect, it } from "vitest";
import type { Product } from "@/lib/types";
import { cartCount, cartReducer, cartSubtotal } from "./cart";
import type { CartLine, CartSnapshot } from "./cart";

const pen: CartSnapshot = { productId: 1, categoryId: 1, name: "Pen", price: "2.50", stock: 5 };
const mug: CartSnapshot = { productId: 2, categoryId: 2, name: "Mug", price: "8.00", stock: 3 };

const line = (snapshot: CartSnapshot, quantity: number): CartLine => ({ ...snapshot, quantity });

describe("cartReducer", () => {
  it("adds a new product", () => {
    expect(cartReducer([], { type: "add", item: pen, quantity: 2 })).toEqual([line(pen, 2)]);
  });

  it("adds to an existing line instead of duplicating it", () => {
    const next = cartReducer([line(pen, 2)], { type: "add", item: pen, quantity: 1 });
    expect(next).toEqual([line(pen, 3)]);
  });

  it("never lets a line exceed the stock", () => {
    const next = cartReducer([line(mug, 2)], { type: "add", item: mug, quantity: 10 });
    expect(next[0]?.quantity).toBe(3);
  });

  it("ignores products with no stock", () => {
    expect(cartReducer([], { type: "add", item: { ...pen, stock: 0 }, quantity: 1 })).toEqual([]);
  });

  it("removes a line when its quantity is set below 1", () => {
    expect(cartReducer([line(pen, 2), line(mug, 1)], { type: "set", productId: 1, quantity: 0 })).toEqual([line(mug, 1)]);
  });

  it("clamps a set quantity to the stock", () => {
    expect(cartReducer([line(pen, 1)], { type: "set", productId: 1, quantity: 99 })[0]?.quantity).toBe(5);
  });

  it("clears everything", () => {
    expect(cartReducer([line(pen, 1)], { type: "clear" })).toEqual([]);
  });

  describe("refresh", () => {
    const server = (over: Partial<Product>): Product => ({
      id: 1,
      category_id: 1,
      name: "Pen",
      description: "",
      price: "2.50",
      stock_quantity: 5,
      is_active: true,
      available: true,
      created_at: "",
      updated_at: "",
      ...over,
    });

    it("takes the new price from the server", () => {
      const next = cartReducer([line(pen, 2)], { type: "refresh", products: [server({ price: "3.00" })] });
      expect(next[0]).toMatchObject({ price: "3.00", quantity: 2 });
    });

    it("shrinks the quantity when stock dropped", () => {
      const next = cartReducer([line(pen, 5)], { type: "refresh", products: [server({ stock_quantity: 2 })] });
      expect(next[0]).toMatchObject({ stock: 2, quantity: 2 });
    });

    it("keeps a sold-out line so the page can warn about it", () => {
      const next = cartReducer([line(pen, 2)], { type: "refresh", products: [server({ stock_quantity: 0, available: false })] });
      expect(next).toHaveLength(1);
      expect(next[0]?.stock).toBe(0);
    });
  });
});

describe("cart totals", () => {
  const lines = [line(pen, 2), line(mug, 1)];
  it("counts units", () => expect(cartCount(lines)).toBe(3));
  it("sums prices", () => expect(cartSubtotal(lines)).toBe("13.00"));
});
