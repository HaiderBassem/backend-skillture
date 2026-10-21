"""Schemas (also called DTOs, data transfer objects): the exact JSON shape of
every request and response. Pydantic checks requests BEFORE any business code
runs; the service layer then applies the business rules.

    *Request   what the client sends    (unknown fields are refused)
    *Response  what the API returns     (only the fields listed are ever sent)
"""

from .accounts import AccountResponse, LoginRequest, RegisterRequest, TokenResponse
from .catalog import (
    CategoryRequest,
    CategoryResponse,
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
)
from .common import ErrorResponse, error_responses
from .orders import (
    AdminOrderResponse,
    OrderItemRequest,
    OrderItemResponse,
    OrderResponse,
    PlaceOrderRequest,
)

__all__ = [
    "AccountResponse",
    "AdminOrderResponse",
    "CategoryRequest",
    "CategoryResponse",
    "ErrorResponse",
    "LoginRequest",
    "OrderItemRequest",
    "OrderItemResponse",
    "OrderResponse",
    "PlaceOrderRequest",
    "ProductCreateRequest",
    "ProductResponse",
    "ProductUpdateRequest",
    "RegisterRequest",
    "TokenResponse",
    "error_responses",
]
