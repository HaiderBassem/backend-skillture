"""Categories (FR-02) and products (FR-03): who may do what, and the rules."""

from decimal import Decimal

import pytest

from services import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

# ------------------------------------------------------------- categories


def test_only_admins_change_categories(catalog, category, customer):
    for action in (
        lambda actor: catalog.create_category(actor, "Games"),
        lambda actor: catalog.update_category(actor, category.id, "Renamed"),
        lambda actor: catalog.delete_category(actor, category.id),
    ):
        with pytest.raises(AuthenticationError):
            action(None)  # guest
        with pytest.raises(PermissionDeniedError):
            action(customer)
    assert [c.name for c in catalog.list_categories()] == ["Books"]  # nothing changed


def test_anyone_can_list_and_read_categories(catalog, category):
    assert [c.id for c in catalog.list_categories()] == [category.id]
    assert catalog.get_category(category.id).name == "Books"
    with pytest.raises(NotFoundError):
        catalog.get_category(9999)


def test_category_names_are_unique_ignoring_case(catalog, admin, category):
    with pytest.raises(ConflictError):
        catalog.create_category(admin, "  BOOKS ")
    other = catalog.create_category(admin, "Games")
    with pytest.raises(ConflictError):
        catalog.update_category(admin, other.id, "books")


def test_category_input_is_validated(catalog, admin):
    for bad_name in ["", "   ", None, "x" * 101]:
        with pytest.raises(ValidationError):
            catalog.create_category(admin, bad_name)


def test_update_category(catalog, admin, category):
    updated = catalog.update_category(admin, category.id, " Magazines ", "  ")
    assert (updated.name, updated.description) == ("Magazines", None)  # blank description -> none
    with pytest.raises(NotFoundError):
        catalog.update_category(admin, 9999, "Whatever")


def test_delete_category_rules(catalog, admin, category, make_product):  # FR-02
    make_product("Novel", "9.99")
    with pytest.raises(ConflictError):
        catalog.delete_category(admin, category.id)  # still has products

    empty = catalog.create_category(admin, "Empty")
    catalog.delete_category(admin, empty.id)
    with pytest.raises(NotFoundError):
        catalog.delete_category(admin, empty.id)  # already gone


# ---------------------------------------------------------------- products


def test_only_admins_create_and_change_products(catalog, category, customer, make_product):
    product = make_product("Novel", "9.99")
    for action in (
        lambda actor: catalog.create_product(actor, category.id, "New", "1.00"),
        lambda actor: catalog.update_product(actor, product.id, price="1.00"),
    ):
        with pytest.raises(AuthenticationError):
            action(None)
        with pytest.raises(PermissionDeniedError):
            action(customer)
    assert catalog.get_product(None, product.id).price == Decimal("9.99")


def test_create_product(catalog, admin, category):
    product = catalog.create_product(
        admin, category.id, "  Novel ", "9.5", description="A story", stock_quantity=3
    )
    assert (product.name, product.price, product.stock_quantity) == ("Novel", Decimal("9.50"), 3)
    assert product.is_active is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"price": 0},
        {"price": "-1"},
        {"price": 9.99},
        {"price": "1.005"},
        {"price": None},  # BR-01
        {"stock_quantity": -1},
        {"stock_quantity": 1.5},
        {"stock_quantity": "3"},  # BR-02
        {"name": ""},
        {"name": "x" * 151},
        {"is_active": "yes"},
        {"description": 5},
    ],
)
def test_bad_product_input_is_refused(catalog, admin, category, overrides):
    fields = {"name": "Novel", "price": "9.99", **overrides}
    with pytest.raises(ValidationError):
        catalog.create_product(admin, category.id, **fields)
    assert catalog.list_products(admin, include_inactive=True) == []


def test_product_needs_an_existing_category(catalog, admin):
    with pytest.raises(NotFoundError):
        catalog.create_product(admin, 9999, "Orphan", "1.00")


