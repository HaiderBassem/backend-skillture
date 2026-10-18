"""create categories (FR-02)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from migrations.sql_runner import run_sql_file

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("0003_create_categories.up.sql")


def downgrade() -> None:
    run_sql_file("0003_create_categories.down.sql")
