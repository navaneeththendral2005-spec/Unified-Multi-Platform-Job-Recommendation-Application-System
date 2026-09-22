import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(
    BASE_DIR / ".env"
)


@dataclass(frozen=True, slots=True)
class ProviderCredentials:
    """
    Provider credential configuration loaded from environment
    variables.

    Secret values must never be exposed through API responses
    or committed to source control.
    """

    provider_name: str

    client_id: str | None = None
    client_secret: str | None = None

    api_key: str | None = None
    api_secret: str | None = None

    @property
    def configured(self) -> bool:
        """
        Return whether at least one credential value exists.
        """

        return any(
            (
                self.client_id,
                self.client_secret,
                self.api_key,
                self.api_secret,
            )
        )


def load_provider_credentials(
    provider_name: str,
) -> ProviderCredentials:
    """
    Load provider credentials using a standardized
    environment-variable naming convention.

    Examples:

        LINKEDIN_CLIENT_ID
        LINKEDIN_CLIENT_SECRET

        NAUKRI_API_KEY
        NAUKRI_API_SECRET

        INDEED_CLIENT_ID
        INDEED_CLIENT_SECRET
    """

    normalized_name = (
        provider_name.strip().lower()
    )

    prefix = normalized_name.upper()

    return ProviderCredentials(
        provider_name=normalized_name,

        client_id=os.getenv(
            f"{prefix}_CLIENT_ID"
        ),

        client_secret=os.getenv(
            f"{prefix}_CLIENT_SECRET"
        ),

        api_key=os.getenv(
            f"{prefix}_API_KEY"
        ),

        api_secret=os.getenv(
            f"{prefix}_API_SECRET"
        ),
    )