"""Macroeconomic data ingestion with data-contract validation."""

from __future__ import annotations

import pandas as pd

from src.schemas import MacroRecord, normalize_columns, read_tabular_file, validate_dataframe

MACRO_COLUMN_MAP: dict[str, str] = {
    "geo_key": "geo_key",
    "zip_code": "geo_key",
    "zip": "geo_key",
    "region": "geo_key",
    "as_of_date": "as_of_date",
    "date": "as_of_date",
    "mortgage_rate_30y": "mortgage_rate_30y",
    "mortgage_rate": "mortgage_rate_30y",
    "unemployment_rate": "unemployment_rate",
    "cpi_yoy": "cpi_yoy",
}

MACRO_REQUIRED_COLUMNS = [
    "geo_key",
    "as_of_date",
    "mortgage_rate_30y",
    "unemployment_rate",
]


def load_macro_data(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load and validate macro data from CSV/JSON/Parquet."""
    raw = read_tabular_file(file_path)
    standardized = normalize_columns(raw, MACRO_COLUMN_MAP)
    return validate_dataframe(
        standardized,
        MacroRecord,
        MACRO_REQUIRED_COLUMNS,
        source_name="macro",
        strict=strict,
    )
