"""Test setup.

The API tests send real HTTP requests (FastAPI's TestClient) through every
layer down to a REAL Postgres database, like the DAL and service tests:
TEST_DATABASE_URL (in ../commercecore-dal/.env) must point at a migrated
database whose name contains "test". Every table is emptied before each test.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from api.config import Settings
from api.main import create_app
from dal import UnitOfWork, UserRole
from dal.config import normalize_url  # importing dal.config also loads the DAL's .env

ALL_TABLES = "order_items, orders, products, categories, users"
PASSWORD = "correct-horse-battery"
TEST_SETTINGS = Settings(jwt_secret="test-only-secret-" + "x" * 32, token_minutes=5)


@pytest.fixture(scope="session")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set (see commercecore-dal/.env.example)")
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
def client(new_uow):
    with TestClient(create_app(TEST_SETTINGS, new_uow)) as client:
        yield client


@pytest.fixture
def register(client):
    """register("alice") -> the Authorization header of a new, logged-in customer"""

    def _register(name):
        email = f"{name}@example.com"
        body = {"full_name": f"{name.title()} Tester", "email": email, "password": PASSWORD}
        assert client.post("/auth/register", json=body).status_code == 201
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return _register


@pytest.fixture
def set_role(new_uow):
    def _set_role(email, role):
        with new_uow() as uow:
            uow.users.set_role(uow.users.get_by_email(email).id, role)

    return _set_role


@pytest.fixture
def customer(register):
    return register("alice")


@pytest.fixture
def other_customer(register):
    return register("bob")


@pytest.fixture
def admin(register, set_role):
    headers = register("ada")
    set_role("ada@example.com", UserRole.ADMIN)  # the same token now acts as an admin:
    return headers  # the role is read from the database on every request


@pytest.fixture
def category(client, admin):
    response = client.post("/admin/categories", json={"name": "Books"}, headers=admin)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def make_product(client, admin, category):
    """make_product("Product A", "10.00", stock=10) -> the product as JSON"""

    def _make(name, price, stock=10, active=True):
        body = {
            "category_id": category["id"],
            "name": name,
            "price": price,
            "stock_quantity": stock,
            "is_active": active,
        }
        response = client.post("/admin/products", json=body, headers=admin)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def stock_of(client, admin):
    """stock_of(product_id) -> the current stock, as an admin sees it"""

    def _stock_of(product_id):
        return client.get(f"/admin/products/{product_id}", headers=admin).json()["stock_quantity"]

    return _stock_of
