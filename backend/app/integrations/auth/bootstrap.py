from app.integrations.auth.provider_factory import (
    build_all_auth_providers,
)
from app.integrations.auth.registry import (
    auth_provider_registry,
)


def register_auth_providers() -> None:
    """
    Register every configured provider authentication
    implementation exactly once.
    """

    if auth_provider_registry.list_providers():
        return

    providers = build_all_auth_providers()

    auth_provider_registry.register_all(providers)