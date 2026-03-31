"""Zillow data ingestion placeholders."""

from __future__ import annotations

import pandas as pd


def load_zillow_property_data(file_path: str) -> pd.DataFrame:
    """Load Zillow property level data from CSV."""
    return pd.read_csv(file_path)


def fetch_zillow_api_data(_region: str, _api_key: str) -> pd.DataFrame:
    """Placeholder for Zillow API integration."""
    return pd.DataFrame()
