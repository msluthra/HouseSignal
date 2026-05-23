"""Data contract tests for ingestion sources."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ingestion.firm_data_loader import load_firm_deal_history
from src.ingestion.macro_loader import load_fred_macro_data
from src.ingestion.redfin_loader import load_redfin_market_data
from src.ingestion.zillow_loader import load_zillow_market_explorer_data, load_zillow_property_data, load_zillow_rental_data
from src.schemas import DataContractError


def test_redfin_contract_validates_and_normalizes_columns(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "Region": "San Jose, CA",
                "Region Type": "metro",
                "Period End": "2025-12-31",
                "Median Sale Price": 1250000,
                "Median PPSF": 810,
                "Homes Sold": 123,
                "Inventory": 250,
                "Median DOM": 18,
            }
        ]
    )
    file_path = tmp_path / "redfin.csv"
    df.to_csv(file_path, index=False)

    validated = load_redfin_market_data(str(file_path))

    assert len(validated) == 1
    assert "median_sale_price" in validated.columns
    assert validated.loc[0, "region"] == "San Jose, CA"


def test_zillow_contract_rejects_bad_values(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "address": "1 Test Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
                "beds": 0,
                "baths": 2,
                "sqft": 1200,
                "list_price": 900000,
            }
        ]
    )
    file_path = tmp_path / "zillow.csv"
    df.to_csv(file_path, index=False)

    with pytest.raises(DataContractError):
        load_zillow_property_data(str(file_path))


def test_zillow_market_explorer_utf16_export_loads(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "date": "4/30/2026",
                "metric": "ZHVI",
                "datavalue": "1,500,000",
                "mom": "1.25%",
                "yoy": "4.50%",
            }
        ]
    )
    file_path = tmp_path / "zhv.csv"
    df.to_csv(file_path, sep="\t", encoding="utf-16", index=False)

    validated = load_zillow_market_explorer_data(str(file_path), region_name="San Jose")

    assert len(validated) == 1
    assert validated.loc[0, "metric"] == "ZHVI"
    assert validated.loc[0, "value"] == 1500000
    assert validated.loc[0, "mom_change"] == 0.0125
    assert validated.loc[0, "yoy_change"] == 0.045


def test_zillow_rental_wide_export_loads_pilot_city(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "RegionID": 1,
                "SizeRank": 1,
                "RegionName": "San Jose",
                "RegionType": "city",
                "StateName": "CA",
                "2026-03-31": 3200,
                "2026-04-30": 3225,
            },
            {
                "RegionID": 2,
                "SizeRank": 2,
                "RegionName": "Austin",
                "RegionType": "city",
                "StateName": "TX",
                "2026-03-31": 1800,
                "2026-04-30": 1810,
            },
        ]
    )
    file_path = tmp_path / "city_zori_all_sm.csv"
    df.to_csv(file_path, index=False)

    validated = load_zillow_rental_data(str(file_path))

    assert len(validated) == 2
    assert set(validated["region"]) == {"San Jose"}
    assert validated.loc[0, "metric"] == "zori_all_city"


def test_fred_macro_export_loads_month_end_rows(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {"observation_date": "2026-04-23", "MORTGAGE30US": 6.23},
            {"observation_date": "2026-04-30", "MORTGAGE30US": 6.30},
            {"observation_date": "2026-05-07", "MORTGAGE30US": 6.37},
            {"observation_date": "2026-05-14", "MORTGAGE30US": 6.36},
        ]
    )
    file_path = tmp_path / "MORTGAGE30US.csv"
    df.to_csv(file_path, index=False)

    validated = load_fred_macro_data(str(file_path))

    assert len(validated) == 2
    assert validated.loc[0, "metric"] == "mortgage_rate_30y"
    assert str(validated.loc[0, "as_of_date"]) == "2026-04-30"
    assert validated.loc[0, "value"] == 6.30


def test_firm_contract_accepts_valid_csv(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "deal_id": "D-1001",
                "address": "10 Main St",
                "city": "Irvine",
                "state": "CA",
                "zip_code": "92602",
                "purchase_date": "2024-01-15",
                "purchase_price": 720000,
                "exit_date": "2025-02-01",
                "exit_price": 840000,
                "hold_months": 13,
                "irr": 0.19,
            }
        ]
    )
    file_path = tmp_path / "firm.csv"
    df.to_csv(file_path, index=False)

    validated = load_firm_deal_history(str(file_path))
    assert len(validated) == 1
    assert validated.loc[0, "deal_id"] == "D-1001"
