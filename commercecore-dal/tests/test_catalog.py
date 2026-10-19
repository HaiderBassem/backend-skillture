"""Users (FR-01), categories (FR-02) and products (FR-03)."""

from decimal import Decimal

import pytest

from dal import CategoryInUseError, DuplicateError, RuleViolationError, UserRole


# ---------------------------------------------------------------- users


def test_new_user_is_a_customer_by_default(customer):
    assert customer.role == UserRole.CUSTOMER
    assert customer.password_hash == "hash-1"


def test_duplicate_email_is_rejected_ignoring_case(new_uow, customer):
    with pytest.raises(DuplicateError):
        with new_uow() as uow:
            uow.users.add("Someone Else", "ALICE@Example.com", "hash")


def test_find_user_by_email_ignores_case(new_uow, customer):
    with new_uow() as uow:
        assert uow.users.get_by_email("Alice@EXAMPLE.com").id == customer.id
        assert uow.users.get_by_email("nobody@example.com") is None


def test_invalid_email_is_refused_by_the_database(new_uow):
    with pytest.raises(RuleViolationError):
        with new_uow() as uow:
            uow.users.add("No Email", "not-an-email", "hash")


# ----------------------------------------------------------- categories


def test_duplicate_category_name_is_rejected(new_uow, category):
    with pytest.raises(DuplicateError):
        with new_uow() as uow:
            uow.categories.add("books")


def test_category_with_products_cannot_be_deleted(new_uow, category, make_product):
    make_product("Novel", "9.99")
    with pytest.raises(CategoryInUseError):
        with new_uow() as uow:
            uow.categories.delete(category.id)


def test_empty_category_can_be_updated_and_deleted(new_uow, category):
    with new_uow() as uow:
        updated = uow.categories.update(category.id, "Magazines", None)
        assert (updated.name, updated.description) == ("Magazines", None)
        assert uow.categories.delete(category.id) is True
        assert uow.categories.delete(category.id) is False  # already gone
        assert uow.categories.get_by_id(category.id) is None


# ------------------------------------------------------------- products


def test_product_price_must_be_greater_than_zero(new_uow, category):  # BR-01
    for bad_price in ("0", "-5.00"):
        with pytest.raises(RuleViolationError):
            with new_uow() as uow:
                uow.products.add(category.id, "Bad", Decimal(bad_price))


def test_product_stock_cannot_be_negative(new_uow, category):  # BR-02
    with pytest.raises(RuleViolationError):
        with new_uow() as uow:
            uow.products.add(category.id, "Bad", Decimal("1.00"), stock_quantity=-1)


def test_product_needs_an_existing_category(new_uow):
    with pytest.raises(RuleViolationError):
        with new_uow() as uow:
            uow.products.add(9999, "Orphan", Decimal("1.00"))


def test_customers_browse_only_active_products(new_uow, category, make_product):
    visible = make_product("Visible", "5.00")
    make_product("Hidden", "5.00", active=False)

    with new_uow() as uow:
        assert [p.id for p in uow.products.list_products()] == [visible.id]
        assert len(uow.products.list_products(only_active=False)) == 2  # admin view


def test_products_can_be_filtered_by_category(new_uow, category, make_product):
    book = make_product("Book", "5.00")
    with new_uow() as uow:
        other = uow.categories.add("Games")
        uow.products.add(other.id, "Chess", Decimal("12.00"))

        assert [p.id for p in uow.products.list_products(category_id=category.id)] == [book.id]
        assert [p.name for p in uow.products.list_products(category_id=other.id)] == ["Chess"]


def test_admin_can_change_price_details_and_activation(new_uow, category, make_product):
    product = make_product("Old name", "10.00")
    with new_uow() as uow:
        assert uow.products.set_price(product.id, Decimal("12.50")).price == Decimal("12.50")
        assert uow.products.set_active(product.id, False).is_active is False
        renamed = uow.products.update_details(product.id, category.id, "New name", "Now described")
        assert (renamed.name, renamed.description) == ("New name", "Now described")
        assert uow.products.set_price(9999, Decimal("1.00")) is None  # unknown id


def test_decrease_stock_is_refused_when_not_enough(new_uow, make_product):
    product = make_product("Scarce", "10.00", stock=4)
    with new_uow() as uow:
        assert uow.products.decrease_stock(product.id, 10) is False
        assert uow.products.get_by_id(product.id).stock_quantity == 4  # unchanged

        assert uow.products.decrease_stock(product.id, 4) is True
        assert uow.products.get_by_id(product.id).stock_quantity == 0

        assert uow.products.increase_stock(product.id, 3) is True
        assert uow.products.get_by_id(product.id).stock_quantity == 3
