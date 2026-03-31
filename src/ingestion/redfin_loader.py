"""Redfin data ingestion placeholders."""

from __future__ import annotations

import pandas as pd


def load_redfin_market_data(file_path: str) -> pd.DataFrame:
    """Load Redfin market data from a local CSV file."""
    return pd.read_csv(file_path)


def fetch_redfin_api_data(_region: str, _api_key: str) -> pd.DataFrame:
    """Placeholder for Redfin API integration."""
    return pd.DataFrame()
