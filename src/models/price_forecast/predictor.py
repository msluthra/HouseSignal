"""Inference utilities for appreciation forecasting."""

from __future__ import annotations

import joblib
import numpy as np


class PriceForecastPredictor:
    """Predictor that outputs 3m/6m/12m appreciation estimates."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model = joblib.load(model_path) if model_path else None

    def predict_annual_appreciation(self, features: dict[str, float]) -> float:
        """Predict 12-month appreciation as a decimal (e.g., 0.08 = 8%)."""
        if self.model is None:
            # Baseline heuristic for scaffolding before training data is connected.
            return min(max(0.03 + 0.000002 * features.get("sqft", 0), -0.05), 0.20)
        feature_array = np.array([list(features.values())])
        return float(self.model.predict(feature_array)[0])

    def forecast_horizons(self, features: dict[str, float]) -> dict[str, float]:
        """Convert annual appreciation forecast into 3/6/12-month horizons."""
        annual = self.predict_annual_appreciation(features)
        appreciation_3m = (1 + annual) ** 0.25 - 1
        appreciation_6m = (1 + annual) ** 0.5 - 1
        return {
            "appreciation_3m": float(appreciation_3m),
            "appreciation_6m": float(appreciation_6m),
            "appreciation_12m": float(annual),
        }
