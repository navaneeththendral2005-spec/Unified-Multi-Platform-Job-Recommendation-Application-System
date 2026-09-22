from app.services.provider_credential_validation_service import (
    ProviderCredentialValidationService,
)


def test_provider_validation_service_lists_all_providers():
    service = ProviderCredentialValidationService()

    providers = service.list_providers()

    assert providers == [
        "linkedin",
        "naukri",
        "internshala",
        "indeed",
        "wellfound",
    ]


def test_unknown_provider_is_rejected():
    service = ProviderCredentialValidationService()

    result = service.validate("does-not-exist")

    assert result.status == "UNKNOWN_PROVIDER"
    assert result.valid is False
    assert result.configured is False


def test_unconfigured_linkedin_reports_missing_environment_variables(
    monkeypatch,
):
    monkeypatch.delenv("LINKEDIN_CLIENT_ID", raising=False)
    monkeypatch.delenv("LINKEDIN_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("LINKEDIN_REDIRECT_URI", raising=False)

    service = ProviderCredentialValidationService()

    result = service.validate("linkedin")

    assert result.status == "INCOMPLETE"
    assert result.valid is False

    assert "LINKEDIN_CLIENT_ID" in result.missing
    assert "LINKEDIN_CLIENT_SECRET" in result.missing
    assert "LINKEDIN_REDIRECT_URI" in result.missing


def test_linkedin_configuration_is_not_marked_remote_authorized(
    monkeypatch,
):
    monkeypatch.setenv(
        "LINKEDIN_CLIENT_ID",
        "test-client-id",
    )
    monkeypatch.setenv(
        "LINKEDIN_CLIENT_SECRET",
        "test-client-secret",
    )
    monkeypatch.setenv(
        "LINKEDIN_REDIRECT_URI",
        "https://example.com/auth/linkedin/callback",
    )

    service = ProviderCredentialValidationService()

    result = service.validate("linkedin")

    assert result.status == "CONFIGURED"
    assert result.configured is True
    assert result.valid is True

    # Local configuration does not equal remote authorization.
    assert "authorization" in result.message.lower()


def test_invalid_linkedin_redirect_uri_is_detected(
    monkeypatch,
):
    monkeypatch.setenv(
        "LINKEDIN_CLIENT_ID",
        "test-client-id",
    )
    monkeypatch.setenv(
        "LINKEDIN_CLIENT_SECRET",
        "test-client-secret",
    )
    monkeypatch.setenv(
        "LINKEDIN_REDIRECT_URI",
        "not-a-valid-url",
    )

    service = ProviderCredentialValidationService()

    result = service.validate("linkedin")

    assert result.status == "INVALID_CONFIGURATION"
    assert result.valid is False
    assert result.issues