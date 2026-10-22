# CommerceCore

A small e-commerce backend, API only (Skillture BRD v1.0): customers browse and order,
administrators manage categories, products, stock and orders.

## Four projects, one per layer

```
 HTTP client
     │  JSON
     ▼
 commercecore-api          FastAPI + Pydantic   routes, request/response schemas (DTOs), login tokens, HTTP errors
     │  Python calls
     ▼
 commercecore-services     plain Python         business rules, roles, one transaction per operation
     │
     ▼
 commercecore-dal          SQLAlchemy Core      repositories with plain SQL, unit of work
     │  SQL
     ▼
 PostgreSQL  ◀── commercecore-migrations (Alembic + SQL)   tables, constraints, triggers
```

Each layer only talks to the one directly below it, and each has its own README and tests.

| Project | Tests | Read first |
|---|---|---|
| `commercecore-migrations` | — | `migrations/sql/` |
| `commercecore-dal` | 30 | `dal/unit_of_work.py`, `dal/repositories/` |
| `commercecore-services` | 141 | `services/order_service.py` |
| `commercecore-api` | 80 | `api/main.py`, `api/schemas/`, `api/routers/` |
| `commercecore-web` | 26 | `src/app/router.tsx`, `src/features/`, its `README.md` |

`commercecore-web` is the browser front end (React + TypeScript): a storefront for customers and an admin
console. It sits on top of the API and uses nothing else: `make run` then `make web`.

## Getting started

Everything runs from this folder through the `Makefile`, with **one shared `.venv`** for all four projects.

```bash
createdb commercecore && createdb commercecore_test
cp .env.example .env     # ONE settings file: database URLs + JWT_SECRET
make install     # .venv (Python 3.12) with every dependency
make migrate     # build the dev and the test database
make test        # every layer: DAL -> services -> API
make run         # http://127.0.0.1:8000/docs
make seed        # optional: demo data (all passwords: password123)
make admin EMAIL=you@example.com
make lint        # ruff, same rules for every project (pyproject.toml)
```

| Root file | Purpose |
|---|---|
| `Makefile` | every command for every layer |
| `requirements-dev.txt` | installs all four projects' dependencies into the shared `.venv` |
| `pyproject.toml` | shared tool settings (ruff) |
| `.env.example` | the settings template: copy it to `.env` (databases, token secret) |

All settings live in **one file**, `.env` at the root (git-ignored); `.env.example` is the template to copy.

## Where each requirement lives

| BRD | Enforced in |
|---|---|
| FR-01 registration, hashing, no self-made admins | `services/account_service.py`, `api/schemas/accounts.py` (no `role` field) |
| FR-02 / FR-03 categories, products, admin only | `services/catalog_service.py`, `api/routers/admin_catalog.py` |
| FR-04 / FR-05 placing an order, all or nothing | `services/order_service.py` (`place_order`), database triggers |
| FR-06 status changes, stock back exactly once | `services/order_service.py` (`_decide`), `dal/repositories/order_repository.py` |
| FR-07 only your own orders | `services/order_service.py` (`get_order`), `dal` (`get_for_user`) |
| BR-04 price never from the client | `api/schemas/orders.py` (no price field), services, database |

## One column through every layer: `users.international_id`

A good example of how a change travels from the bottom to the top:

| Layer | File | Change |
|---|---|---|
| migrations | `sql/0008_add_international_id.up.sql` | the column: BIGINT, default 0 |
| DAL | `dal/entities.py`, `repositories/user_repository.py` | `User.international_id`; read and written by SQL |
| services | `services/account_service.py` | optional at registration, must be a positive whole number |
| API | `api/schemas/accounts.py` | `RegisterRequest.international_id` (optional), shown in `AccountResponse` |
