"""The demo data (api/seed.py) loads cleanly and shows every situation."""

import pytest

from api.seed import ADMIN_EMAIL, PASSWORD, seed


def login(client, email):
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_seed_covers_every_situation(client, new_uow):
    seed(new_uow)
    admin = login(client, ADMIN_EMAIL)

    orders = client.get("/admin/orders", headers=admin).json()
    assert sorted(o["status"] for o in orders) == ["cancelled", "confirmed", "confirmed"] + ["pending"] * 3

    products = {
        p["name"]: p for p in client.get("/admin/products", params={"limit": 100}, headers=admin).json()
    }
    assert products["Coffee Mug"]["stock_quantity"] == 40  # cancelled order gave the mugs back
    assert products["Noise-Cancelling Headphones"]["available"] is False  # out of stock
    assert products["Python 2 Cookbook"]["is_active"] is False
    assert products["The Pragmatic Programmer"]["price"] == "39.00"

    lina = login(client, "lina@example.com")
    lina_orders = client.get("/orders", headers=lina).json()
    bought = {i["product_name"]: i["unit_price"] for o in lina_orders for i in o["items"]}
    assert bought["The Pragmatic Programmer"] == "35.00"  # price at purchase, not today's
    assert "Python 2 Cookbook" in bought  # still in history after being deactivated
    assert client.get("/auth/me", headers=lina).json()["international_id"] == 0  # not given
    assert client.get("/auth/me", headers=login(client, "sara@example.com")).json()["international_id"] > 0

    toys = next(c for c in client.get("/categories").json() if c["name"] == "Toys")
    assert client.delete(f"/admin/categories/{toys['id']}", headers=admin).status_code == 204


def test_seed_refuses_a_database_that_has_data(new_uow):
    seed(new_uow)
    with pytest.raises(RuntimeError):
        seed(new_uow)
