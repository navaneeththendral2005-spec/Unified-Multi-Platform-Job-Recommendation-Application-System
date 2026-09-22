from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from app.integrations.auth.provider_configs import (
    get_provider_auth_config,
)
from app.integrations.auth.provider_credentials import (
    ProviderCredentials,
    load_provider_credentials,
)


class ProviderConfigurationStatus(str, Enum):
    """
    Configuration state of an external provider.

    This describes application-level configuration only.
    It does not claim that the provider has granted API access.
    """

    CONFIGURED = "CONFIGURED"
    PARTIALLY_CONFIGURED = "PARTIALLY_CONFIGURED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNKNOWN_PROVIDER = "UNKNOWN_PROVIDER"


@dataclass(frozen=True, slots=True)
class ProviderOnboardingMetadata:
    """
    User-facing onboarding information for one provider.

    This describes what the system currently knows about the
    provider integration without exposing credentials or inventing
    unsupported credential requirements.
    """

    provider_name: str
    display_name: str
    auth_type: str
    description: str

    required_environment_variables: tuple[str, ...]
    setup_steps: tuple[str, ...]

    credentials_required: bool
    authorization_required: bool

    notes: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderConfiguration:
    """
    Runtime configuration information for one provider.
    """

    provider_name: str
    status: ProviderConfigurationStatus
    credentials: ProviderCredentials
    required_environment_variables: tuple[str, ...]
    missing_environment_variables: tuple[str, ...]
    message: str

    @property
    def configured(self) -> bool:
        return (
            self.status
            == ProviderConfigurationStatus.CONFIGURED
        )

    @property
    def partially_configured(self) -> bool:
        return (
            self.status
            == ProviderConfigurationStatus.PARTIALLY_CONFIGURED
        )


# ------------------------------------------------------------------
# Provider environment configuration
# ------------------------------------------------------------------

PROVIDER_ENVIRONMENT_REQUIREMENTS: dict[
    str,
    tuple[str, ...],
] = {
    # LinkedIn OAuth is implemented in our project.
    "linkedin": (
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_REDIRECT_URI",
    ),

    # These remain intentionally unspecified until the deployment
    # has an authorized integration and its actual credential
    # contract is known.
    "naukri": (),
    "internshala": (),
    "indeed": (),
    "wellfound": (),
}


# ------------------------------------------------------------------
# Provider onboarding metadata
# ------------------------------------------------------------------

PROVIDER_ONBOARDING_METADATA: dict[
    str,
    ProviderOnboardingMetadata,
] = {
    "linkedin": ProviderOnboardingMetadata(
        provider_name="linkedin",
        display_name="LinkedIn",
        auth_type="OAUTH2",
        description=(
            "Connect a LinkedIn application using OAuth 2.0. "
            "The deployment must provide its own LinkedIn "
            "application credentials."
        ),
        required_environment_variables=(
            "LINKEDIN_CLIENT_ID",
            "LINKEDIN_CLIENT_SECRET",
            "LINKEDIN_REDIRECT_URI",
        ),
        setup_steps=(
            "Create or use an authorized LinkedIn developer application.",
            "Add the application's Client ID to the environment.",
            "Add the application's Client Secret to the environment.",
            "Configure the registered OAuth Redirect URI.",
            "Start the application and complete LinkedIn authorization.",
        ),
        credentials_required=True,
        authorization_required=True,
        notes=(
            "OAuth authorization is user-specific. "
            "Credentials belong to the deployment operator."
        ),
    ),

    "naukri": ProviderOnboardingMetadata(
        provider_name="naukri",
        display_name="Naukri",
        auth_type="PROVIDER_AUTH",
        description=(
            "Naukri integration requires an authorized provider "
            "integration and its corresponding credentials."
        ),
        required_environment_variables=(),
        setup_steps=(
            "Obtain authorized Naukri integration access.",
            "Configure the credentials supplied for that integration.",
            "Restart the application and run the provider health check.",
        ),
        credentials_required=True,
        authorization_required=True,
        notes=(
            "The exact credential contract is intentionally not "
            "hard-coded until authorized integration requirements "
            "are established."
        ),
    ),

    "internshala": ProviderOnboardingMetadata(
        provider_name="internshala",
        display_name="Internshala",
        auth_type="PROVIDER_AUTH",
        description=(
            "Internshala integration requires an authorized "
            "provider integration and its corresponding credentials."
        ),
        required_environment_variables=(),
        setup_steps=(
            "Obtain authorized Internshala integration access.",
            "Configure the credentials supplied for that integration.",
            "Restart the application and run the provider health check.",
        ),
        credentials_required=True,
        authorization_required=True,
        notes=(
            "The exact credential contract is intentionally not "
            "hard-coded until authorized integration requirements "
            "are established."
        ),
    ),

    "indeed": ProviderOnboardingMetadata(
        provider_name="indeed",
        display_name="Indeed",
        auth_type="PROVIDER_AUTH",
        description=(
            "Indeed integration requires an authorized partner or "
            "provider integration and its corresponding credentials."
        ),
        required_environment_variables=(),
        setup_steps=(
            "Obtain authorized Indeed integration access.",
            "Configure the credentials supplied for that integration.",
            "Restart the application and run the provider health check.",
        ),
        credentials_required=True,
        authorization_required=True,
        notes=(
            "The exact credential contract depends on the authorized "
            "Indeed integration available to the deployment."
        ),
    ),

    "wellfound": ProviderOnboardingMetadata(
        provider_name="wellfound",
        display_name="Wellfound",
        auth_type="PROVIDER_AUTH",
        description=(
            "Wellfound integration requires an authorized provider "
            "integration and its corresponding credentials."
        ),
        required_environment_variables=(),
        setup_steps=(
            "Obtain authorized Wellfound integration access.",
            "Configure the credentials supplied for that integration.",
            "Restart the application and run the provider health check.",
        ),
        credentials_required=True,
        authorization_required=True,
        notes=(
            "The exact credential contract is intentionally not "
            "hard-coded until authorized integration requirements "
            "are established."
        ),
    ),
}


