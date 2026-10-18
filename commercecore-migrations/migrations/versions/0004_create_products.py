"""create products (FR-03)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from migrations.sql_runner import run_sql_file

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("0004_create_products.up.sql")


def downgrade() -> None:
    run_sql_file("0004_create_products.down.sql")
