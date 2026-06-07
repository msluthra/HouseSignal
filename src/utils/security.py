"""Security validation helpers for HouseSignal AI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

BACKEND_ONLY_SECRET_NAMES = frozenset(
    {
        "RENTCAST_API_KEY",
        "OPENAI_API_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    }
)

SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(rentcast|openai|supabase)[A-Za-z0-9_-]{24,}"),
)


@dataclass(frozen=True)
class SecretCheck:
    """Non-sensitive status for a required secret."""

    name: str
    configured: bool


@dataclass(frozen=True)
class PublicSecretCheck:
    """UI-safe status label for a required backend service."""

    label: str
    configured: bool


def validate_required_keys(env: Mapping[str, str], required_keys: list[str] | tuple[str, ...]) -> list[SecretCheck]:
    """Check required env vars without exposing their values."""
    return [SecretCheck(name=key, configured=bool(env.get(key))) for key in required_keys]


def missing_required_keys(env: Mapping[str, str], required_keys: list[str] | tuple[str, ...]) -> list[str]:
    """Return only missing key names, never values."""
    return [check.name for check in validate_required_keys(env, required_keys) if not check.configured]


def require_keys(env: Mapping[str, str], required_keys: list[str] | tuple[str, ...]) -> None:
    """Raise a safe error if required env vars are missing."""
    missing = missing_required_keys(env, required_keys)
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def public_service_status(env: Mapping[str, str]) -> list[PublicSecretCheck]:
    """Return UI-safe service status labels without backend secret names."""
    return [
        PublicSecretCheck("Supabase project", bool(env.get("SUPABASE_URL")) and bool(env.get("SUPABASE_ANON_KEY"))),
        PublicSecretCheck("Supabase backend access", bool(env.get("SUPABASE_SERVICE_ROLE_KEY"))),
        PublicSecretCheck("OpenAI backend access", bool(env.get("OPENAI_API_KEY"))),
        PublicSecretCheck("RentCast backend access", bool(env.get("RENTCAST_API_KEY"))),
    ]


def contains_secret_value(text: str) -> bool:
    """Return True when text appears to contain a real secret value."""
    return any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS)
