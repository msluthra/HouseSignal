"""Rent data ingestion with data-contract validation."""

from __future__ import annotations

import pandas as pd

from src.schemas import RentRecord, normalize_columns, read_tabular_file, validate_dataframe

RENT_COLUMN_MAP: dict[str, str] = {
    "address": "address",
    "street_address": "address",
    "city": "city",
    "state": "state",
    "zip": "zip_code",
    "zipcode": "zip_code",
    "zip_code": "zip_code",
    "as_of_date": "as_of_date",
    "date": "as_of_date",
    "monthly_rent": "monthly_rent",
    "rent": "monthly_rent",
    "occupancy_rate": "occupancy_rate",
}

RENT_REQUIRED_COLUMNS = [
    "address",
    "city",
    "state",
    "zip_code",
    "as_of_date",
    "monthly_rent",
]


def load_rent_data(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load and validate rent data from CSV/JSON/Parquet."""
    raw = read_tabular_file(file_path)
    standardized = normalize_columns(raw, RENT_COLUMN_MAP)
    return validate_dataframe(
        standardized,
        RentRecord,
        RENT_REQUIRED_COLUMNS,
        source_name="rent",
        strict=strict,
    )
