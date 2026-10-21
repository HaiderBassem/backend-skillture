"""Categories (FR-02), products (FR-03) and who may manage them (BR-09)."""

import pytest


def test_guests_browse_active_products_only(client, make_product):
    make_product("Pen", "1.50", stock=3)
    make_product("Old pen", "1.00", active=False)

    response = client.get("/products")  # no token: a guest

    assert response.status_code == 200
    [pen] = response.json()
    assert pen["name"] == "Pen"
    assert pen["price"] == "1.50"  # money is an exact string, never a float
    assert pen["available"] is True


def test_an_inactive_product_looks_missing_to_customers(client, customer, make_product):
    hidden = make_product("Old pen", "1.00", active=False)
    assert client.get(f"/products/{hidden['id']}", headers=customer).status_code == 404


def test_out_of_stock_product_is_shown_as_not_available(client, make_product):
    product = make_product("Pen", "1.50", stock=0)
    assert client.get(f"/products/{product['id']}").json()["available"] is False


def test_browse_one_category(client, admin, make_product):
    other = client.post("/admin/categories", json={"name": "Games"}, headers=admin).json()
    make_product("Book", "5.00")

    assert client.get("/categories").json()[0]["name"] == "Books"
    assert client.get("/products", params={"category_id": other["id"]}).json() == []


def test_paging_limits_are_checked(client):
    assert client.get("/products", params={"limit": 101}).status_code == 422
    assert client.get("/products", params={"offset": -1}).status_code == 422


def test_admins_see_inactive_products(client, admin, make_product):
    make_product("Old pen", "1.00", active=False)

    [product] = client.get("/admin/products", headers=admin).json()
    assert product["is_active"] is False


@pytest.mark.parametrize(
    "method, url",
    [
        ("post", "/admin/categories"),
        ("put", "/admin/categories/1"),
        ("delete", "/admin/categories/1"),
        ("get", "/admin/products"),
        ("post", "/admin/products"),
        ("patch", "/admin/products/1"),
    ],
)
def test_only_admins_manage_the_catalog(client, customer, method, url):
    as_guest = client.request(method, url, json={})
    as_customer = client.request(method, url, json={}, headers=customer)

    assert as_guest.status_code == 401
    assert as_customer.status_code == 403
    assert as_customer.json()["code"] == "forbidden"


def test_admin_manages_categories(client, admin, category):
    renamed = client.put(
        f"/admin/categories/{category['id']}",
        json={"name": "Novels", "description": "Fiction"},
        headers=admin,
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Novels"

    duplicate = client.post("/admin/categories", json={"name": "Novels"}, headers=admin)
    assert duplicate.status_code == 409

    assert client.delete(f"/admin/categories/{category['id']}", headers=admin).status_code == 204
    assert client.get(f"/categories/{category['id']}").status_code == 404


def test_a_category_with_products_cannot_be_deleted(client, admin, category, make_product):
    make_product("Book", "5.00")

    response = client.delete(f"/admin/categories/{category['id']}", headers=admin)

    assert response.status_code == 409
    assert client.get(f"/categories/{category['id']}").status_code == 200


@pytest.mark.parametrize(
    "change, field",
    [
        ({"price": "0"}, "price"),  # BR-01
        ({"price": "-5.00"}, "price"),
        ({"price": "1.999"}, "price"),
        ({"price": "abc"}, "price"),
        ({"stock_quantity": -1}, "stock_quantity"),  # BR-02
        ({"stock_quantity": "5"}, "stock_quantity"),
        ({"name": ""}, "name"),
        ({"is_active": "yes"}, "is_active"),
        ({"surprise": 1}, "surprise"),
    ],
)
def test_invalid_products_are_refused(client, admin, category, change, field):
    body = {"category_id": category["id"], "name": "Pen", "price": "1.50", **change}

    response = client.post("/admin/products", json=body, headers=admin)

    assert response.status_code == 422
    assert response.json()["field"] == field


def test_product_in_unknown_category_is_refused(client, admin):
    body = {"category_id": 999, "name": "Pen", "price": "1.50"}
    assert client.post("/admin/products", json=body, headers=admin).status_code == 404


def test_admin_changes_price_stock_and_availability(client, admin, make_product):
    product = make_product("Pen", "1.50", stock=3)

    response = client.patch(
        f"/admin/products/{product['id']}",
        json={"price": "2.25", "stock_quantity": 40},
        headers=admin,
    )
    assert response.status_code == 200
    assert (response.json()["price"], response.json()["stock_quantity"]) == ("2.25", 40)
    assert response.json()["name"] == "Pen"  # untouched fields stay as they were

    client.patch(f"/admin/products/{product['id']}", json={"is_active": False}, headers=admin)
    assert client.get(f"/products/{product['id']}").status_code == 404


def test_updating_a_missing_product_is_not_found(client, admin):
    response = client.patch("/admin/products/999", json={"price": "2.00"}, headers=admin)
    assert response.status_code == 404
