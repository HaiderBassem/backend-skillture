# CommerceCore – Migrations (the database schema)

The bottom layer: it **creates the tables and the hard rules** in PostgreSQL. Nothing else in the
project creates or changes tables.

- The schema is written in **plain SQL** (`migrations/sql/`), so you can read exactly what the database gets.
- **Alembic** only runs those files in the right order and remembers which ones are already applied.

## Structure

```
commercecore-migrations/
├── alembic.ini              Alembic settings (where the migrations live)
├── requirements.txt         alembic + the Postgres driver
└── migrations/
    ├── env.py               connects using DATABASE_URL; autogenerate is OFF (no ORM models)
    ├── sql_runner.py        runs one .sql file inside the migration's transaction
    ├── script.py.mako       template for a new revision file
    ├── versions/            one small Python file per step: WHICH sql file, and the order
    └── sql/                 the real SQL: NNNN_name.up.sql (apply) and NNNN_name.down.sql (undo)
```

## The steps

| Step | Creates | BRD |
|---|---|---|
| 0001 | enums `user_role`, `order_status`; shared trigger functions (`updated_at`, "this row cannot change") | |
| 0002 | `users` (unique e-mail, role defaults to customer) | FR-01 |
| 0003 | `categories` | FR-02 |
| 0004 | `products`: price > 0, stock >= 0, a category that has products cannot be deleted | FR-03, BR-01, BR-02 |
| 0005 | `orders`: never deleted, indexes for "my orders" and "pending orders" | FR-05 |
| 0006 | `order_items`: product name and price copied at purchase, never changed | BR-08 |
| 0007 | triggers: item price must equal the product's current price, only pending → confirmed / cancelled by an admin, an order needs ≥ 1 item and a correct total | BR-04 … BR-11 |
| 0008 | `users.international_id` (BIGINT, 0 = not given) | |

The rules are in the database **as well as** in the service layer: even raw SQL cannot break them.

## Run

From the repository root:

```bash
make migrate     # upgrades BOTH the dev and the test database to the latest step
```

The database URLs come from `../commercecore-dal/.env` (the only place they are configured).
By hand: `cd commercecore-migrations && DATABASE_URL=postgresql+psycopg://... ../.venv/bin/python -m alembic upgrade head`.

Useful Alembic commands (same `DATABASE_URL`): `alembic current` (where am I?), `alembic history`,
`alembic downgrade -1` (undo the last step).

## Adding a migration

1. Write `migrations/sql/0009_<name>.up.sql` and `0009_<name>.down.sql`.
2. Copy `versions/0008_add_international_id.py` to `versions/0009_<name>.py`; set `revision = "0009"`,
   `down_revision = "0008"` and the SQL file names.
3. `make migrate`, then carry the change up through the layers (see how `international_id` goes
   through `dal/entities.py` → `user_repository.py` → `account_service.py` → `api/schemas/accounts.py`).
