"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from src.utils.config import load_environment


load_environment()


@dataclass(frozen=True)
class Settings:
    """Centralized settings for API, database, and data providers."""

    app_env: str = os.getenv("APP_ENV", "local")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    frontend_origins: str = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./housesignal.db",
    )
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    db_pool_timeout_seconds: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    db_pool_recycle_seconds: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))

    redfin_api_key: str = os.getenv("REDFIN_API_KEY", "")
    zillow_api_key: str = os.getenv("ZILLOW_API_KEY", "")
    firm_data_path: str = os.getenv("FIRM_DATA_PATH", "data/raw/firm_deals.csv")

    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_storage_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "deal-documents")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    rentcast_api_key: str = os.getenv("RENTCAST_API_KEY", "")
    rentcast_base_url: str = os.getenv("RENTCAST_BASE_URL", "https://api.rentcast.io/v1")
    rentcast_daily_limit: int = int(os.getenv("RENTCAST_DAILY_LIMIT", "5"))
    rentcast_cache_ttl_hours: int = int(os.getenv("RENTCAST_CACHE_TTL_HOURS", "720"))


settings = Settings()
