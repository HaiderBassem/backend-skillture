"""Errors raised by the data access layer.

The database already enforces the business rules (CHECK constraints, unique
indexes, foreign keys and triggers). When it refuses something, SQLAlchemy raises
a low-level driver error; here we turn it into a small, readable exception.
"""

from contextlib import contextmanager

from sqlalchemy.exc import DBAPIError

# Postgres error codes (SQLSTATE) we translate
UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"  # e.g. a product points to a category that does not exist
RESTRICT_VIOLATION = "23001"  # ON DELETE RESTRICT, and the "order history is immutable" triggers
_RULE_VIOLATIONS = {
    "23502",  # not_null_violation
    FOREIGN_KEY_VIOLATION,
    RESTRICT_VIOLATION,
    "23514",  # check_violation  (price > 0, stock >= 0, quantity > 0, triggers ...)
    "42501",  # insufficient_privilege (raised by the trigger: only admins decide orders)
}


class DALError(Exception):
    """Base class for every error raised by this layer."""

    def __init__(self, message: str, sqlstate: str | None = None, constraint: str | None = None):
        super().__init__(message)
        self.message = message
        self.sqlstate = sqlstate
        self.constraint = constraint


class DuplicateError(DALError):
    """A unique rule was broken (e.g. the email or category name already exists)."""


class RuleViolationError(DALError):
    """The database refused the change because it breaks a business rule."""


class CategoryInUseError(RuleViolationError):
    """A category that still contains products cannot be deleted (FR-02)."""


def _translate(exc: DBAPIError) -> DALError | None:
    orig = exc.orig
    sqlstate = getattr(orig, "sqlstate", None)
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    message = getattr(diag, "message_primary", None) or str(orig)

    if sqlstate == UNIQUE_VIOLATION:
        return DuplicateError(message, sqlstate, constraint)
    if sqlstate in _RULE_VIOLATIONS:
        return RuleViolationError(message, sqlstate, constraint)
    return None


@contextmanager
def translate_errors():
    """Inside this block, known database errors become DALError subclasses.

    Anything we do not recognise (connection lost, syntax error, ...) is left
    untouched so real problems are never hidden.
    """
    try:
        yield
    except DBAPIError as exc:
        translated = _translate(exc)
        if translated is None:
            raise
        raise translated from exc
