from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from ..exceptions import translate_errors


class BaseRepository:
    """Shared plumbing: every repository runs SQL through `_execute`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _execute(self, sql: str, params: dict | list[dict] | None = None) -> CursorResult:
        """Run one SQL statement with :named parameters.

        Pass a list of dicts to run the same statement once per dict.
        """
        with translate_errors():
            return self.session.execute(text(sql), params or {})
