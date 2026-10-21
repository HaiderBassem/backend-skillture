"""CommerceCore service layer (business logic).

    from services import AccountService, CatalogService, OrderService, OrderLine

    accounts, catalog, orders = AccountService(), CatalogService(), OrderService()

    account = accounts.login("ali@example.com", "secret-password")
    order = orders.place_order(account.as_actor(), [OrderLine(product_id=1, quantity=2)])

The layer above (the API) authenticates the caller, builds an `Actor` from it
(`None` for a guest), calls a service method and turns `ServiceError`
subclasses into HTTP responses.
"""

from .account_service import Account, AccountService
from .actor import Actor
from .catalog_service import CatalogService
from .errors import (
    AuthenticationError,
    ConflictError,
    InvalidStateError,
    NotFoundError,
    OutOfStockError,
    PermissionDeniedError,
    ProductUnavailableError,
    ServiceError,
    ValidationError,
)
from .order_service import OrderLine, OrderService

__all__ = [
    "Account",
    "AccountService",
    "Actor",
    "AuthenticationError",
    "CatalogService",
    "ConflictError",
    "InvalidStateError",
    "NotFoundError",
    "OrderLine",
    "OrderService",
    "OutOfStockError",
    "PermissionDeniedError",
    "ProductUnavailableError",
    "ServiceError",
    "ValidationError",
]
