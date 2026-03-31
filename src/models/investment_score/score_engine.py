"""Investment score construction and recommendation mapping."""

from __future__ import annotations

from config.constants import RecommendationThresholds, ScoreWeights


class InvestmentScoreEngine:
    """Combines model outputs into a normalized score (0-100)."""

    def __init__(self) -> None:
        self.weights = ScoreWeights()
        self.thresholds = RecommendationThresholds()

    @staticmethod
    def _clip(value: float, low: float, high: float) -> float:
        return max(low, min(value, high))

    def compute_score(
        self,
        appreciation_12m: float,
        rental_yield: float,
        downside_risk: float,
        valuation_discount: float,
    ) -> float:
        """Compute weighted investment score from key components."""
        appreciation_component = self._clip(appreciation_12m / 0.15, 0, 1)
        yield_component = self._clip(rental_yield / 0.08, 0, 1)
        risk_component = 1 - self._clip(downside_risk, 0, 1)
        valuation_component = self._clip(valuation_discount / 0.2, 0, 1)

        raw = (
            self.weights.appreciation * appreciation_component
            + self.weights.rental_yield * yield_component
            + self.weights.downside_risk * risk_component
            + self.weights.valuation_discount * valuation_component
        )
        return round(raw * 100, 2)

    def label(self, score: float) -> str:
        """Map score to recommendation label."""
        if score >= self.thresholds.strong_buy:
            return "strong buy"
        if score >= self.thresholds.buy_with_caution:
            return "buy with caution"
        if score >= self.thresholds.hold_monitor:
            return "hold/monitor"
        return "avoid"
