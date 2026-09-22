from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class AuthStatus:
    """
    Describes the current authorization state of an integration.
    """

    provider: str
    authorized: bool
    status: str
    message: str | None = None


class AuthProvider(ABC):
    """
    Base contract for provider authentication.

    Authentication implementations must not expose secrets through
    application responses, logs, or error messages.
    """

    provider_name: str

    @abstractmethod
    async def get_auth_status(self) -> AuthStatus:
        """
        Return the current authorization state.
        """

    @abstractmethod
    async def get_access_token(self) -> str | None:
        """
        Return a usable access token when available.

        Implementations should return None when authorization is
        unavailable rather than exposing credentials or raising
        unnecessary errors.
        """

    @abstractmethod
    async def revoke(self) -> None:
        """
        Revoke or invalidate the provider authorization when
        supported by the provider.
        """