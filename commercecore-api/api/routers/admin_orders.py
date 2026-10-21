"""Reviewing and deciding orders (FR-06, FR-07).

Administrators only (BR-09). Only a pending order can be confirmed or cancelled:

    pending ──confirm──▶ confirmed
       └─────cancel───▶ cancelled   (stock goes back, exactly once)
"""

from fastapi import APIRouter

from dal import OrderStatus

from ..dependencies import AdminActor, Limit, Offset, Orders, require_admin_role
from ..schemas import AdminOrderResponse, error_responses

router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin: orders"],
    dependencies=[require_admin_role],
    responses=error_responses(401, 403),
)


@router.get("", response_model=list[AdminOrderResponse])
def list_all_orders(
    actor: AdminActor,
    orders: Orders,
    status: OrderStatus | None = None,
    limit: Limit = 50,
    offset: Offset = 0,
):
    """Every customer's orders, newest first. Add `?status=pending` to see what needs a decision."""
    return orders.list_orders(actor, status, limit, offset)


@router.get("/{order_id}", response_model=AdminOrderResponse, responses=error_responses(404))
def get_any_order(order_id: int, actor: AdminActor, orders: Orders):
    return orders.get_order(actor, order_id)


@router.post(
    "/{order_id}/confirm",
    response_model=AdminOrderResponse,
    responses=error_responses(404, 409),
)
def confirm_order(order_id: int, actor: AdminActor, orders: Orders):
    """pending → confirmed. A confirmed order can no longer be cancelled."""
    return orders.confirm_order(actor, order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=AdminOrderResponse,
    responses=error_responses(404, 409),
)
def cancel_order(order_id: int, actor: AdminActor, orders: Orders):
    """pending → cancelled, and the stock is put back. Cancelling twice is refused (409)."""
    return orders.cancel_order(actor, order_id)
