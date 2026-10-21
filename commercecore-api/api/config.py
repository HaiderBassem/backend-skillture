"""Settings for the HTTP layer, read from the environment (and from commercecore-api/.env).

The database connection is NOT configured here: the data access layer reads
DATABASE_URL from ../commercecore-dal/.env.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Variables already set in the real environment win over the .env file.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MIN_SECRET_LENGTH = 32


@dataclass(frozen=True)
class Settings:
    jwt_secret: str  # signs the access tokens; anyone who knows it can forge a login
    token_minutes: int = 60  # how long a login stays valid


def get_settings() -> Settings:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET must be a random string of at least {MIN_SECRET_LENGTH} characters. "
            "Copy .env.example to .env and fill it in."
        )
    return Settings(
        jwt_secret=secret,
        token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "60")),
    )
