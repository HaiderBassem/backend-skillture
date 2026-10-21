"""Categories (FR-02) and products / inventory (FR-03).

Anyone, even a guest, may browse. Only administrators may change anything.
"""

from __future__ import annotations

from collections.abc import Callable

from dal import Category, CategoryInUseError, DuplicateError, Product, UnitOfWork

from . import validation
from .actor import Actor, require_admin
from .errors import ConflictError, NotFoundError, ValidationError


class CatalogService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork] = UnitOfWork) -> None:
        self._uow_factory = uow_factory

    # -------------------------------------------------------------- categories

    def list_categories(self) -> list[Category]:
        with self._uow_factory() as uow:
            return uow.categories.list_all()

    def get_category(self, category_id) -> Category:
        category_id = validation.identifier(category_id, "category_id")
        with self._uow_factory() as uow:
            category = uow.categories.get_by_id(category_id)
        if category is None:
            raise NotFoundError(f"category {category_id} not found")
        return category

    def create_category(self, actor: Actor | None, name, description=None) -> Category:
        require_admin(actor)
        name = validation.text(name, "name", 100)
        description = validation.text(description, "description", 10_000, required=False)
        try:
            with self._uow_factory() as uow:
                return uow.categories.add(name, description)
        except DuplicateError:
            raise ConflictError(f"a category named '{name}' already exists") from None

    def update_category(self, actor: Actor | None, category_id, name, description=None) -> Category:
        """Replace the name and description of a category."""
        require_admin(actor)
        category_id = validation.identifier(category_id, "category_id")
        name = validation.text(name, "name", 100)
        description = validation.text(description, "description", 10_000, required=False)
        try:
            with self._uow_factory() as uow:
                category = uow.categories.update(category_id, name, description)
        except DuplicateError:
            raise ConflictError(f"a category named '{name}' already exists") from None
        if category is None:
            raise NotFoundError(f"category {category_id} not found")
        return category

    def delete_category(self, actor: Actor | None, category_id) -> None:
        """Delete an empty category. A category that still has products is refused."""
        require_admin(actor)
        category_id = validation.identifier(category_id, "category_id")
        try:
            with self._uow_factory() as uow:
                deleted = uow.categories.delete(category_id)
        except CategoryInUseError:
            raise ConflictError(
                "this category still contains products; move or deactivate them first"
            ) from None
        if not deleted:
            raise NotFoundError(f"category {category_id} not found")

    # ---------------------------------------------------------------- products

    def list_products(
        self,
        actor: Actor | None = None,
        category_id=None,
        include_inactive: bool = False,
        limit=None,
        offset=0,
    ) -> list[Product]:
        """Browse the catalog. Guests and customers see active products only;
        an administrator may ask for `include_inactive=True` to see everything.
        """
        if include_inactive:
            require_admin(actor)
        if category_id is not None:
            category_id = validation.identifier(category_id, "category_id")
        limit, offset = validation.page(limit, offset, default_limit=20)
        with self._uow_factory() as uow:
            return uow.products.list_products(
                category_id=category_id,
                only_active=not include_inactive,
                limit=limit,
                offset=offset,
            )

    def get_product(self, actor: Actor | None, product_id) -> Product:
        """One product. An inactive product looks missing to everyone but administrators."""
        product_id = validation.identifier(product_id, "product_id")
        with self._uow_factory() as uow:
            product = uow.products.get_by_id(product_id)
        is_admin = actor is not None and actor.is_admin
        if product is None or not (product.is_active or is_admin):
            raise NotFoundError(f"product {product_id} not found")
        return product

    def create_product(
        self,
        actor: Actor | None,
        category_id,
        name,
        price,
        description="",
        stock_quantity=0,
        is_active=True,
    ) -> Product:
        require_admin(actor)
        category_id = validation.identifier(category_id, "category_id")
        name = validation.text(name, "name", 150)
        description = validation.text(description, "description", 100_000, required=False) or ""
        price = validation.price(price)
        stock_quantity = validation.integer(stock_quantity, "stock_quantity")
        is_active = _boolean(is_active, "is_active")

        with self._uow_factory() as uow:
            if uow.categories.get_by_id(category_id) is None:
                raise NotFoundError(f"category {category_id} not found")
            return uow.products.add(category_id, name, price, description, stock_quantity, is_active)

    def update_product(
        self,
        actor: Actor | None,
        product_id,
        *,
        category_id=None,
        name=None,
        description=None,
        price=None,
        stock_quantity=None,
        is_active=None,
    ) -> Product:
        """Change only the fields that are given (None = leave as it is).

        `stock_quantity` is the new absolute stock level (an inventory
        correction). Deactivate a product instead of deleting it. Orders that
        already exist keep the old price and name (BR-08).
        """
        require_admin(actor)
        product_id = validation.identifier(product_id, "product_id")
        changes: dict = {}
        if category_id is not None:
            changes["category_id"] = validation.identifier(category_id, "category_id")
        if name is not None:
            changes["name"] = validation.text(name, "name", 150)
        if description is not None:
            changes["description"] = (
                validation.text(description, "description", 100_000, required=False) or ""
            )
        if price is not None:
            changes["price"] = validation.price(price)
        if stock_quantity is not None:
            changes["stock_quantity"] = validation.integer(stock_quantity, "stock_quantity")
        if is_active is not None:
            changes["is_active"] = _boolean(is_active, "is_active")

        with self._uow_factory() as uow:
            # Lock the row so a customer's order cannot change stock/price under us.
            locked = uow.products.get_many_for_update([product_id])
            if not locked:
                raise NotFoundError(f"product {product_id} not found")
            product = locked[0]
            if "category_id" in changes and uow.categories.get_by_id(changes["category_id"]) is None:
                raise NotFoundError(f"category {changes['category_id']} not found")

            if {"category_id", "name", "description"} & changes.keys():
                product = uow.products.update_details(
                    product_id,
                    changes.get("category_id", product.category_id),
                    changes.get("name", product.name),
                    changes.get("description", product.description),
                )
            if "price" in changes:
                product = uow.products.set_price(product_id, changes["price"])
            if "stock_quantity" in changes:
                product = uow.products.set_stock(product_id, changes["stock_quantity"])
            if "is_active" in changes:
                product = uow.products.set_active(product_id, changes["is_active"])
            return product


def _boolean(value, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be true or false", field)
    return value
