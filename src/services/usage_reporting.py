"""Reporting helpers for API usage dashboards."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.cache.api_cache import ApiCache


def load_api_usage_frame(db_path: str | Path = "data/cache/api_cache.sqlite3") -> pd.DataFrame:
    """Load local API usage logs into a dataframe for Streamlit dashboards."""
    cache = ApiCache(db_path)
    with cache._connect() as conn:  # noqa: SLF001 - local reporting utility.
        return pd.read_sql_query("select * from api_usage_logs order by created_at desc", conn)
