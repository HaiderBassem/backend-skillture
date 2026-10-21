"""Access tokens (JWT).

After logging in, the client receives a signed token and sends it back on
every request that needs a login:

    Authorization: Bearer <token>

The token only says WHO you are (`sub` = user id) and until when it is valid.
It does not carry the role: the role is read fresh from the database on every
request (see dependencies.py), so taking away an admin role works immediately.
"""

from datetime import UTC, datetime, timedelta

import jwt

from services import AuthenticationError

from .config import Settings

ALGORITHM = "HS256"


def create_access_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.token_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)


def read_access_token(token: str, settings: Settings) -> int:
    """The user id inside a valid token. Raises AuthenticationError for a
    forged, damaged or expired token."""
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM],  # never let the token choose its own algorithm
            options={"require": ["sub", "exp"]},
        )
        user_id = int(claims["sub"])
    except (jwt.PyJWTError, ValueError):
        raise AuthenticationError("invalid or expired token") from None
    if user_id < 1:
        raise AuthenticationError("invalid or expired token")
    return user_id
