"""Orders (FR-04 .. FR-07) and the five example scenarios (A-E) from the BRD.

`place_order` and `cancel_order` below are tiny stand-ins for the future service
layer. They show how the repositories are meant to be combined inside one
UnitOfWork, which is what makes an order "all or nothing".
"""

from decimal import Decimal

import pytest

from dal import NewOrderItem, OrderStatus, RuleViolationError


class OutOfStock(Exception):
    pass


def place_order(uow, user_id, wanted):
    """wanted = {product_id: quantity}"""
    locked = {p.id: p for p in uow.products.get_many_for_update(list(wanted))}
    items = []
    for product_id, quantity in wanted.items():
        product = locked.get(product_id)
        if product is None or not product.is_active:
            raise OutOfStock(f"product {product_id} is not available")
        if not uow.products.decrease_stock(product_id, quantity):
            raise OutOfStock(f"not enough stock for product {product_id}")
        # price and name come from the database row, never from the customer (BR-04)
        items.append(NewOrderItem(product_id, product.name, product.price, quantity))
    return uow.orders.create(user_id, items)


def cancel_order(uow, order_id, admin_id):
    order = uow.orders.decide(order_id, OrderStatus.CANCELLED, admin_id)
    if order is None:
        return None  # missing, or no longer pending: restore nothing
    for item in order.items:
        uow.products.increase_stock(item.product_id, item.quantity)
    return order


def stock(new_uow, product):
    with new_uow() as uow:
        return uow.products.get_by_id(product.id).stock_quantity


# ------------------------------------------------- Scenario A: successful order


def test_a_successful_order(new_uow, customer, make_product):
    a = make_product("Product A", "10.00", stock=10)
    b = make_product("Product B", "15.00", stock=10)

    with new_uow() as uow:
        order = place_order(uow, customer.id, {a.id: 2, b.id: 1})

    assert order.status == OrderStatus.PENDING
    assert order.total_amount == Decimal("35.00")  # (2 x 10.00) + (1 x 15.00)
    assert {(i.product_name, i.unit_price, i.quantity) for i in order.items} == {
        ("Product A", Decimal("10.00"), 2),
        ("Product B", Decimal("15.00"), 1),
    }
    assert stock(new_uow, a) == 8
    assert stock(new_uow, b) == 9


# ------------------------------------------- Scenario B: insufficient inventory


def test_b_insufficient_stock_leaves_nothing_behind(new_uow, customer, make_product):
    a = make_product("Product A", "10.00", stock=5)
    scarce = make_product("Scarce", "20.00", stock=4)

    with pytest.raises(OutOfStock):
        with new_uow() as uow:
            place_order(uow, customer.id, {a.id: 1, scarce.id: 10})  # 2nd line fails

    with new_uow() as uow:
        assert uow.orders.list_all() == []  # no partial order (BR-06, BR-12)
    assert stock(new_uow, a) == 5  # first line's stock change was rolled back too
    assert stock(new_uow, scarce) == 4


def test_inactive_product_cannot_be_ordered(new_uow, customer, make_product):  # BR-05
    hidden = make_product("Hidden", "10.00", active=False)
    with pytest.raises(RuleViolationError):  # refused by the database itself
        with new_uow() as uow:
            uow.orders.create(customer.id, [NewOrderItem(hidden.id, "Hidden", Decimal("10.00"), 1)])


def test_customer_cannot_choose_the_price(new_uow, customer, make_product):  # BR-04
    product = make_product("Product A", "10.00")
    with pytest.raises(RuleViolationError):
        with new_uow() as uow:
            uow.orders.create(customer.id, [NewOrderItem(product.id, "Product A", Decimal("0.01"), 1)])


def test_order_needs_at_least_one_item(new_uow, customer):  # BR-07
    with pytest.raises(ValueError):
        with new_uow() as uow:
            uow.orders.create(customer.id, [])


# ------------------------------------------------ Scenario C: price changes later


def test_c_existing_orders_keep_the_old_price(new_uow, customer, admin, make_product):
    product = make_product("Product A", "20.00")
    with new_uow() as uow:
        first = place_order(uow, customer.id, {product.id: 1})

    with new_uow() as uow:
        uow.products.set_price(product.id, Decimal("25.00"))
        uow.products.update_details(product.id, product.category_id, "Renamed", "")
        second = place_order(uow, customer.id, {product.id: 1})

    with new_uow() as uow:
        old = uow.orders.get_by_id(first.id)
        assert old.items[0].unit_price == Decimal("20.00")  # BR-08
        assert old.items[0].product_name == "Product A"  # name snapshot too
        assert old.total_amount == Decimal("20.00")
        assert uow.orders.get_by_id(second.id).items[0].unit_price == Decimal("25.00")


