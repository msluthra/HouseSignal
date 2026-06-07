"""Security helpers for environment-only secret handling."""

from __future__ import annotations

import os
from src.utils.security import PublicSecretCheck, public_service_status


def require_secret(value: str, name: str) -> str:
    """Return a secret value or raise without exposing the secret itself."""
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_secret_status() -> list[PublicSecretCheck]:
    """Return UI-safe configured/not-configured service statuses."""
    return public_service_status(os.environ)
