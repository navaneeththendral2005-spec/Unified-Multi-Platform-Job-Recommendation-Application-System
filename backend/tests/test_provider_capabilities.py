from app.integrations.job_sources.capabilities import JobSourceCapability
from app.services.provider_capability_service import (
    capability_status,
    is_operational,
)


def test_external_apply_is_operational_when_declared_supported():
    assert is_operational("linkedin", JobSourceCapability.EXTERNAL_APPLY)


def test_direct_apply_requires_provider_access_when_declared():
    status = capability_status("linkedin", JobSourceCapability.APPLY)
    assert status.value == "REQUIRES_PARTNER_ACCESS"
