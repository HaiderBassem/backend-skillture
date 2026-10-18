"""Alembic environment for CommerceCore.

The schema lives in plain .sql files under migrations/sql/.
Each revision in migrations/versions/ only runs its up/down file.
There are NO SQLAlchemy models, so autogenerate is intentionally disabled
(target_metadata = None). Write every new migration by hand.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer the environment variable so no password lives in alembic.ini
#   export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/commercecore"
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = None


def run_migrations_offline() -> None:
    """`alembic upgrade head --sql` → prints the SQL instead of running it."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # each revision commits on its own: a failure leaves the DB at the last good revision
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
