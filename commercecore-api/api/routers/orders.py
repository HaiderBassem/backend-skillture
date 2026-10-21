"""A customer's own orders (FR-04, FR-05, FR-07). Login required."""

from fastapi import APIRouter

from services import OrderLine

from ..dependencies import CurrentActor, Limit, Offset, Orders
from ..schemas import OrderResponse, PlaceOrderRequest, error_responses

router = APIRouter(prefix="/orders", tags=["Orders"], responses=error_responses(401))


@router.post(
    "",
    status_code=201,
    response_model=OrderResponse,
    responses=error_responses(409, 422),
)
def place_order(body: PlaceOrderRequest, actor: CurrentActor, orders: Orders):
    """Order one or more products.

    - Prices come from the products, never from the request (BR-04).
    - Every product must be active and in stock; stock goes down by the quantities ordered.
    - The new order is **pending** until an administrator decides.
    - All or nothing: if any line is refused, no order is created and no stock changes.
    """
    lines = [OrderLine(item.product_id, item.quantity) for item in body.items]
    return orders.place_order(actor, lines)


@router.get("", response_model=list[OrderResponse])
def list_my_orders(actor: CurrentActor, orders: Orders, limit: Limit = 50, offset: Offset = 0):
    """Your own orders, newest first."""
    return orders.list_my_orders(actor, limit, offset)


@router.get("/{order_id}", response_model=OrderResponse, responses=error_responses(404))
def get_my_order(order_id: int, actor: CurrentActor, orders: Orders):
    """One of your orders with its items. Someone else's order is reported as not found (BR-10)."""
    return orders.get_order(actor, order_id)
