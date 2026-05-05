"""Redfin ingestion with data-contract validation."""

from __future__ import annotations

import pandas as pd

from src.schemas import (
    REDFIN_COLUMN_MAP,
    RedfinMarketRecord,
    normalize_columns,
    read_tabular_file,
    validate_dataframe,
)


REDFIN_REQUIRED_COLUMNS = [
    "region",
    "region_type",
    "period_end",
    "median_sale_price",
]


def load_redfin_market_data(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load and validate Redfin market data from CSV/JSON/Parquet."""
    raw = read_tabular_file(file_path)
    standardized = normalize_columns(raw, REDFIN_COLUMN_MAP)
    return validate_dataframe(
        standardized,
        RedfinMarketRecord,
        REDFIN_REQUIRED_COLUMNS,
        source_name="redfin",
        strict=strict,
    )


def fetch_redfin_api_data(_region: str, _api_key: str) -> pd.DataFrame:
    """Placeholder for future Redfin API integration."""
    raise NotImplementedError(
        "Redfin API ingestion is not implemented yet. Use load_redfin_market_data for file ingestion."
    )
