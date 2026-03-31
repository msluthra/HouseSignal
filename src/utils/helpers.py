"""General-purpose helper utilities."""

from __future__ import annotations


def safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide two numbers and return 0 when denominator is 0."""
    if denominator == 0:
        return 0.0
    return numerator / denominator
