def test_provider_status_does_not_expose_secret_values():
    from app.integrations.auth.provider_readiness import (
        provider_readiness_service,
    )

    readiness = provider_readiness_service.inspect("linkedin")

    payload = provider_readiness_service.to_public_dict(readiness)

    assert "client_id" not in payload
    assert "client_secret" not in payload
    assert "api_key" not in payload
    assert "api_secret" not in payload


def test_all_supported_providers_are_registered():
    from app.integrations.auth.provider_readiness import (
        provider_readiness_service,
    )

    assert provider_readiness_service.list_providers() == [
        "linkedin",
        "naukri",
        "internshala",
        "indeed",
        "wellfound",
    ]
