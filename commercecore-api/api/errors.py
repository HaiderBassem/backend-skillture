"""Turn errors into HTTP responses.

Every error the API returns has the same JSON shape (schemas.ErrorResponse):

    {"code": "out_of_stock", "message": "not enough stock for 'Pen': 4 left, 10 requested", "field": null}

The service layer raises a ServiceError subclass; the table below picks the
HTTP status and the machine-readable `code`. Subclasses are listed before
their parent (OutOfStockError before ConflictError).
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from services import (
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

from .schemas import ErrorResponse

SERVICE_ERRORS: dict[type[ServiceError], tuple[int, str]] = {
    ValidationError: (422, "validation_error"),
    AuthenticationError: (401, "not_authenticated"),
    PermissionDeniedError: (403, "forbidden"),
    NotFoundError: (404, "not_found"),
    OutOfStockError: (409, "out_of_stock"),
    ProductUnavailableError: (409, "product_unavailable"),
    InvalidStateError: (409, "invalid_state"),
    ConflictError: (409, "conflict"),
}

HTTP_CODES = {
    400: "bad_request",
    401: "not_authenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
}


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, _service_error)
    app.add_exception_handler(RequestValidationError, _request_validation_error)
    app.add_exception_handler(HTTPException, _http_error)


def _error(status: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    body = ErrorResponse(code=code, message=message, field=field).model_dump()
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(body, status_code=status, headers=headers)


async def _service_error(request: Request, exc: ServiceError) -> JSONResponse:
    """A business rule said no (raised by the service layer)."""
    for cls in type(exc).__mro__:
        if cls in SERVICE_ERRORS:
            status, code = SERVICE_ERRORS[cls]
            return _error(status, code, exc.message, getattr(exc, "field", None))
    return _error(400, "bad_request", exc.message)


async def _request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """The request did not match the Pydantic schema (wrong type, missing field,
    unknown field such as a `price` in an order line ...).

    Only the first problem is reported, and the submitted values are never echoed
    back (they could contain a password).
    """
    first = exc.errors()[0]
    location = [str(part) for part in first["loc"]]
    if location and location[0] in ("body", "query", "path"):
        location = location[1:]
    return _error(422, "validation_error", first["msg"], ".".join(location) or None)


async def _http_error(request: Request, exc: HTTPException) -> JSONResponse:
    """Errors raised by FastAPI itself, e.g. an unknown URL (404)."""
    return _error(exc.status_code, HTTP_CODES.get(exc.status_code, "error"), str(exc.detail))
