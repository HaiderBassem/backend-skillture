# CommerceCore – Service Layer (business logic)

Sits between the API (`../commercecore-api`) and the data access layer (`../commercecore-dal`).

- **Validates** every input (names, e-mail, money, quantities, paging).
- **Decides who may do what** (guest / customer / administrator).
- **Hashes passwords** (scrypt from the standard library, no extra package).
- **Combines repositories** into real operations ("place order", "cancel order"), each in ONE transaction: all or nothing.
- **Hides the database**: only `ServiceError` subclasses leave this layer, never SQL errors.

It does not know about HTTP, tokens or JSON. The API layer does that.

## Structure

```
commercecore-services/
├── pytest.ini               lets `import services` and `import dal` work from here
├── requirements*.txt        same dependencies as the DAL (+ pytest)
├── services/
│   ├── errors.py            ValidationError, AuthenticationError, PermissionDeniedError, NotFoundError, ConflictError (+ OutOfStock, ProductUnavailable, InvalidState)
│   ├── actor.py             Actor(user_id, role): who is calling.  A guest is None.
│   ├── validation.py        input checks (price, integer, text, email, paging ...)
│   ├── passwords.py         hash_password / verify_password
│   ├── account_service.py   register, login, get_account, actor_for
│   ├── catalog_service.py   categories + products: browse (anyone), manage (admin)
│   └── order_service.py     place_order, get_order, list_my_orders, list_orders, confirm_order, cancel_order
└── tests/                   run against the real, migrated Postgres test database
```

## Using it

```python
from services import AccountService, CatalogService, OrderService, OrderLine

accounts, catalog, orders = AccountService(), CatalogService(), OrderService()

account = accounts.register("Ali Hassan", "ali@example.com", "a-long-password")
actor = accounts.login("ali@example.com", "a-long-password").as_actor()  # what the API layer passes on

catalog.list_products()  # guests can browse (actor defaults to None)
order = orders.place_order(actor, [OrderLine(product_id=1, quantity=2)])
orders.get_order(actor, order.id)  # only their own orders
orders.cancel_order(admin_actor, order.id)  # admin only; stock goes back, exactly once
```

Every method that needs a caller takes the `Actor` as its first argument (`None` = guest).
The API layer turns errors into responses:

| Error | Meaning | HTTP |
|---|---|---|
| `ValidationError` (has `.field`) | the request is malformed | 400 / 422 |
| `AuthenticationError` | not logged in / wrong credentials | 401 |
| `PermissionDeniedError` | logged in, wrong role | 403 |
| `NotFoundError` | missing, or hidden from this caller (BR-10) | 404 |
| `ConflictError` and subclasses | valid request, current state refuses it (duplicate e-mail, out of stock, order already decided ...) | 409 |

## Rules implemented here

| Area | Rule |
|---|---|
| Accounts | New accounts are always Customers. `international_id` is optional (0 = not given), otherwise a positive whole number. E-mail is trimmed, lower-cased and unique. Login gives the same error for an unknown e-mail and a wrong password. The password hash never leaves the layer (`Account` has no hash). |
| Catalog | Anyone browses **active** products. Only administrators create/edit categories and products, and see inactive products. A category with products cannot be deleted. Products are deactivated, never deleted. Price > 0, stock >= 0, money has at most 2 decimals and floats are refused. |
| Placing an order | Needs a logged-in user. Lines are merged per product, quantities must be >= 1. The price and name are read from the product, never from the request (BR-04). Inactive/missing products and not enough stock are refused (BR-05, BR-06). Products are locked first, so two buyers can never take the last unit. Any failure rolls back everything, including stock. |
| Deciding orders | Administrators only. Only Pending orders can be confirmed or cancelled. Cancelling puts the stock back exactly once, even when two admins click at the same time (BR-11). A user whose admin role was removed is refused by the database as well. |
| Reading orders | Customers see only their own orders; someone else's order looks exactly like a missing one. Administrators see all, and can filter by status. |

## Tests

Same database setup as the DAL (`TEST_DATABASE_URL` in the root `.env`, migrated, name contains `test`):

```bash
cd commercecore-services
../.venv/bin/python -m pytest        # or `make test` from the root: every layer
```

141 tests: validation, every service method, the BRD scenarios A-E, and concurrency (last unit, simultaneous cancels, confirm vs cancel).

## Notes

- `users.international_id` (migration 0008) is optional at registration: `register(..., international_id=None)` stores 0 when it is not given.
- Roles come from the `Actor` the API layer builds. Order decisions are additionally verified by the database, so a stale "admin" claim cannot decide an order.
