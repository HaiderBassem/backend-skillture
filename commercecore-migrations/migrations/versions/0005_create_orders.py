"""create orders (FR-04 .. FR-07)

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from migrations.sql_runner import run_sql_file

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("0005_create_orders.up.sql")


def downgrade() -> None:
    run_sql_file("0005_create_orders.down.sql")
