from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from app.integrations.auth.provider_configuration import (
    ProviderConfiguration,
    provider_configuration_manager,
)
from app.integrations.auth.provider_credentials import (
    ProviderCredentials,
    load_provider_credentials,
)


@dataclass(frozen=True, slots=True)
class CredentialValidationResult:
    provider: str
    status: str
    configured: bool
    valid: bool
    missing: tuple[str, ...]
    issues: tuple[str, ...]
    message: str


class ProviderCredentialValidationService:
    """
    Performs safe local validation of provider credentials/configuration.

    This service NEVER returns credential values and NEVER assumes that a
    non-empty secret proves that a remote provider integration is authorized.
    Remote authorization is verified separately by the provider adapter/OAuth
    flow.
    """

    def list_providers(self) -> list[str]:
        return provider_configuration_manager.list_providers()

    @staticmethod
    def _validate_redirect_uri(
        provider: str,
        credentials: ProviderCredentials,
        configuration: ProviderConfiguration,
    ) -> list[str]:
        issues: list[str] = []

        if provider != "linkedin":
            return issues

        # LinkedIn redirect URI is part of the provider configuration rather
        # than ProviderCredentials, so inspect the environment/configuration.
        if "LINKEDIN_REDIRECT_URI" in configuration.required_environment_variables:
            import os

            redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "").strip()

            if redirect_uri:
                parsed = urlparse(redirect_uri)

                if parsed.scheme not in {"http", "https"}:
                    issues.append(
                        "LINKEDIN_REDIRECT_URI must use http or https."
                    )

                if not parsed.netloc:
                    issues.append(
                        "LINKEDIN_REDIRECT_URI must contain a valid host."
                    )

        return issues

    def validate(self, provider_name: str) -> CredentialValidationResult:
        provider = provider_name.strip().lower()

        configuration = provider_configuration_manager.inspect(provider)

        if configuration.status.value == "UNKNOWN_PROVIDER":
            return CredentialValidationResult(
                provider=provider,
                status="UNKNOWN_PROVIDER",
                configured=False,
                valid=False,
                missing=(),
                issues=("Provider is not registered in the system.",),
                message="Unknown provider.",
            )

        credentials = load_provider_credentials(provider)

        missing = tuple(configuration.missing_environment_variables)
        issues: list[str] = []

        if missing:
            return CredentialValidationResult(
                provider=provider,
                status="INCOMPLETE",
                configured=False,
                valid=False,
                missing=missing,
                issues=(),
                message="Required provider configuration is incomplete.",
            )

        # A provider-specific integration contract may not yet be available.
        # In that case, do not pretend that credentials are remotely valid.
        if not configuration.required_environment_variables:
            if not credentials.configured:
                return CredentialValidationResult(
                    provider=provider,
                    status="NOT_CONFIGURED",
                    configured=False,
                    valid=False,
                    missing=(),
                    issues=(
                        "No authorized provider credential contract is "
                        "configured for this provider.",
                    ),
                    message=(
                        "Provider credentials cannot be validated until an "
                        "authorized integration contract is available."
                    ),
                )

            return CredentialValidationResult(
                provider=provider,
                status="CONFIGURED_UNVERIFIED",
                configured=True,
                valid=True,
                missing=(),
                issues=(
                    "Credentials are present but remote authorization has "
                    "not been verified by an approved provider integration.",
                ),
                message=(
                    "Credentials are configured locally. Remote validity "
                    "requires the authorized provider integration."
                ),
            )

        issues.extend(
            self._validate_redirect_uri(
                provider,
                credentials,
                configuration,
            )
        )

        if issues:
            return CredentialValidationResult(
                provider=provider,
                status="INVALID_CONFIGURATION",
                configured=True,
                valid=False,
                missing=(),
                issues=tuple(issues),
                message="Provider configuration contains invalid values.",
            )

        return CredentialValidationResult(
            provider=provider,
            status="CONFIGURED",
            configured=True,
            valid=True,
            missing=(),
            issues=(),
            message=(
                "Required provider configuration is present. "
                "Remote authorization must still be verified separately."
            ),
        )

    def validate_all(self) -> list[CredentialValidationResult]:
        return [
            self.validate(provider)
            for provider in self.list_providers()
        ]

    @staticmethod
    def to_public_dict(
        result: CredentialValidationResult,
    ) -> dict:
        return {
            "provider": result.provider,
            "status": result.status,
            "configured": result.configured,
            "valid": result.valid,
            "missing": list(result.missing),
            "issues": list(result.issues),
            "message": result.message,
        }


provider_credential_validation_service = (
    ProviderCredentialValidationService()
)