def test_update_product_changes_only_the_given_fields(catalog, admin, make_product):
    product = make_product("Novel", "10.00", stock=5)

    updated = catalog.update_product(admin, product.id, price="12.50")
    assert (updated.name, updated.price, updated.stock_quantity) == ("Novel", Decimal("12.50"), 5)

    updated = catalog.update_product(
        admin, product.id, name="Better Novel", stock_quantity=0, is_active=False
    )
    assert (updated.name, updated.price, updated.stock_quantity, updated.is_active) == (
        "Better Novel",
        Decimal("12.50"),
        0,
        False,
    )

    assert catalog.update_product(admin, product.id) == updated  # nothing to change is fine


def test_update_product_can_move_it_to_another_category(catalog, admin, make_product):
    product = make_product("Novel", "10.00")
    games = catalog.create_category(admin, "Games")
    assert catalog.update_product(admin, product.id, category_id=games.id).category_id == games.id
    with pytest.raises(NotFoundError):
        catalog.update_product(admin, product.id, category_id=9999)


def test_update_product_errors(catalog, admin, make_product):
    product = make_product("Novel", "10.00")
    with pytest.raises(NotFoundError):
        catalog.update_product(admin, 9999, price="1.00")
    for bad in ({"price": 0}, {"price": "1.234"}, {"stock_quantity": -1}, {"name": "  "}, {"is_active": 1}):
        with pytest.raises(ValidationError):
            catalog.update_product(admin, product.id, **bad)
    assert catalog.get_product(admin, product.id).price == Decimal("10.00")


# ---------------------------------------------------------------- browsing


def test_guests_and_customers_see_only_active_products(catalog, customer, make_product):
    visible = make_product("Visible", "5.00")
    hidden = make_product("Hidden", "5.00", active=False)

    for actor in (None, customer):
        assert [p.id for p in catalog.list_products(actor)] == [visible.id]
        assert catalog.get_product(actor, visible.id).id == visible.id
        with pytest.raises(NotFoundError):  # an inactive product looks missing
            catalog.get_product(actor, hidden.id)


def test_admins_see_inactive_products_too(catalog, admin, make_product):
    visible = make_product("Visible", "5.00")
    hidden = make_product("Hidden", "5.00", active=False)

    assert {p.id for p in catalog.list_products(admin, include_inactive=True)} == {visible.id, hidden.id}
    assert [p.id for p in catalog.list_products(admin)] == [visible.id]  # default is active only
    assert catalog.get_product(admin, hidden.id).id == hidden.id


def test_only_admins_may_ask_for_inactive_products(catalog, customer):
    with pytest.raises(AuthenticationError):
        catalog.list_products(None, include_inactive=True)
    with pytest.raises(PermissionDeniedError):
        catalog.list_products(customer, include_inactive=True)


def test_products_can_be_filtered_by_category_and_paged(catalog, admin, category, make_product):
    for name in ("A", "B", "C"):
        make_product(name, "1.00")
    games = catalog.create_category(admin, "Games")
    chess = catalog.create_product(admin, games.id, "Chess", "12.00")

    assert [p.id for p in catalog.list_products(category_id=games.id)] == [chess.id]
    assert [p.name for p in catalog.list_products(category_id=category.id, limit=2)] == ["A", "B"]
    assert [p.name for p in catalog.list_products(category_id=category.id, limit=2, offset=2)] == ["C"]
    assert catalog.list_products(category_id=9999) == []


@pytest.mark.parametrize("kwargs", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"category_id": 0}])
def test_bad_paging_input_is_refused(catalog, kwargs):
    with pytest.raises(ValidationError):
        catalog.list_products(**kwargs)


def test_get_product_with_a_bad_id(catalog):
    with pytest.raises(ValidationError):
        catalog.get_product(None, "1")
    with pytest.raises(NotFoundError):
        catalog.get_product(None, 12345)
