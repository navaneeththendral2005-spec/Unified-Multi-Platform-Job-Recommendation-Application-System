"""Safe provider capability inspection and enforcement helpers."""
from __future__ import annotations

from app.integrations.job_sources.capabilities import (
    CapabilityStatus,
    JobSourceCapability,
    get_provider_capabilities,
)


def capability_status(provider_name: str, capability: JobSourceCapability) -> CapabilityStatus:
    for item in get_provider_capabilities(provider_name):
        if item.capability == capability:
            return item.status
    return CapabilityStatus.NOT_AVAILABLE


def is_operational(provider_name: str, capability: JobSourceCapability) -> bool:
    return capability_status(provider_name, capability) == CapabilityStatus.SUPPORTED


def public_capability_report(provider_name: str) -> dict:
    capabilities = get_provider_capabilities(provider_name)
    return {
        "provider": provider_name.strip().lower(),
        "capabilities": [
            {
                "capability": item.capability.value,
                "status": item.status.value,
                "description": item.description,
            }
            for item in capabilities
        ],
    }
