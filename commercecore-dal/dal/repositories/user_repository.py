from ..entities import User, UserRole
from .base import BaseRepository

_COLUMNS = "id, full_name, email, password_hash, role, created_at, updated_at"


class UserRepository(BaseRepository):
    """Accounts (FR-01)."""

    def add(self, full_name: str, email: str, password_hash: str) -> User:
        """Create a user. The role is always Customer: nobody registers as admin.

        `password_hash` must already be hashed (bcrypt / argon2), never plain text.
        Raises DuplicateError if the email exists (case-insensitive).
        """
        row = self._execute(
            f"""
            INSERT INTO users (full_name, email, password_hash)
            VALUES (:full_name, :email, :password_hash)
            RETURNING {_COLUMNS}
            """,
            {"full_name": full_name, "email": email, "password_hash": password_hash},
        ).mappings().one()
        return User.from_row(row)

    def get_by_id(self, user_id: int) -> User | None:
        row = self._execute(
            f"SELECT {_COLUMNS} FROM users WHERE id = :id", {"id": user_id}
        ).mappings().first()
        return User.from_row(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        """Case-insensitive lookup (used by login)."""
        row = self._execute(
            f"SELECT {_COLUMNS} FROM users WHERE lower(email) = lower(:email)",
            {"email": email},
        ).mappings().first()
        return User.from_row(row) if row else None

    def set_role(self, user_id: int, role: UserRole) -> User | None:
        """Promote / demote a user. Meant for manual admin setup, not for sign-up."""
        row = self._execute(
            f"UPDATE users SET role = :role WHERE id = :id RETURNING {_COLUMNS}",
            {"id": user_id, "role": role.value},
        ).mappings().first()
        return User.from_row(row) if row else None
