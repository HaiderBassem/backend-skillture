"""Orders (FR-04 .. FR-07): the BRD scenarios A-E and the rules around them."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from dal import OrderStatus, UserRole
from services import (
    Actor,
    AuthenticationError,
    ConflictError,
    InvalidStateError,
    NotFoundError,
    OrderLine,
    OutOfStockError,
    PermissionDeniedError,
    ProductUnavailableError,
    ValidationError,
)


@pytest.fixture
def stock_of(catalog, admin):
    return lambda product: catalog.get_product(admin, product.id).stock_quantity


# ------------------------------------------------- Scenario A: successful order


def test_a_successful_order(orders, customer, make_product, stock_of):
    a = make_product("Product A", "10.00", stock=10)
    b = make_product("Product B", "15.00", stock=10)

    order = orders.place_order(customer, [OrderLine(a.id, 2), OrderLine(b.id, 1)])

    assert order.status == OrderStatus.PENDING
    assert order.user_id == customer.user_id
    assert order.total_amount == Decimal("35.00")  # (2 x 10.00) + (1 x 15.00)
    assert {(i.product_name, i.unit_price, i.quantity) for i in order.items} == {
        ("Product A", Decimal("10.00"), 2),
        ("Product B", Decimal("15.00"), 1),
    }
    assert (stock_of(a), stock_of(b)) == (8, 9)


def test_the_same_product_listed_twice_is_merged(orders, customer, make_product, stock_of):
    product = make_product("Product A", "10.00", stock=10)
    order = orders.place_order(customer, [OrderLine(product.id, 2), OrderLine(product.id, 3)])
    assert [(i.product_id, i.quantity) for i in order.items] == [(product.id, 5)]
    assert order.total_amount == Decimal("50.00")
    assert stock_of(product) == 5


def test_the_whole_stock_can_be_bought(orders, customer, make_product, stock_of):
    product = make_product("Product A", "10.00", stock=3)
    orders.place_order(customer, [OrderLine(product.id, 3)])
    assert stock_of(product) == 0
    with pytest.raises(OutOfStockError):
        orders.place_order(customer, [OrderLine(product.id, 1)])


def test_guests_cannot_order(orders, make_product):
    product = make_product("Product A", "10.00")
    with pytest.raises(AuthenticationError):
        orders.place_order(None, [OrderLine(product.id, 1)])


# ------------------------------------------- Scenario B: insufficient inventory


def test_b_insufficient_stock_leaves_nothing_behind(orders, admin, customer, make_product, stock_of):
    a = make_product("Product A", "10.00", stock=5)
    scarce = make_product("Scarce", "20.00", stock=4)

    with pytest.raises(OutOfStockError) as error:
        orders.place_order(customer, [OrderLine(a.id, 1), OrderLine(scarce.id, 10)])

    assert "Scarce" in error.value.message and "4 left, 10 requested" in error.value.message
    assert orders.list_orders(admin) == []  # no partial order (BR-06, BR-12)
    assert (stock_of(a), stock_of(scarce)) == (5, 4)  # the first line's stock change did not stick


def test_inactive_and_missing_products_cannot_be_ordered(orders, admin, customer, make_product):  # BR-05
    hidden = make_product("Hidden", "10.00", active=False)
    ok = make_product("Fine", "10.00")

    for bad_id in (hidden.id, 9999):
        with pytest.raises(ProductUnavailableError):
            orders.place_order(customer, [OrderLine(ok.id, 1), OrderLine(bad_id, 1)])
    assert orders.list_orders(admin) == []


@pytest.mark.parametrize(
    "lines",
    [
        [],
        None,
        "not a list",
        [(1, 1)],  # lines must be OrderLine objects
        [OrderLine(1, 0)],  # BR-03
        [OrderLine(1, -2)],
        [OrderLine(1, 1.5)],
        [OrderLine(1, "2")],
        [OrderLine(1, True)],
        [OrderLine(0, 1)],
        [OrderLine("1", 1)],
        [OrderLine(1, 1_500_000_000), OrderLine(1, 1_500_000_000)],  # merged quantity overflows
    ],
)
def test_malformed_lines_are_refused(orders, customer, make_product, stock_of, lines):
    product = make_product("Product A", "10.00")
    with pytest.raises(ValidationError):
        orders.place_order(customer, lines)
    assert stock_of(product) == 10


def test_an_order_total_too_large_for_the_database_is_a_clean_error(orders, customer, make_product, stock_of):
    pricey = make_product("Pricey", "9999999999.99", stock=1000)
    with pytest.raises(ValidationError):
        orders.place_order(customer, [OrderLine(pricey.id, 1000)])
    assert stock_of(pricey) == 1000


def test_an_account_that_no_longer_exists_cannot_order(orders, make_product, stock_of):
    product = make_product("Product A", "10.00")
    ghost = Actor(user_id=424242, role=UserRole.CUSTOMER)
    with pytest.raises(AuthenticationError):
        orders.place_order(ghost, [OrderLine(product.id, 1)])
    assert stock_of(product) == 10


# ----------------------------------------------- Scenario C: price changes later


def test_c_existing_orders_keep_the_old_price(orders, catalog, admin, customer, make_product):
    product = make_product("Product A", "20.00")
    first = orders.place_order(customer, [OrderLine(product.id, 1)])

    catalog.update_product(admin, product.id, price="25.00", name="Renamed")
    second = orders.place_order(customer, [OrderLine(product.id, 1)])

    old = orders.get_order(customer, first.id)
    assert (old.items[0].unit_price, old.items[0].product_name) == (Decimal("20.00"), "Product A")  # BR-08
    assert old.total_amount == Decimal("20.00")
    assert second.items[0].unit_price == Decimal("25.00")
    assert second.items[0].product_name == "Renamed"


# ------------------------------------------------ Scenario D: cancelling an order


def test_d_cancelling_restores_stock_exactly_once(orders, admin, customer, make_product, stock_of):
    a = make_product("Product A", "10.00", stock=10)
    b = make_product("Product B", "10.00", stock=10)
    order = orders.place_order(customer, [OrderLine(a.id, 3), OrderLine(b.id, 4)])
    assert (stock_of(a), stock_of(b)) == (7, 6)

    cancelled = orders.cancel_order(admin, order.id)

    assert cancelled.status == OrderStatus.CANCELLED
    assert cancelled.decided_by == admin.user_id and cancelled.decided_at is not None
    assert (stock_of(a), stock_of(b)) == (10, 10)

    with pytest.raises(InvalidStateError):  # a second cancel must not restore again
        orders.cancel_order(admin, order.id)
    assert (stock_of(a), stock_of(b)) == (10, 10)


def test_a_confirmed_order_cannot_be_cancelled_or_confirmed_again(
    orders, admin, customer, make_product, stock_of
):
    product = make_product("Product A", "10.00")
    order = orders.place_order(customer, [OrderLine(product.id, 2)])

    assert orders.confirm_order(admin, order.id).status == OrderStatus.CONFIRMED
    with pytest.raises(InvalidStateError):
        orders.cancel_order(admin, order.id)
    with pytest.raises(InvalidStateError):
        orders.confirm_order(admin, order.id)
    assert orders.get_order(admin, order.id).status == OrderStatus.CONFIRMED
    assert stock_of(product) == 8  # confirming keeps the stock taken


def test_a_cancelled_order_cannot_be_confirmed(orders, admin, customer, make_product):
    product = make_product("Product A", "10.00")
    order = orders.place_order(customer, [OrderLine(product.id, 1)])
    orders.cancel_order(admin, order.id)
    with pytest.raises(InvalidStateError):
        orders.confirm_order(admin, order.id)


def test_deciding_a_missing_order(orders, admin):
    with pytest.raises(NotFoundError):
        orders.confirm_order(admin, 9999)
    with pytest.raises(ValidationError):
        orders.cancel_order(admin, 0)


def test_only_admins_decide_orders(orders, customer, other_customer, make_product, stock_of):  # BR-09
    product = make_product("Product A", "10.00")
    order = orders.place_order(customer, [OrderLine(product.id, 1)])

    for decide in (orders.confirm_order, orders.cancel_order):
        with pytest.raises(AuthenticationError):
            decide(None, order.id)
        with pytest.raises(PermissionDeniedError):
            decide(customer, order.id)  # not even the owner
        with pytest.raises(PermissionDeniedError):
            decide(other_customer, order.id)

    assert orders.get_order(customer, order.id).status == OrderStatus.PENDING
    assert stock_of(product) == 9


def test_a_stale_admin_claim_is_caught_by_the_database(orders, customer, make_product, stock_of):
    """The caller's token still says "admin", but the user is only a customer in the database."""
    product = make_product("Product A", "10.00")
    order = orders.place_order(customer, [OrderLine(product.id, 1)])
    fake_admin = Actor(customer.user_id, UserRole.ADMIN)

    with pytest.raises(PermissionDeniedError):
        orders.cancel_order(fake_admin, order.id)
    assert orders.get_order(customer, order.id).status == OrderStatus.PENDING
    assert stock_of(product) == 9  # and no stock was restored


