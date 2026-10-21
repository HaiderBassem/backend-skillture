"""Input checks shared by the services.

Each function returns the cleaned value or raises ValidationError. They mirror
(and are slightly stricter than) the database limits, so a bad request becomes
a clear message here instead of a raw database error later.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .errors import ValidationError

# Same shape as ck_users_email_format in the database.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_PRICE = Decimal("9999999999.99")  # products.price is NUMERIC(12,2)
MAX_ORDER_TOTAL = Decimal("999999999999.99")  # orders.total_amount is NUMERIC(14,2)
MAX_INT = 2_147_483_647  # Postgres INTEGER (stock_quantity, quantity)
MAX_ID = 2**63 - 1  # Postgres BIGINT
PASSWORD_MIN, PASSWORD_MAX = 8, 128
MAX_PAGE_SIZE = 100


def text(value, field: str, max_length: int, required: bool = True) -> str | None:
    """A trimmed string. With required=False, None or blank becomes None."""
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be text", field)
    value = value.strip()
    if "\x00" in value:
        raise ValidationError(f"{field} contains invalid characters", field)
    if not value:
        if required:
            raise ValidationError(f"{field} is required", field)
        return None
    if len(value) > max_length:
        raise ValidationError(f"{field} must be at most {max_length} characters", field)
    return value


def email(value) -> str:
    """Trimmed, lower-cased e-mail address."""
    value = text(value, "email", 255)
    if not _EMAIL.match(value):
        raise ValidationError("email is not a valid address", "email")
    return value.lower()


def password(value) -> str:
    if not isinstance(value, str):
        raise ValidationError("password must be text", "password")
    if not PASSWORD_MIN <= len(value) <= PASSWORD_MAX:
        raise ValidationError(f"password must be {PASSWORD_MIN}-{PASSWORD_MAX} characters", "password")
    return value


def price(value, field: str = "price") -> Decimal:
    """Money greater than zero with at most 2 decimals. Floats are refused (they are inexact)."""
    if isinstance(value, bool) or not isinstance(value, (int, str, Decimal)):
        raise ValidationError(f"{field} must be a decimal number such as '9.99'", field)
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValidationError(f"{field} must be a decimal number such as '9.99'", field) from None
    if not amount.is_finite():
        raise ValidationError(f"{field} must be a number", field)
    if amount <= 0:
        raise ValidationError(f"{field} must be greater than zero", field)
    if amount > MAX_PRICE:
        raise ValidationError(f"{field} must be at most {MAX_PRICE}", field)
    cents = Decimal("0.01")
    if amount != amount.quantize(cents):
        raise ValidationError(f"{field} can have at most 2 decimal places", field)
    return amount.quantize(cents)


def integer(value, field: str, minimum: int = 0) -> int:
    """A whole number >= minimum that fits the database INTEGER."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field} must be a whole number", field)
    if value < minimum:
        raise ValidationError(f"{field} must be at least {minimum}", field)
    if value > MAX_INT:
        raise ValidationError(f"{field} is too large", field)
    return value


def identifier(value, field: str) -> int:
    """A database id: a positive whole number that fits BIGINT."""
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ID:
        raise ValidationError(f"{field} must be a positive whole number", field)
    return value


def page(limit, offset, default_limit: int) -> tuple[int, int]:
    """Pagination: limit 1..MAX_PAGE_SIZE (None = default), offset >= 0."""
    limit = default_limit if limit is None else integer(limit, "limit", minimum=1)
    if limit > MAX_PAGE_SIZE:
        raise ValidationError(f"limit must be at most {MAX_PAGE_SIZE}", "limit")
    return limit, integer(offset, "offset", minimum=0)
