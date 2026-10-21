"""Registration, login and tokens (FR-01)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from tests.conftest import PASSWORD, TEST_SETTINGS

ALICE = {"full_name": "Alice Tester", "email": "alice@example.com", "password": PASSWORD}


def test_register_creates_a_customer_and_never_returns_the_password(client):
    response = client.post("/auth/register", json=ALICE)

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "customer"
    assert body["email"] == "alice@example.com"
    assert not {"password", "password_hash"} & body.keys()


def test_nobody_can_register_as_admin(client):
    response = client.post("/auth/register", json={**ALICE, "role": "admin"})

    assert response.status_code == 422
    assert response.json()["field"] == "role"


def test_duplicate_email_is_refused(client):
    client.post("/auth/register", json=ALICE)
    response = client.post("/auth/register", json={**ALICE, "email": "ALICE@example.com"})

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


@pytest.mark.parametrize(
    "change, field",
    [
        ({"email": "not-an-email"}, "email"),
        ({"password": "short"}, "password"),
        ({"full_name": ""}, "full_name"),
        ({"full_name": "   "}, "full_name"),
        ({"full_name": None}, "full_name"),
    ],
)
def test_invalid_registration_is_refused(client, change, field):
    response = client.post("/auth/register", json={**ALICE, **change})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["field"] == field


def test_validation_errors_never_echo_the_password(client):
    response = client.post("/auth/register", json={**ALICE, "password": "secret1"})
    assert "secret1" not in response.text


def test_login_returns_a_token_that_identifies_the_user(client):
    client.post("/auth/register", json=ALICE)
    login = client.post("/auth/login", json={"email": "alice@example.com", "password": PASSWORD})

    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


def test_wrong_password_and_unknown_email_look_the_same(client):
    client.post("/auth/register", json=ALICE)
    wrong_password = client.post("/auth/login", json={"email": ALICE["email"], "password": "wrong-pass"})
    unknown_email = client.post("/auth/login", json={"email": "who@example.com", "password": PASSWORD})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_needs_a_login(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def _token(user_id="1", secret=TEST_SETTINGS.jwt_secret, minutes=5):
    now = datetime.now(UTC)
    claims = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(claims, secret, algorithm="HS256")


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        _token(secret="a-different-secret-that-is-long-enough!"),  # forged
        _token(minutes=-1),  # expired
        _token(user_id="999"),  # valid signature, but no such user
        _token(user_id="abc"),
    ],
)
def test_bad_tokens_are_refused(client, customer, token):
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_unknown_url_uses_the_same_error_shape(client):
    response = client.get("/no-such-page")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_international_id_is_optional(client):
    assert client.post("/auth/register", json=ALICE).json()["international_id"] == 0


def test_international_id_is_saved_and_shown_in_me(client):
    client.post("/auth/register", json={**ALICE, "international_id": 29001011234567})
    login = client.post("/auth/login", json={"email": ALICE["email"], "password": PASSWORD})

    assert login.json()["account"]["international_id"] == 29001011234567
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.json()["international_id"] == 29001011234567


@pytest.mark.parametrize("bad_id", [0, -1, "123", 1.5, True, 2**63])
def test_bad_international_id_is_refused(client, bad_id):
    response = client.post("/auth/register", json={**ALICE, "international_id": bad_id})

    assert response.status_code == 422
    assert response.json()["field"] == "international_id"
