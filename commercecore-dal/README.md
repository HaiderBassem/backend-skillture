# CommerceCore – Data Access Layer

The database access layer (repository pattern) for CommerceCore.

- **The tables are NOT created here.** `../commercecore-migrations` (plain SQL) owns the schema.
- **SQLAlchemy is only the connection**: engine, sessions and transactions. Each repository runs plain SQL.
- Repositories return small plain objects (`dal/entities.py`), not ORM models.

## Structure

```
commercecore-dal/
├── pytest.ini            lets the tests `import dal`
├── requirements.txt      runtime dependencies  (requirements-dev.txt adds pytest)
├── dal/
│   ├── config.py         reads the root .env  ->  DATABASE_URL
│   ├── database.py       SQLAlchemy engine + session factory
│   ├── entities.py       User, Category, Product, Order, OrderItem (+ enums)
│   ├── exceptions.py     DuplicateError, RuleViolationError, CategoryInUseError
│   ├── unit_of_work.py   one transaction  ->  uow.users / categories / products / orders
│   ├── check.py          `python -m dal.check` tests the connection
│   └── repositories/     one file per table group: SQL lives here
└── tests/                run against a real, migrated Postgres test database
```

## Setup

All commands run from the **repository root** (one shared `.venv` for every layer, see the root `Makefile`):

```bash
createdb commercecore && createdb commercecore_test
cp .env.example .env                                      # then edit DATABASE_URL and TEST_DATABASE_URL
make install                                              # shared .venv with every dependency
make migrate                                              # build both databases (../commercecore-migrations)
make check                                                # = python -m dal.check: connection + tables
```

The root `.env` is the only settings file: the migrations, the DAL, the services and the API all read it.

## Using it

```python
from dal import UnitOfWork, NewOrderItem

with UnitOfWork() as uow:  # opens a transaction
    product = uow.products.get_many_for_update([1])[0]  # locks the row
    uow.products.decrease_stock(product.id, 2)
    uow.orders.create(
        user_id=7,
        items=[
            NewOrderItem(product.id, product.name, product.price, 2),  # price from the DB, never the client
        ],
    )
# leaving the block commits; an exception rolls EVERYTHING back (all or nothing)
```

`tests/test_orders.py` contains complete `place_order` / `cancel_order` examples (BRD scenarios A–E).

## What belongs where

| Layer | Responsibility |
|---|---|
| **This layer** | Talk to the database. Atomic stock updates, row locks, "only my orders" queries, translate DB errors. |
| **Service layer** (`../commercecore-services`) | Business flow: validate the request, who may do what (roles), hash passwords, combine repositories into "place order" / "cancel order". |

The database itself already enforces the hard rules (price > 0, stock >= 0, immutable order history,
only admins decide orders, order total = sum of items). Breaking one raises `RuleViolationError`.

## Tests

```bash
make test                                         # from the root: DAL, then services, then API
cd commercecore-dal && ../.venv/bin/python -m pytest   # only this layer (30 tests)
```

`TEST_DATABASE_URL` (in the root `.env`) must point at a database whose name contains `test`: every table is emptied before each test.
