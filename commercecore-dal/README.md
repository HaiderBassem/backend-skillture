# CommerceCore – Data Access Layer

The database access layer (repository pattern) for CommerceCore.

- **The tables are NOT created here.** `../commercecore-migrations` (plain SQL) owns the schema.
- **SQLAlchemy is only the connection**: engine, sessions and transactions. Each repository runs plain SQL.
- Repositories return small plain objects (`dal/entities.py`), not ORM models.

## Structure

```
commercecore-dal/
├── .env                  your local settings (git-ignored)
├── .env.example          template for .env
├── requirements.txt      runtime dependencies  (requirements-dev.txt adds pytest)
├── dal/
│   ├── config.py         reads .env  ->  DATABASE_URL
│   ├── database.py       SQLAlchemy engine + session factory
│   ├── entities.py       User, Category, Product, Order, OrderItem (+ enums)
│   ├── exceptions.py     DuplicateError, RuleViolationError, CategoryInUseError
│   ├── unit_of_work.py   one transaction  ->  uow.users / categories / products / orders
│   ├── check.py          `python -m dal.check` tests the connection
│   └── repositories/     one file per table group: SQL lives here
└── tests/                run against a real, migrated Postgres test database
```

## Setup

```bash
cd commercecore-dal
uv venv .venv && uv pip install -r requirements-dev.txt   # or: python -m venv .venv && pip install -r requirements-dev.txt
cp .env.example .env                                       # then edit DATABASE_URL
.venv/bin/python -m dal.check                              # connection + tables test
```

Create the database and run the migrations first (they are in `../commercecore-migrations`):

```bash
createdb commercecore
cd ../commercecore-migrations
uv pip install -r requirements.txt     # alembic + driver (into any venv)
DATABASE_URL=postgresql+psycopg://USER@localhost:5432/commercecore alembic upgrade head
```

## Using it

```python
from dal import UnitOfWork, NewOrderItem

with UnitOfWork() as uow:                      # opens a transaction
    product = uow.products.get_many_for_update([1])[0]      # locks the row
    uow.products.decrease_stock(product.id, 2)
    uow.orders.create(user_id=7, items=[
        NewOrderItem(product.id, product.name, product.price, 2),   # price from the DB, never the client
    ])
# leaving the block commits; an exception rolls EVERYTHING back (all or nothing)
```

`tests/test_orders.py` contains complete `place_order` / `cancel_order` examples (BRD scenarios A–E).

## What belongs where

| Layer | Responsibility |
|---|---|
| **This layer** | Talk to the database. Atomic stock updates, row locks, "only my orders" queries, translate DB errors. |
| **Service layer (next)** | Business flow: validate the request, who may do what (roles), hash passwords, combine repositories into "place order" / "cancel order". |

The database itself already enforces the hard rules (price > 0, stock >= 0, immutable order history,
only admins decide orders, order total = sum of items). Breaking one raises `RuleViolationError`.

## Tests

```bash
createdb commercecore_test                        # then run the migrations against it
.venv/bin/python -m pytest
```

`TEST_DATABASE_URL` (in `.env`) must point at a database whose name contains `test`: every table is emptied before each test.
