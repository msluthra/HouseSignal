"""Firm historical deal ingestion with data-contract validation."""

from __future__ import annotations

import pandas as pd

from src.schemas import (
    FIRM_COLUMN_MAP,
    FirmDealRecord,
    normalize_columns,
    read_tabular_file,
    validate_dataframe,
)


FIRM_REQUIRED_COLUMNS = [
    "deal_id",
    "address",
    "city",
    "state",
    "zip_code",
    "purchase_date",
    "purchase_price",
]


def load_firm_deal_history(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load and validate firm historical deal records from CSV/JSON/Parquet."""
    raw = read_tabular_file(file_path)
    standardized = normalize_columns(raw, FIRM_COLUMN_MAP)
    return validate_dataframe(
        standardized,
        FirmDealRecord,
        FIRM_REQUIRED_COLUMNS,
        source_name="firm_data",
        strict=strict,
    )
