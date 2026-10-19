"""CommerceCore data access layer.

    from dal import UnitOfWork

    with UnitOfWork() as uow:
        products = uow.products.list_products(category_id=1)
"""

from .entities import (
    Category,
    NewOrderItem,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    User,
    UserRole,
)
from .exceptions import (
    CategoryInUseError,
    DALError,
    DuplicateError,
    RuleViolationError,
)
from .unit_of_work import UnitOfWork

__all__ = [
    "Category",
    "CategoryInUseError",
    "DALError",
    "DuplicateError",
    "NewOrderItem",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Product",
    "RuleViolationError",
    "UnitOfWork",
    "User",
    "UserRole",
]
