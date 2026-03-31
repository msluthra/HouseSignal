"""Inference for monthly rent forecasting."""

from __future__ import annotations

import joblib
import numpy as np


class RentForecastPredictor:
    """Predict expected monthly rent."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model = joblib.load(model_path) if model_path else None

    def predict_monthly_rent(self, features: dict[str, float]) -> float:
        """Predict monthly rent in USD."""
        if self.model is None:
            # Baseline heuristic: rent approximated from sqft and bedroom count.
            sqft_component = 1.9 * features.get("sqft", 0)
            bed_component = 250 * features.get("beds", 0)
            return float(max(1000, sqft_component + bed_component))
        feature_array = np.array([list(features.values())])
        return float(self.model.predict(feature_array)[0])
