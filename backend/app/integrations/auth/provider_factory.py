from app.integrations.auth.base import (
    AuthProvider,
    AuthStatus,
)
from app.integrations.auth.oauth2 import OAuth2AuthProvider
from app.integrations.auth.provider_configs import (
    ProviderAuthConfig,
    get_provider_auth_config,
)
from app.integrations.auth.provider_credentials import (
    load_provider_credentials,
)


class ProviderSpecificAuthProvider(AuthProvider):
    """
    Authentication boundary for providers whose exact
    authentication mechanism has not yet been established.

    This implementation intentionally does not guess or invent
    provider authentication behavior.
    """

    def __init__(
        self,
        config: ProviderAuthConfig,
    ) -> None:
        self.provider_name = config.provider_name
        self.config = config

    async def get_auth_status(self) -> AuthStatus:
        return AuthStatus(
            provider=self.provider_name,
            authorized=False,
            status="AUTHORIZATION_REQUIRED",
            message=(
                "Provider-specific authorization is required "
                "before this integration can be activated."
            ),
        )

    async def get_access_token(self) -> str | None:
        return None

    async def revoke(self) -> None:
        return None


def build_auth_provider(
    provider_name: str,
) -> AuthProvider:
    """
    Build the appropriate authentication provider from the
    centralized provider configuration.

    No credentials are stored in this factory.
    """

    normalized_name = provider_name.strip().lower()

    config = get_provider_auth_config(normalized_name)

    if config is None:
        raise ValueError(
            f"No authentication configuration exists for "
            f"provider '{normalized_name}'."
        )

    if config.auth_type == "OAUTH2":
        credentials = load_provider_credentials(
            normalized_name
        )

        return OAuth2AuthProvider(
            provider_name=normalized_name,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
        )

    return ProviderSpecificAuthProvider(config)


def build_all_auth_providers() -> list[AuthProvider]:
    """
    Build authentication providers for every configured source.
    """

    from app.integrations.auth.provider_configs import (
        list_provider_auth_configs,
    )

    return [
        build_auth_provider(config.provider_name)
        for config in list_provider_auth_configs()
    ]