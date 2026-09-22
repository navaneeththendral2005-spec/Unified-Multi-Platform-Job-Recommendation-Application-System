import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


class TokenVault:
    """Encrypts and decrypts OAuth tokens using Fernet."""

    def __init__(self) -> None:
        self._fernet: Fernet | None = None

    def _get_fernet(self) -> Fernet:
        if self._fernet is not None:
            return self._fernet

        key = os.getenv("OAUTH_TOKEN_ENCRYPTION_KEY")

        if not key:
            raise RuntimeError(
                "OAUTH_TOKEN_ENCRYPTION_KEY is not configured."
            )

        try:
            self._fernet = Fernet(key.encode())
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "OAUTH_TOKEN_ENCRYPTION_KEY is invalid. "
                "Generate a valid Fernet key."
            ) from exc

        return self._fernet

    def encrypt(self, value: str) -> str:
        if not value:
            raise ValueError("Cannot encrypt an empty token.")

        return self._get_fernet().encrypt(
            value.encode()
        ).decode()

    def decrypt(self, value: str) -> str:
        if not value:
            raise ValueError("Cannot decrypt an empty token.")

        try:
            return self._get_fernet().decrypt(
                value.encode()
            ).decode()
        except InvalidToken as exc:
            raise ValueError(
                "Unable to decrypt OAuth token."
            ) from exc


token_vault = TokenVault()