"""Firm historical deal data ingestion."""

from __future__ import annotations

import pandas as pd


def load_firm_deal_history(file_path: str) -> pd.DataFrame:
    """Load internal historical deal records for model feature enrichment."""
    return pd.read_csv(file_path)
