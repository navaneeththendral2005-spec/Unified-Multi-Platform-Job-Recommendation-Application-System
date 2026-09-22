import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.auth.token_vault import token_vault
from app.models.oauth_connection import OAuthConnection
from app.models.oauth_state import OAuthState
from app.utils.time import utc_now


# Load backend/.env when this module is imported directly.
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


LINKEDIN_AUTHORIZATION_URL = (
    "https://www.linkedin.com/oauth/v2/authorization"
)

LINKEDIN_TOKEN_URL = (
    "https://www.linkedin.com/oauth/v2/accessToken"
)

LINKEDIN_PROVIDER = "linkedin"

OAUTH_STATE_EXPIRY_MINUTES = 10


class LinkedInOAuthError(Exception):
    """Raised when a LinkedIn OAuth operation fails."""


class LinkedInOAuthService:
    """Handles LinkedIn OAuth authorization and token persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @staticmethod
    def _get_config() -> dict[str, str]:
        client_id = os.getenv("LINKEDIN_CLIENT_ID")
        client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")

        if not client_id:
            raise LinkedInOAuthError(
                "LINKEDIN_CLIENT_ID is not configured."
            )

        if not client_secret:
            raise LinkedInOAuthError(
                "LINKEDIN_CLIENT_SECRET is not configured."
            )

        if not redirect_uri:
            raise LinkedInOAuthError(
                "LINKEDIN_REDIRECT_URI is not configured."
            )

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

    @staticmethod
    def _get_scopes() -> str:
        return os.getenv(
            "LINKEDIN_OAUTH_SCOPES",
            "openid profile email",
        )

    # ------------------------------------------------------------------
    # Authorization URL
    # ------------------------------------------------------------------

    def create_authorization_url(self, user_id: int) -> str:
        """
        Create and persist a secure OAuth state, then return
        the LinkedIn authorization URL.
        """

        config = self._get_config()

        state_value = secrets.token_urlsafe(32)

        oauth_state = OAuthState(
            state=state_value,
            user_id=user_id,
            provider=LINKEDIN_PROVIDER,
            expires_at=(
                utc_now()
                + timedelta(minutes=OAUTH_STATE_EXPIRY_MINUTES)
            ),
        )

        self.db.add(oauth_state)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        params = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "state": state_value,
            "scope": self._get_scopes(),
        }

        return (
            f"{LINKEDIN_AUTHORIZATION_URL}"
            f"?{urlencode(params)}"
        )

    # ------------------------------------------------------------------
    # OAuth callback
    # ------------------------------------------------------------------

    async def handle_callback(
        self,
        *,
        code: str,
        state: str,
    ) -> OAuthConnection:
        """
        Validate the OAuth state, exchange the authorization code
        for tokens, encrypt the tokens, and persist the connection.

        The OAuth state is only marked as used after successful
        token exchange and database persistence.
        """

        if not code:
            raise LinkedInOAuthError(
                "LinkedIn authorization code is missing."
            )

        if not state:
            raise LinkedInOAuthError(
                "OAuth state is missing."
            )

        config = self._get_config()

        oauth_state = self.db.scalar(
            select(OAuthState).where(
                OAuthState.state == state,
                OAuthState.provider == LINKEDIN_PROVIDER,
                OAuthState.used_at.is_(None),
            )
        )

        if oauth_state is None:
            raise LinkedInOAuthError(
                "Invalid or already-used OAuth state."
            )

        if oauth_state.expires_at < utc_now():
            raise LinkedInOAuthError(
                "OAuth state has expired."
            )

        token_data = await self._exchange_code(
            code=code,
            config=config,
        )

        access_token = token_data.get("access_token")

        if not access_token:
            raise LinkedInOAuthError(
                "LinkedIn did not return an access token."
            )

        refresh_token = token_data.get("refresh_token")

        expires_in = token_data.get("expires_in")

        token_expires_at = None

        if expires_in is not None:
            try:
                token_expires_at = (
                    utc_now()
                    + timedelta(seconds=int(expires_in))
                )
            except (TypeError, ValueError) as exc:
                raise LinkedInOAuthError(
                    "LinkedIn returned an invalid token expiry."
                ) from exc

        scopes = token_data.get("scope")

        try:
            existing_connection = self.db.scalar(
                select(OAuthConnection).where(
                    OAuthConnection.user_id == oauth_state.user_id,
                    OAuthConnection.provider == LINKEDIN_PROVIDER,
                )
            )

            encrypted_access_token = token_vault.encrypt(
                access_token
            )

            encrypted_refresh_token = (
                token_vault.encrypt(refresh_token)
                if refresh_token
                else None
            )

            if existing_connection:
                connection = existing_connection

                connection.access_token_encrypted = (
                    encrypted_access_token
                )

                connection.refresh_token_encrypted = (
                    encrypted_refresh_token
                )

                connection.token_expires_at = (
                    token_expires_at
                )

                connection.scopes = scopes
                connection.is_active = True

            else:
                connection = OAuthConnection(
                    user_id=oauth_state.user_id,
                    provider=LINKEDIN_PROVIDER,
                    access_token_encrypted=encrypted_access_token,
                    refresh_token_encrypted=encrypted_refresh_token,
                    token_expires_at=token_expires_at,
                    scopes=scopes,
                    is_active=True,
                )

                self.db.add(connection)

            # Consume the state only after successful token exchange
            # and successful preparation of the OAuth connection.
            oauth_state.used_at = utc_now()

            self.db.commit()
            self.db.refresh(connection)

            return connection

        except Exception:
            self.db.rollback()
            raise

    # ------------------------------------------------------------------
    # Token exchange
    # ------------------------------------------------------------------

    async def _exchange_code(
        self,
        *,
        code: str,
        config: dict[str, str],
    ) -> dict:
        """
        Exchange a LinkedIn authorization code for OAuth tokens.
        """

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
        }

        try:
            async with httpx.AsyncClient(
                timeout=20.0
            ) as client:
                response = await client.post(
                    LINKEDIN_TOKEN_URL,
                    data=payload,
                    headers={
                        "Content-Type": (
                            "application/x-www-form-urlencoded"
                        )
                    },
                )
        except httpx.HTTPError as exc:
            raise LinkedInOAuthError(
                "Unable to communicate with LinkedIn "
                "during token exchange."
            ) from exc

        if response.is_error:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = {}

            error_description = (
                error_payload.get("error_description")
                or error_payload.get("error")
                or "Unknown LinkedIn OAuth error."
            )

            raise LinkedInOAuthError(
                f"LinkedIn token exchange failed: "
                f"{error_description}"
            )

        try:
            token_data = response.json()
        except ValueError as exc:
            raise LinkedInOAuthError(
                "LinkedIn returned an invalid token response."
            ) from exc

        if not isinstance(token_data, dict):
            raise LinkedInOAuthError(
                "LinkedIn returned an unexpected token response."
            )

        return token_data