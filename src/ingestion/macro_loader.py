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

FRED_REQUIRED_COLUMNS = [
    "as_of_date",
    "metric",
    "value",
]

FRED_METRIC_MAP = {
    "MORTGAGE30US": "mortgage_rate_30y",
    "FEDFUNDS": "fed_funds_rate",
    "DGS10": "treasury_10y",
    "CPIAUCSL": "cpi_index",
}


def load_fred_macro_data(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load raw FRED CSV exports into monthly macro metric rows."""
    from pathlib import Path

    from src.schemas import FredMacroMetricRecord

    raw = pd.read_csv(file_path)
    if "observation_date" not in raw.columns or len(raw.columns) < 2:
        raise ValueError(f"fred_macro: invalid FRED file shape: {file_path}")

    series_id = raw.columns[1]
    metric = FRED_METRIC_MAP.get(series_id, series_id.lower())
    working = raw.rename(columns={"observation_date": "as_of_date", series_id: "value"})
    working["as_of_date"] = pd.to_datetime(working["as_of_date"], errors="coerce")
    working["value"] = pd.to_numeric(working["value"].replace(".", pd.NA), errors="coerce")
    working = working.dropna(subset=["as_of_date", "value"])
    working["month"] = working["as_of_date"].dt.to_period("M").dt.to_timestamp("M")

    monthly = working.sort_values("as_of_date").groupby("month", as_index=False).tail(1)
    standardized = pd.DataFrame(
        {
            "as_of_date": monthly["month"].dt.date,
            "metric": metric,
            "value": monthly["value"].astype(float),
            "source_file": Path(file_path).name,
        }
    )

    return validate_dataframe(
        standardized,
        FredMacroMetricRecord,
        FRED_REQUIRED_COLUMNS,
        source_name="fred_macro",
        strict=strict,
    )
