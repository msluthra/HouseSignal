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

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/ca_investment_advisor",
    )

    redfin_api_key: str = os.getenv("REDFIN_API_KEY", "")
    zillow_api_key: str = os.getenv("ZILLOW_API_KEY", "")
    firm_data_path: str = os.getenv("FIRM_DATA_PATH", "data/raw/firm_deals.csv")


settings = Settings()
