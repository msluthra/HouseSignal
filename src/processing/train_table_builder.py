"""Build unified training tables from multiple source datasets."""

from __future__ import annotations

import pandas as pd


def build_training_table(
    properties_df: pd.DataFrame,
    market_df: pd.DataFrame,
    rent_df: pd.DataFrame,
    firm_df: pd.DataFrame,
) -> pd.DataFrame:
    """Join source tables into a single training-ready dataframe."""
    merged = properties_df.merge(
        market_df,
        on=["zip_code"],
        how="left",
        suffixes=("", "_market"),
    )
    if "address" in rent_df.columns:
        merged = merged.merge(rent_df, on="address", how="left", suffixes=("", "_rent"))
    if "address" in firm_df.columns:
        merged = merged.merge(firm_df, on="address", how="left", suffixes=("", "_firm"))
    return merged
