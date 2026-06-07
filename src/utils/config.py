"""Safe environment configuration helpers for HouseSignal AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class AppConfig:
    """Environment-backed application config.

    Values are loaded from environment variables only. Secret values should stay
    inside backend-only modules and should never be rendered in UI or logs.
    """

    app_env: str
    database_url: str
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    openai_api_key: str
    rentcast_api_key: str
    rentcast_daily_limit: int
    rentcast_cache_ttl_hours: int
    supabase_storage_bucket: str


def load_environment(env_path: str | Path | None = None) -> None:
    """Load local environment variables without overriding already-set values."""
    path = Path(env_path) if env_path else DEFAULT_ENV_PATH
    if path.exists():
        load_dotenv(path, override=False)


def get_env(name: str, default: str = "") -> str:
    """Read an environment variable as a string."""
    return os.getenv(name, default)


def get_int_env(name: str, default: int) -> int:
    """Read an environment variable as an integer with a safe fallback."""
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc


def load_config(env_path: str | Path | None = None) -> AppConfig:
    """Load HouseSignal AI config from environment variables."""
    load_environment(env_path)
    return AppConfig(
        app_env=get_env("APP_ENV", "local"),
        database_url=get_env("DATABASE_URL", "sqlite:///./housesignal.db"),
        supabase_url=get_env("SUPABASE_URL"),
        supabase_anon_key=get_env("SUPABASE_ANON_KEY"),
        supabase_service_role_key=get_env("SUPABASE_SERVICE_ROLE_KEY"),
        openai_api_key=get_env("OPENAI_API_KEY"),
        rentcast_api_key=get_env("RENTCAST_API_KEY"),
        rentcast_daily_limit=get_int_env("RENTCAST_DAILY_LIMIT", 5),
        rentcast_cache_ttl_hours=get_int_env("RENTCAST_CACHE_TTL_HOURS", 720),
        supabase_storage_bucket=get_env("SUPABASE_STORAGE_BUCKET", "deal-documents"),
    )
