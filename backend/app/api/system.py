from fastapi import APIRouter, Response, status

from app.services.system_readiness_service import (
    system_readiness_service,
)

from app.services.provider_credential_validation_service import (
    provider_credential_validation_service,
)

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/readiness")
def system_readiness() -> dict:
    """
    Detailed production-readiness diagnostics.

    No secret values are returned.
    """
    return system_readiness_service.inspect()


@router.get("/health/ready")
def readiness_probe(response: Response) -> dict:
    """
    Kubernetes/load-balancer style readiness probe.

    Returns HTTP 503 until core application dependencies are ready.
    Optional external job providers are reported separately.
    """
    result = system_readiness_service.inspect()

    if not result["ready"]:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result

@router.get("/credentials")
def validate_provider_credentials() -> dict:
    results = (
        provider_credential_validation_service.validate_all()
    )

    return {
        "providers": [
            provider_credential_validation_service.to_public_dict(result)
            for result in results
        ],
        "total": len(results),
    }

@router.get("/credentials/{provider_name}")
def validate_provider_credentials_for_provider(
    provider_name: str,
) -> dict:
    result = provider_credential_validation_service.validate(
        provider_name
    )

    return provider_credential_validation_service.to_public_dict(
        result
    )