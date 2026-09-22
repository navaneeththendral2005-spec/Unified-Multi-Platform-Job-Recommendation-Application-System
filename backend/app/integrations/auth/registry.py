from app.integrations.auth.base import (
    AuthProvider,
    AuthStatus,
)


class AuthProviderRegistry:
    """
    Central registry for provider authentication implementations.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AuthProvider] = {}

    def register(
        self,
        provider: AuthProvider,
    ) -> None:
        name = provider.provider_name.strip().lower()

        if not name:
            raise ValueError(
                "Authentication provider name cannot be empty."
            )

        if name in self._providers:
            raise ValueError(
                f"Authentication provider '{name}' "
                "is already registered."
            )

        self._providers[name] = provider

    def register_all(
        self,
        providers: list[AuthProvider],
    ) -> None:
        """
        Register multiple authentication providers.
        """

        for provider in providers:
            self.register(provider)

    def get(
        self,
        provider_name: str,
    ) -> AuthProvider | None:
        return self._providers.get(
            provider_name.strip().lower()
        )

    def has(
        self,
        provider_name: str,
    ) -> bool:
        return (
            provider_name.strip().lower()
            in self._providers
        )

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    async def get_status(
        self,
        provider_name: str,
    ) -> AuthStatus:
        """
        Return authorization status for one provider.
        """

        provider = self.get(provider_name)

        if provider is None:
            raise ValueError(
                f"Authentication provider '{provider_name}' "
                "is not registered."
            )

        return await provider.get_auth_status()

    async def get_all_statuses(self) -> list[AuthStatus]:
        """
        Return authorization status for every registered provider.
        """

        statuses: list[AuthStatus] = []

        for provider in self._providers.values():
            statuses.append(
                await provider.get_auth_status()
            )

        return statuses


auth_provider_registry = AuthProviderRegistry()