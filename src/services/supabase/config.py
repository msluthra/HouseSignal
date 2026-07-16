"""Supabase runtime configuration for mock/live operation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from config.settings import settings


PLACEHOLDER_MARKERS = (
    "your-project-ref",
    "your-publishable-or-anon-key",
    "replace-with",
    "your-",
)


class SupabaseMode(str, Enum):
    """Supported Supabase runtime modes."""

    MOCK = "mock"
    LIVE = "live"


@dataclass(frozen=True)
class SupabaseRuntimeConfig:
    """Non-secret Supabase runtime status."""

    mode: SupabaseMode
    has_url: bool
    has_anon_key: bool
    has_service_role_key: bool
    storage_bucket: str

    @property
    def live_ready(self) -> bool:
        """Return whether live backend Supabase operations can run."""
        return self.has_url and self.has_anon_key and self.has_service_role_key

    @property
    def is_mock(self) -> bool:
        """Return whether mock mode is active."""
        return self.mode == SupabaseMode.MOCK


def get_supabase_runtime_config() -> SupabaseRuntimeConfig:
    """Read Supabase mode from environment without exposing secrets."""
    requested_mode = os.getenv("SUPABASE_MODE", "auto").strip().lower()
    supabase_url = os.getenv("SUPABASE_URL", settings.supabase_url)
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", settings.supabase_anon_key)
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", settings.supabase_service_role_key)
    storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", settings.supabase_storage_bucket)
    has_url = _is_configured(supabase_url)
    has_anon_key = _is_configured(supabase_anon_key)
    has_service_role_key = _is_configured(supabase_service_role_key)
    live_ready = has_url and has_anon_key and has_service_role_key
    mode = SupabaseMode.LIVE if requested_mode == "live" and live_ready else SupabaseMode.MOCK
    if requested_mode == "auto" and live_ready:
        mode = SupabaseMode.LIVE
    return SupabaseRuntimeConfig(
        mode=mode,
        has_url=has_url,
        has_anon_key=has_anon_key,
        has_service_role_key=has_service_role_key,
        storage_bucket=storage_bucket,
    )


def _is_configured(value: str) -> bool:
    """Return whether a config value appears real, not blank or placeholder."""
    normalized = value.strip().lower()
    if not normalized:
        return False
    return not any(marker in normalized for marker in PLACEHOLDER_MARKERS)
