from collections import defaultdict
from dataclasses import replace
from decimal import Decimal
from typing import Sequence

from ..entities import NewOrderItem, Order, OrderItem, OrderStatus
from .base import BaseRepository

_ORDER_COLUMNS = (
    "id, user_id, status, total_amount, decided_by, decided_at, created_at, updated_at"
)
_ITEM_COLUMNS = (
    "id, order_id, product_id, product_name, unit_price, quantity, line_total, created_at"
)


class OrderRepository(BaseRepository):
    """Orders and their items (FR-04 .. FR-07).

    Orders are history: they are created and their status is decided once, but
    never edited or deleted. The database enforces this with triggers.
    Every method returns orders together with their items.
    """

    # ------------------------------------------------------------------ create

    def create(self, user_id: int, items: Sequence[NewOrderItem]) -> Order:
        """Insert an order (status Pending) and its items. Returns the saved order.

        The total is worked out here as the sum of unit_price x quantity.
        This does NOT touch stock; the caller decreases it in the same
        UnitOfWork. If anything fails, the whole UnitOfWork rolls back.

        The database refuses (RuleViolationError) an inactive product, a price
        or name that differs from the current product, or a repeated product.
        """
        if not items:
            raise ValueError("an order needs at least one item (BR-07)")

        total = sum((i.unit_price * i.quantity for i in items), Decimal("0"))
        order_row = self._execute(
            f"""
            INSERT INTO orders (user_id, total_amount)
            VALUES (:user_id, :total_amount)
            RETURNING {_ORDER_COLUMNS}
            """,
            {"user_id": user_id, "total_amount": total},
        ).mappings().one()

        self._execute(
            """
            INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity)
            VALUES (:order_id, :product_id, :product_name, :unit_price, :quantity)
            """,
            [
                {
                    "order_id": order_row["id"],
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "unit_price": i.unit_price,
                    "quantity": i.quantity,
                }
                for i in items
            ],
        )
        return self._with_items([Order.from_row(order_row)])[0]

    # -------------------------------------------------------------------- read

    def get_by_id(self, order_id: int) -> Order | None:
        """Any order, by id. For administrators."""
        row = self._execute(
            f"SELECT {_ORDER_COLUMNS} FROM orders WHERE id = :id", {"id": order_id}
        ).mappings().first()
        return self._with_items([Order.from_row(row)])[0] if row else None

    def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        """An order, but ONLY if it belongs to `user_id` (BR-10).

        Someone else's order and a missing order both return None, so nothing
        about another customer's order is revealed.
        """
        row = self._execute(
            f"SELECT {_ORDER_COLUMNS} FROM orders WHERE id = :id AND user_id = :user_id",
            {"id": order_id, "user_id": user_id},
        ).mappings().first()
        return self._with_items([Order.from_row(row)])[0] if row else None

    def list_for_user(self, user_id: int, limit: int = 50, offset: int = 0) -> list[Order]:
        """A customer's own orders, newest first."""
        rows = self._execute(
            f"""
            SELECT {_ORDER_COLUMNS} FROM orders
            WHERE user_id = :user_id
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """,
            {"user_id": user_id, "limit": limit, "offset": offset},
        ).mappings().all()
        return self._with_items([Order.from_row(r) for r in rows])

    def list_all(
        self, status: OrderStatus | None = None, limit: int = 50, offset: int = 0
    ) -> list[Order]:
        """Every customer's orders, newest first, optionally filtered by status. For administrators."""
        where = "WHERE status = :status" if status else ""
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status.value
        rows = self._execute(
            f"""
            SELECT {_ORDER_COLUMNS} FROM orders {where}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """,
            params,
        ).mappings().all()
        return self._with_items([Order.from_row(r) for r in rows])

    # ------------------------------------------------------------------ decide

    def decide(self, order_id: int, new_status: OrderStatus, admin_id: int) -> Order | None:
        """Confirm or cancel an order, but only while it is Pending (FR-06).

        Returns the updated order, or None if the order does not exist OR is no
        longer Pending. Because the status check and the change happen in one
        statement, only ONE caller can ever win: put the stock back only when
        this returns an order, and it happens exactly once (BR-11).

        The database also checks that `admin_id` really is an administrator.
        """
        if new_status == OrderStatus.PENDING:
            raise ValueError("an order can only be decided as confirmed or cancelled")

        row = self._execute(
            f"""
            UPDATE orders SET status = :status, decided_by = :admin_id
            WHERE id = :id AND status = 'pending'
            RETURNING {_ORDER_COLUMNS}
            """,
            {"id": order_id, "status": new_status.value, "admin_id": admin_id},
        ).mappings().first()
        return self._with_items([Order.from_row(row)])[0] if row else None

    # ----------------------------------------------------------------- helpers

    def _with_items(self, orders: list[Order]) -> list[Order]:
        """Load the items of all given orders with ONE query."""
        if not orders:
            return []
        rows = self._execute(
            f"""
            SELECT {_ITEM_COLUMNS} FROM order_items
            WHERE order_id = ANY(:order_ids)
            ORDER BY id
            """,
            {"order_ids": [o.id for o in orders]},
        ).mappings().all()

        items_by_order: dict[int, list[OrderItem]] = defaultdict(list)
        for row in rows:
            items_by_order[row["order_id"]].append(OrderItem.from_row(row))
        return [replace(o, items=tuple(items_by_order[o.id])) for o in orders]
