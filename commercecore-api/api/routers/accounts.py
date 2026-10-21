"""Register, log in, and "who am I" (FR-01)."""

from fastapi import APIRouter

from ..dependencies import Accounts, AppSettings, CurrentActor
from ..schemas import AccountResponse, LoginRequest, RegisterRequest, TokenResponse, error_responses
from ..security import create_access_token

router = APIRouter(prefix="/auth", tags=["Accounts"])


@router.post(
    "/register",
    status_code=201,
    response_model=AccountResponse,
    responses=error_responses(409, 422),
)
def register(body: RegisterRequest, accounts: Accounts):
    """Create an account. Every new account is a **customer**: nobody can register as an administrator."""
    return accounts.register(body.full_name, body.email, body.password, body.international_id)


@router.post("/login", response_model=TokenResponse, responses=error_responses(401, 422))
def login(body: LoginRequest, accounts: Accounts, settings: AppSettings):
    """Exchange e-mail and password for an access token.

    A wrong password and an unknown e-mail get the same answer, so nobody can find out who has an account.
    """
    account = accounts.login(body.email, body.password)
    return TokenResponse(
        access_token=create_access_token(account.id, settings),
        expires_in=settings.token_minutes * 60,
        account=AccountResponse.model_validate(account),
    )


@router.get("/me", response_model=AccountResponse, responses=error_responses(401))
def me(actor: CurrentActor, accounts: Accounts):
    """The logged-in user's own account."""
    return accounts.get_account(actor)
