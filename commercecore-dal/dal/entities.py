"""Plain Python objects returned by the repositories.

They mirror the table columns (see commercecore-migrations/migrations/sql).
They are NOT SQLAlchemy models: they only carry data out of the database.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


def _from_row(cls, row: Mapping, **converted):
    """Build `cls` from a DB row: copy the matching columns, apply `converted`."""
    values = {f.name: row[f.name] for f in fields(cls) if f.name in row}
    values.update(converted)
    return cls(**values)


@dataclass(frozen=True)
class User:
    id: int
    full_name: str
    email: str
    password_hash: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Mapping) -> User:
        return _from_row(cls, row, role=UserRole(row["role"]))


@dataclass(frozen=True)
class Category:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Mapping) -> Category:
        return _from_row(cls, row)


@dataclass(frozen=True)
class Product:
    id: int
    category_id: int
    name: str
    description: str
    price: Decimal
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Mapping) -> Product:
        return _from_row(cls, row)


@dataclass(frozen=True)
class OrderItem:
    id: int
    order_id: int
    product_id: int
    product_name: str  # snapshot at purchase time (BR-08)
    unit_price: Decimal  # snapshot at purchase time (BR-08)
    quantity: int
    line_total: Decimal  # unit_price * quantity, computed by the database
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping) -> OrderItem:
        return _from_row(cls, row)


@dataclass(frozen=True)
class Order:
    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    decided_by: int | None  # admin who confirmed / cancelled
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: tuple[OrderItem, ...] = ()

    @classmethod
    def from_row(cls, row: Mapping) -> Order:
        return _from_row(cls, row, status=OrderStatus(row["status"]))


@dataclass(frozen=True)
class NewOrderItem:
    """One line of an order that is about to be created.

    `unit_price` and `product_name` must be copied from the CURRENT product row
    (never from the customer): the database refuses anything else (BR-04).
    """

    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
