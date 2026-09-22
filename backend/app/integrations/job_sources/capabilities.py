from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    REQUIRES_AUTHORIZATION = "REQUIRES_AUTHORIZATION"
    REQUIRES_PARTNER_ACCESS = "REQUIRES_PARTNER_ACCESS"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class JobSourceCapability(str, Enum):
    SEARCH_JOBS = "SEARCH_JOBS"
    GET_JOB = "GET_JOB"
    GET_COMPANY = "GET_COMPANY"
    APPLY = "APPLY"
    GET_APPLICATION_STATUS = "GET_APPLICATION_STATUS"
    SYNC_APPLICATIONS = "SYNC_APPLICATIONS"
    OAUTH = "OAUTH"
    API_KEY = "API_KEY"
    PARTNER_ACCESS = "PARTNER_ACCESS"
    EXTERNAL_APPLY = "EXTERNAL_APPLY"


@dataclass(frozen=True, slots=True)
class ProviderCapability: 
    capability: JobSourceCapability
    status: CapabilityStatus
    description: str


PROVIDER_CAPABILITIES: dict[str, tuple[ProviderCapability, ...]] = {
    "linkedin": (
        ProviderCapability(JobSourceCapability.OAUTH, CapabilityStatus.SUPPORTED, "OAuth 2.0/OIDC authorization is implemented."),
        ProviderCapability(JobSourceCapability.SEARCH_JOBS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job discovery requires an approved LinkedIn product/integration."),
        ProviderCapability(JobSourceCapability.GET_JOB, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job retrieval depends on the approved LinkedIn integration."),
        ProviderCapability(JobSourceCapability.EXTERNAL_APPLY, CapabilityStatus.SUPPORTED, "Original job/application URLs can be surfaced when available."),
        ProviderCapability(JobSourceCapability.APPLY, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Direct application submission requires an approved LinkedIn application product."),
        ProviderCapability(JobSourceCapability.GET_APPLICATION_STATUS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Application status access depends on approved Talent capabilities."),
        ProviderCapability(JobSourceCapability.SYNC_APPLICATIONS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Application synchronization depends on approved provider access."),
        ProviderCapability(JobSourceCapability.PARTNER_ACCESS, CapabilityStatus.SUPPORTED, "The architecture supports partner-authorized integrations."),
    ),
    "naukri": (
        ProviderCapability(JobSourceCapability.SEARCH_JOBS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job discovery requires an authorized Naukri integration."),
        ProviderCapability(JobSourceCapability.GET_JOB, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job retrieval requires an authorized Naukri integration."),
        ProviderCapability(JobSourceCapability.EXTERNAL_APPLY, CapabilityStatus.SUPPORTED, "Original job/application URLs can be surfaced when available."),
        ProviderCapability(JobSourceCapability.PARTNER_ACCESS, CapabilityStatus.SUPPORTED, "The adapter supports provider-authorized integration contracts."),
    ),
    "internshala": (
        ProviderCapability(JobSourceCapability.SEARCH_JOBS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job discovery requires an authorized Internshala integration."),
        ProviderCapability(JobSourceCapability.GET_JOB, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job retrieval requires an authorized Internshala integration."),
        ProviderCapability(JobSourceCapability.EXTERNAL_APPLY, CapabilityStatus.SUPPORTED, "Original job/application URLs can be surfaced when available."),
        ProviderCapability(JobSourceCapability.PARTNER_ACCESS, CapabilityStatus.SUPPORTED, "The adapter supports provider-authorized integration contracts."),
    ),
    "indeed": (
        ProviderCapability(JobSourceCapability.SEARCH_JOBS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Indeed job discovery requires an approved Indeed integration/partner arrangement."),
        ProviderCapability(JobSourceCapability.GET_JOB, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job retrieval depends on the approved Indeed integration."),
        ProviderCapability(JobSourceCapability.EXTERNAL_APPLY, CapabilityStatus.SUPPORTED, "Original job/application URLs can be surfaced when available."),
        ProviderCapability(JobSourceCapability.APPLY, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Direct application submission requires an approved Indeed integration."),
        ProviderCapability(JobSourceCapability.PARTNER_ACCESS, CapabilityStatus.SUPPORTED, "The architecture supports Indeed partner integrations."),
    ),
    "wellfound": (
        ProviderCapability(JobSourceCapability.SEARCH_JOBS, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job discovery requires an authorized Wellfound integration."),
        ProviderCapability(JobSourceCapability.GET_JOB, CapabilityStatus.REQUIRES_PARTNER_ACCESS, "Job retrieval requires an authorized Wellfound integration."),
        ProviderCapability(JobSourceCapability.EXTERNAL_APPLY, CapabilityStatus.SUPPORTED, "Original job/application URLs can be surfaced when available."),
        ProviderCapability(JobSourceCapability.PARTNER_ACCESS, CapabilityStatus.SUPPORTED, "The adapter supports provider-authorized integration contracts."),
    ),
}


def get_provider_capabilities(provider_name: str) -> tuple[ProviderCapability, ...]:
    return PROVIDER_CAPABILITIES.get(provider_name.strip().lower(), ())


def capabilities_to_public_dict(provider_name: str) -> list[dict[str, str]]:
    return [
        {
            "capability": item.capability.value,
            "status": item.status.value,
            "description": item.description,
        }
        for item in get_provider_capabilities(provider_name)
    ]
