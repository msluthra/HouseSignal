"""Zillow ingestion with data-contract validation."""

from __future__ import annotations

import pandas as pd

from src.schemas import (
    ZILLOW_COLUMN_MAP,
    ZillowPropertyRecord,
    normalize_columns,
    read_tabular_file,
    validate_dataframe,
)


ZILLOW_REQUIRED_COLUMNS = [
    "address",
    "city",
    "state",
    "zip_code",
    "beds",
    "baths",
    "sqft",
    "list_price",
]


def load_zillow_property_data(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load and validate Zillow property data from CSV/JSON/Parquet."""
    raw = read_tabular_file(file_path)
    standardized = normalize_columns(raw, ZILLOW_COLUMN_MAP)
    return validate_dataframe(
        standardized,
        ZillowPropertyRecord,
        ZILLOW_REQUIRED_COLUMNS,
        source_name="zillow",
        strict=strict,
    )


def fetch_zillow_api_data(_region: str, _api_key: str) -> pd.DataFrame:
    """Placeholder for future Zillow API integration."""
    raise NotImplementedError(
        "Zillow API ingestion is not implemented yet. Use load_zillow_property_data for file ingestion."
    )
