"""Zillow ingestion with data-contract validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.schemas import (
    ZILLOW_COLUMN_MAP,
    ZillowMarketMetricRecord,
    ZillowPropertyRecord,
    ZillowRentalMetricRecord,
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

ZILLOW_RENTAL_REQUIRED_COLUMNS = [
    "region",
    "state",
    "region_type",
    "as_of_date",
    "metric",
    "value",
]

PILOT_CITY_NAMES = {"San Jose", "Sacramento"}
PILOT_METRO_NAMES = {"San Jose, CA", "Sacramento, CA"}


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


def _infer_region_name(file_path: str, fallback: str) -> str:
    """Infer market region from the export filename when available."""
    filename = Path(file_path).name.lower()
    if "sacramento" in filename:
        return "Sacramento"
    if "san_jose" in filename or "sanjose" in filename:
        return "San Jose"
    return fallback


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
    region = _infer_region_name(file_path, region_name)

    value_col = "datavalue.1" if "datavalue.1" in normalized.columns else "datavalue"
    required_source_cols = ["date", "metric", value_col]
    missing = [col for col in required_source_cols if col not in normalized.columns]
    if missing:
        raise ValueError(f"zillow_market: missing required source columns: {missing}")

    standardized = pd.DataFrame(
        {
            "region": region,
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


def _date_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if len(str(col)) >= 10 and str(col)[:4].isdigit()]


def _rental_metric_name(file_path: str) -> str:
    filename = Path(file_path).name.lower()
    if "zordi" in filename and "sfr" in filename and "all" not in filename:
        return "zordi_sfr_metro"
    if "zordi" in filename:
        return "zordi_all_metro"
    if "city_zori" in filename and "sa" in filename:
        return "zori_all_city_sa"
    if "city_zori" in filename:
        return "zori_all_city"
    if "metro_zori" in filename and "sa" in filename:
        return "zori_sfr_metro_sa"
    if "metro_zori" in filename:
        return "zori_sfr_metro"
    return Path(file_path).stem


def _clean_region_name(value: object) -> str:
    name = str(value).strip()
    if name.endswith(", CA"):
        return name[:-4]
    return name


def load_zillow_rental_data(file_path: str, *, strict: bool = True) -> pd.DataFrame:
    """Load Zillow Research rental index/demand files into long format."""
    raw = pd.read_csv(file_path)
    dates = _date_columns(raw)
    if not dates:
        raise ValueError(f"zillow_rentals: no date columns found in {file_path}")

    metric = _rental_metric_name(file_path)
    region_type = "metro" if Path(file_path).name.lower().startswith("metro") else "city"
    region_filter = PILOT_METRO_NAMES if region_type == "metro" else PILOT_CITY_NAMES

    filtered = raw[
        (raw["StateName"].astype(str).str.upper() == "CA")
        & (raw["RegionName"].astype(str).isin(region_filter))
    ].copy()

    long = filtered.melt(
        id_vars=["RegionName", "RegionType", "StateName"],
        value_vars=dates,
        var_name="as_of_date",
        value_name="value",
    )
    long = long.dropna(subset=["value"]).reset_index(drop=True)
    standardized = pd.DataFrame(
        {
            "region": long["RegionName"].map(_clean_region_name),
            "state": long["StateName"].astype(str).str.upper(),
            "region_type": region_type,
            "as_of_date": pd.to_datetime(long["as_of_date"], errors="coerce").dt.date,
            "metric": metric,
            "value": long["value"].map(_parse_numeric),
            "source_file": [Path(file_path).name] * len(long),
        }
    )
    standardized = standardized.dropna(subset=["as_of_date", "value"]).reset_index(drop=True)

    return validate_dataframe(
        standardized,
        ZillowRentalMetricRecord,
        ZILLOW_RENTAL_REQUIRED_COLUMNS,
        source_name="zillow_rentals",
        strict=strict,
    )


def fetch_zillow_api_data(_region: str, _api_key: str) -> pd.DataFrame:
    """Placeholder for future Zillow API integration."""
    raise NotImplementedError(
        "Zillow API ingestion is not implemented yet. Use load_zillow_property_data for file ingestion."
    )
