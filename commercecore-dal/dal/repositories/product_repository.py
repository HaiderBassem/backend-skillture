from collections.abc import Sequence
from decimal import Decimal

from ..entities import Product
from .base import BaseRepository

_COLUMNS = "id, category_id, name, description, price, stock_quantity, is_active, created_at, updated_at"


class ProductRepository(BaseRepository):
    """Product catalog and inventory (FR-03).

    The database refuses price <= 0 and negative stock (BR-01, BR-02) by raising
    RuleViolationError.
    """

    def add(
        self,
        category_id: int,
        name: str,
        price: Decimal,
        description: str = "",
        stock_quantity: int = 0,
        is_active: bool = True,
    ) -> Product:
        row = (
            self._execute(
                f"""
            INSERT INTO products (category_id, name, description, price, stock_quantity, is_active)
            VALUES (:category_id, :name, :description, :price, :stock_quantity, :is_active)
            RETURNING {_COLUMNS}
            """,
                {
                    "category_id": category_id,
                    "name": name,
                    "description": description,
                    "price": price,
                    "stock_quantity": stock_quantity,
                    "is_active": is_active,
                },
            )
            .mappings()
            .one()
        )
        return Product.from_row(row)

    def get_by_id(self, product_id: int) -> Product | None:
        row = (
            self._execute(f"SELECT {_COLUMNS} FROM products WHERE id = :id", {"id": product_id})
            .mappings()
            .first()
        )
        return Product.from_row(row) if row else None

    def list_products(
        self,
        category_id: int | None = None,
        only_active: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Product]:
        """Browse products. Customers/guests use only_active=True (the default);
        administrators pass only_active=False to see everything."""
        conditions = []
        params: dict = {"limit": limit, "offset": offset}
        if only_active:
            conditions.append("is_active")
        if category_id is not None:
            conditions.append("category_id = :category_id")
            params["category_id"] = category_id
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = (
            self._execute(
                f"""
            SELECT {_COLUMNS} FROM products {where}
            ORDER BY name, id
            LIMIT :limit OFFSET :offset
            """,
                params,
            )
            .mappings()
            .all()
        )
        return [Product.from_row(r) for r in rows]

    def get_many_for_update(self, product_ids: Sequence[int]) -> list[Product]:
        """Fetch products and LOCK their rows until the transaction ends.

        Use this at the start of placing an order so nobody else can change the
        price or stock while we check it. Rows come back ordered by id, which
        keeps two concurrent orders from deadlocking each other.
        Ids that do not exist are simply missing from the result.
        """
        rows = (
            self._execute(
                f"""
            SELECT {_COLUMNS} FROM products
            WHERE id = ANY(:ids)
            ORDER BY id
            FOR UPDATE
            """,
                {"ids": list(product_ids)},
            )
            .mappings()
            .all()
        )
        return [Product.from_row(r) for r in rows]

    def update_details(
        self, product_id: int, category_id: int, name: str, description: str
    ) -> Product | None:
        return self._update_one(
            product_id,
            "category_id = :category_id, name = :name, description = :description",
            {"category_id": category_id, "name": name, "description": description},
        )

    def set_price(self, product_id: int, price: Decimal) -> Product | None:
        return self._update_one(product_id, "price = :price", {"price": price})

    def set_active(self, product_id: int, is_active: bool) -> Product | None:
        """Activate / deactivate. Products are deactivated, never deleted."""
        return self._update_one(product_id, "is_active = :is_active", {"is_active": is_active})

    def set_stock(self, product_id: int, stock_quantity: int) -> Product | None:
        """Admin inventory adjustment: set the available quantity."""
        return self._update_one(
            product_id, "stock_quantity = :stock_quantity", {"stock_quantity": stock_quantity}
        )

    def decrease_stock(self, product_id: int, quantity: int) -> bool:
        """Take `quantity` units out of stock (an order was placed).

        Done in ONE atomic statement, so two orders can never both take the last
        unit. Returns False (and changes nothing) if there is not enough stock.
        """
        result = self._execute(
            """
            UPDATE products SET stock_quantity = stock_quantity - :quantity
            WHERE id = :id AND stock_quantity >= :quantity
            """,
            {"id": product_id, "quantity": quantity},
        )
        return result.rowcount == 1

    def increase_stock(self, product_id: int, quantity: int) -> bool:
        """Put `quantity` units back (a Pending order was cancelled).

        Returns False if the product does not exist.
        """
        result = self._execute(
            "UPDATE products SET stock_quantity = stock_quantity + :quantity WHERE id = :id",
            {"id": product_id, "quantity": quantity},
        )
        return result.rowcount == 1

    def _update_one(self, product_id: int, set_clause: str, params: dict) -> Product | None:
        row = (
            self._execute(
                f"UPDATE products SET {set_clause} WHERE id = :id RETURNING {_COLUMNS}",
                {"id": product_id, **params},
            )
            .mappings()
            .first()
        )
        return Product.from_row(row) if row else None
