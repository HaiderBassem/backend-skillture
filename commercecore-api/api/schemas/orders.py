"""Placing and reading orders (FR-04 .. FR-07)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, StrictInt

from dal import OrderStatus

from .common import MAX_INT, Id, RequestModel, ResponseModel

Quantity = Annotated[StrictInt, Field(ge=1, le=MAX_INT)]  # a positive integer (BR-03)
MAX_LINES = 100


class OrderItemRequest(RequestModel):
    """One line of a new order. There is deliberately NO price field: the price
    always comes from the product in the database (BR-04)."""

    product_id: Id
    quantity: Quantity


class PlaceOrderRequest(RequestModel):
    items: list[OrderItemRequest] = Field(
        min_length=1,  # at least one item (BR-07)
        max_length=MAX_LINES,
        examples=[[{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}]],
    )


class OrderItemResponse(ResponseModel):
    """Name and price as they were at the time of purchase (BR-08)."""

    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class OrderResponse(ResponseModel):
    """What a customer sees of their own order."""

    id: int
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    decided_at: datetime | None
    items: list[OrderItemResponse]


class AdminOrderResponse(OrderResponse):
    """What an administrator sees: also who ordered and who decided."""

    user_id: int
    decided_by: int | None
