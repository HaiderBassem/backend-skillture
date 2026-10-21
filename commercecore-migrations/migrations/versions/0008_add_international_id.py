"""add users.international_id

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-19
"""

from collections.abc import Sequence

from migrations.sql_runner import run_sql_file

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    run_sql_file("0008_add_international_id.up.sql")


def downgrade() -> None:
    run_sql_file("0008_add_international_id.down.sql")
