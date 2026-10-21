"""Registration and login (FR-01)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from dal import DuplicateError, UnitOfWork, User, UserRole

from . import validation
from .actor import Actor, require_login
from .errors import AuthenticationError, ConflictError, NotFoundError
from .passwords import DUMMY_HASH, hash_password, verify_password


@dataclass(frozen=True)
class Account:
    """A user as the outside world may see it: never contains the password hash."""

    id: int
    full_name: str
    email: str
    international_id: int  # 0 = not given
    role: UserRole
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> Account:
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            international_id=user.international_id,
            role=user.role,
            created_at=user.created_at,
        )

    def as_actor(self) -> Actor:
        return Actor(self.id, self.role)


class AccountService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork] = UnitOfWork) -> None:
        self._uow_factory = uow_factory

    def register(self, full_name, email, password, international_id=None) -> Account:
        """Create a Customer account. Nobody can register as an administrator.

        `international_id` is optional (None = not given, stored as 0); when
        given it must be a positive whole number.
        Raises ValidationError for bad input, ConflictError if the e-mail is taken.
        """
        full_name = validation.text(full_name, "full_name", 100)
        email = validation.email(email)
        password = validation.password(password)
        if international_id is None:
            international_id = 0
        else:
            international_id = validation.identifier(international_id, "international_id")
        password_hash = hash_password(password)  # slow on purpose: done before opening a transaction

        try:
            with self._uow_factory() as uow:
                user = uow.users.add(full_name, email, password_hash, international_id)
        except DuplicateError:
            raise ConflictError("this email is already registered") from None
        return Account.from_user(user)

    def login(self, email, password) -> Account:
        """Check the credentials. The same error is raised for an unknown e-mail
        and a wrong password, so nobody can discover which e-mails are registered.
        """
        failure = AuthenticationError("invalid email or password")
        if not isinstance(email, str) or not isinstance(password, str) or "\x00" in email:
            raise failure

        with self._uow_factory() as uow:
            user = uow.users.get_by_email(email.strip())

        # Always run one hash check, even for an unknown e-mail (same timing).
        password_ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
        if user is None or not password_ok:
            raise failure
        return Account.from_user(user)

    def actor_for(self, user_id: int) -> Actor:
        """Who is behind an already verified token, with the role as it is NOW in the
        database (a removed admin role takes effect immediately).

        Raises AuthenticationError if the account no longer exists.
        """
        with self._uow_factory() as uow:
            user = uow.users.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("your account no longer exists")
        return Actor.from_user(user)

    def get_account(self, actor: Actor | None) -> Account:
        """The logged-in user's own account."""
        actor = require_login(actor)
        with self._uow_factory() as uow:
            user = uow.users.get_by_id(actor.user_id)
        if user is None:
            raise NotFoundError("account not found")
        return Account.from_user(user)
