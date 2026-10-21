"""Store management: categories, products, prices and stock (FR-02, FR-03).

Administrators only (BR-09): every route in this file needs an admin token.
"""

from fastapi import APIRouter

from ..dependencies import AdminActor, Catalog, Limit, Offset, require_admin_role
from ..schemas import (
    CategoryRequest,
    CategoryResponse,
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
    error_responses,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin: catalog"],
    dependencies=[require_admin_role],
    responses=error_responses(401, 403),
)


# ------------------------------------------------------------------ categories


@router.post(
    "/categories",
    status_code=201,
    response_model=CategoryResponse,
    responses=error_responses(409, 422),
)
def create_category(body: CategoryRequest, actor: AdminActor, catalog: Catalog):
    return catalog.create_category(actor, body.name, body.description)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    responses=error_responses(404, 409, 422),
)
def update_category(category_id: int, body: CategoryRequest, actor: AdminActor, catalog: Catalog):
    """Replace the name and description."""
    return catalog.update_category(actor, category_id, body.name, body.description)


@router.delete("/categories/{category_id}", status_code=204, responses=error_responses(404, 409))
def delete_category(category_id: int, actor: AdminActor, catalog: Catalog) -> None:
    """Only an empty category can be deleted (409 while it still contains products)."""
    catalog.delete_category(actor, category_id)


# -------------------------------------------------------------------- products


@router.get("/products", response_model=list[ProductResponse])
def list_all_products(
    actor: AdminActor,
    catalog: Catalog,
    category_id: int | None = None,
    limit: Limit = 20,
    offset: Offset = 0,
):
    """Every product, including inactive ones."""
    return catalog.list_products(actor, category_id, include_inactive=True, limit=limit, offset=offset)


@router.get("/products/{product_id}", response_model=ProductResponse, responses=error_responses(404))
def get_any_product(product_id: int, actor: AdminActor, catalog: Catalog):
    return catalog.get_product(actor, product_id)


@router.post(
    "/products",
    status_code=201,
    response_model=ProductResponse,
    responses=error_responses(404, 422),
)
def create_product(body: ProductCreateRequest, actor: AdminActor, catalog: Catalog):
    return catalog.create_product(
        actor,
        body.category_id,
        body.name,
        body.price,
        description=body.description,
        stock_quantity=body.stock_quantity,
        is_active=body.is_active,
    )


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
    responses=error_responses(404, 422),
)
def update_product(product_id: int, body: ProductUpdateRequest, actor: AdminActor, catalog: Catalog):
    """Change details, price, stock or availability. Send only the fields to change."""
    changes = body.model_dump(exclude_unset=True)
    return catalog.update_product(actor, product_id, **changes)
