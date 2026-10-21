"""Placing, viewing and deciding orders (FR-04 .. FR-07).

Every method that changes data runs inside ONE UnitOfWork, so it is all or
nothing: if any step fails (not enough stock, inactive product, ...) nothing
is saved, including the stock changes made by earlier steps.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from dal import (
    NewOrderItem,
    Order,
    OrderStatus,
    RuleViolationError,
    UnitOfWork,
)

from . import validation
from .actor import Actor, require_admin, require_login
from .errors import (
    AuthenticationError,
    ConflictError,
    InvalidStateError,
    NotFoundError,
    OutOfStockError,
    PermissionDeniedError,
    ProductUnavailableError,
    ValidationError,
)

_INSUFFICIENT_PRIVILEGE = "42501"  # the database refused: not an administrator


@dataclass(frozen=True)
class OrderLine:
    """What a customer asks for: a product and how many. The price is NOT part
    of the request; it is always read from the product (BR-04)."""

    product_id: int
    quantity: int


class OrderService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork] = UnitOfWork) -> None:
        self._uow_factory = uow_factory

    # ------------------------------------------------------------------- place

    def place_order(self, actor: Actor | None, lines: Sequence[OrderLine]) -> Order:
        """Create a Pending order for the logged-in user and take the stock out.

        Steps (FR-04), all in one transaction:
          1. validate the lines; the same product listed twice is merged
          2. lock the products, so price and stock cannot change meanwhile
          3. every product must exist, be active and have enough stock
          4. decrease the stock, then save the order with the current prices

        Raises ValidationError, ProductUnavailableError, OutOfStockError.
        """
        actor = require_login(actor)
        wanted = _merge_lines(lines)

        try:
            with self._uow_factory() as uow:
                products = {p.id: p for p in uow.products.get_many_for_update(list(wanted))}

                items: list[NewOrderItem] = []
                total = Decimal("0")
                for product_id, quantity in wanted.items():  # ascending ids: no deadlocks
                    product = products.get(product_id)
                    if product is None or not product.is_active:
                        raise ProductUnavailableError(f"product {product_id} is not available")
                    if product.stock_quantity < quantity:
                        raise OutOfStockError(
                            f"not enough stock for '{product.name}': "
                            f"{product.stock_quantity} left, {quantity} requested"
                        )
                    # price and name come from the database row, never from the customer
                    items.append(NewOrderItem(product_id, product.name, product.price, quantity))
                    total += product.price * quantity

                if total > validation.MAX_ORDER_TOTAL:
                    raise ValidationError("the order total is too large", "lines")

                for item in items:
                    if not uow.products.decrease_stock(item.product_id, item.quantity):
                        raise OutOfStockError(f"not enough stock for '{item.product_name}'")
                return uow.orders.create(actor.user_id, items)
        except RuleViolationError as exc:
            if exc.constraint == "fk_orders_user":
                raise AuthenticationError("your account no longer exists") from None
            raise ConflictError(f"the order was refused: {exc.message}") from None

    # -------------------------------------------------------------------- read

    def get_order(self, actor: Actor | None, order_id) -> Order:
        """One order with its items. Customers can only open their own orders;
        someone else's order looks exactly like a missing one (BR-10).
        Administrators can open any order.
        """
        actor = require_login(actor)
        order_id = validation.identifier(order_id, "order_id")
        with self._uow_factory() as uow:
            if actor.is_admin:
                order = uow.orders.get_by_id(order_id)
            else:
                order = uow.orders.get_for_user(order_id, actor.user_id)
        if order is None:
            raise NotFoundError(f"order {order_id} not found")
        return order

    def list_my_orders(self, actor: Actor | None, limit=None, offset=0) -> list[Order]:
        """The logged-in user's own orders, newest first."""
        actor = require_login(actor)
        limit, offset = validation.page(limit, offset, default_limit=50)
        with self._uow_factory() as uow:
            return uow.orders.list_for_user(actor.user_id, limit, offset)

    def list_orders(
        self, actor: Actor | None, status: OrderStatus | None = None, limit=None, offset=0
    ) -> list[Order]:
        """Every customer's orders, newest first, optionally by status. Administrators only (FR-07)."""
        require_admin(actor)
        if status is not None and not isinstance(status, OrderStatus):
            raise ValidationError("status must be pending, confirmed or cancelled", "status")
        limit, offset = validation.page(limit, offset, default_limit=50)
        with self._uow_factory() as uow:
            return uow.orders.list_all(status, limit, offset)

    # ------------------------------------------------------------------ decide

    def confirm_order(self, actor: Actor | None, order_id) -> Order:
        """Administrators only. A Pending order becomes Confirmed."""
        return self._decide(actor, order_id, OrderStatus.CONFIRMED)

    def cancel_order(self, actor: Actor | None, order_id) -> Order:
        """Administrators only. A Pending order becomes Cancelled and its
        stock is put back, exactly once (BR-11)."""
        return self._decide(actor, order_id, OrderStatus.CANCELLED)

    def _decide(self, actor: Actor | None, order_id, new_status: OrderStatus) -> Order:
        admin = require_admin(actor)
        order_id = validation.identifier(order_id, "order_id")

        try:
            with self._uow_factory() as uow:
                # One statement checks "still Pending" and changes the status, so when two
                # admins act at the same time only one gets an order back.
                order = uow.orders.decide(order_id, new_status, admin.user_id)
                if order is None:
                    existing = uow.orders.get_by_id(order_id)
                    if existing is None:
                        raise NotFoundError(f"order {order_id} not found")
                    raise InvalidStateError(
                        f"order {order_id} is already {existing.status.value}; "
                        "only pending orders can be decided"
                    )

                if new_status == OrderStatus.CANCELLED:
                    # ascending product ids, like place_order: concurrent cancels cannot deadlock
                    for item in sorted(order.items, key=lambda i: i.product_id):
                        if not uow.products.increase_stock(item.product_id, item.quantity):
                            raise ConflictError(f"cannot restore stock: product {item.product_id} is missing")
                return order
        except RuleViolationError as exc:
            if exc.sqlstate == _INSUFFICIENT_PRIVILEGE:
                # the token said "admin" but the database says otherwise (role was removed)
                raise PermissionDeniedError("administrator access is required") from None
            raise ConflictError(f"the change was refused: {exc.message}") from None


def _merge_lines(lines) -> dict[int, int]:
    """Validate the requested lines and merge repeated products: {product_id: quantity}.

    Returned in ascending product id order.
    """
    if isinstance(lines, (str, bytes)) or not isinstance(lines, Sequence) or not lines:
        raise ValidationError("an order needs at least one item", "lines")

    merged: dict[int, int] = {}
    for line in lines:
        if not isinstance(line, OrderLine):
            raise ValidationError("each line must be an OrderLine(product_id, quantity)", "lines")
        product_id = validation.identifier(line.product_id, "product_id")
        quantity = validation.integer(line.quantity, "quantity", minimum=1)
        merged[product_id] = merged.get(product_id, 0) + quantity
        if merged[product_id] > validation.MAX_INT:
            raise ValidationError("quantity is too large", "quantity")
    return dict(sorted(merged.items()))
