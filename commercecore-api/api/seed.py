"""Demo data: a little of everything, so every endpoint has something to show.

    python -m api.seed        (or: make seed)

Everything goes through the service layer, so the business rules apply exactly
as they do over HTTP: stock goes down when orders are placed, comes back when
one is cancelled, and order items keep the price they were bought at.

What you get (every password is  password123):
    admin@commercecore.dev     administrator
    sara@example.com           1 confirmed order, 1 pending                (has an international_id)
    omar@example.com           1 cancelled order (stock restored), 1 pending (has an international_id)
    lina@example.com           (no international_id)
                               1 confirmed order bought before a price change and
                               1 order of a product that was later deactivated
    5 categories (Toys is empty, so it can be deleted)
    11 products: in stock, low stock, out of stock, inactive
"""

import sys
from collections.abc import Callable

from dal import UnitOfWork, UserRole
from services import AccountService, Actor, CatalogService, OrderLine, OrderService

PASSWORD = "password123"
ADMIN_EMAIL = "admin@commercecore.dev"

# key: (name, email, international_id)  None = not given, to show that it is optional
CUSTOMERS = {
    "sara": ("Sara Ahmed", "sara@example.com", 29001011234567),
    "omar": ("Omar Khalil", "omar@example.com", 28505152345678),
    "lina": ("Lina Haddad", "lina@example.com", None),
}

CATEGORIES = {
    "electronics": ("Electronics", "Computer accessories and audio"),
    "books": ("Books", "Programming and software books"),
    "home": ("Home & Kitchen", "Mugs, coffee and everyday items"),
    "clothing": ("Clothing", "T-shirts and hoodies"),
    "toys": ("Toys", "Coming soon: no products yet, so this category can be deleted"),
}

# key: (category, name, price, stock, description)
PRODUCTS = {
    "mouse": ("electronics", "Wireless Mouse", "15.00", 50, "Silent clicks, 12-month battery"),
    "keyboard": ("electronics", "Mechanical Keyboard", "45.00", 20, "Brown switches, backlit"),
    "cable": ("electronics", "USB-C Cable", "5.00", 100, "1 meter, fast charging"),
    "headphones": ("electronics", "Noise-Cancelling Headphones", "60.00", 0, "Out of stock"),
    "clean_code": ("books", "Clean Code", "30.00", 15, "Robert C. Martin"),
    "pragmatic": ("books", "The Pragmatic Programmer", "35.00", 10, "20th anniversary edition"),
    "old_book": ("books", "Python 2 Cookbook", "12.00", 8, "Old edition, will be taken off sale"),
    "mug": ("home", "Coffee Mug", "8.00", 40, "350 ml ceramic"),
    "french_press": ("home", "French Press", "25.00", 5, "1 liter, glass"),
    "tshirt": ("clothing", "Logo T-Shirt", "12.00", 30, "100% cotton"),
    "hoodie": ("clothing", "Hoodie", "28.00", 4, "Low stock"),
}


def seed(uow_factory: Callable[[], UnitOfWork] = UnitOfWork) -> None:
    accounts = AccountService(uow_factory)
    catalog = CatalogService(uow_factory)
    orders = OrderService(uow_factory)

    with uow_factory() as uow:
        if uow.categories.list_all() or uow.users.get_by_email(ADMIN_EMAIL):
            raise RuntimeError("The database already has data; seed only runs on an empty one.")

    # --- people
    admin_account = accounts.register("Store Admin", ADMIN_EMAIL, PASSWORD)
    with uow_factory() as uow:
        uow.users.set_role(admin_account.id, UserRole.ADMIN)
    admin = Actor(admin_account.id, UserRole.ADMIN)
    customer = {
        key: accounts.register(name, email, PASSWORD, international_id).as_actor()
        for key, (name, email, international_id) in CUSTOMERS.items()
    }

    # --- catalog
    category = {
        key: catalog.create_category(admin, name, description).id
        for key, (name, description) in CATEGORIES.items()
    }
    product = {
        key: catalog.create_product(
            admin, category[cat], name, price, description=description, stock_quantity=stock
        ).id
        for key, (cat, name, price, stock, description) in PRODUCTS.items()
    }

    def order(who: str, *lines: tuple[str, int]) -> int:
        return orders.place_order(customer[who], [OrderLine(product[key], qty) for key, qty in lines]).id

    # --- orders, one for every situation
    sara_confirmed = order("sara", ("mouse", 2), ("keyboard", 1))  # 2x15 + 45 = 75.00
    orders.confirm_order(admin, sara_confirmed)
    order("sara", ("clean_code", 1), ("cable", 3))  # pending

    omar_cancelled = order("omar", ("mug", 3))  # cancelled: the 3 mugs go back to stock
    orders.cancel_order(admin, omar_cancelled)
    order("omar", ("tshirt", 2), ("hoodie", 1))  # pending, hoodie now low on stock

    lina_confirmed = order("lina", ("pragmatic", 1), ("french_press", 1))  # 35 + 25 = 60.00
    orders.confirm_order(admin, lina_confirmed)
    catalog.update_product(admin, product["pragmatic"], price="39.00")  # Lina's order keeps 35.00

    order("lina", ("old_book", 1))  # pending, then the product is taken off sale:
    catalog.update_product(admin, product["old_book"], is_active=False)  # the order keeps its name


def main() -> int:
    try:
        seed()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    print("Demo data added.\n\nWhat you get" + __doc__.split("What you get", 1)[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
