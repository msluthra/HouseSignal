"""Training pipeline for rent forecasting model."""

from __future__ import annotations

import joblib
import pandas as pd
from xgboost import XGBRegressor


class RentForecastTrainer:
    """Trainer for monthly rent prediction model."""

    def __init__(self, random_state: int = 42) -> None:
        self.model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
        )

    def train(self, df: pd.DataFrame, feature_cols: list[str], target_col: str) -> XGBRegressor:
        """Train the rent model and return it."""
        self.model.fit(df[feature_cols], df[target_col])
        return self.model

    def save_model(self, path: str) -> None:
        """Persist trained model to disk."""
        joblib.dump(self.model, path)
