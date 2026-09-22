from typing import Any


JOB_SOURCE_CATALOG: list[dict[str, Any]] = [
    {
        "name": "linkedin",
        "display_name": "LinkedIn",
        "source_type": "EXTERNAL",
        "base_url": "https://www.linkedin.com",
        "search_supported": False,
        "job_details_supported": False,
        "direct_apply_supported": False,
        "application_status_sync_supported": False,
        "webhook_supported": False,
        "is_active": True,
        "health_status": "AUTHORIZATION_REQUIRED",
        "notes": (
            "Provider integration is prepared but requires "
            "authorized LinkedIn access."
        ),
    },
    {
        "name": "naukri",
        "display_name": "Naukri",
        "source_type": "EXTERNAL",
        "base_url": "https://www.naukri.com",
        "search_supported": False,
        "job_details_supported": False,
        "direct_apply_supported": False,
        "application_status_sync_supported": False,
        "webhook_supported": False,
        "is_active": True,
        "health_status": "AUTHORIZATION_REQUIRED",
        "notes": (
            "Provider integration boundary is prepared and "
            "awaits authorized access."
        ),
    },
    {
        "name": "internshala",
        "display_name": "Internshala",
        "source_type": "EXTERNAL",
        "base_url": "https://internshala.com",
        "search_supported": False,
        "job_details_supported": False,
        "direct_apply_supported": False,
        "application_status_sync_supported": False,
        "webhook_supported": False,
        "is_active": True,
        "health_status": "AUTHORIZATION_REQUIRED",
        "notes": (
            "Provider integration boundary is prepared and "
            "awaits authorized access."
        ),
    },
    {
        "name": "indeed",
        "display_name": "Indeed",
        "source_type": "EXTERNAL",
        "base_url": "https://www.indeed.com",
        "search_supported": False,
        "job_details_supported": False,
        "direct_apply_supported": False,
        "application_status_sync_supported": False,
        "webhook_supported": False,
        "is_active": True,
        "health_status": "AUTHORIZATION_REQUIRED",
        "notes": (
            "Provider integration boundary is prepared and "
            "awaits authorized access."
        ),
    },
    {
        "name": "wellfound",
        "display_name": "Wellfound",
        "source_type": "EXTERNAL",
        "base_url": "https://wellfound.com",
        "search_supported": False,
        "job_details_supported": False,
        "direct_apply_supported": False,
        "application_status_sync_supported": False,
        "webhook_supported": False,
        "is_active": True,
        "health_status": "AUTHORIZATION_REQUIRED",
        "notes": (
            "Provider integration boundary is prepared and "
            "awaits authorized access."
        ),
    },
]