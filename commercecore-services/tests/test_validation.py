"""Input checks and password hashing. No database needed."""

from decimal import Decimal

import pytest

from services import ValidationError, validation
from services.passwords import hash_password, verify_password

# ------------------------------------------------------------------ price


@pytest.mark.parametrize(
    "value, expected",
    [("9.99", "9.99"), (10, "10.00"), (Decimal("0.01"), "0.01"), ("5.5", "5.50"), ("1e2", "100.00")],
)
def test_valid_prices(value, expected):
    assert validation.price(value) == Decimal(expected)


@pytest.mark.parametrize(
    "value",
    [0, "0", "-1", "0.001", "1.234", 1.5, True, None, "abc", "", "NaN", "Infinity", "10000000000.00", ["1"]],
)
def test_invalid_prices(value):
    with pytest.raises(ValidationError):
        validation.price(value)


def test_largest_price_is_accepted():
    assert validation.price("9999999999.99") == Decimal("9999999999.99")


# ---------------------------------------------------------------- numbers


def test_integer_accepts_whole_numbers_in_range():
    assert validation.integer(0, "n") == 0
    assert validation.integer(validation.MAX_INT, "n") == validation.MAX_INT


@pytest.mark.parametrize("value", [-1, 1.0, "3", True, None, validation.MAX_INT + 1])
def test_integer_rejects_everything_else(value):
    with pytest.raises(ValidationError):
        validation.integer(value, "n")


def test_integer_minimum():
    with pytest.raises(ValidationError):
        validation.integer(0, "quantity", minimum=1)


@pytest.mark.parametrize("value", [0, -3, True, "1", 1.0, None, 2**63])
def test_invalid_ids(value):
    with pytest.raises(ValidationError):
        validation.identifier(value, "id")


def test_pagination():
    assert validation.page(None, 0, default_limit=20) == (20, 0)
    assert validation.page(100, 5, default_limit=20) == (100, 5)
    for limit, offset in [(0, 0), (101, 0), (10, -1), ("5", 0), (5, "0")]:
        with pytest.raises(ValidationError):
            validation.page(limit, offset, default_limit=20)


# ------------------------------------------------------------------- text


def test_text_is_trimmed_and_checked():
    assert validation.text("  hello  ", "name", 10) == "hello"
    assert validation.text("   ", "name", 10, required=False) is None
    assert validation.text(None, "name", 10, required=False) is None
    for bad in ["", "   ", None, 5, "x" * 11, "a\x00b"]:
        with pytest.raises(ValidationError):
            validation.text(bad, "name", 10)


def test_email_is_normalised_and_checked():
    assert validation.email("  Ali@Example.COM ") == "ali@example.com"
    for bad in ["", "plain", "a@b", "a b@c.com", "@x.com", "a@b.", None, 12, "a@b.com\x00"]:
        with pytest.raises(ValidationError):
            validation.email(bad)


def test_password_length():
    assert validation.password("12345678")
    for bad in ["1234567", "x" * 129, None, 12345678]:
        with pytest.raises(ValidationError):
            validation.password(bad)


# -------------------------------------------------------------- passwords


def test_password_hash_roundtrip():
    stored = hash_password("s3cret-pass")
    assert "s3cret-pass" not in stored
    assert verify_password("s3cret-pass", stored)
    assert not verify_password("S3cret-pass", stored)


def test_same_password_gets_different_hashes():
    assert hash_password("same-password") != hash_password("same-password")


@pytest.mark.parametrize(
    "stored",
    [
        "",
        "garbage",
        "scrypt$1$2",
        "bcrypt$16384$8$1$AAAA$AAAA",
        "scrypt$x$8$1$AAAA$AAAA",
        "scrypt$99999999$8$1$AAAA$AAAA",
    ],
)
def test_malformed_hashes_never_match_and_never_raise(stored):
    assert verify_password("anything", stored) is False