# ------------------------------------------------- Scenario D: cancelling an order


def test_d_cancelling_restores_stock_exactly_once(new_uow, customer, admin, make_product):
    product = make_product("Product A", "10.00", stock=10)
    with new_uow() as uow:
        order = place_order(uow, customer.id, {product.id: 3})
    assert stock(new_uow, product) == 7

    with new_uow() as uow:
        cancelled = cancel_order(uow, order.id, admin.id)
    assert cancelled.status == OrderStatus.CANCELLED
    assert cancelled.decided_by == admin.id and cancelled.decided_at is not None
    assert stock(new_uow, product) == 10

    with new_uow() as uow:  # cancelling again must not restore a second time
        assert cancel_order(uow, order.id, admin.id) is None
    assert stock(new_uow, product) == 10


def test_confirmed_orders_cannot_be_cancelled(new_uow, customer, admin, make_product):
    product = make_product("Product A", "10.00")
    with new_uow() as uow:
        order = place_order(uow, customer.id, {product.id: 1})
        assert uow.orders.decide(order.id, OrderStatus.CONFIRMED, admin.id).status == OrderStatus.CONFIRMED

    with new_uow() as uow:
        assert cancel_order(uow, order.id, admin.id) is None
        assert uow.orders.get_by_id(order.id).status == OrderStatus.CONFIRMED


def test_only_an_admin_can_decide_an_order(new_uow, customer, make_product):  # BR-09
    product = make_product("Product A", "10.00")
    with new_uow() as uow:
        order = place_order(uow, customer.id, {product.id: 1})

    with pytest.raises(RuleViolationError):
        with new_uow() as uow:
            uow.orders.decide(order.id, OrderStatus.CONFIRMED, customer.id)  # a customer, not an admin

    with new_uow() as uow:
        assert uow.orders.get_by_id(order.id).status == OrderStatus.PENDING


def test_deciding_a_missing_order_returns_none(new_uow, admin):
    with new_uow() as uow:
        assert uow.orders.decide(9999, OrderStatus.CONFIRMED, admin.id) is None


# ------------------------------------------- Scenario E: someone else's order


def test_e_customers_see_only_their_own_orders(new_uow, customer, other_customer, admin, make_product):
    product = make_product("Product A", "10.00", stock=10)
    with new_uow() as uow:
        mine = place_order(uow, customer.id, {product.id: 1})
        theirs = place_order(uow, other_customer.id, {product.id: 2})

    with new_uow() as uow:
        assert uow.orders.get_for_user(mine.id, customer.id).id == mine.id
        # someone else's order looks exactly like a missing one (BR-10)
        assert uow.orders.get_for_user(theirs.id, customer.id) is None
        assert uow.orders.get_for_user(9999, customer.id) is None

        assert [o.id for o in uow.orders.list_for_user(customer.id)] == [mine.id]
        # administrators can review everything (FR-07)
        assert {o.id for o in uow.orders.list_all()} == {mine.id, theirs.id}


def test_orders_are_listed_newest_first_with_their_items(new_uow, customer, make_product):
    product = make_product("Product A", "10.00", stock=10)
    ids = []
    for _ in range(3):
        with new_uow() as uow:  # separate transactions -> separate timestamps
            ids.append(place_order(uow, customer.id, {product.id: 1}).id)

    with new_uow() as uow:
        orders = uow.orders.list_for_user(customer.id)
        assert [o.id for o in orders] == ids[::-1]
        assert all(len(o.items) == 1 for o in orders)


def test_two_buyers_cannot_take_the_last_unit(new_uow, customer, make_product):
    """Several customers race for the last unit: exactly one order may succeed."""
    from concurrent.futures import ThreadPoolExecutor

    product = make_product("Last one", "10.00", stock=1)

    def try_to_buy(_):
        try:
            with new_uow() as uow:
                place_order(uow, customer.id, {product.id: 1})
            return True
        except OutOfStock:
            return False

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(try_to_buy, range(5)))

    assert results.count(True) == 1
    assert stock(new_uow, product) == 0  # never negative (BR-02)
    with new_uow() as uow:
        assert len(uow.orders.list_all()) == 1


def test_admin_can_filter_orders_by_status(new_uow, customer, admin, make_product):
    product = make_product("Product A", "10.00", stock=10)
    with new_uow() as uow:
        first = place_order(uow, customer.id, {product.id: 1})
        place_order(uow, customer.id, {product.id: 1})
        uow.orders.decide(first.id, OrderStatus.CONFIRMED, admin.id)

    with new_uow() as uow:
        assert [o.id for o in uow.orders.list_all(OrderStatus.CONFIRMED)] == [first.id]
        assert len(uow.orders.list_all(OrderStatus.PENDING)) == 1
