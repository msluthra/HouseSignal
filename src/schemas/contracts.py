"""Data contracts and validation helpers for ingestion sources."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class DataContractError(ValueError):
    """Raised when source data violates a contract."""


class RedfinMarketRecord(BaseModel):
    """Canonical Redfin market trend row."""

    model_config = ConfigDict(extra="forbid")

    region: str
    region_type: str
    period_end: date
    median_sale_price: float = Field(gt=0)
    median_price_per_sqft: float | None = Field(default=None, gt=0)
    homes_sold: int | None = Field(default=None, ge=0)
    inventory: int | None = Field(default=None, ge=0)
    median_days_on_market: float | None = Field(default=None, ge=0)


class ZillowPropertyRecord(BaseModel):
    """Canonical Zillow property row."""

    model_config = ConfigDict(extra="forbid")

    address: str
    city: str
    state: str
    zip_code: str
    beds: float = Field(gt=0)
    baths: float = Field(gt=0)
    sqft: float = Field(gt=0)
    list_price: float = Field(gt=0)


class ZillowMarketMetricRecord(BaseModel):
    """Canonical Zillow Market Explorer metric row."""

    model_config = ConfigDict(extra="forbid")

    region: str
    state: str = "CA"
    as_of_date: date
    metric: str
    value: float = Field(ge=0)
    mom_change: float | None = None
    yoy_change: float | None = None
    source_file: str | None = None


class ZillowRentalMetricRecord(BaseModel):
    """Canonical Zillow rental research metric row."""

    model_config = ConfigDict(extra="forbid")

    region: str
    state: str = "CA"
    region_type: str
    as_of_date: date
    metric: str
    value: float = Field(ge=0)
    source_file: str | None = None


class FredMacroMetricRecord(BaseModel):
    """Canonical FRED macroeconomic metric row."""

    model_config = ConfigDict(extra="forbid")

    as_of_date: date
    metric: str
    value: float = Field(ge=0)
    source_file: str | None = None


class RentRecord(BaseModel):
    """Canonical rent observation row."""

    model_config = ConfigDict(extra="forbid")

    address: str
    city: str
    state: str
    zip_code: str
    as_of_date: date
    monthly_rent: float = Field(gt=0)
    occupancy_rate: float | None = Field(default=None, ge=0, le=1)


class MacroRecord(BaseModel):
    """Canonical macroeconomic feature row."""

    model_config = ConfigDict(extra="forbid")

    geo_key: str
    as_of_date: date
    mortgage_rate_30y: float = Field(ge=0)
    unemployment_rate: float = Field(ge=0)
    cpi_yoy: float | None = None


class FirmDealRecord(BaseModel):
    """Canonical internal historical deal row."""

    model_config = ConfigDict(extra="forbid")

    deal_id: str
    address: str
    city: str
    state: str
    zip_code: str
    purchase_date: date
    purchase_price: float = Field(gt=0)
    exit_date: date | None = None
    exit_price: float | None = Field(default=None, gt=0)
    hold_months: int | None = Field(default=None, ge=0)
    irr: float | None = None


REDFIN_COLUMN_MAP: dict[str, str] = {
    "region": "region",
    "region_type": "region_type",
    "period_end": "period_end",
    "period_end_date": "period_end",
    "median_sale_price": "median_sale_price",
    "median_sale_price_usd": "median_sale_price",
    "median_ppsf": "median_price_per_sqft",
    "median_price_per_sqft": "median_price_per_sqft",
    "homes_sold": "homes_sold",
    "inventory": "inventory",
    "median_dom": "median_days_on_market",
    "median_days_on_market": "median_days_on_market",
}

ZILLOW_COLUMN_MAP: dict[str, str] = {
    "street_address": "address",
    "address": "address",
    "city": "city",
    "state": "state",
    "zipcode": "zip_code",
    "zip": "zip_code",
    "zip_code": "zip_code",
    "bedrooms": "beds",
    "beds": "beds",
    "bathrooms": "baths",
    "baths": "baths",
    "living_area": "sqft",
    "sqft": "sqft",
    "list_price": "list_price",
    "price": "list_price",
}

FIRM_COLUMN_MAP: dict[str, str] = {
    "deal_id": "deal_id",
    "address": "address",
    "city": "city",
    "state": "state",
    "zip_code": "zip_code",
    "zip": "zip_code",
    "purchase_date": "purchase_date",
    "purchase_price": "purchase_price",
    "exit_date": "exit_date",
    "exit_price": "exit_price",
    "hold_months": "hold_months",
    "irr": "irr",
}


def read_tabular_file(file_path: str) -> pd.DataFrame:
    """Read CSV, JSON, or Parquet into a dataframe based on extension."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix == ".json":
        return pd.read_json(file_path)
    if suffix == ".parquet":
        return pd.read_parquet(file_path)
    raise ValueError(f"Unsupported file format: {suffix}. Use .csv, .json, or .parquet")


def _sanitize_column_name(col: str) -> str:
    return col.strip().lower().replace(" ", "_")


def normalize_columns(df: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    """Normalize source column naming and map to canonical names."""
    normalized = df.copy()
    normalized.columns = [_sanitize_column_name(col) for col in normalized.columns]

    mapped: dict[str, str] = {}
    for raw_col in normalized.columns:
        if raw_col in column_map:
            mapped[raw_col] = column_map[raw_col]
    return normalized.rename(columns=mapped)


def validate_dataframe(
    df: pd.DataFrame,
    model_cls: type[BaseModel],
    required_columns: list[str],
    source_name: str,
    *,
    strict: bool = True,
) -> pd.DataFrame:
    """Validate dataframe rows against a pydantic contract model."""
    working = df.copy()

    # Normalize common identifier/text fields before row-level validation.
    for text_col in ("zip_code", "state", "city", "address", "region", "region_type", "geo_key", "deal_id"):
        if text_col in working.columns:
            working[text_col] = working[text_col].astype(str).str.strip()

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise DataContractError(f"{source_name}: missing required columns: {missing}")

    records: list[dict[str, Any]] = []
    errors: list[str] = []

    for idx, row in enumerate(working.to_dict(orient="records")):
        payload = {k: row.get(k) for k in model_cls.model_fields.keys()}
        try:
            parsed = model_cls.model_validate(payload)
            records.append(parsed.model_dump())
        except ValidationError as exc:
            errors.append(f"row={idx}: {exc.errors()}")

    if errors and strict:
        sample = errors[:5]
        raise DataContractError(
            f"{source_name}: contract validation failed with {len(errors)} row errors. "
            f"Sample: {sample}"
        )

    return pd.DataFrame(records)
