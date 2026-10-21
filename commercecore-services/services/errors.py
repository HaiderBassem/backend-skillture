"""Errors raised by the service layer.

The layer above (the API) only has to catch these. Each one maps naturally to
an HTTP status, shown on the right:

    ValidationError        400/422  the request itself is wrong
    AuthenticationError    401      not logged in / wrong credentials
    PermissionDeniedError  403      logged in, but not allowed
    NotFoundError          404
    ConflictError          409      valid request, but the current state refuses it

Database errors (`dal.DALError`) never leave this layer.
"""


class ServiceError(Exception):
    """Base class for every error raised by this layer."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(ServiceError):
    """The input is malformed or breaks a rule (empty name, price <= 0, ...)."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class AuthenticationError(ServiceError):
    """The caller is not logged in, or the credentials are wrong."""


class PermissionDeniedError(ServiceError):
    """The caller is logged in but their role does not allow this."""


class NotFoundError(ServiceError):
    """The thing asked for does not exist (or is hidden from this caller)."""


class ConflictError(ServiceError):
    """The request is valid, but the current state does not allow it."""


class OutOfStockError(ConflictError):
    """Not enough units of a product (BR-02, BR-06)."""


class ProductUnavailableError(ConflictError):
    """The product does not exist or is inactive, so it cannot be ordered (BR-05)."""


class InvalidStateError(ConflictError):
    """The order was already decided: only Pending orders can change (FR-06)."""
