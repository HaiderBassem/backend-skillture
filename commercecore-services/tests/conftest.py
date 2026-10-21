"""Test setup.

Like the DAL tests, these run against a REAL Postgres database already built by
commercecore-migrations. TEST_DATABASE_URL (in the root .env) must
point at a migrated database whose name contains "test": every table is emptied
before each test that uses the database.
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from dal import UnitOfWork, UserRole
from dal.config import normalize_url  # importing dal.config also loads the root .env
from services import AccountService, Actor, CatalogService, OrderService

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


@pytest.fixture
def new_uow(engine):
    """Empties the database, then returns a factory for transactions: `with new_uow() as uow:`"""
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {ALL_TABLES} RESTART IDENTITY CASCADE"))
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return lambda: UnitOfWork(factory)


@pytest.fixture
def accounts(new_uow):
    return AccountService(new_uow)


@pytest.fixture
def catalog(new_uow):
    return CatalogService(new_uow)


@pytest.fixture
def orders(new_uow):
    return OrderService(new_uow)


@pytest.fixture
def make_actor(accounts, new_uow):
    """make_actor("alice") -> Actor (a customer);  make_actor("ada", admin=True) -> admin Actor"""

    def _make(name, admin=False):
        account = accounts.register(f"{name} Tester", f"{name}@example.com", "correct-horse-battery")
        if admin:
            with new_uow() as uow:
                uow.users.set_role(account.id, UserRole.ADMIN)
            return Actor(account.id, UserRole.ADMIN)
        return account.as_actor()

    return _make


@pytest.fixture
def customer(make_actor):
    return make_actor("alice")


@pytest.fixture
def other_customer(make_actor):
    return make_actor("bob")


@pytest.fixture
def admin(make_actor):
    return make_actor("ada", admin=True)


@pytest.fixture
def category(catalog, admin):
    return catalog.create_category(admin, "Books", "Paper and e-books")


@pytest.fixture
def make_product(catalog, admin, category):
    """make_product("Product A", "10.00", stock=10) -> Product"""

    def _make(name, price, stock=10, active=True):
        return catalog.create_product(admin, category.id, name, price, stock_quantity=stock, is_active=active)

    return _make
