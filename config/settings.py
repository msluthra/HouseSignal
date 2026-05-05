"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Centralized settings for API, database, and data providers."""

    app_env: str = os.getenv("APP_ENV", "local")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    frontend_origins: str = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000")

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./prophetai.db",
    )
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    db_pool_timeout_seconds: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    db_pool_recycle_seconds: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))

    redfin_api_key: str = os.getenv("REDFIN_API_KEY", "")
    zillow_api_key: str = os.getenv("ZILLOW_API_KEY", "")
    firm_data_path: str = os.getenv("FIRM_DATA_PATH", "data/raw/firm_deals.csv")


settings = Settings()
