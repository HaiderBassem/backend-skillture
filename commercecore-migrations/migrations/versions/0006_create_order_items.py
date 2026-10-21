"""create order_items (FR-04, FR-05)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-18
"""

from collections.abc import Sequence

from migrations.sql_runner import run_sql_file

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    run_sql_file("0006_create_order_items.up.sql")


def downgrade() -> None:
    run_sql_file("0006_create_order_items.down.sql")
