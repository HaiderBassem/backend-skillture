# CommerceCore – HTTP API (FastAPI + Pydantic)

The top layer. It turns HTTP requests into service calls and service results into JSON.
**It contains no business rules**: those live in `../commercecore-services`.

| This layer does | It does not |
|---|---|
| Check the JSON shape of every request (Pydantic schemas = DTOs) | Decide prices, stock or who may see an order |
| Read the login token and find out who is calling | Open transactions or write SQL |
| Turn every error into the same JSON error shape | |

## How a request flows

```
POST /orders  {"items": [{"product_id": 1, "quantity": 2}]}
  │
  ├─ routers/orders.py        place_order(...)      which endpoint
  ├─ dependencies.py          CurrentActor          token → user id → role read from the database   (401)
  ├─ schemas/orders.py        PlaceOrderRequest     right shape? unknown field like "price"?         (422)
  ├─ services.OrderService    place_order()         business rules, ONE transaction                  (409 ...)
  └─ schemas/orders.py        OrderResponse         exactly which fields go back
```

## Structure

```
commercecore-api/
├── .env.example           JWT_SECRET, ACCESS_TOKEN_MINUTES  (the database URL is in ../commercecore-dal/.env)
├── api/
│   ├── main.py            create_app(): builds the app, plugs in services, routers, error handlers
│   ├── config.py          settings from .env
│   ├── security.py        create / read the JWT access token
│   ├── dependencies.py    CurrentActor, AdminActor, services, paging
│   ├── errors.py          ServiceError → HTTP status + {"code", "message", "field"}
│   ├── manage.py          python -m api.manage make-admin EMAIL
│   ├── seed.py            demo data for an empty database (make seed)
│   ├── schemas/           the DTOs: *Request (what comes in) and *Response (what goes out)
│   │   ├── accounts.py    RegisterRequest, LoginRequest, AccountResponse, TokenResponse
│   │   ├── catalog.py     CategoryRequest/Response, ProductCreate/UpdateRequest, ProductResponse
│   │   └── orders.py      PlaceOrderRequest, OrderResponse, AdminOrderResponse
│   └── routers/           one file per area; each endpoint is ~3 lines
│       ├── accounts.py    /auth/...
│       ├── catalog.py     /categories, /products              (public)
│       ├── orders.py      /orders                             (logged in: your own orders)
│       ├── admin_catalog.py  /admin/categories, /admin/products  (admin)
│       └── admin_orders.py   /admin/orders                       (admin)
└── tests/                 80 tests, real HTTP calls down to the real test database
```

## Run it

Every command runs from the **repository root** (the root `Makefile` drives all four layers).
You need the databases first: see the DAL README (`make install`, `make migrate`).

```bash
cp commercecore-api/.env.example commercecore-api/.env   # then set JWT_SECRET (how to generate one is in the file)
make run                                                 # http://127.0.0.1:8000/docs
make seed                                                # optional: demo data, all passwords "password123"
```

In `/docs`: register, log in, copy `access_token`, click **Authorize**, paste it.

**The first administrator.** Nobody can become an admin through the API. Register normally, then on the server:

```bash
make admin EMAIL=you@example.com    # = python -m api.manage make-admin you@example.com
```

## Endpoints

| Who | Method & path | What | BRD |
|---|---|---|---|
| anyone | `POST /auth/register` | create a **customer** account (`international_id` optional) | FR-01 |
| anyone | `POST /auth/login` | e-mail + password → access token | FR-01 |
| logged in | `GET /auth/me` | your account | |
| anyone | `GET /categories`, `GET /categories/{id}` | browse categories | FR-02 |
| anyone | `GET /products?category_id=&limit=&offset=` | active products, current prices, `available` | FR-03 |
| anyone | `GET /products/{id}` | one active product | FR-03 |
| customer | `POST /orders` | place an order | FR-04 |
| customer | `GET /orders`, `GET /orders/{id}` | your own orders only | FR-07 |
| admin | `POST /admin/categories`, `PUT` / `DELETE /admin/categories/{id}` | manage categories | FR-02 |
| admin | `GET /admin/products`, `GET /admin/products/{id}` | all products, including inactive | FR-03 |
| admin | `POST /admin/products`, `PATCH /admin/products/{id}` | create; change details, price, stock, active | FR-03 |
| admin | `GET /admin/orders?status=`, `GET /admin/orders/{id}` | all orders | FR-07 |
| admin | `POST /admin/orders/{id}/confirm` · `/cancel` | pending → confirmed / cancelled | FR-06 |

## Errors

Every error has the same body:

```json
{"code": "out_of_stock", "message": "not enough stock for 'Product A': 8 left, 99 requested", "field": null}
```

| Status | `code` | When |
|---|---|---|
| 401 | `not_authenticated` | no token, bad / expired token, wrong login |
| 403 | `forbidden` | logged in, but not an administrator |
| 404 | `not_found` | missing — or not yours (someone else's order looks exactly like a missing one) |
| 409 | `conflict`, `out_of_stock`, `product_unavailable`, `invalid_state` | valid request, but the current state refuses it |
| 422 | `validation_error` | the request is malformed; `field` says where (`items.0.quantity`) |

## Design choices worth explaining

- **Schemas refuse unknown fields** (`extra="forbid"`). Sending `"unit_price"` in an order line or `"role"` at
  registration is a 422, not silently ignored. That makes BR-04 and FR-01 visible in the API contract.
- **Money is a string** in JSON (`"10.00"`), never a float, so `0.1 + 0.2` problems cannot happen.
  Requests accept `"9.99"` or `9.99`; more than 2 decimals is refused.
- **Strict integers**: a quantity must be a JSON integer; `"2"`, `1.5` and `true` are refused (BR-03).
- **The token holds only the user id.** The role is read from the database on every request, so removing
  someone's admin role works immediately, not when their token expires.
- **Two views of an order**: customers get `OrderResponse`; admins get `AdminOrderResponse`, which adds
  `user_id` and `decided_by`. The schema decides what each audience can see.
- **Endpoints are plain `def`**, not `async def`: the database driver is synchronous, so FastAPI runs them in
  a thread pool and the server never blocks.
- **Validation happens twice on purpose**: Pydantic checks the shape (fast, good messages, documented in
  `/docs`); the service layer checks again, because it must stay correct no matter who calls it.

## Tests

```bash
make test        # from the root; needs TEST_DATABASE_URL in ../commercecore-dal/.env (a migrated database named *test*)
```

They cover the BRD scenarios A–E over HTTP, every business rule that has an HTTP face (BR-01 … BR-12),
roles (guest / customer / admin on every admin route), tokens (forged, expired, unknown user), and the
error format.
