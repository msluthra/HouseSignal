"""Tests for advisor orchestration logic."""

from __future__ import annotations

from src.advisor.investment_advisor import InvestmentAdvisor, PropertyInput


def test_investment_advisor_evaluate_returns_expected_schema() -> None:
    advisor = InvestmentAdvisor()
    payload = PropertyInput(
        address="123 Main St, San Jose, CA",
        list_price=850000,
        beds=3,
        baths=2,
        sqft=1500,
        neighborhood_price_per_sqft=550,
    )

    result = advisor.evaluate(payload)

    expected_keys = {
        "address",
        "fair_value",
        "appreciation_3m",
        "appreciation_6m",
        "appreciation_12m",
        "expected_monthly_rent",
        "rental_yield",
        "downside_risk",
        "investment_score",
        "recommendation_label",
    }

    assert set(result.keys()) == expected_keys
    assert result["address"] == payload.address
    assert isinstance(result["investment_score"], float)
    assert result["recommendation_label"] in {
        "strong buy",
        "buy with caution",
        "hold/monitor",
        "avoid",
    }
