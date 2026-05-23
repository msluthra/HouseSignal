"""Zillow ingestion with data-contract validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.schemas import (
    ZILLOW_COLUMN_MAP,
    ZillowMarketMetricRecord,
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

ZILLOW_MARKET_REQUIRED_COLUMNS = [
    "region",
    "state",
    "as_of_date",
    "metric",
    "value",
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


def _read_zillow_market_export(file_path: str) -> pd.DataFrame:
    """Read Zillow Market Explorer exports, including UTF-16 tab-separated CSVs."""
    try:
        return pd.read_csv(file_path)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="utf-16", sep="\t")


def _parse_numeric(value: object) -> float | None:
    """Convert Zillow-formatted numeric strings to floats."""
    if pd.isna(value):
        return None
    cleaned = str(value).strip().replace(",", "").replace("$", "")
    if cleaned == "":
        return None
    return float(cleaned)


def _parse_percent(value: object) -> float | None:
    """Convert Zillow percent strings to decimal values."""
    if pd.isna(value):
        return None
    cleaned = str(value).strip().replace("%", "")
    if cleaned == "":
        return None
    return float(cleaned) / 100


def load_zillow_market_explorer_data(
    file_path: str,
    *,
    region_name: str = "San Jose",
    state: str = "CA",
    strict: bool = True,
) -> pd.DataFrame:
    """Load and validate Zillow Market Explorer time-series exports."""
    raw = _read_zillow_market_export(file_path)
    normalized = normalize_columns(raw, {})

    value_col = "datavalue.1" if "datavalue.1" in normalized.columns else "datavalue"
    required_source_cols = ["date", "metric", value_col]
    missing = [col for col in required_source_cols if col not in normalized.columns]
    if missing:
        raise ValueError(f"zillow_market: missing required source columns: {missing}")

    standardized = pd.DataFrame(
        {
            "region": region_name,
            "state": state,
            "as_of_date": pd.to_datetime(normalized["date"], errors="coerce").dt.date,
            "metric": normalized["metric"].astype(str).str.strip(),
            "value": normalized[value_col].map(_parse_numeric),
            "mom_change": normalized["mom"].map(_parse_percent) if "mom" in normalized.columns else None,
            "yoy_change": normalized["yoy"].map(_parse_percent) if "yoy" in normalized.columns else None,
            "source_file": [Path(file_path).name] * len(normalized),
        }
    )
    standardized = standardized.dropna(subset=["as_of_date", "metric", "value"]).reset_index(drop=True)

    return validate_dataframe(
        standardized,
        ZillowMarketMetricRecord,
        ZILLOW_MARKET_REQUIRED_COLUMNS,
        source_name="zillow_market",
        strict=strict,
    )


def fetch_zillow_api_data(_region: str, _api_key: str) -> pd.DataFrame:
    """Placeholder for future Zillow API integration."""
    raise NotImplementedError(
        "Zillow API ingestion is not implemented yet. Use load_zillow_property_data for file ingestion."
    )
