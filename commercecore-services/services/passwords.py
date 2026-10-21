"""Password hashing with scrypt from the Python standard library (no extra package).

A stored hash looks like   scrypt$<n>$<r>$<p>$<salt>$<hash>
so the cost settings travel with the hash and can be raised later without
breaking old passwords.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_N, _R, _P = 2**14, 8, 1  # ~16 MB of memory and ~50 ms per hash
_SALT_BYTES = 16
_KEY_BYTES = 32
_MAX_COST = 2**20  # never run scrypt with parameters read from a stored hash beyond this


def _derive(password: str, salt: bytes, n: int, r: int, p: int, length: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=length, maxmem=128 * n * r * 2
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    key = _derive(password, salt, _N, _R, _P, _KEY_BYTES)
    return "$".join(
        ["scrypt", str(_N), str(_R), str(_P)] + [base64.b64encode(raw).decode("ascii") for raw in (salt, key)]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """True if `password` matches `stored_hash`. Never raises on a malformed hash."""
    try:
        scheme, n, r, p, salt, key = stored_hash.split("$")
        n, r, p = int(n), int(r), int(p)
        if scheme != "scrypt" or max(n, r, p) > _MAX_COST:
            return False
        expected = base64.b64decode(key)
        actual = _derive(password, base64.b64decode(salt), n, r, p, len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# Lets login spend the same time on an unknown e-mail as on a wrong password.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