class ProviderConfigurationManager:
    """
    Central manager for external provider configuration.

    Responsibilities:
    - determine whether a provider is known
    - inspect environment configuration
    - detect missing credentials
    - expose safe configuration status
    - expose provider onboarding metadata
    - never expose secret values
    """

    def __init__(self) -> None:
        self._requirements = PROVIDER_ENVIRONMENT_REQUIREMENTS
        self._onboarding = PROVIDER_ONBOARDING_METADATA

    # ------------------------------------------------------------------
    # Provider discovery
    # ------------------------------------------------------------------

    def list_providers(self) -> list[str]:
        return list(self._requirements.keys())

    # ------------------------------------------------------------------
    # Onboarding metadata
    # ------------------------------------------------------------------

    def get_onboarding_metadata(
        self,
        provider_name: str,
    ) -> ProviderOnboardingMetadata | None:
        """
        Return onboarding metadata for one provider.
        """

        normalized_name = (
            provider_name.strip().lower()
        )

        return self._onboarding.get(
            normalized_name
        )

    def list_onboarding_metadata(
        self,
    ) -> list[ProviderOnboardingMetadata]:
        """
        Return onboarding metadata for every registered provider.
        """

        return [
            self._onboarding[provider_name]
            for provider_name in self.list_providers()
        ]

    # ------------------------------------------------------------------
    # Environment helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_present(
        environment_variable: str,
    ) -> bool:
        value = os.getenv(
            environment_variable
        )

        return bool(
            value
            and value.strip()
        )

    # ------------------------------------------------------------------
    # Configuration inspection
    # ------------------------------------------------------------------

    def inspect(
        self,
        provider_name: str,
    ) -> ProviderConfiguration:
        normalized_name = (
            provider_name.strip().lower()
        )

        requirements = self._requirements.get(
            normalized_name
        )

        if requirements is None:
            credentials = load_provider_credentials(
                normalized_name
            )

            return ProviderConfiguration(
                provider_name=normalized_name,
                status=(
                    ProviderConfigurationStatus
                    .UNKNOWN_PROVIDER
                ),
                credentials=credentials,
                required_environment_variables=(),
                missing_environment_variables=(),
                message=(
                    "Provider is not registered in the "
                    "central configuration manager."
                ),
            )

        # --------------------------------------------------------------
        # Authentication configuration
        # --------------------------------------------------------------

        auth_config = get_provider_auth_config(
            normalized_name
        )

        if auth_config is None:
            credentials = load_provider_credentials(
                normalized_name
            )

            return ProviderConfiguration(
                provider_name=normalized_name,
                status=(
                    ProviderConfigurationStatus
                    .UNKNOWN_PROVIDER
                ),
                credentials=credentials,
                required_environment_variables=requirements,
                missing_environment_variables=requirements,
                message=(
                    "Provider authentication configuration "
                    "has not been registered."
                ),
            )

        credentials = load_provider_credentials(
            normalized_name
        )

        # --------------------------------------------------------------
        # Providers without a verified credential contract
        # --------------------------------------------------------------

        if not requirements:
            return ProviderConfiguration(
                provider_name=normalized_name,
                status=(
                    ProviderConfigurationStatus
                    .NOT_CONFIGURED
                ),
                credentials=credentials,
                required_environment_variables=(),
                missing_environment_variables=(),
                message=(
                    "Provider-specific authorized credentials "
                    "have not been configured yet."
                ),
            )

        # --------------------------------------------------------------
        # Required environment variables
        # --------------------------------------------------------------

        missing = tuple(
            variable
            for variable in requirements
            if not self._is_present(variable)
        )

        # --------------------------------------------------------------
        # Fully configured
        # --------------------------------------------------------------

        if not missing:
            return ProviderConfiguration(
                provider_name=normalized_name,
                status=(
                    ProviderConfigurationStatus
                    .CONFIGURED
                ),
                credentials=credentials,
                required_environment_variables=requirements,
                missing_environment_variables=(),
                message=(
                    "Required provider configuration is present."
                ),
            )

        # --------------------------------------------------------------
        # Partially configured
        # --------------------------------------------------------------

        configured_count = (
            len(requirements)
            - len(missing)
        )

        if configured_count > 0:
            configuration_status = (
                ProviderConfigurationStatus
                .PARTIALLY_CONFIGURED
            )

            message = (
                "Provider configuration is incomplete."
            )

        # --------------------------------------------------------------
        # Not configured
        # --------------------------------------------------------------

        else:
            configuration_status = (
                ProviderConfigurationStatus
                .NOT_CONFIGURED
            )

            message = (
                "Required provider configuration is missing."
            )

        return ProviderConfiguration(
            provider_name=normalized_name,
            status=configuration_status,
            credentials=credentials,
            required_environment_variables=requirements,
            missing_environment_variables=missing,
            message=message,
        )

    # ------------------------------------------------------------------
    # All providers
    # ------------------------------------------------------------------

    def inspect_all(
        self,
    ) -> list[ProviderConfiguration]:
        return [
            self.inspect(provider_name)
            for provider_name in self.list_providers()
        ]

    # ------------------------------------------------------------------
    # Safe configuration API representation
    # ------------------------------------------------------------------

    def to_public_dict(
        self,
        configuration: ProviderConfiguration,
    ) -> dict:
        """
        Return configuration information safe for API responses.

        Secret values are NEVER returned.
        """

        metadata = self.get_onboarding_metadata(
            configuration.provider_name
        )

        return {
            "provider": configuration.provider_name,
            "status": configuration.status.value,
            "configured": configuration.configured,
            "partially_configured": (
                configuration.partially_configured
            ),
            "required_environment_variables": list(
                configuration.required_environment_variables
            ),
            "missing_environment_variables": list(
                configuration.missing_environment_variables
            ),
            "message": configuration.message,

            # ----------------------------------------------------------
            # Onboarding information
            # ----------------------------------------------------------

            "onboarding": (
                self.onboarding_to_public_dict(
                    metadata
                )
                if metadata
                else None
            ),
        }

    # ------------------------------------------------------------------
    # Safe onboarding API representation
    # ------------------------------------------------------------------

    @staticmethod
    def onboarding_to_public_dict(
        metadata: ProviderOnboardingMetadata,
    ) -> dict:
        """
        Return onboarding information safe for API responses.

        No secret values are included.
        """

        return {
            "provider": metadata.provider_name,
            "display_name": metadata.display_name,
            "auth_type": metadata.auth_type,
            "description": metadata.description,
            "required_environment_variables": list(
                metadata.required_environment_variables
            ),
            "setup_steps": list(
                metadata.setup_steps
            ),
            "credentials_required": (
                metadata.credentials_required
            ),
            "authorization_required": (
                metadata.authorization_required
            ),
            "notes": metadata.notes,
        }


provider_configuration_manager = (
    ProviderConfigurationManager()
)