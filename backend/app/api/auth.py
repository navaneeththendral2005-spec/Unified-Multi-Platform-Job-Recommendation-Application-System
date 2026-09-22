from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.schemas.user import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse,
)

from app.services.auth_service import (
    get_user_by_email,
    create_user,
    verify_password,
)

from app.services.security import (
    create_access_token,
    verify_access_token,
)

from app.integrations.auth.linkedin_oauth import (
    LinkedInOAuthError,
    LinkedInOAuthService,
)

from app.integrations.auth.provider_readiness import (
    provider_readiness_service,
)

from app.models.oauth_connection import OAuthConnection


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ----------------------------------------------------------------------
# Existing application authentication
# ----------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(
        db,
        user.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    new_user = create_user(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password,
    )

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(
        db,
        user.email,
    )

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    password_valid = verify_password(
        user.password,
        existing_user.password_hash,
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={
            "sub": str(existing_user.id),
            "email": existing_user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_current_user(
    user_id: int = Depends(verify_access_token),
):
    return {
        "message": "You are authenticated!",
        "user": {
            "id": user_id,
        },
    }


# ----------------------------------------------------------------------
# LinkedIn OAuth
# ----------------------------------------------------------------------


@router.get("/linkedin/connect")
def connect_linkedin(
    user_id: int = Depends(verify_access_token),
    db: Session = Depends(get_db),
):
    """
    Start the LinkedIn OAuth authorization flow.

    The user's application JWT authenticates the request.

    A separate OAuth state identifies the user when LinkedIn
    redirects back to the callback.
    """

    service = LinkedInOAuthService(db)

    try:
        authorization_url = (
            service.create_authorization_url(
                user_id=user_id,
            )
        )

    except LinkedInOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "provider": "linkedin",
        "authorization_url": authorization_url,
        "message": (
            "Open authorization_url in your browser "
            "to connect LinkedIn."
        ),
    }


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Handle LinkedIn's OAuth callback.

    LinkedIn redirects here after the user authorizes or
    denies the requested permissions.
    """

    if error:
        detail = (
            f"LinkedIn authorization failed: "
            f"{error_description or error}"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn authorization code is missing.",
        )

    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state is missing.",
        )

    service = LinkedInOAuthService(db)

    try:
        connection = await service.handle_callback(
            code=code,
            state=state,
        )

    except LinkedInOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "provider": connection.provider,
        "user_id": connection.user_id,
        "connected": connection.is_active,
        "scopes": connection.scopes,
        "token_expires_at": connection.token_expires_at,
        "message": (
            "LinkedIn account connected successfully."
        ),
    }


@router.get("/linkedin/status")
def linkedin_status(
    user_id: int = Depends(verify_access_token),
    db: Session = Depends(get_db),
):
    """
    Return the LinkedIn connection status for the current user.

    No access or refresh token is ever returned.
    """

    connection = db.scalar(
        select(OAuthConnection).where(
            OAuthConnection.user_id == user_id,
            OAuthConnection.provider == "linkedin",
        )
    )

    if connection is None:
        return {
            "provider": "linkedin",
            "connected": False,
            "active": False,
            "scopes": None,
            "token_expires_at": None,
        }

    return {
        "provider": "linkedin",
        "connected": True,
        "active": connection.is_active,
        "scopes": connection.scopes,
        "token_expires_at": connection.token_expires_at,
    }


# ----------------------------------------------------------------------
# Common provider readiness
# ----------------------------------------------------------------------


@router.get("/providers/status")
def provider_status(
    user_id: int = Depends(verify_access_token),
    db: Session = Depends(get_db),
):
    """
    Return provider configuration, authentication, and readiness
    status for the currently authenticated user.

    Provider credentials and OAuth tokens are never returned.
    """

    providers = []

    for provider_name in (
        provider_readiness_service.list_providers()
    ):
        readiness = (
            provider_readiness_service.inspect_for_user(
                db=db,
                user_id=user_id,
                provider_name=provider_name,
            )
        )

        providers.append(
            provider_readiness_service.to_public_dict(
                readiness
            )
        )

    return {
        "user_id": user_id,
        "providers": providers,
    }