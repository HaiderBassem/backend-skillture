"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

SQL lives in: migrations/sql/${up_revision}_<name>.up.sql / .down.sql
"""
from typing import Sequence, Union

from migrations.sql_runner import run_sql_file

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    run_sql_file("${up_revision}_CHANGE_ME.up.sql")


def downgrade() -> None:
    run_sql_file("${up_revision}_CHANGE_ME.down.sql")
