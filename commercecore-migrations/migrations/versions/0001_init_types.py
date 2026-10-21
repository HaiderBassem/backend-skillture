"""init types: enums + shared trigger functions

Revision ID: 0001
Revises:
Create Date: 2026-10-18
"""

from collections.abc import Sequence

from migrations.sql_runner import run_sql_file

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    run_sql_file("0001_init_types.up.sql")


def downgrade() -> None:
    run_sql_file("0001_init_types.down.sql")
