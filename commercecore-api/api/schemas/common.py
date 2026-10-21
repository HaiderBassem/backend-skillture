"""Building blocks shared by all schemas (DTOs)."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt

MAX_INT = 2_147_483_647  # Postgres INTEGER (stock, quantity)
MAX_ID = 2**63 - 1  # Postgres BIGINT (ids)

# Ids, quantities and stock must be real JSON integers: "2", 2.5 and true are refused.
Id = Annotated[StrictInt, Field(ge=1, le=MAX_ID)]


class RequestModel(BaseModel):
    """Base for everything the client SENDS.

    Unknown fields are refused, not silently ignored: a client that sends a
    `price` in an order line (BR-04) or a `role` when registering (FR-01) gets
    a clear 422 error.
    """

    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    """Base for everything the API RETURNS.

    Built directly from the objects the service layer returns (`from_attributes`),
    and it lists exactly which fields leave the server: anything not declared
    here (a password hash, ...) can never leak.
    """

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """The body of every error response (4xx)."""

    code: str = Field(examples=["out_of_stock"])
    message: str = Field(examples=["not enough stock for 'Pen': 4 left, 10 requested"])
    field: str | None = Field(default=None, examples=[None])


def error_responses(*statuses: int) -> dict:
    """For the OpenAPI docs: which error statuses an endpoint can return."""
    return {status: {"model": ErrorResponse} for status in statuses}
