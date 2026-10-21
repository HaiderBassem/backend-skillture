"""The FastAPI application.

    HTTP request
      -> router       (routers/)       which endpoint, who is calling
      -> schema       (schemas/)       is the JSON well-formed?          -> 422
      -> service      (../services)    business rules, roles, one transaction
      -> DAL          (../dal)         SQL
      <- schema                        exactly which fields are returned
    errors.py turns every refusal into   {"code", "message", "field"}

Run it (see the Makefile):   uvicorn api.main:create_app --factory --reload
Interactive docs:            http://127.0.0.1:8000/docs
"""

from collections.abc import Callable

from fastapi import FastAPI

from dal import UnitOfWork
from services import AccountService, CatalogService, OrderService

from .config import Settings, get_settings
from .errors import install_error_handlers
from .routers import accounts, admin_catalog, admin_orders, catalog, orders

DESCRIPTION = """
A small online store, API only. Customers browse and order; administrators manage the store.

**How to log in here:** `POST /auth/register`, then `POST /auth/login`, copy the `access_token`,
click **Authorize** and paste it.
"""


def create_app(
    settings: Settings | None = None,
    uow_factory: Callable[[], UnitOfWork] = UnitOfWork,
) -> FastAPI:
    """Build the application. Tests pass their own settings and a test-database `uow_factory`."""
    app = FastAPI(title="CommerceCore API", version="1.0.0", description=DESCRIPTION)

    app.state.settings = settings or get_settings()
    app.state.accounts = AccountService(uow_factory)
    app.state.catalog = CatalogService(uow_factory)
    app.state.orders = OrderService(uow_factory)

    install_error_handlers(app)
    for module in (accounts, catalog, orders, admin_catalog, admin_orders):
        app.include_router(module.router)

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
