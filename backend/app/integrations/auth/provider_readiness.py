from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.auth.provider_configs import (
    ProviderAuthConfig,
    get_provider_auth_config,
    list_provider_auth_configs,
)
from app.integrations.auth.provider_credentials import (
    ProviderCredentials,
    load_provider_credentials,
)
from app.models.oauth_connection import OAuthConnection
from app.utils.time import utc_now


class ProviderAuthenticationStatus(str):
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    AUTHORIZED = "AUTHORIZED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"


class ProviderReadinessStatus(str):
    WAITING_FOR_CREDENTIALS = "WAITING_FOR_CREDENTIALS"
    WAITING_FOR_AUTHORIZATION = "WAITING_FOR_AUTHORIZATION"
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ProviderReadiness:
    """
    Unified runtime state for an external job provider.

    Combines:
    - provider authentication requirements
    - environment configuration
    - user-specific authorization
    - overall provider readiness
    """

    provider_name: str

    auth_config: ProviderAuthConfig | None
    credentials: ProviderCredentials

    configuration_status: str
    authentication_status: str
    readiness_status: str

    message: str

    @property
    def configured(self) -> bool:
        return self.configuration_status == "CONFIGURED"

    @property
    def authorized(self) -> bool:
        return (
            self.authentication_status
            == ProviderAuthenticationStatus.AUTHORIZED
        )

    @property
    def ready(self) -> bool:
        return (
            self.readiness_status
            == ProviderReadinessStatus.READY
        )