# ------------------------------------------- Scenario E: someone else's order


def test_e_customers_see_only_their_own_orders(orders, admin, customer, other_customer, make_product):
    product = make_product("Product A", "10.00", stock=10)
    mine = orders.place_order(customer, [OrderLine(product.id, 1)])
    theirs = orders.place_order(other_customer, [OrderLine(product.id, 2)])

    assert orders.get_order(customer, mine.id).id == mine.id
    with pytest.raises(NotFoundError) as someone_elses:  # BR-10
        orders.get_order(customer, theirs.id)
    with pytest.raises(NotFoundError) as missing:
        orders.get_order(customer, 9999)
    assert someone_elses.value.message.replace(str(theirs.id), "N") == missing.value.message.replace(
        "9999", "N"
    )

    assert [o.id for o in orders.list_my_orders(customer)] == [mine.id]
    assert orders.get_order(admin, theirs.id).id == theirs.id  # administrators see everything (FR-07)


def test_orders_need_login_to_be_read(orders):
    with pytest.raises(AuthenticationError):
        orders.get_order(None, 1)
    with pytest.raises(AuthenticationError):
        orders.list_my_orders(None)


def test_my_orders_are_newest_first_with_paging(orders, customer, make_product):
    product = make_product("Product A", "10.00", stock=10)
    ids = [orders.place_order(customer, [OrderLine(product.id, 1)]).id for _ in range(3)]

    mine = orders.list_my_orders(customer)
    assert [o.id for o in mine] == ids[::-1]
    assert all(len(o.items) == 1 for o in mine)
    assert [o.id for o in orders.list_my_orders(customer, limit=1, offset=1)] == [ids[1]]
    with pytest.raises(ValidationError):
        orders.list_my_orders(customer, limit=0)


