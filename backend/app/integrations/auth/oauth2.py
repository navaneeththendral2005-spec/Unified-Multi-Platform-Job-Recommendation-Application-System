from dataclasses import dataclass
from datetime import datetime, timezone

from app.integrations.auth.base import AuthProvider, AuthStatus


@dataclass(slots=True)
class OAuthToken:
    """
    In-memory representation of an OAuth access token.

    Tokens should not be persisted here. A dedicated secure token
    store can be introduced when real OAuth integrations are added.
    """

    access_token: str
    expires_at: datetime | None = None
    refresh_token: str | None = None
    token_type: str = "Bearer"

    def is_expired(self) -> bool:
        """
        Determine whether the access token has expired.
        """

        if self.expires_at is None:
            return False

        return datetime.now(timezone.utc) >= self.expires_at


class OAuth2AuthProvider(AuthProvider):
    """
    Generic OAuth 2.0 authentication boundary.

    Provider-specific authorization URLs, scopes, token endpoints,
    and refresh behavior belong in provider-specific implementations.
    """

    def __init__(
        self,
        *,
        provider_name: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        scopes: list[str] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or []
        self._token: OAuthToken | None = None

    async def get_auth_status(self) -> AuthStatus:
        """
        Return the current OAuth authorization state.
        """

        if not self.client_id or not self.client_secret:
            return AuthStatus(
                provider=self.provider_name,
                authorized=False,
                status="CREDENTIALS_NOT_CONFIGURED",
                message=(
                    "OAuth client credentials are not configured."
                ),
            )

        if self._token is None:
            return AuthStatus(
                provider=self.provider_name,
                authorized=False,
                status="AUTHORIZATION_REQUIRED",
                message=(
                    "OAuth authorization has not been completed."
                ),
            )

        if self._token.is_expired():
            return AuthStatus(
                provider=self.provider_name,
                authorized=False,
                status="TOKEN_EXPIRED",
                message="The OAuth access token has expired.",
            )

        return AuthStatus(
            provider=self.provider_name,
            authorized=True,
            status="AUTHORIZED",
        )

    async def get_access_token(self) -> str | None:
        """
        Return the currently available access token.

        Token acquisition and refresh will be implemented by
        provider-specific OAuth clients.
        """

        if self._token is None:
            return None

        if self._token.is_expired():
            return None

        return self._token.access_token

    async def revoke(self) -> None:
        """
        Clear the in-memory authorization state.

        Provider-specific token revocation can be implemented later.
        """

        self._token = None

    def set_token(
        self,
        token: OAuthToken,
    ) -> None:
        """
        Store an OAuth token in memory for the current process.

        This method is intended for the authentication implementation,
        not direct use by API endpoints.
        """

        self._token = token