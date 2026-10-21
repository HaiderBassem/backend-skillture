"""Orders over HTTP: the BRD scenarios A-E (section 5), the business rules
BR-03 .. BR-12, and the status changes (FR-06)."""

import pytest

from dal import UserRole


def place(client, headers, *lines):
    """place(client, customer, (product_id, quantity), ...) -> response"""
    items = [{"product_id": product_id, "quantity": quantity} for product_id, quantity in lines]
    return client.post("/orders", json={"items": items}, headers=headers)


# ---------------------------------------------------------------- scenarios A-E


def test_scenario_a_successful_order(client, customer, make_product, stock_of):
    a = make_product("Product A", "10.00", stock=10)
    b = make_product("Product B", "15.00", stock=10)

    response = place(client, customer, (a["id"], 2), (b["id"], 1))

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "pending"
    assert order["total_amount"] == "35.00"  # (2 x 10.00) + (1 x 15.00)
    assert [(i["product_name"], i["unit_price"], i["quantity"]) for i in order["items"]] == [
        ("Product A", "10.00", 2),
        ("Product B", "15.00", 1),
    ]
    assert (stock_of(a["id"]), stock_of(b["id"])) == (8, 9)


def test_scenario_b_insufficient_inventory(client, customer, make_product, stock_of):
    product = make_product("Pen", "1.00", stock=4)

    response = place(client, customer, (product["id"], 10))

    assert response.status_code == 409
    assert response.json()["code"] == "out_of_stock"
    assert client.get("/orders", headers=customer).json() == []  # no partial order
    assert stock_of(product["id"]) == 4  # inventory exactly as it was


def test_scenario_c_price_change_keeps_history(client, admin, customer, make_product):
    product = make_product("Lamp", "20.00")
    old_order = place(client, customer, (product["id"], 1)).json()

    client.patch(
        f"/admin/products/{product['id']}",
        json={"price": "25.00", "name": "Big lamp"},
        headers=admin,
    )

    old_order = client.get(f"/orders/{old_order['id']}", headers=customer).json()
    assert (old_order["items"][0]["unit_price"], old_order["total_amount"]) == ("20.00", "20.00")
    assert old_order["items"][0]["product_name"] == "Lamp"
    new_order = place(client, customer, (product["id"], 1)).json()
    assert new_order["total_amount"] == "25.00"


def test_scenario_d_cancellation_restores_stock_exactly_once(client, admin, customer, make_product, stock_of):
    product = make_product("Mug", "4.00", stock=10)
    order = place(client, customer, (product["id"], 3)).json()
    assert stock_of(product["id"]) == 7

    cancelled = client.post(f"/admin/orders/{order['id']}/cancel", headers=admin)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert stock_of(product["id"]) == 10

    again = client.post(f"/admin/orders/{order['id']}/cancel", headers=admin)
    assert again.status_code == 409
    assert again.json()["code"] == "invalid_state"
    assert stock_of(product["id"]) == 10  # not restored a second time


def test_scenario_e_customers_cannot_open_each_others_orders(client, customer, other_customer, make_product):
    product = make_product("Pen", "1.00")
    bobs_order = place(client, other_customer, (product["id"], 1)).json()

    response = client.get(f"/orders/{bobs_order['id']}", headers=customer)
    missing = client.get("/orders/999999", headers=customer)

    # Exactly the answer for an order that does not exist: nothing about Bob's order leaks.
    assert response.status_code == missing.status_code == 404
    assert response.json()["code"] == missing.json()["code"] == "not_found"
    assert "Pen" not in response.text
    assert client.get("/orders", headers=customer).json() == []


# ------------------------------------------------------------------ the request


def test_the_client_cannot_send_a_price(client, customer, make_product):
    product = make_product("Pen", "10.00")
    body = {"items": [{"product_id": product["id"], "quantity": 1, "unit_price": "0.01"}]}

    response = client.post("/orders", json=body, headers=customer)

    assert response.status_code == 422  # BR-04: refused, not silently ignored
    assert response.json()["field"] == "items.0.unit_price"


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", True, None])
def test_quantity_must_be_a_positive_integer(client, customer, make_product, quantity):
    product = make_product("Pen", "1.00")
    body = {"items": [{"product_id": product["id"], "quantity": quantity}]}

    response = client.post("/orders", json=body, headers=customer)

    assert response.status_code == 422  # BR-03
    assert response.json()["field"] == "items.0.quantity"


