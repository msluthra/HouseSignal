"""Tests for Zillow market training-table construction."""

from __future__ import annotations

import pandas as pd

from src.processing.train_table_builder import build_zillow_market_training_table


def test_zillow_market_training_table_builds_targets(tmp_path) -> None:
    rows = []
    for month in range(1, 15):
        as_of_date = pd.Timestamp(2024, month if month <= 12 else month - 12, 28)
        if month > 12:
            as_of_date = pd.Timestamp(2025, month - 12, 28)
        rows.extend(
            [
                {"region": "San Jose", "state": "CA", "as_of_date": as_of_date, "metric": "ZHVI", "value": 100 + month, "mom_change": 0.01, "yoy_change": 0.05},
                {"region": "San Jose", "state": "CA", "as_of_date": as_of_date, "metric": "Median Sale Price", "value": 110 + month, "mom_change": 0.01, "yoy_change": 0.04},
                {"region": "San Jose", "state": "CA", "as_of_date": as_of_date, "metric": "Active Listings", "value": 50 + month, "mom_change": 0.01, "yoy_change": 0.03},
            ]
        )
    source = tmp_path / "zillow_market.parquet"
    pd.DataFrame(rows).to_parquet(source, index=False)

    table = build_zillow_market_training_table(source)

    assert len(table) == 14
    assert "target_appreciation_12m" in table.columns
    assert table.loc[0, "target_appreciation_12m"] == (113 / 101) - 1
