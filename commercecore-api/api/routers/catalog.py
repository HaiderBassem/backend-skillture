"""Browsing the store (FR-02, FR-03): open to everyone, no login needed.

Only ACTIVE products appear here. Administrators manage and see everything under /admin.
"""

from fastapi import APIRouter

from ..dependencies import Catalog, Limit, Offset
from ..schemas import CategoryResponse, ProductResponse, error_responses

router = APIRouter(tags=["Catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(catalog: Catalog):
    return catalog.list_categories()


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    responses=error_responses(404),
)
def get_category(category_id: int, catalog: Catalog):
    return catalog.get_category(category_id)


@router.get("/products", response_model=list[ProductResponse], responses=error_responses(422))
def list_products(
    catalog: Catalog,
    category_id: int | None = None,
    limit: Limit = 20,
    offset: Offset = 0,
):
    """Active products with their current prices. Add `?category_id=` to browse one category."""
    return catalog.list_products(category_id=category_id, limit=limit, offset=offset)


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    responses=error_responses(404),
)
def get_product(product_id: int, catalog: Catalog):
    """One active product. An inactive product is reported as not found."""
    return catalog.get_product(None, product_id)
