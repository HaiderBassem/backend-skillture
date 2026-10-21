"""Who is making the request.

The API layer authenticates the caller (token, session, ...) and hands every
service method an `Actor`. A guest (not logged in) is simply `None`.
"""

from __future__ import annotations

from dataclasses import dataclass

from dal import User, UserRole

from .errors import AuthenticationError, PermissionDeniedError


@dataclass(frozen=True)
class Actor:
    user_id: int
    role: UserRole

    @classmethod
    def from_user(cls, user: User) -> Actor:
        return cls(user.id, user.role)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


def require_login(actor: Actor | None) -> Actor:
    if actor is None:
        raise AuthenticationError("you must be logged in")
    return actor


def require_admin(actor: Actor | None) -> Actor:
    actor = require_login(actor)
    if not actor.is_admin:
        raise PermissionDeniedError("administrator access is required")
    return actor
