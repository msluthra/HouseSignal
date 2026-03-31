"""Training pipeline for property appreciation forecasting."""

from __future__ import annotations

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


class PriceForecastTrainer:
    """Trainer for 12-month appreciation forecast model."""

    def __init__(self, random_state: int = 42) -> None:
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            random_state=random_state,
        )

    def train(self, df: pd.DataFrame, feature_cols: list[str], target_col: str) -> RandomForestRegressor:
        """Train and return the appreciation model."""
        x = df[feature_cols]
        y = df[target_col]
        self.model.fit(x, y)
        return self.model

    def save_model(self, path: str) -> None:
        """Persist trained model to disk."""
        joblib.dump(self.model, path)
