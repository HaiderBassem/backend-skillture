"""Runs a plain .sql file from migrations/sql/ inside the current Alembic transaction.

The SQL files are the source of truth. The Python revision files only say
WHICH file to run and in WHAT order.
"""

from pathlib import Path

from alembic import op

SQL_DIR = Path(__file__).resolve().parent / "sql"


def run_sql_file(filename: str) -> None:
    path = SQL_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"SQL migration file not found: {path}")
    op.execute(path.read_text(encoding="utf-8"))
