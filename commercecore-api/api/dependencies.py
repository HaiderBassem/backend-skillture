"""FastAPI dependencies: small functions FastAPI runs BEFORE an endpoint, passing
their result in as a parameter. An endpoint just declares what it needs:

    def place_order(body: PlaceOrderRequest, actor: CurrentActor, orders: Orders): ...

The caller, from the `Authorization: Bearer <token>` header:
    CurrentActor   must be logged in         otherwise 401
    AdminActor     must be an administrator  otherwise 401 / 403

The services: one instance each, created in main.create_app().
"""

from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services import AccountService, Actor, CatalogService, OrderService
from services.actor import require_admin, require_login

from .config import Settings
from .security import read_access_token

# Adds the "Authorize" button to /docs. auto_error=False: a missing token is not
# an error by itself; require_login / require_admin decide.
bearer_scheme = HTTPBearer(auto_error=False, description="The access_token from POST /auth/login")


def _current_actor(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Actor | None:
    """None for a guest. Otherwise check the token, then read the user's CURRENT
    role from the database (the token itself does not carry the role)."""
    if credentials is None:
        return None
    user_id = read_access_token(credentials.credentials, request.app.state.settings)
    return request.app.state.accounts.actor_for(user_id)


def _logged_in_actor(actor: Annotated[Actor | None, Depends(_current_actor)]) -> Actor:
    return require_login(actor)


def _admin_actor(actor: Annotated[Actor | None, Depends(_current_actor)]) -> Actor:
    return require_admin(actor)


CurrentActor = Annotated[Actor, Depends(_logged_in_actor)]
AdminActor = Annotated[Actor, Depends(_admin_actor)]
require_admin_role = Depends(_admin_actor)  # for a whole router: APIRouter(dependencies=[...])


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _accounts(request: Request) -> AccountService:
    return request.app.state.accounts


def _catalog(request: Request) -> CatalogService:
    return request.app.state.catalog


def _orders(request: Request) -> OrderService:
    return request.app.state.orders


AppSettings = Annotated[Settings, Depends(_settings)]
Accounts = Annotated[AccountService, Depends(_accounts)]
Catalog = Annotated[CatalogService, Depends(_catalog)]
Orders = Annotated[OrderService, Depends(_orders)]

# Paging for list endpoints: ?limit=20&offset=40
Limit = Annotated[int, Query(ge=1, le=100, description="how many results (max 100)")]
Offset = Annotated[int, Query(ge=0, description="how many results to skip")]