def test_only_admins_list_all_orders_and_can_filter_by_status(orders, admin, customer, make_product):
    product = make_product("Product A", "10.00", stock=10)
    first = orders.place_order(customer, [OrderLine(product.id, 1)])
    second = orders.place_order(customer, [OrderLine(product.id, 1)])
    orders.confirm_order(admin, first.id)

    assert {o.id for o in orders.list_orders(admin)} == {first.id, second.id}
    assert [o.id for o in orders.list_orders(admin, OrderStatus.CONFIRMED)] == [first.id]
    assert [o.id for o in orders.list_orders(admin, OrderStatus.PENDING)] == [second.id]

    with pytest.raises(PermissionDeniedError):
        orders.list_orders(customer)
    with pytest.raises(AuthenticationError):
        orders.list_orders(None)
    with pytest.raises(ValidationError):
        orders.list_orders(admin, status="pending")  # must be an OrderStatus


# ----------------------------------------------------------- concurrency


def test_two_buyers_cannot_take_the_last_unit(orders, make_actor, make_product, stock_of):
    product = make_product("Last one", "10.00", stock=1)
    buyers = [make_actor(f"buyer{i}") for i in range(5)]

    def try_to_buy(buyer):
        try:
            orders.place_order(buyer, [OrderLine(product.id, 1)])
            return "bought"
        except OutOfStockError:
            return "sold out"

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(try_to_buy, buyers))

    assert sorted(results) == ["bought"] + ["sold out"] * 4
    assert stock_of(product) == 0  # never negative (BR-02)


def test_two_admins_cancelling_at_once_restore_stock_only_once(
    orders, make_actor, customer, make_product, stock_of
):
    product = make_product("Product A", "10.00", stock=10)
    order = orders.place_order(customer, [OrderLine(product.id, 4)])
    admins = [make_actor(f"admin{i}", admin=True) for i in range(4)]

    def try_to_cancel(admin):
        try:
            orders.cancel_order(admin, order.id)
            return "cancelled"
        except InvalidStateError:
            return "too late"

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(try_to_cancel, admins))

    assert sorted(results) == ["cancelled"] + ["too late"] * 3
    assert stock_of(product) == 10  # 10 - 4 + 4, not 14


def test_confirm_and_cancel_racing_leave_one_consistent_result(
    orders, make_actor, customer, make_product, stock_of
):
    product = make_product("Product A", "10.00", stock=10)
    order = orders.place_order(customer, [OrderLine(product.id, 4)])
    admin_one, admin_two = make_actor("admin1", admin=True), make_actor("admin2", admin=True)

    def run(action):
        try:
            return action().status
        except ConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        confirm = pool.submit(run, lambda: orders.confirm_order(admin_one, order.id))
        cancel = pool.submit(run, lambda: orders.cancel_order(admin_two, order.id))
        outcomes = [confirm.result(), cancel.result()]

    final = orders.get_order(admin_one, order.id).status
    assert sorted(o for o in outcomes if o) == [final]  # exactly one decision won
    assert stock_of(product) == (10 if final == OrderStatus.CANCELLED else 6)
