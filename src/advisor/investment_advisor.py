"""Orchestration layer that generates investment recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.investment_score.score_engine import InvestmentScoreEngine
from src.models.price_forecast.predictor import PriceForecastPredictor
from src.models.rent_forecast.predictor import RentForecastPredictor
from src.models.risk_model.trainer import RiskModel
from src.valuation.fair_value_engine import estimate_fair_value


@dataclass
class PropertyInput:
    """Input payload for a property under evaluation."""

    address: str
    list_price: float
    beds: float
    baths: float
    sqft: float
    neighborhood_price_per_sqft: float = 550.0


class InvestmentAdvisor:
    """Coordinates valuation, forecasting, scoring, and recommendation labeling."""

    def __init__(self) -> None:
        self.price_predictor = PriceForecastPredictor()
        self.rent_predictor = RentForecastPredictor()
        self.risk_model = RiskModel()
        self.score_engine = InvestmentScoreEngine()

    def evaluate(self, property_input: PropertyInput) -> dict[str, float | str]:
        """Generate full recommendation output for a property."""
        features = {
            "beds": property_input.beds,
            "baths": property_input.baths,
            "sqft": property_input.sqft,
            "list_price": property_input.list_price,
        }

        fair_value = estimate_fair_value(
            list_price=property_input.list_price,
            neighborhood_price_per_sqft=property_input.neighborhood_price_per_sqft,
            sqft=property_input.sqft,
        )
        appreciation = self.price_predictor.forecast_horizons(features)
        expected_rent = self.rent_predictor.predict_monthly_rent(features)
        downside_risk = self.risk_model.predict_downside_risk(features)

        annual_rent = expected_rent * 12
        rental_yield = annual_rent / property_input.list_price if property_input.list_price else 0.0
        valuation_discount = (fair_value - property_input.list_price) / property_input.list_price if property_input.list_price else 0.0

        score = self.score_engine.compute_score(
            appreciation_12m=appreciation["appreciation_12m"],
            rental_yield=rental_yield,
            downside_risk=downside_risk,
            valuation_discount=valuation_discount,
        )
        label = self.score_engine.label(score)

        return {
            "address": property_input.address,
            "fair_value": round(fair_value, 2),
            "appreciation_3m": round(appreciation["appreciation_3m"], 4),
            "appreciation_6m": round(appreciation["appreciation_6m"], 4),
            "appreciation_12m": round(appreciation["appreciation_12m"], 4),
            "expected_monthly_rent": round(expected_rent, 2),
            "rental_yield": round(rental_yield, 4),
            "downside_risk": round(downside_risk, 4),
            "investment_score": score,
            "recommendation_label": label,
        }
