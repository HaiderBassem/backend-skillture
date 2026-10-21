"""Check that the app can reach the database:   python -m dal.check"""

import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .database import get_engine

EXPECTED_TABLES = {"users", "categories", "products", "orders", "order_items"}


def main() -> int:
    engine = get_engine()
    print(f"Connecting to {engine.url.render_as_string(hide_password=True)} ...")
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar_one()
            tables = set(
                conn.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                ).scalars()
            )
    except SQLAlchemyError as exc:
        print(f"FAILED: {exc.__cause__ or exc}")
        return 1

    print(f"Connected: {version}")
    missing = sorted(EXPECTED_TABLES - tables)
    if missing:
        print(
            f"Tables missing: {', '.join(missing)}  ->  run the migrations in commercecore-migrations first."
        )
        return 1
    print("All CommerceCore tables found. Ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
