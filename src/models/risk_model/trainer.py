"""Downside risk model training and inference."""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted


class RiskModel:
    """Model that estimates downside risk as probability in [0, 1]."""

    def __init__(self, random_state: int = 42) -> None:
        self.model = GradientBoostingRegressor(random_state=random_state)

    def train(self, df: pd.DataFrame, feature_cols: list[str], target_col: str) -> GradientBoostingRegressor:
        """Train downside risk regressor and return fitted model."""
        self.model.fit(df[feature_cols], df[target_col])
        return self.model

    def save_model(self, path: str) -> None:
        """Persist model to disk."""
        joblib.dump(self.model, path)

    @staticmethod
    def load(path: str) -> "RiskModel":
        """Load model from disk and wrap in RiskModel."""
        instance = RiskModel()
        instance.model = joblib.load(path)
        return instance

    def predict_downside_risk(self, features: dict[str, float]) -> float:
        """Predict downside risk probability."""
        if self.model is None:
            return 0.25
        try:
            check_is_fitted(self.model)
        except NotFittedError:
            return 0.25

        prediction = float(self.model.predict(np.array([list(features.values())]))[0])
        return float(min(max(prediction, 0.0), 1.0))
