from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from .database import get_session_factory
from .exceptions import translate_errors
from .repositories import (
    CategoryRepository,
    OrderRepository,
    ProductRepository,
    UserRepository,
)


class UnitOfWork:
    """One database transaction that gives access to all repositories.

        with UnitOfWork() as uow:
            product = uow.products.get_by_id(1)
            uow.orders.create(...)
        # leaving the block normally  -> everything is COMMITTED
        # an exception inside it      -> everything is ROLLED BACK

    This is what makes "all or nothing" (BR-06, BR-12) simple: if any step of
    placing an order fails, nothing is saved.

    Note: after a database error the transaction is unusable, so let the
    exception leave the `with` block (do not catch it and carry on inside).
    """

    session: Session
    users: UserRepository
    categories: CategoryRepository
    products: ProductRepository
    orders: OrderRepository

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def __enter__(self) -> UnitOfWork:
        self.session = self._session_factory()
        self.users = UserRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.products = ProductRepository(self.session)
        self.orders = OrderRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.session.close()

    def commit(self) -> None:
        # Some rules (e.g. "an order must have items and a correct total") are
        # checked by the database only at COMMIT time, so errors can show up here.
        try:
            with translate_errors():
                self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def rollback(self) -> None:
        self.session.rollback()