@pytest.mark.parametrize("body", [{"items": []}, {}, {"items": "pen"}])
def test_an_order_needs_at_least_one_item(client, customer, body):
    response = client.post("/orders", json=body, headers=customer)
    assert response.status_code == 422  # BR-07


def test_guests_cannot_order(client, make_product):
    product = make_product("Pen", "1.00")
    assert place(client, {}, (product["id"], 1)).status_code == 401


# ------------------------------------------------------------- all or nothing


def test_inactive_product_cannot_be_ordered(client, customer, make_product):
    product = make_product("Old pen", "1.00", active=False)

    response = place(client, customer, (product["id"], 1))

    assert response.status_code == 409  # BR-05
    assert response.json()["code"] == "product_unavailable"


def test_one_bad_line_cancels_the_whole_order(client, customer, make_product, stock_of):
    good = make_product("Pen", "1.00", stock=10)
    scarce = make_product("Rare pen", "9.00", stock=1)

    response = place(client, customer, (good["id"], 2), (scarce["id"], 5))

    assert response.status_code == 409  # BR-06 / BR-12
    assert stock_of(good["id"]) == 10
    assert client.get("/orders", headers=customer).json() == []


def test_unknown_product_cancels_the_whole_order(client, customer, make_product, stock_of):
    good = make_product("Pen", "1.00", stock=10)

    response = place(client, customer, (good["id"], 1), (999, 1))

    assert response.status_code == 409
    assert stock_of(good["id"]) == 10


# ------------------------------------------------------------ deciding orders


def test_customers_cannot_decide_orders(client, customer, make_product):
    product = make_product("Pen", "1.00")
    order = place(client, customer, (product["id"], 1)).json()

    for action in ("confirm", "cancel"):
        response = client.post(f"/admin/orders/{order['id']}/{action}", headers=customer)
        assert response.status_code == 403  # BR-09
    assert client.get(f"/orders/{order['id']}", headers=customer).json()["status"] == "pending"


def test_a_confirmed_order_cannot_be_cancelled(client, admin, customer, make_product, stock_of):
    product = make_product("Pen", "1.00", stock=5)
    order = place(client, customer, (product["id"], 2)).json()

    confirmed = client.post(f"/admin/orders/{order['id']}/confirm", headers=admin)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["decided_at"] is not None

    response = client.post(f"/admin/orders/{order['id']}/cancel", headers=admin)
    assert response.status_code == 409
    assert stock_of(product["id"]) == 3  # nothing given back


def test_deciding_a_missing_order_is_not_found(client, admin):
    assert client.post("/admin/orders/999/confirm", headers=admin).status_code == 404


# -------------------------------------------------------------------- reading


def test_customers_list_only_their_own_orders(client, customer, other_customer, make_product):
    product = make_product("Pen", "1.00")
    mine = place(client, customer, (product["id"], 1)).json()
    place(client, other_customer, (product["id"], 1))

    orders = client.get("/orders", headers=customer).json()

    assert [o["id"] for o in orders] == [mine["id"]]
    assert "user_id" not in orders[0]  # customers get the customer view


def test_admins_review_all_orders_and_filter_by_status(client, admin, customer, other_customer, make_product):
    product = make_product("Pen", "1.00")
    first = place(client, customer, (product["id"], 1)).json()
    second = place(client, other_customer, (product["id"], 1)).json()
    client.post(f"/admin/orders/{first['id']}/confirm", headers=admin)

    all_orders = client.get("/admin/orders", headers=admin).json()
    pending = client.get("/admin/orders", params={"status": "pending"}, headers=admin).json()

    assert {o["id"] for o in all_orders} == {first["id"], second["id"]}
    assert [o["id"] for o in pending] == [second["id"]]
    assert client.get("/admin/orders", params={"status": "lost"}, headers=admin).status_code == 422
    assert client.get(f"/admin/orders/{first['id']}", headers=admin).json()["decided_by"] is not None


def test_customers_cannot_list_all_orders(client, customer):
    assert client.get("/admin/orders", headers=customer).status_code == 403


def test_a_removed_admin_role_takes_effect_immediately(client, admin, set_role, make_product, customer):
    product = make_product("Pen", "1.00")
    order = place(client, customer, (product["id"], 1)).json()

    set_role("ada@example.com", UserRole.CUSTOMER)  # same token as before

    assert client.post(f"/admin/orders/{order['id']}/confirm", headers=admin).status_code == 403
