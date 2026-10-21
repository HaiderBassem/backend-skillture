"""add order business-rule triggers

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-18
"""

from collections.abc import Sequence

from migrations.sql_runner import run_sql_file

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    run_sql_file("0007_add_order_rule_triggers.up.sql")


def downgrade() -> None:
    run_sql_file("0007_add_order_rule_triggers.down.sql")
