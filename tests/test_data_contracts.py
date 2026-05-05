"""Data contract tests for ingestion sources."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ingestion.firm_data_loader import load_firm_deal_history
from src.ingestion.redfin_loader import load_redfin_market_data
from src.ingestion.zillow_loader import load_zillow_property_data
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