class ProviderReadinessService:
    """
    Central service for calculating provider readiness.

    This service does not perform OAuth itself.

    Provider-specific authentication implementations remain
    responsible for actually obtaining and maintaining access.
    """

    # ------------------------------------------------------------------
    # Provider discovery
    # ------------------------------------------------------------------

    def list_providers(self) -> list[str]:
        return [
            config.provider_name
            for config in list_provider_auth_configs()
        ]

    # ------------------------------------------------------------------
    # Configuration state
    # ------------------------------------------------------------------

    @staticmethod
    def _configuration_status(
        auth_config: ProviderAuthConfig,
        credentials: ProviderCredentials,
    ) -> str:
        """
        Determine whether the credentials required by the provider
        authentication configuration are present.
        """

        required_values: list[str | None] = []

        if auth_config.requires_client_id:
            required_values.append(
                credentials.client_id
            )

        if auth_config.requires_client_secret:
            required_values.append(
                credentials.client_secret
            )

        if auth_config.requires_api_key:
            required_values.append(
                credentials.api_key
            )

        # No concrete credential contract has been defined yet.
        if not required_values:
            return "NOT_CONFIGURED"

        if all(
            value and value.strip()
            for value in required_values
        ):
            return "CONFIGURED"

        if any(
            value and value.strip()
            for value in required_values
        ):
            return "PARTIALLY_CONFIGURED"

        return "NOT_CONFIGURED"

    # ------------------------------------------------------------------
    # Base provider readiness
    # ------------------------------------------------------------------

    def inspect(
        self,
        provider_name: str,
        *,
        authorized: bool = False,
        unavailable: bool = False,
    ) -> ProviderReadiness:
        """
        Inspect provider readiness without user-specific database
        authorization.

        This is useful for installation/global provider status.
        """

        normalized_name = provider_name.strip().lower()

        auth_config = get_provider_auth_config(
            normalized_name
        )

        credentials = load_provider_credentials(
            normalized_name
        )

        # --------------------------------------------------------------
        # Unknown provider
        # --------------------------------------------------------------

        if auth_config is None:
            return ProviderReadiness(
                provider_name=normalized_name,
                auth_config=None,
                credentials=credentials,
                configuration_status="NOT_CONFIGURED",
                authentication_status=(
                    ProviderAuthenticationStatus.NOT_AUTHORIZED
                ),
                readiness_status=(
                    ProviderReadinessStatus.UNAVAILABLE
                ),
                message=(
                    "Provider is not registered in the "
                    "authentication configuration."
                ),
            )

        configuration_status = (
            self._configuration_status(
                auth_config,
                credentials,
            )
        )

        # --------------------------------------------------------------
        # Provider unavailable
        # --------------------------------------------------------------

        if unavailable:
            return ProviderReadiness(
                provider_name=normalized_name,
                auth_config=auth_config,
                credentials=credentials,
                configuration_status=configuration_status,
                authentication_status=(
                    ProviderAuthenticationStatus.AUTHORIZATION_REQUIRED
                    if configuration_status == "CONFIGURED"
                    else ProviderAuthenticationStatus.NOT_AUTHORIZED
                ),
                readiness_status=(
                    ProviderReadinessStatus.UNAVAILABLE
                ),
                message=(
                    "Provider is currently unavailable."
                ),
            )

        # --------------------------------------------------------------
        # Credentials missing
        # --------------------------------------------------------------

        if configuration_status != "CONFIGURED":
            return ProviderReadiness(
                provider_name=normalized_name,
                auth_config=auth_config,
                credentials=credentials,
                configuration_status=configuration_status,
                authentication_status=(
                    ProviderAuthenticationStatus.NOT_AUTHORIZED
                ),
                readiness_status=(
                    ProviderReadinessStatus.WAITING_FOR_CREDENTIALS
                ),
                message=(
                    "Required provider credentials "
                    "have not been configured."
                ),
            )

        # --------------------------------------------------------------
        # Credentials configured but authorization not confirmed
        # --------------------------------------------------------------

        if not authorized:
            return ProviderReadiness(
                provider_name=normalized_name,
                auth_config=auth_config,
                credentials=credentials,
                configuration_status=configuration_status,
                authentication_status=(
                    ProviderAuthenticationStatus
                    .AUTHORIZATION_REQUIRED
                ),
                readiness_status=(
                    ProviderReadinessStatus.WAITING_FOR_AUTHORIZATION
                ),
                message=(
                    "Provider credentials are configured, "
                    "but authorization is required."
                ),
            )

        # --------------------------------------------------------------
        # Fully ready
        # --------------------------------------------------------------

        return ProviderReadiness(
            provider_name=normalized_name,
            auth_config=auth_config,
            credentials=credentials,
            configuration_status=configuration_status,
            authentication_status=(
                ProviderAuthenticationStatus.AUTHORIZED
            ),
            readiness_status=(
                ProviderReadinessStatus.READY
            ),
            message=(
                "Provider is configured and authorized."
            ),
        )

    # ------------------------------------------------------------------
    # User-specific provider readiness
    # ------------------------------------------------------------------

    def inspect_for_user(
        self,
        db: Session,
        user_id: int,
        provider_name: str,
    ) -> ProviderReadiness:
        """
        Calculate provider readiness for one authenticated user.

        Global configuration comes from environment variables.

        User-specific OAuth authorization comes from the user's
        OAuthConnection record.

        No OAuth tokens are returned.
        """

        normalized_name = provider_name.strip().lower()

        base_readiness = self.inspect(
            normalized_name,
            authorized=False,
        )

        # --------------------------------------------------------------
        # Provider is not configured
        # --------------------------------------------------------------

        if not base_readiness.configured:
            return base_readiness

        auth_config = base_readiness.auth_config

        # --------------------------------------------------------------
        # OAuth-based providers
        # --------------------------------------------------------------

        if auth_config and auth_config.supports_oauth:

            connection = db.scalar(
                select(OAuthConnection).where(
                    OAuthConnection.user_id == user_id,
                    OAuthConnection.provider == normalized_name,
                )
            )

            # No user OAuth connection.
            if connection is None:
                return base_readiness

            # Connection exists but was disabled.
            if not connection.is_active:
                return base_readiness

            # Token expiry.
            if (
                connection.token_expires_at is not None
                and connection.token_expires_at <= utc_now()
            ):
                return ProviderReadiness(
                    provider_name=normalized_name,
                    auth_config=auth_config,
                    credentials=base_readiness.credentials,
                    configuration_status=(
                        base_readiness.configuration_status
                    ),
                    authentication_status=(
                        ProviderAuthenticationStatus
                        .AUTHORIZATION_REQUIRED
                    ),
                    readiness_status=(
                        ProviderReadinessStatus
                        .WAITING_FOR_AUTHORIZATION
                    ),
                    message=(
                        "Provider authorization exists, "
                        "but the stored access token has expired."
                    ),
                )

            return self.inspect(
                normalized_name,
                authorized=True,
            )

        # --------------------------------------------------------------
        # Non-OAuth providers
        # --------------------------------------------------------------
        #
        # For API-key / partner-auth providers, credentials being
        # configured does not automatically prove that the provider
        # has granted usable access.
        #
        # The provider adapter will later confirm this through its
        # actual authorized API/partner integration.
        # --------------------------------------------------------------

        return base_readiness

    # ------------------------------------------------------------------
    # Inspect every provider
    # ------------------------------------------------------------------

    def inspect_all(
        self,
    ) -> list[ProviderReadiness]:
        return [
            self.inspect(provider_name)
            for provider_name in self.list_providers()
        ]

    # ------------------------------------------------------------------
    # Safe public representation
    # ------------------------------------------------------------------

    @staticmethod
    def to_public_dict(
        readiness: ProviderReadiness,
    ) -> dict:
        """
        Return provider readiness information safe for API output.

        Credential and token values are never exposed.
        """

        return {
            "provider": readiness.provider_name,
            "configuration": (
                readiness.configuration_status
            ),
            "authentication": (
                readiness.authentication_status
            ),
            "readiness": (
                readiness.readiness_status
            ),
            "configured": readiness.configured,
            "authorized": readiness.authorized,
            "ready": readiness.ready,
            "auth_type": (
                readiness.auth_config.auth_type
                if readiness.auth_config
                else None
            ),
            "message": readiness.message,
        }


provider_readiness_service = (
    ProviderReadinessService()
)