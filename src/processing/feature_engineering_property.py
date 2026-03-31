"""Property and market feature engineering routines."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_property_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create model-ready numerical features from raw property records."""
    features = df.copy()
    features["price_per_sqft"] = features["list_price"] / features["sqft"].replace(0, np.nan)
    features["bath_bed_ratio"] = features["baths"] / features["beds"].replace(0, np.nan)
    features["is_large_home"] = (features["sqft"] >= 2200).astype(int)
    features = features.fillna(0)
    return features
