"""The database connection.

SQLAlchemy is used ONLY to connect, open sessions and manage transactions.
The tables are created by commercecore-migrations (plain SQL), never from here.
"""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


@lru_cache
def get_engine() -> Engine:
    """One engine (connection pool) for the whole process, created on first use."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,  # drop dead connections instead of failing on them
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
