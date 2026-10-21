"""Categories (FR-02) and products (FR-03)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, StrictBool, StrictInt, computed_field

from .common import MAX_INT, Id, RequestModel, ResponseModel

# Money: greater than zero (BR-01), at most 2 decimals, fits NUMERIC(12,2).
# Send it as a string ("9.99") or a number (9.99); it is always returned as a string.
Price = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2, examples=["10.00"])]
Stock = Annotated[StrictInt, Field(ge=0, le=MAX_INT)]  # never negative (BR-02)


# ------------------------------------------------------------------ categories


class CategoryRequest(RequestModel):
    """Create a category, or replace its name and description (PUT)."""

    name: str = Field(min_length=1, max_length=100, examples=["Books"])
    description: str | None = Field(default=None, max_length=10_000, examples=["Paper and e-books"])


class CategoryResponse(ResponseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------------- products


class ProductCreateRequest(RequestModel):
    category_id: Id
    name: str = Field(min_length=1, max_length=150, examples=["Product A"])
    description: str = Field(default="", max_length=100_000)
    price: Price
    stock_quantity: Stock = 0
    is_active: StrictBool = True


class ProductUpdateRequest(RequestModel):
    """Send only the fields you want to change; the rest stays as it is.

    `stock_quantity` is the new stock level (an inventory correction).
    Set `is_active` to false to take a product off sale; products are never deleted.
    Existing orders keep the old name and price (BR-08).
    """

    category_id: Id | None = None
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=100_000)
    price: Price | None = None
    stock_quantity: Stock | None = None
    is_active: StrictBool | None = None


class ProductResponse(ResponseModel):
    id: int
    category_id: int
    name: str
    description: str
    price: Decimal
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def available(self) -> bool:
        """Can this product be bought right now? (FR-03)"""
        return self.is_active and self.stock_quantity > 0
