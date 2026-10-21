"""Test setup.

The tests run against a REAL Postgres database that was already built by
commercecore-migrations (the SQL files are the source of truth for the schema).
Point TEST_DATABASE_URL (in the root .env) at an empty, migrated database whose name
contains "test": every table is emptied before each test.
"""

import os
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from dal import UnitOfWork, UserRole
from dal.config import normalize_url  # importing dal.config also loads the root .env

ALL_TABLES = "order_items, orders, products, categories, users"


@pytest.fixture(scope="session")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set (see the root .env.example)")
    engine = create_engine(normalize_url(url))
    if "test" not in (engine.url.database or ""):
        pytest.exit(f"Refusing to run: '{engine.url.database}' does not look like a test database.")
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def empty_database(engine):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {ALL_TABLES} RESTART IDENTITY CASCADE"))


@pytest.fixture
def new_uow(engine):
    """Call it to start a transaction on the test database: `with new_uow() as uow:`"""
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return lambda: UnitOfWork(factory)


@pytest.fixture
def customer(new_uow):
    with new_uow() as uow:
        return uow.users.add("Alice Customer", "alice@example.com", "hash-1")


@pytest.fixture
def other_customer(new_uow):
    with new_uow() as uow:
        return uow.users.add("Bob Customer", "bob@example.com", "hash-2")


@pytest.fixture
def admin(new_uow):
    with new_uow() as uow:
        user = uow.users.add("Ada Admin", "ada@example.com", "hash-3")
        return uow.users.set_role(user.id, UserRole.ADMIN)


@pytest.fixture
def category(new_uow):
    with new_uow() as uow:
        return uow.categories.add("Books", "Paper and e-books")


@pytest.fixture
def make_product(new_uow, category):
    """Factory: make_product("Product A", "10.00", stock=10) -> Product"""

    def _make(name, price, stock=10, active=True):
        with new_uow() as uow:
            return uow.products.add(category.id, name, Decimal(price), stock_quantity=stock, is_active=active)

    return _make
