"""Registration and login (FR-01)."""

import pytest

from dal import UserRole
from services import AuthenticationError, ConflictError, ValidationError


def test_register_creates_a_customer_without_leaking_the_hash(accounts, new_uow):
    account = accounts.register("  Alice Tester ", "  Alice@Example.COM ", "correct-horse-battery")

    assert (account.full_name, account.email) == ("Alice Tester", "alice@example.com")
    assert account.role == UserRole.CUSTOMER
    assert not hasattr(account, "password_hash")
    with new_uow() as uow:  # what is stored is a hash, never the password
        stored = uow.users.get_by_id(account.id).password_hash
    assert stored.startswith("scrypt$") and "correct-horse-battery" not in stored


def test_duplicate_email_is_refused_ignoring_case(accounts):
    accounts.register("Alice", "alice@example.com", "correct-horse-battery")
    with pytest.raises(ConflictError):
        accounts.register("Impostor", "ALICE@example.com", "another-password")


@pytest.mark.parametrize(
    "name, email, password",
    [
        ("", "a@example.com", "long-enough-pw"),
        ("   ", "a@example.com", "long-enough-pw"),
        ("A" * 101, "a@example.com", "long-enough-pw"),
        ("Alice", "not-an-email", "long-enough-pw"),
        ("Alice", "a@example.com", "short"),
        ("Alice", "a@example.com", None),
        (None, "a@example.com", "long-enough-pw"),
    ],
)
def test_bad_registration_input_is_refused(accounts, name, email, password):
    with pytest.raises(ValidationError):
        accounts.register(name, email, password)


def test_login_with_the_right_password(accounts):
    registered = accounts.register("Alice", "alice@example.com", "correct-horse-battery")
    logged_in = accounts.login(" ALICE@example.com ", "correct-horse-battery")
    assert logged_in.id == registered.id
    assert logged_in.as_actor().user_id == registered.id


def test_wrong_password_and_unknown_email_look_the_same(accounts):
    accounts.register("Alice", "alice@example.com", "correct-horse-battery")

    with pytest.raises(AuthenticationError) as wrong_password:
        accounts.login("alice@example.com", "wrong-password")
    with pytest.raises(AuthenticationError) as unknown_email:
        accounts.login("nobody@example.com", "correct-horse-battery")

    assert wrong_password.value.message == unknown_email.value.message


@pytest.mark.parametrize(
    "email, password", [(None, "x"), ("a@example.com", None), ("a\x00@example.com", "x"), (5, 5)]
)
def test_login_with_garbage_is_a_normal_login_failure(accounts, email, password):
    with pytest.raises(AuthenticationError):
        accounts.login(email, password)


def test_get_account_returns_the_callers_own_account(accounts, customer):
    assert accounts.get_account(customer).id == customer.user_id


def test_get_account_needs_login(accounts):
    with pytest.raises(AuthenticationError):
        accounts.get_account(None)


def test_actor_for_reads_the_current_role(accounts, new_uow):
    account = accounts.register("Alice", "alice@example.com", "correct-horse-battery")
    assert accounts.actor_for(account.id).role == UserRole.CUSTOMER

    with new_uow() as uow:
        uow.users.set_role(account.id, UserRole.ADMIN)
    assert accounts.actor_for(account.id).is_admin


def test_actor_for_an_unknown_user_is_not_authenticated(accounts):
    with pytest.raises(AuthenticationError):
        accounts.actor_for(999)


def test_international_id_is_optional(accounts):
    account = accounts.register("Alice", "alice@example.com", "correct-horse-battery")
    assert account.international_id == 0


def test_international_id_is_stored_when_given(accounts):
    accounts.register("Alice", "alice@example.com", "correct-horse-battery", international_id=12345)
    assert accounts.login("alice@example.com", "correct-horse-battery").international_id == 12345


@pytest.mark.parametrize("bad_id", [0, -5, "123", 1.5, True, 2**63])
def test_bad_international_id_is_refused(accounts, bad_id):
    with pytest.raises(ValidationError) as error:
        accounts.register("Alice", "alice@example.com", "correct-horse-battery", international_id=bad_id)
    assert error.value.field == "international_id"
