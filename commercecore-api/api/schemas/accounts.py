"""Registration, login and the logged-in user (FR-01)."""

from datetime import datetime

from pydantic import BaseModel, Field

from dal import UserRole

from .common import Id, RequestModel, ResponseModel


class RegisterRequest(RequestModel):
    """There is deliberately no `role` field: everyone who registers is a Customer."""

    full_name: str = Field(min_length=1, max_length=100, examples=["Ali Hassan"])
    email: str = Field(min_length=3, max_length=255, examples=["ali@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["a-long-password"])
    international_id: Id | None = Field(default=None, examples=[29001011234567])  # optional


class LoginRequest(RequestModel):
    email: str = Field(max_length=255, examples=["ali@example.com"])
    password: str = Field(max_length=128, examples=["a-long-password"])


class AccountResponse(ResponseModel):
    id: int
    full_name: str
    email: str
    international_id: int = Field(description="0 when it was not given at registration")
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    """Send `access_token` back as   Authorization: Bearer <access_token>"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="seconds until the token expires")
    account: AccountResponse
