from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderAuthConfig:
    """
    Static authentication requirements for an external provider.

    This describes how authentication is expected to work; it does
    not contain credentials or perform authentication itself.
    """

    provider_name: str
    auth_type: str
    requires_client_id: bool = False
    requires_client_secret: bool = False
    requires_api_key: bool = False
    supports_refresh_token: bool = False
    supports_oauth: bool = False
    notes: str | None = None


PROVIDER_AUTH_CONFIGS: dict[str, ProviderAuthConfig] = {
    "linkedin": ProviderAuthConfig(
        provider_name="linkedin",
        auth_type="OAUTH2",
        requires_client_id=True,
        requires_client_secret=True,
        supports_oauth=True,
        supports_refresh_token=True,
        notes=(
            "OAuth-based authorization. Exact scopes and approved "
            "products depend on the LinkedIn integration."
        ),
    ),
    "naukri": ProviderAuthConfig(
        provider_name="naukri",
        auth_type="PROVIDER_AUTH",
        notes=(
            "Provider-specific authorization requirements must be "
            "configured after an approved integration is available."
        ),
    ),
    "internshala": ProviderAuthConfig(
        provider_name="internshala",
        auth_type="PROVIDER_AUTH",
        notes=(
            "Provider-specific authorization requirements must be "
            "configured after an approved integration is available."
        ),
    ),
    "indeed": ProviderAuthConfig(
        provider_name="indeed",
        auth_type="PROVIDER_AUTH",
        notes=(
            "Provider-specific authorization requirements must be "
            "configured after an approved integration is available."
        ),
    ),
    "wellfound": ProviderAuthConfig(
        provider_name="wellfound",
        auth_type="PROVIDER_AUTH",
        notes=(
            "Provider-specific authorization requirements must be "
            "configured after an approved integration is available."
        ),
    ),
}


def get_provider_auth_config(
    provider_name: str,
) -> ProviderAuthConfig | None:
    """
    Return authentication configuration for a provider.
    """

    return PROVIDER_AUTH_CONFIGS.get(
        provider_name.strip().lower()
    )


def list_provider_auth_configs() -> list[ProviderAuthConfig]:
    """
    Return all configured provider authentication definitions.
    """

    return list(PROVIDER_AUTH_CONFIGS.values())