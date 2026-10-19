from ..entities import Category
from ..exceptions import (
    FOREIGN_KEY_VIOLATION,
    RESTRICT_VIOLATION,
    CategoryInUseError,
    RuleViolationError,
)
from .base import BaseRepository

_COLUMNS = "id, name, description, created_at, updated_at"


class CategoryRepository(BaseRepository):
    """Product categories (FR-02)."""

    def add(self, name: str, description: str | None = None) -> Category:
        """Raises DuplicateError if the name exists (case-insensitive)."""
        row = self._execute(
            f"""
            INSERT INTO categories (name, description)
            VALUES (:name, :description)
            RETURNING {_COLUMNS}
            """,
            {"name": name, "description": description},
        ).mappings().one()
        return Category.from_row(row)

    def get_by_id(self, category_id: int) -> Category | None:
        row = self._execute(
            f"SELECT {_COLUMNS} FROM categories WHERE id = :id", {"id": category_id}
        ).mappings().first()
        return Category.from_row(row) if row else None

    def list_all(self) -> list[Category]:
        rows = self._execute(f"SELECT {_COLUMNS} FROM categories ORDER BY name").mappings().all()
        return [Category.from_row(r) for r in rows]

    def update(self, category_id: int, name: str, description: str | None) -> Category | None:
        """Replace name and description. Returns None if the category does not exist."""
        row = self._execute(
            f"""
            UPDATE categories SET name = :name, description = :description
            WHERE id = :id
            RETURNING {_COLUMNS}
            """,
            {"id": category_id, "name": name, "description": description},
        ).mappings().first()
        return Category.from_row(row) if row else None

    def delete(self, category_id: int) -> bool:
        """Delete a category. True if deleted, False if it did not exist.

        Raises CategoryInUseError if products still belong to it.
        """
        try:
            result = self._execute("DELETE FROM categories WHERE id = :id", {"id": category_id})
        except RuleViolationError as exc:
            if exc.sqlstate in (RESTRICT_VIOLATION, FOREIGN_KEY_VIOLATION):
                raise CategoryInUseError(
                    "category still contains products and cannot be deleted",
                    exc.sqlstate,
                    exc.constraint,
                ) from exc
            raise
        return result.rowcount > 0
