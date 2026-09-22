from app.integrations.job_sources.capabilities import (
    CapabilityStatus,
    JobSourceCapability,
    capabilities_to_public_dict,
    get_provider_capabilities,
)


def test_all_supported_providers_have_capability_metadata():
    expected = {"linkedin", "naukri", "internshala", "indeed", "wellfound"}
    actual = {"linkedin", "naukri", "internshala", "indeed", "wellfound"}
    assert actual == expected
    for provider in expected:
        capabilities = get_provider_capabilities(provider)
        assert capabilities
        assert all(item.capability for item in capabilities)


def test_capability_public_payload_is_secret_free():
    payload = capabilities_to_public_dict("linkedin")
    assert payload
    assert all(set(item) == {"capability", "status", "description"} for item in payload)
    assert any(item["capability"] == JobSourceCapability.OAUTH.value for item in payload)
    assert all(item["status"] in {status.value for status in CapabilityStatus} for item in payload)
    assert not any("secret" in str(item).lower() or "token" in str(item).lower() for item in payload)
