from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import text

from app.database.connection import engine
from app.integrations.auth.provider_configuration import (
    provider_configuration_manager,
)
from app.integrations.auth.token_vault import token_vault


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    name: str
    status: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "message": self.message,
        }


class SystemReadinessService:
    """
    Production diagnostics for the application itself.

    Provider integrations are reported separately and are not allowed
    to make a fresh installation look broken merely because optional
    provider credentials have not been supplied yet.
    """

    def check_database(self) -> ReadinessCheck:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

                inspector = sqlalchemy_inspect(connection)
                if not inspector.has_table("alembic_version"):
                    return ReadinessCheck(
                        "database",
                        "NOT_READY",
                        "Database is reachable but Alembic migrations have not been initialized.",
                    )

            return ReadinessCheck(
                "database",
                "READY",
                "Database connection and migration metadata are available.",
            )
        except Exception:
            return ReadinessCheck(
                "database",
                "NOT_READY",
                "Database connectivity or migration metadata check failed.",
            )

    def check_security(self) -> ReadinessCheck:
        secret_key = os.getenv("SECRET_KEY", "").strip()
        if not secret_key:
            return ReadinessCheck(
                "security",
                "NOT_READY",
                "SECRET_KEY is not configured.",
            )

        if len(secret_key) < 32:
            return ReadinessCheck(
                "security",
                "NOT_READY",
                "SECRET_KEY must contain at least 32 characters.",
            )

        return ReadinessCheck(
            "security",
            "READY",
            "Application signing secret is configured.",
        )

    def check_token_vault(self) -> ReadinessCheck:
        try:
            token_vault._get_fernet()
            return ReadinessCheck(
                "oauth_token_encryption",
                "READY",
                "OAuth token encryption key is valid.",
            )
        except Exception:
            return ReadinessCheck(
                "oauth_token_encryption",
                "NOT_READY",
                "OAuth token encryption is not configured with a valid Fernet key.",
            )

    def provider_summary(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for provider in provider_configuration_manager.list_providers():
            configuration = provider_configuration_manager.inspect(provider)
            results.append({
                "provider": provider,
                "status": configuration.status.value,
                "configured": configuration.configured,
                "partially_configured": configuration.partially_configured,
                "missing_environment_variables": list(
                    configuration.missing_environment_variables
                ),
            })

        return results

    def inspect(self) -> dict[str, Any]:
        checks = [
            self.check_database(),
            self.check_security(),
            self.check_token_vault(),
        ]

        ready = all(check.status == "READY" for check in checks)

        return {
            "status": "READY" if ready else "NOT_READY",
            "ready": ready,
            "checks": {
                check.name: check.to_dict()
                for check in checks
            },
            "providers": self.provider_summary(),
        }


system_readiness_service = SystemReadinessService()
