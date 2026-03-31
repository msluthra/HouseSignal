"""Fair market value estimation engine."""

from __future__ import annotations


def estimate_fair_value(
    list_price: float,
    neighborhood_price_per_sqft: float,
    sqft: float,
    condition_adjustment: float = 0.0,
) -> float:
    """Estimate fair value using comp-based baseline and condition adjustment."""
    comp_value = neighborhood_price_per_sqft * sqft
    blended = 0.6 * comp_value + 0.4 * list_price
    return round(blended * (1 + condition_adjustment), 2)
