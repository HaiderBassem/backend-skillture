"""Settings read from the environment (and from the ONE .env file at the repository root)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # <repo>/.env, shared by every layer

# Variables already set in the real environment win over the .env file.
load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    database_url: str
    db_echo: bool


def normalize_url(url: str) -> str:
    """Make a plain postgresql:// URL use the psycopg (v3) driver we install."""
    for plain in ("postgresql://", "postgres://"):
        if url.startswith(plain):
            return "postgresql+psycopg://" + url[len(plain) :]
    return url


def get_settings() -> Settings:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(f"DATABASE_URL is not set. Copy .env.example to {ENV_FILE} and fill it in.")
    return Settings(
        database_url=normalize_url(url),
        db_echo=os.getenv("DB_ECHO", "false").lower() in ("1", "true", "yes"),
    )
