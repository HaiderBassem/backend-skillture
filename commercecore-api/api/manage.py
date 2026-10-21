"""Command-line administration.

Roles are changed here, on the server, never over HTTP: nobody can make
themselves an administrator through the API (FR-01).

    python -m api.manage make-admin ali@example.com      # the user must have registered first
    python -m api.manage make-customer ali@example.com   # take the admin role away
"""

import argparse
import sys

from dal import UnitOfWork, UserRole

COMMANDS = {"make-admin": UserRole.ADMIN, "make-customer": UserRole.CUSTOMER}


def set_role(email: str, role: UserRole) -> bool:
    with UnitOfWork() as uow:
        user = uow.users.get_by_email(email.strip())
        if user is None:
            return False
        uow.users.set_role(user.id, role)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m api.manage", description="CommerceCore administration")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        commands.add_parser(name).add_argument("email")
    args = parser.parse_args(argv)

    role = COMMANDS[args.command]
    if not set_role(args.email, role):
        print(f"No user with e-mail {args.email!r}. Register first (POST /auth/register).", file=sys.stderr)
        return 1
    print(f"{args.email} is now: {role.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
