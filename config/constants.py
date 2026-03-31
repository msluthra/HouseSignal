"""Global constants for investment scoring and recommendation labeling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreWeights:
    """Weights used to build the composite investment score."""

    appreciation: float = 0.35
    rental_yield: float = 0.30
    downside_risk: float = 0.20
    valuation_discount: float = 0.15


@dataclass(frozen=True)
class RecommendationThresholds:
    """Score thresholds for recommendation labels."""

    strong_buy: float = 80.0
    buy_with_caution: float = 65.0
    hold_monitor: float = 50.0


DEFAULT_CAP_RATE_BENCHMARK = 0.045
MONTHS_IN_YEAR = 12
